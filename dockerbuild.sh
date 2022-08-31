#!/bin/bash
SYSTEM_TYPE=$(uname)
user=`id -n -u`
uid=`id -u`
GID=`id -g`

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
if [ -e "$SCRIPT_DIR/.hub_token" ]; then
    TOKEN=`cat "$SCRIPT_DIR/.hub_token"`
else
    TOKEN=""
fi
BUILD="latest"
MAC=""
for argwhole in "$@"; do
    IFS='=' read -r -a array <<< "$argwhole"
    arg="${array[0]}"
    val=$(printf "=%s" "${array[@]:1}")
    val=${val:1}
    case "$arg" in
        --hub_token) TOKEN="$val";;
        --build) BUILD="$val";;
        --mac) MAC="--mac-address $val"
    esac
done

if [ "$TOKEN" != "" ]; then
    if [ "$TOKEN" != "public" ]; then
        echo "$TOKEN" | docker login -u jferlez --password-stdin
        if [ $? != 0 ]; then
            echo "ERROR: Unable to login to DockerHub using available access token! Quitting..."
            exit 1
        fi
    fi
    docker pull jferlez/matlab_docker:$BUILD
    if [ $? != 0 ]; then
        echo "ERROR: docker pull command failed! Quitting..."
        exit 1
    fi
    PROCESSING="s/jferlez\/matlab_docker:latest/jferlez\/matlab_docker:$BUILD/"
    cd "$SCRIPT_DIR"
    echo "$TOKEN" > .hub_token
fi


cd "$SCRIPT_DIR"

if [ $SYSTEM_TYPE = "Darwin" ];
then
    CORES=$(( `sysctl -n hw.ncpu` / 2 ))
    PYTHON="python3.10"
else
    CORES_PER_SOCKET=`lscpu | grep "Core(s) per socket:" | sed -e 's/[^0-9]//g'`
    SOCKETS=`lscpu | grep "Socket(s):" | sed -e 's/[^0-9]//g'`
    CORES=$(( $CORES_PER_SOCKET * $SOCKETS ))
    PYTHON=""
fi

cat Dockerfile | sed -u -e $PROCESSING | docker build --no-cache --build-arg USER_NAME=$user --build-arg UID=$UID --build-arg GID=$GID --build-arg CORES=$CORES -t acc-matlab-pre:${user} -f- .

# Create a docker container with the correct mac address, so we can install nnv
docker create $MAC -it --name pre-nnv acc-matlab-pre:${user} ${user} $uid $GID 1
docker start pre-nnv

# install nnv
docker exec pre-nnv sudo -u ${user} sh -c "cd ~/tools/nnv/code/nnv && matlab -r \"install; addpath('/home/james/tools/nnv/code/nnv/engine/nnmt'); savepath; exit\""

docker commit pre-nnv acc23matlab-run:${user}
docker container stop pre-nnv
docker container rm pre-nnv