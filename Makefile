.PHONY: setup unittest integration-test test listen mypy all black

all: black test

setup:
	pipenv --dev

black:
	pipenv run black .

unittest:
	pipenv run nosetests tests

integration-test:
	./run_integration_tests.sh

mypy:
	pipenv run mypy . --ignore-missing-imports

test: mypy unittest integration-test

listen:
	pipenv run python ./application.py

