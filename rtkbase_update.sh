#!/bin/bash
### THIS SCRIPT SHOULD NOT BE RUN MANUALLY ###

#'shopt -s extglob' is needed for using (!pattern) exclusion pattern
#from inside a script
shopt -s extglob

#enable this line to send the script output to /var/log/syslog.
#exec 1> >(logger -s -t $(basename $0)) 2>&1

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

}

insert_rtcm_msg() {
# inserting new message inside a rtcm message list
# and "return" the new strings with the ${new_rtcm} global variable
# it will try to insert it a the lowest possible position


    local text_line=${1}
    local msg_to_insert=${2}
    local highest_msg=${3}
    local delay=${4}
    
    new_rtcm=''
    if [[ ! $(echo ${text_line} | grep ${msg_to_insert}) ]]
    then
        for (( i=${msg_to_insert}; i<=${highest_msg}; i++ ))
            do
                if [[ $(echo ${text_line} | grep $i) ]]
                then
                    echo 'insert '${msg_to_insert}' before '$i
                    new_rtcm=$(echo ${text_line} | sed 's|'"${i}"'|'"${msg_to_insert}${delay}"',&|')
                    #echo ${new_rtcm}
                    break
                fi
            done
    else
        #msg already inside the string
        return 1
    fi
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
  #systemctl stop rtkbase_web <- don't do that, it will kill this script process.
  systemctl stop str2str_tcp
  #Get Rtklib 2.4.3 b34 release
  wget -qO - https://github.com/tomojitakasu/RTKLIB/archive/v2.4.3-b34.tar.gz | tar -xvz
  #Install Rtklib app
  make --directory=RTKLIB-2.4.3-b34/app/consapp/str2str/gcc
  make --directory=RTKLIB-2.4.3-b34/app/consapp/str2str/gcc install
  make --directory=RTKLIB-2.4.3-b34/app/consapp/rtkrcv/gcc
  make --directory=RTKLIB-2.4.3-b34/app/consapp/rtkrcv/gcc install
  make --directory=RTKLIB-2.4.3-b34/app/consapp/convbin/gcc
  make --directory=RTKLIB-2.4.3-b34/app/consapp/convbin/gcc install
  #deleting RTKLIB
  rm -rf RTKLIB-2.4.3-b34/
  
  #restarting str2str_tcp service
  systemctl start str2str_tcp
  
  #update python module
  python3 -m pip install -r ${destination_directory}'/web_app/requirements.txt'
  
  #copying new service
  file_path=${destination_directory}'/unit/str2str_rtcm_serial.service'
  file_name=$(basename ${file_path})
  echo copying ${file_name}
  sed -e 's|{script_path}|'"$(dirname "$(readlink -f "$0")")"'|' -e 's|{user}|'"$(logname)"'|' ${file_path} > /etc/systemd/system/${file_name}
  systemctl daemon-reload

  #inserting new rtcm message 1008 and 1033 inside rtcm_msg and rtcm_svr_msg
  insert_rtcm_msg $(grep "^rtcm_msg=" ${destination_directory}/settings.conf) 1008 1042 '(10)' && \
      sed -i '/^rtcm_msg=/c\'"${new_rtcm}" ${destination_directory}/settings.conf
  insert_rtcm_msg $(grep "^rtcm_msg=" ${destination_directory}/settings.conf) 1033 1230 '(10)' && \
      sed -i '/^rtcm_msg=/c\'"${new_rtcm}" ${destination_directory}/settings.conf
  insert_rtcm_msg $(grep "^rtcm_svr_msg=" ${destination_directory}/settings.conf) 1008 1042 '(10)' && \
      sed -i '/^rtcm_svr_msg=/c\'"${new_rtcm}" ${destination_directory}/settings.conf
  insert_rtcm_msg $(grep "^rtcm_svr_msg=" ${destination_directory}/settings.conf) 1033 1230 '(10)' && \
      sed -i '/^rtcm_svr_msg=/c\'"${new_rtcm}" ${destination_directory}/settings.conf
  
  #restarting runnning rtcm services to send the new messages.
  systemctl is-active --quiet str2str_ntrip && systemctl restart str2str_ntrip
  systemctl is-active --quiet str2str_rtcm_svr && systemctl restart str2str_rtcm_svr

}

update
upd_${old_version}

echo "delete the line version= in settings.conf"
# The new version number will be imported from settings.conf.default during the web server startup.
sed -i '/version=/d' ${destination_directory}/settings.conf

#change rtkbase's content owner
chown -R ${standard_user}:${standard_user} ${destination_directory}

#if a reboot is needed
#sudo reboot now

echo "Restart web server"
sudo systemctl restart rtkbase_web.service


