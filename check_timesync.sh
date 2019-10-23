#!/bin/bash
#
# script to check if the system date & time is synced.
# It is used to be sure that the logfile name will be correct.

# if you want to use your gnss receiver to set time date and maybe use pps, you need
# to change this script to use ntpstat instead of timedatectl and modifying the str2str_file.service unit file dependencies
# to ntp.service or something else.

ntp_exit_code=1
while [ ${ntp_exit_code} -ne 0 ]
do
    sleep 1
    timedatectl show | grep 'NTPSynchronized=yes' > /dev/null
    ntp_exit_code=$?
done
exit 0
