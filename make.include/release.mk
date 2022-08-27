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
latest_release != $(RELEASE) -J latest

github-latest:
	@echo $(latest release)

# build a wheel file for the current version
.dist: $(project)/version.py
	$(call gitclean)
	@echo Building $(project)
	flit build
	[ -s $(current_wheel) ] && touch $@

.PHONY: dist 
dist: $(if $(DISABLE_TOX),,tox) .dist

## create a github release
$(current_release): dist
	$(call check_wheel)
	@set -e;\
	if [ $$($(RELEASE) -J latest) = $(version) ]; then \
	  echo "Version $(version) is already released"; \
	else \
	  echo "Creating $(project) release v$(version)..."; \
	  $(RELEASE) create --force >$@; \
	  $(RELEASE) upload --force >>$@; \
	fi

.PHONY: release
release: $(current_release)

# clean up the publish temp files
release-clean:
	rm -f .dist
