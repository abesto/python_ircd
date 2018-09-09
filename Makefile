.PHONY: setup unittest integration-test test listen mypy all black pylint update

all: black test

setup:
	pipenv install --dev

black:
	pipenv run black .

pylint:
	pipenv run pylint python_ircd

unittest:
	pipenv run python -m unittest

integration-test:
	pipenv run python -m unittest integration_tests.py

mypy:
	pipenv run mypy $(CURDIR) --ignore-missing-imports

test: mypy unittest integration-test

listen:
	pipenv run python ./application.py

update:
	pipenv update --pre  # The --pre is needed because of `black`
