#!/bin/bash

BASEDIR=$(dirname "$0")
datadir=$BASEDIR/data
cd ${datadir}

#archive and compress previous day's gnss data.
archive_name=$(date -d "-1 days" +"%Y-%m-%d_%S").tar.bz2
find . -maxdepth 1 -type f -mtime -1 -mmin +60 -name "*.ubx*" -exec tar -jcvf ${archive_name} --remove-files {} +;

#delete gnss data older than 30 days
find . -maxdepth 1 -type f -name "*.tar.bz2" -mtime +10 -delete
