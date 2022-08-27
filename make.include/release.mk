# create distributable files if sources have changed

current_wheel = $(shell ls 2>/dev/null dist/$(project)-$(version)-*.whl)
current_release = dist/$(project)-$(version)-release.json
repository != basename $(PWD)

$(if $(GITHUB_ORG),,$(error GITHUB_ORG is undefined))
$(if $(GITHUB_TOKEN),,$(error GITHUB_TOKEN is undefined))

RELEASE = release -d\
  --organization $(GITHUB_ORG)\
  --repository $(repository)\
  --token $(GITHUB_TOKEN)\
  --module-dir ./$(project)\
  --wheel-dir ./dist\
  --version $(version) 

check_wheel = $(if $(shell [ -s $(current_wheel) ] && echo y),,$(error wheel file null or nonexistent))

latest_release_version = $(RELEASE) -J latest

### query github and output the latest release version
latest-github-release:
	@$(call latest_release_version)

testo:
	rm -rf dist
	[ -n "$(call current_wheel)" -a -s "$(call current_wheel)" ] && echo yup || echo nope
	flit build
	[ -n "$(call current_wheel)" -a -s "$(call current_wheel)" ] && echo yup || echo nope

.dist: $(project)/version.py
	$(call gitclean)
	mkdir -p dist
	flit build

.PHONY: dist 
### build a wheel file for distribution
dist: $(if $(DISABLE_TOX),,tox)
	@echo Building $(current_wheel)...
	@[ -s "$(call current_wheel)" ] && echo "He's already got one." || $(MAKE) .dist 


$(current_release): dist
	$(call check_wheel)
	set -e;\
	if [ "$(call latest_release_version)" = "$(version)" ]; then \
	  echo "Version $(version) is already released"; \
	else \
	  echo "Creating $(project) release v$(version)..."; \
	  $(RELEASE) create --force >$@; \
	  $(RELEASE) upload --force >>$@; \
	fi

.PHONY: release
### create a github release and upload assets
release: $(current_release)

# clean up the release temp files
release-clean:
	rm -f .dist
