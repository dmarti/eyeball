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

if [[ $1 =~ ".py" ]]; then
	# Run any Python file in the container
	container_name=$(basename $1 .py)
	entrypoint=/usr/bin/env
	arg1=python3
	arg2=/srv/eyeball/$1
else
	# Local Flask
	container_name=$1
	entrypoint=/usr/local/bin/flask
	arg1=run
	arg2='--host=0.0.0.0'
fi

cp src/test_config.py src/config.py
docker build --tag=eyeball_$container_name .
docker run -p 5050:5050 \
        -e FLASK_APP=/srv/eyeball/webapp.py \
        -e FLASK_ENV=development \
	-e FLASK_RUN_PORT=5050 \
        -e LC_ALL=C.UTF-8 \
        -e LANG=C.UTF-8 \
	--volume "$(pwd)"/src:/srv/eyeball:ro,Z \
	--volume /var/cache/eyeball:/var/cache/eyeball:rw,Z \
	--entrypoint $entrypoint eyeball_$container_name $arg1 $arg2
