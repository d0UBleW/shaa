#!/bin/bash

docker rmi -f localhost/ubi8-init
docker rmi -f localhost/ubi9-init
docker build -f ./Dockerfile.rhel8 -t localhost/ubi8-init .
docker build -f ./Dockerfile.rhel9 -t localhost/ubi9-init .
