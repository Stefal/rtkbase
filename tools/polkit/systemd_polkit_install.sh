#!/bin/bash
#script to install the policykit rules which let manage the rtkbase services without root.
#the user needs to be member of rtkbase group
RTKBASE_USER=$1
[[ -z "${RTKBASE_USER}" ]] && echo 'Please specify a username' && exit 1
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
apt-get install -y policykit-1
mkdir -p /etc/polkit-1/rules.d/
cp "${SCRIPT_DIR}"/*.rules /etc/polkit-1/rules.d/

groupadd -f rtkbase
usermod -a -G rtkbase "${RTKBASE_USER}"