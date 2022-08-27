# create distributable files if sources have changed

current_wheel=dist/$(project)-$(version)-*.whl
current_release=dist/$(project)-$(version)-release.json

RELEASE = release\
  --organization $(organization)\
  --repository $(repo)\
  --token $(GITHUB_TOKEN)\
  --module-dir ./$(project)\
  --wheel-dir ./dist\
  --version $(version) 

check_wheel = $(if $(shell [ -s $(current_wheel) ] && echo y),,$(error wheel file null or nonexistent))
latest_release_version != $(RELEASE) -J latest

.dist: $(project)/version.py
	mkdir -f dist
	$(call gitclean)
	@echo Building $(project)
	flit build
	[ -s $(current_wheel) ] && touch $@

.PHONY: dist 
### build a wheel file for distribution
dist: $(if $(DISABLE_TOX),,tox) .dist

$(current_release): dist
	$(call check_wheel)
	@set -e;\
	if [ $(latest_release_version) = $(version) ]; then \
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