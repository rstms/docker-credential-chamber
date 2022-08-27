# version - automatic version management
 
# - Prevent version changes with uncommited changes
# - tag and commit version changes
# - Use 'lightweight tags'

bumpversion = bumpversion --allow-dirty $(1)

## bump patch level
bump-patch: version-update
	$(call bumpversion,patch)
	git add requirements*.txt
	git push

## bump minor version, reset patch to zero
bump-minor: version-update
	$(call bumpversion,minor)
	git add requirements*.txt
	git push
	
## bump version, reset minor and patch to zero
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

# clean up version tempfiles
version-clean:
	@:

