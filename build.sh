#!/usr/bin/env bash

IMAGE_NAME=shaa

docker rmi -f "${IMAGE_NAME}"

docker build -f ./Dockerfile -t "${IMAGE_NAME}" .
