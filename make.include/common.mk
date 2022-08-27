# common - initialization, variables, functions

project != toml2json <pyproject.toml | jq -r .project.name
repo != basename $$(pwd)
organization = rstms
registry = $(GITHUB_REGISTRY)
branch != git branch | awk '/\*/{print $$2}'
version != awk <$(project)/version.py -F\" '/^__version__/{print $$2}'
python_src != find . -name \*.py
other_src := $(call makefiles) pyproject.toml
src := $(python_src) $(other_src)

### list make targets with descriptions
help:	
	@set -e;\
	/bin/echo -e '\nmake targets:\n';\
	for FILE in $(call makefiles); do\
	  awk <$$FILE  -F':' '\
	    /^###.*/ { help=$$0; }\
	    /^[a-z-]*:/ { if (last==help){ printf("%-16s %s\n", $$1, substr(help,4));} }\
	    /.*/{ last=$$0 }\
	  ';\
	done
	
help-table:
	$(MAKE) help | awk -F'#' \
	  'BEGIN{ first=1; print ".TS"; print "tab(#),box,nowarn;" } \
	  /^#/{ if(first){ first=0; } else { print ".T&"; print "_ _"; } \
	  print "cw(1i) s"; print "_ _"; print "c | l ."; print $$2; next; } \
	  {print} END{print ".TE";}' |\
	tbl | groff  -T utf8 | awk 'NF';


# generate a random hex string 
genkey:
	@python -c 'import secrets; print(secrets.token_hex())'

#
# --- functions ---
#

# break with an error if there are uncommited changes
define gitclean =
	$(if $(and $(if $(DIRTY),,1),$(shell git status --porcelain)),$(error git status: dirty, commit and push first))
endef


# remove terminal color escape codes
monochrome = sed -e 's/\x1B\[[0-9;]*[JKmsu]//g;' 

# require user confirmation   example: $(call verify_action,do something destructive)
define verify_action =
	$(if $(shell \
	  read -p 'Ready to $(1). Confirm? [no] :' OK;\
	  echo $$OK|grep '^[yY][eE]*[sS]*$$'
	),$(info Confirmed),$(error Cowardy refusing))
endef

# generate a list of makefiles
makefiles = Makefile $(wildcard make.include/*.mk)

# return a list of matching include makefile targets
included = $(foreach file,$(makefiles),$(shell sed <$(file) -n 's/^\([[:alnum:]_-]*-$(1)\):.*/\1/p;'))

# break if not in virtualenv (override with make require_virtualenv=no <TARGET>)
ifndef virtualenv
  virtualenv = $(if $(filter $(require_virtualenv),no),not required,$(shell which python | grep -E virt\|venv))
  $(if $(virtualenv),,$(error virtualenv not detected))
endif
