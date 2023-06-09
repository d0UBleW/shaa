#!/usr/bin/env bash

IMAGE_NAME="d0ublew/shaa"
TAG="${1:-latest}"

# docker rmi -f "${IMAGE_NAME}"

docker build -f ./Dockerfile \
    -t "${IMAGE_NAME}:${TAG}" \
    -t "${IMAGE_NAME}:latest" \
    .
