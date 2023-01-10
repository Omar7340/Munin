#!/bin/bash

# check si permission root
if ! [ $(id -u) = 0 ]; then
   echo "Relancer en root."
   exit 1
fi

/bin/bash ./scripts/install_utils.sh
/bin/bash ./scripts/install_docker.sh