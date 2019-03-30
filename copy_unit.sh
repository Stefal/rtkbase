#!/bin/bash
#
# Script to add the user path and copy unit services to the correct location.

for file_path in $(pwd)/unit/*.service
do
    file_name=$(basename ${file_path})
    echo copying ${file_name}
    sed -e 's|{user_home}|'"${HOME}"'|' ${file_path} > /etc/systemd/system/${file_name}
done

systemctl daemon-reload
