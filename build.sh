#!/usr/bin/env bash

IMAGE_NAME="d0ublew/shaa"

docker rmi -f "${IMAGE_NAME}"

docker build -f ./Dockerfile.alpine -t "${IMAGE_NAME}" .
