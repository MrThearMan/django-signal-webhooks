export DJANGO_SETTINGS_MODULE = tests.project.settings

.PHONY: help
.PHONY: dev
.PHONY: docs
.PHONY: tests
.PHONY: test
.PHONY: tox
.PHONY: hook
.PHONY: lint
.PHONY: mypy
.PHONY: Makefile

# Trick to allow passing commands to make
# Use quotes (" ") if command contains flags (-h / --help)
args = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

# If command doesn't match, do not throw error
%:
	@:

define helptext

  Commands:

  dev                  Serve manual testing server
  docs                 Serve mkdocs for development.
  tests                Run all tests with coverage.
  test <name>          Run all tests maching the given <name>
  tox <args>           Run all tests with tox.
  hook                 Install pre-commit hook.
  lint                 Run pre-commit hooks on all files.
  mypy                 Run mypy on all files.

  Use quotes (" ") if command contains flags (-h / --help)
endef

export helptext

help:
	@echo "$$helptext"

dev:
	@poetry run python manage.py runserver localhost:8000

docs:
	@poetry run mkdocs serve -a localhost:8080

tests:
	@poetry run coverage run -m pytest -m "not e2e"

test:
	@poetry run pytest -m "not e2e" -k $(call args, "")

tox:
	@poetry run tox $(call args, "")

hook:
	@poetry run pre-commit install

lint:
	@poetry run pre-commit run --all-files

mypy:
	@poetry run mypy django_signal_webhooks/
