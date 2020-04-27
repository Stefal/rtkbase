#!/bin/bash

### THIS SCRIPT SHOULD NOT BE RUN MANUALLY ###

destination_directory=$1
data_dir=$2

#remove existing rtkbase.old directory
rm -rf /var/tmp/rtkbase.old
mkdir /var/tmp/rtkbase.old

#copy rtkbase to rtkbase.old except /data directory
cp -r ${destination_directory}/!({data_dir}) /var/tmp/rtkbase.old

#copy new release to destination
cp -rf ${destination_directory}


#if a reboot is needed
#sudo reboot now

#if a reboot isn't needed
#sudo systemctl restart rtkbase_web.service


