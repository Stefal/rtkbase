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
# The new version number will be imported from settings.conf.default during the web server startup.
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

upd_2.1.0() {
  upd_2.1.1
}

upd_2.1.1() {
  #stopping services to copy new rtklib app
  systemctl stop rtkbase_web
  systemctl stop str2str_tcp
  #Get Rtklib 2.4.3 b34 release
  wget -qO - https://github.com/tomojitakasu/RTKLIB/archive/v2.4.3-b34.tar.gz | tar -xvz
  #Install Rtklib app
  make --directory=RTKLIB-2.4.3-b34/app/str2str/gcc
  make --directory=RTKLIB-2.4.3-b34/app/str2str/gcc install
  make --directory=RTKLIB-2.4.3-b34/app/rtkrcv/gcc
  make --directory=RTKLIB-2.4.3-b34/app/rtkrcv/gcc install
  make --directory=RTKLIB-2.4.3-b34/app/convbin/gcc
  make --directory=RTKLIB-2.4.3-b34/app/convbin/gcc install
  #deleting RTKLIB
  rm -rf RTKLIB-2.4.3-b34/
  #restarting str2str_tcp service
  systemctl start str2str_tcp
  #update python module
  python3 -m pip install -r ${destination_directory}'/web_app/requirements.txt'
  #copying new service
  file_path=${destination_directory}'/unit/str2str_serial_rtcm.service'
  file_name=$(basename ${file_path})
    echo copying ${file_name}
    sed -e 's|{script_path}|'"$(dirname "$(readlink -f "$0")")"'|' -e 's|{user}|'"$(logname)"'|' ${file_path} > /etc/systemd/system/${file_name}
    systemctl daemon-reload
  
}

update
upd_${old_version}

#change rtkbase's content owner
chown -R ${standard_user}:${standard_user} ${destination_directory}

#if a reboot is needed
#sudo reboot now

echo "Restart web server"
sudo systemctl restart rtkbase_web.service


