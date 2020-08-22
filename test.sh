#!/bin/bash

# Remove the temp copy of config file and return to the
# original directory on exit.
cleanup(){
        rm -f src/config.py
        popd
}
trap 'cleanup' EXIT

pushd $PWD &> /dev/null
cd $(dirname "$0")

./run.sh test.py
