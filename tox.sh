#!/bin/bash
set -u
set -e
set -x

# Run test server
pserve demo.ini &

SERVER_PID=$!

# Even if tests crash make sure we quit pserve
trap "kill $SERVER_PID" EXIT

# Run functional test suite against test server
nosetests "$@"

exit 0
