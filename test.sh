#!/bin/bash

trap popd EXIT
pushd $PWD &> /dev/null
cd $(dirname "$0")

./run.sh test.py
