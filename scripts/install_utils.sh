#!/bin/bash

# check si permission root
if ! [ $(id -u) = 0 ]; then
   echo "Relancer en root."
   exit 1
fi

# mise a jour des paquets
apt update
apt --yes upgrade

# installation et configuration de git
apt --yes install git-all
git config --global user.name "repo_distant_momomar"
git config --global user.email "repo_distant_momomar@localhost"