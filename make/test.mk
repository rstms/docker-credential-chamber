# python test makefile 
test_cases := $(if $(test),-k $(test),)

ifndef EXTERNAL_SERVER
EXTERNAL_SERVER = 0
endif

test_env = chamber exec ethdev/test ethdev/api/streams -- env TESTING=1 DEBUG=1 EXTERNAL_SERVER=$(EXTERNAL_SERVER)

ifdef ENABLE_METADATA_IMPORT
pytest_opts := $(pytest_opts) --run_metadata
endif

ifdef ENABLE_SLOW_TESTS
pytest_opts := $(pytest_opts) --run_slow
endif

ifdef SHOW_FIXTURES
pytest_opts := $(pytest_opts) --setup-show
endif


### list tests
testls:
	@testls

### regression test
test: fmt
	$(test_env) pytest $(pytest_opts) --log-cli-level=WARNING $(test_cases)

### pytest with break to debugger
debug: fmt
	$(test_env) DEBUG=1 pytest $(pytest_opts) -sv --pdb --log-cli-level=INFO $(test_cases)

### check code coverage quickly with the default Python
coverage:
	coverage run --source $(module) -m pytest
	coverage report -m

# tox dependency sources
tox-src = $(filter-out $(module)/version.py,$(python_src))

.tox: $(tox-src) tox.ini
	$(if $(DISABLE_TOX),@echo 'tox is disabled',$(test_env) tox)

### run tests under tox
tox: .tox

tox-clean:
	rm -rf .tox

test-clean: tox-clean
	rm -f .coverage

test-sterile: test-clean
	@:
