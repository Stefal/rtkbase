#!/bin/bash
#
# Script to add the user name and user path in unit file
# then copy these services to the correct location.

BASEDIR=$(dirname "$0")

for file_path in ${BASEDIR}/unit/*.service ${BASEDIR}/unit/*.timer
do
    file_name=$(basename ${file_path})
    echo copying ${file_name}
    sed -e 's|{script_path}|'"$(dirname "$(readlink -f "$0")")"'|' -e 's|{user}|'"$(logname)"'|' ${file_path} > /etc/systemd/system/${file_name}
done

systemctl daemon-reload
