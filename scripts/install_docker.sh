#!/bin/bash

# check si permission root
if ! [ $(id -u) = 0 ]; then
   echo "Relancer en root."
   exit 1
fi

# Efface toute presence prealable d'une installation docker
apt remove docker docker-engine docker.io containerd runc

apt update
# allow apt to use a repository over HTTPS
apt --yes install ca-certificates curl gnupg lsb-release

# Ajoute la cle GPG officiel de Docker
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Ajout du repository Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# mise a jour des sources
apt update

#installation de Docker et Docker-Compose
apt --yes install docker-ce docker-ce-cli containerd.io docker-compose-plugin
apt --yes install docker-compose-plugin