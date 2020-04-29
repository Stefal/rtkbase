#!/bin/bash

### THIS SCRIPT SHOULD NOT BE RUN MANUALLY ###

destination_directory=$1
data_dir=$2

#remove existing rtkbase.old directory
rm -rf /var/tmp/rtkbase.old
mkdir /var/tmp/rtkbase.old

#copy rtkbase to rtkbase.old except /data directory
#'shopt -s extglob' is needed for using (!pattern) exclusion pattern
#from inside a script
shopt -s extglob
cp -r ${destination_directory}/!(${data_dir}) /var/tmp/rtkbase.old

#copy new release to destination
cp -rfp * ${destination_directory}

#delete the line version= in settings.conf
sed -i '/version=/d' ${destination_directory}/settings.conf
#if a reboot is needed
#sudo reboot now

#if a reboot isn't needed
sudo systemctl restart rtkbase_web.service


