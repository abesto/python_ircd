#!/bin/bash
server='python ./application.py'
$server > integration_test_server.log 2>&1 &
sleep 1
nosetests integration_tests.py $@
kill '%$server'
