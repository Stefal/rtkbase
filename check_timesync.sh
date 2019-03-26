#!/bin/bash
#
# script to check if the system date & time is synced with a ntp server or something else (ie gnss receiver).

ntp_exit_code=1
while [ ${ntp_exit_code} -ne 0 ]
do
    sleep 1
    ntpstat > /dev/null
    ntp_exit_code=$?
done
exit 0
