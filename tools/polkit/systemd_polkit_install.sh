#!/bin/bash
#script to install the policykit rules which let manage the rtkbase services without root.
#the user needs to be member of rtkbase group
RTKBASE_USER=$1

apt install policykit-1
mkdir /etc/polkit-1/rules.d/
cp ./*.rules /etc/polkit-1/rules.d/

groupadd rtkbase
usermod -a -G rtkbase "${RTKBASE_USER}"