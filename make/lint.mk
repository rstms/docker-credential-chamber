# python lint makefile

lint_line_length = 120
lint_python_version = 310

.fmt: $(python_src)
	isort --py $(lint_python_version) --profile black $(src_dirs)
	black --target-version py$(lint_python_version) --line-length $(lint_line_length) $(src_dirs)
	flake8 --max-line-length $(lint_line_length) $(src_dirs)
	touch $@

### format source and lint
fmt:	.fmt

### vim autofix
fix:
	fixlint $(src_dirs)

lint-clean:
	rm -f .black .flake8 .errors .fmt

lint-sterile:
	@:
