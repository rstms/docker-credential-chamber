# version - automatic version management
 
# - Prevent version changes with uncommited changes
# - tag and commit version changes
# - Use 'lightweight tags'

bumpversion = bumpversion --allow-dirty $(1)

### bump patch version
bump-patch: version-update
	$(call bumpversion,patch)
	git add requirements*.txt
	git push

### bump minor version, reset patch to zero
bump-minor: version-update
	$(call bumpversion,minor)
	git add requirements*.txt
	git push
	
### bump major version, reset minor and patch to zero
bump-major: version-update
	$(call bumpversion,major)
	git add requirements*.txt
	git push

# assert gitclean, rewrite requirements.txt, update timestamp, apply version update
version-update:
	$(call gitclean)
	$(MAKE) requirements.txt
	sed -E -i $(project)/version.py -e "s/(.*__timestamp__.*=).*/\1 \"$$(date --rfc-3339=seconds)\"/"
	git add $(project)/version.py
	@echo "Updated version.py timestamp and requirements.txt"

.bumpversion.cfg: 
	echo $(BUMPVERSION_CFG) >$@

# clean up version tempfiles
version-clean:
	@:

define BUMPVERSION_CFG
[bumpversion]
current_version = $(version)
commit = True
tag = True
[bumpversion:file:$(project)/version.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"
endef
