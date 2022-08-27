# test - testing with pytest and tox

options ?= -x --log-cli-level=CRITICAL
testfiles ?= $(wildcard tests/test_*.py)
options := $(if $(test),$(options) -k $(test),$(options))


# run pytest;  example: make options=-svvvx test=cli test 
test:
	$(chamber) exec ethdev/test -- env TESTING=1 pytest $(options) $(testfiles)

# run pytest, dropping into pdb on exceptions or breakpoints
debug:
	${MAKE} options="$(options) --log-cli-level=INFO -xvvvs --pdb" test

# check code coverage quickly with the default Python
coverage:
	env TESTING=1 coverage run --source $(project) -m pytest
	coverage report -m
	coverage html
	$(browser) htmlcov/index.html

# show available test cases
testls:
	@grep -h -R '^def test_' tests/test_*.py | awk -F'[ (]' '{print $$2}' | sort | uniq

# test with tox if sources have changed
.PHONY: tox
tox: .tox 
.tox: $(src) tox.ini
	chamber exec ethdev/test -- env PYTEST='$(if $(TOX_DEBUG),pytest -vvvs -o log_cli_level=INFO --pdb,pytest)' tox
	@touch $@

debugtox:
	$(MAKE) TOX_DEBUG=1 tox

test-clean:
	rm -f tests/data/server_root/templates/*.sol
	rm -rf .tox
