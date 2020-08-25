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

dockerfail() {
	echo
	echo "Docker not found. Check that Docker is installed and running."
	echo 'See the "Getting Started" section of README.md for more info.'
	echo
	exit 1
}
docker ps &> /dev/null || dockerfail

set -e
set -x

sudo chown -R root.www /var/cache/eyeball
sudo chmod -R g+w /var/cache/eyeball/*

container_name=$(basename $1 .py)
cp src/test_config.py src/config.py
docker build --tag=eyeball_$container_name .
docker run --volume "$(pwd)"/src:/srv/eyeball:ro,Z \
	--volume /var/cache/eyeball:/var/cache/eyeball:rw,Z \
	--entrypoint "/usr/bin/env" eyeball_$container_name python3 /srv/eyeball/$1
