#!/bin/bash
#script to install the policykit rules which let manage the rtkbase services without root.
#the user needs to be member of rtkbase group

RTKBASE_USER=$1
[[ -z "${RTKBASE_USER}" ]] && echo 'Please specify a username' && exit 1
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

add_polkit_rules() {
  cp "${SCRIPT_DIR}"/*.rules /etc/polkit-1/rules.d/ && \
  groupadd -f rtkbase                               && \
  usermod -a -G rtkbase "${RTKBASE_USER}"
}

#check if polkitd package is available, else exit
apt-cache --quiet=0 show polkitd 2>&1 | grep 'No packages found' && exit 1
#install it if not already installed
! dpkg-query -W --showformat='${Status}\n' polkitd >/dev/null 2>&1 && apt-get -y install polkitd
add_polkit_rules