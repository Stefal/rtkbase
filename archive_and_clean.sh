#!/bin/bash
#This script should be run from a crontab
#You can customize archive_name and archive_rotate in settings.conf

BASEDIR=$(dirname "$0")
source <( grep = ${BASEDIR}/settings.conf )
cd ${datadir}

#archive and compress previous day's gnss data.
#find . -maxdepth 1 -type f -mtime -1 -mmin +60 -name "*.ubx*" -exec tar -jcvf ${archive_name} --remove-files {} +;
find . -maxdepth 1 -type f -mtime -1 -mmin +60 -name "*.ubx*" -exec zip -m9 ${archive_name} {} +;

#delete gnss data older than x days.
#find . -maxdepth 1 -type f -name "*.tar.bz2" -mtime +${archive_rotate} -delete
find . -maxdepth 1 -type f -name "*.zip" -mtime +${archive_rotate} -delete

