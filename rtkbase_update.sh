#!/bin/bash
### THIS SCRIPT SHOULD NOT BE RUN MANUALLY ###

#'shopt -s extglob' is needed for using (!pattern) exclusion pattern
#from inside a script
shopt -s extglob

source_directory=$1
destination_directory=$2
data_dir=$3
old_version=$4
standard_user=$5

update() {
echo "remove existing rtkbase.old directory"
rm -rf /var/tmp/rtkbase.old
mkdir /var/tmp/rtkbase.old

echo "copy rtkbase to rtkbase.old except /data directory"
cp -r ${destination_directory}/!(${data_dir}) /var/tmp/rtkbase.old

echo "copy new release to destination"
cp -rfp ${source_directory}/. ${destination_directory}

echo "delete the line version= in settings.conf"
sed -i '/version=/d' ${destination_directory}/settings.conf
}

upd_2.0.2() {
  if [[ $(grep -E "^receiver_format='ubx'" ${destination_directory}/settings.conf) ]]
  then
    # Add -TAJD=1 option to rtcm/ntrip output for ublox receivers
    grep -q "^ntrip_receiver_options" ${destination_directory}/settings.conf || \
      sed -i "/^rtcm_msg=.*/a ntrip_receiver_options='-TADJ=1'" ${destination_directory}/settings.conf
    grep -q "^rtcm_receiver_options" ${destination_directory}/settings.conf || \
      sed -i "/^rtcm_svr_msg=.*/a rtcm_receiver_options='-TADJ=1'" ${destination_directory}/settings.conf
  fi
  #upd_2.0.4
}

update
upd_${old_version}

#change rtkbase's content owner
chown -R ${standard_user}:${standard_user} ${destination_directory}

#if a reboot is needed
#sudo reboot now

echo "Restart web server"
sudo systemctl restart rtkbase_web.service


