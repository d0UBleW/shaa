#!/bin/bash

docker rmi -f localhost/ubi8-init
docker rmi -f localhost/ubi9-init
docker rmi -f localhost/almalinux8-init
docker rmi -f localhost/almalinux9-init
docker rmi -f localhost/debian-bullseye-systemd
docker rmi -f localhost/ubuntu-20.04-systemd
docker rmi -f localhost/opensuse-tumbleweed-systemd

docker build -f ./Dockerfile.rhel8 -t localhost/ubi8-init .
docker build -f ./Dockerfile.rhel9 -t localhost/ubi9-init .
docker build -f ./Dockerfile.almalinux8 -t localhost/almalinux8-init .
docker build -f ./Dockerfile.almalinux9 -t localhost/almalinux9-init .
docker build -f ./Dockerfile.debian -t localhost/debian-bullseye-systemd .
docker build -f ./Dockerfile.ubuntu -t localhost/ubuntu-20.04-systemd .
docker build -f ./Dockerfile.opensuse -t localhost/opensuse-tumbleweed-systemd .
