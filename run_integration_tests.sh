#!/bin/bash

set -xeuo pipefail

pipenv run python ./application.py 2>&1 > integration_test_server.log &
trap "kill '%pipenv run python ./application.py'" EXIT
sleep 1
pipenv run nosetests integration_tests.py $@
