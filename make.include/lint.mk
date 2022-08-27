# lint / source format

lint_src = $(project) tests docs

_fmt:
	isort $(lint_src)
	black $(lint_src)

_lint:
	flake8 --config tox.ini $(lint_src)

## reformat python source with black; check style, lint with flake8
fmt: _fmt _lint

# alias for fmt
lint: fmt

# vim:ft=make
