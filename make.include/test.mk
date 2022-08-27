# test - testing with pytest and tox

options ?= -x --log-cli-level=CRITICAL
testfiles ?= $(wildcard tests/test_*.py)
options := $(if $(test),$(options) -k $(test),$(options))


### run tests;  example: make options=-svvx test=cli test 
test:
	env TESTING=1 pytest $(options) $(testfiles)

### run tests; drop into pdb on exceptions or breakpoints
debug:
	${MAKE} options="$(options) --log-cli-level=INFO -xvvvs --pdb" test

### check code coverage quickly with the default Python
coverage:
	env TESTING=1 coverage run --source $(project) -m pytest
	coverage report -m
	coverage html
	$(browser) htmlcov/index.html

### list test cases
testls:
	@grep -h -R '^def test_' tests/test_*.py | awk -F'[ (]' '{print $$2}' | sort | uniq

.PHONY: tox
### test with tox if sources have changed
tox: .tox 
.tox: $(src) tox.ini
	env PYTEST='$(if $(TOX_DEBUG),pytest -vvvs -o log_cli_level=INFO --pdb,pytest)' tox
	@touch $@

# run tox in debug mode
debugtox:
	$(MAKE) TOX_DEBUG=1 tox

test-clean:
	rm -rf .tox
