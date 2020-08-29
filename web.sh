#!/bin/bash

trap popd EXIT
pushd $PWD &> /dev/null
cd $(dirname "$0")

rm -rf src/__pycache__
./run.sh web
