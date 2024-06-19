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
checking=$6

#argument checking
[[ -d "${source_directory}" ]] || { echo 'ERROR! source_directory is not a directory'; exit 1; }
[[ -d "${destination_directory}" ]] || { echo 'ERROR! destination_directory is not a directory'; exit 1; }
#[[ -d "${data_dir}" ]] || { echo 'ERROR! data_dir is not a directory'; exit 1; } <- not a full path directory, just the directory name
#[[ "${old_version}" =~ ^[+-]?[0-9]+\.?[0-9]*$ ]] || { echo 'ERROR! wrong type for current_version variable'; exit 1; } <- doesn't work for 2.5.0 or 2.4b
[[ $(id -u "${standard_user}") ]] &>/dev/null || { echo 'ERROR! user does not exist'; exit 1; }
# $checking variable doesn't need to be checked as it is used only if it is set to '--checking'

#store service status before upgrade
str2str_active=$(systemctl is-active str2str_tcp)
str2str_ntrip_A_active=$(systemctl is-active str2str_ntrip_A)
str2str_ntrip_B_active=$(systemctl is-active str2str_ntrip_B)
str2str_local_caster=$(systemctl is-active str2str_local_ntrip_caster)
str2str_rtcm=$(systemctl is-active str2str_rtcm_svr)
str2str_serial=$(systemctl is-active str2str_rtcm_serial)
str2str_file=$(systemctl is-active str2str_file)
rtkrcv_raw2nmea=$(systemctl is-active rtkbase_raw2nmea)

check_before_update() {
  TOO_OLD='<b>You'"'"'re Operating System is too old!</b>\n
    Please reflash your SDCard with a more recent RTKBase image, or upgrade your OS.\n
    Don'"'"'t forget to backup your settings.\n\n
    <a href="https://github.com/Stefal/rtkbase" target="_blank">RTKBase repository</a>\n\n
    <a href="https://docs.centipede.fr/docs/base/Installation.html" target="_blank">Documentation CentipedeRTK</a>'

  if [[ -f /etc/os-release ]]
    then
      source /etc/os-release
    else
      printf "Warning! We can't check your Os release, upgrade at your own risk\n"      
  fi

  case $ID in
    debian)
      if (( $(echo "$VERSION_ID < 11" | bc -l) ))
      then
        printf "${TOO_OLD}" >/dev/stderr
        exit 1
      fi
      ;;
    raspbian)
    if (( $(echo "$VERSION_ID < 11" | bc -l) ))
      then
        printf "${TOO_OLD}" >/dev/stderr
        exit 1
      fi
      ;;
    ubuntu)
      if (( $(echo "$VERSION_ID < 22.04" | bc -l) ))
      then
        printf "${TOO_OLD}" >/dev/stderr
        exit 1
      fi
      ;;
  esac
}

update() {
echo 'remove existing rtkbase.old directory'
rm -rf /var/tmp/rtkbase.old
mkdir /var/tmp/rtkbase.old

echo "copy rtkbase to rtkbase.old except /data directory"
cp -r ${destination_directory}/!(${data_dir}|venv) /var/tmp/rtkbase.old

#Don't do that or it will stop the update process
#systemctl stop rtkbase_web.service

echo "copy new release to destination"
if [[ -d ${source_directory} ]] && [[ -d ${destination_directory} ]] 
  then
    cp -rfp ${source_directory}/. ${destination_directory}
  else
    echo 'can t copy'
    exit 1
fi
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
    if [[ ! $(echo ${text_line} | grep -q ${msg_to_insert}) ]]
    then
        for (( i=${msg_to_insert}; i<=${highest_msg}; i++ ))
            do
                if [[ $(echo ${text_line} | grep -q $i) ]]
                then
                    echo 'insert '${msg_to_insert}' before '$i
                    new_rtcm=$(echo ${text_line} | sed 's|'"${i}"'|'"${msg_to_insert}${delay}"',&|')
                    echo ${new_rtcm}
                    break
                fi
            done
    else
        #msg already inside the string
        return 1
    fi
 }

upgrade_rtklib() {
  systemctl stop str2str_tcp
  systemctl stop rtkbase_raw2nmea
  bin_path=$(dirname "$(command -v str2str)")
  rm "${bin_path}"'/str2str' "${bin_path}"'/rtkrcv' "${bin_path}"'/convbin'
  "${destination_directory}"'/tools/install.sh' --user "${standard_user}" --rtklib
}

upd_2.4.0() {
  echo '####################'
  echo 'Update from 2.4.0'
  echo '####################'
  upd_2.4.1 "$@"
}

upd_2.4.1() {
  echo '####################'
  echo 'Update from 2.4.1'
  echo '####################'
  upd_2.4.2 "$@"
}

upd_2.4.2() {
  echo '####################'
  echo 'Update from 2.4.2'
  echo '####################'
  apt-get update -y --allow-releaseinfo-change
  apt-get --fix-broken install # needed for old installation (raspi image v2.1 from july 2020)
  # only for Orange Pi Zero, disable sysstats-collect (https://github.com/Stefal/build/issues/14)
  # and update hostapd if error (https://github.com/Stefal/build/issues/15)
  computer_model=$(tr -d '\0' < /sys/firmware/devicetree/base/model)
  sbc_array=('Xunlong Orange Pi Zero')
    if printf '%s\0' "${sbc_array[@]}" | grep -Fxqz -- "${computer_model}"
      then
        echo 'Masking sysstat-collect.timer service and upgrading hostapd'
        systemctl mask sysstat-collect.timer
        dpkg -s hostapd | grep -q 'Version: 2:2.9' && apt-get upgrade -y hostapd
        rm -r /var/log/sysstat/
    fi
  # end of Orange Pi Zero section
  "${destination_directory}"/tools/install.sh --user "${standard_user}" --dependencies --rtkbase-requirements --unit-files
  #upgrade rtklib to b34h
  upgrade_rtklib
  #restart str2str if it was active before upgrading rtklib
  [ $str2str_active = 'active' ] && systemctl start str2str_tcp
  # restart previously running services
  [ $str2str_ntrip_A_active = 'active' ] && systemctl start str2str_ntrip_A
  [ $str2str_ntrip_B_active = 'active' ] && systemctl start str2str_ntrip_B  
  [ $str2str_local_caster = 'active' ] && systemctl start str2str_local_ntrip_caster
  [ $str2str_rtcm = 'active' ] && systemctl start str2str_rtcm_svr
  [ $str2str_serial = 'active' ] && systemctl start str2str_rtcm_serial
  [ $str2str_file = 'active' ] && systemctl start str2str_file
  return 0
}

upd_2.5.0 () {
  # only for Orange Pi Zero, update armbian-ramlog (https://github.com/Stefal/build/issues/16)
  computer_model=$(tr -d '\0' < /sys/firmware/devicetree/base/model)
  sbc_array=('Xunlong Orange Pi Zero')
    if printf '%s\0' "${sbc_array[@]}" | grep -Fxqz -- "${computer_model}" &&
       lsb_release -c | grep -qE 'bullseye|bookworm' &&
       grep -qE 'armbian' /etc/os-release
      then
        echo 'Updating armbian-ramlog'
        sed -i 's/armbian-ramlog)" | while/armbian-ramlog)|\\.journal" | while/' /usr/lib/armbian/armbian-ramlog
    fi
  # end of Orange Pi Zero section
  "${destination_directory}"/tools/install.sh --user "${standard_user}" --dependencies --rtkbase-requirements --unit-files
  "${destination_directory}"/venv/bin/python -m pip uninstall eventlet -y
  #upgrade rtklib to b34j
  upgrade_rtklib
  #remove sbas rtcm message
  sed -i -r '/^rtcm_/s/1107(\([0-9]+\))?,//' "${destination_directory}"/settings.conf

}

#this update function is here only for testing update, but could be useful in case of a failed 2.5 to 2.6 update.
upd_2.6.0() {
  upd_2.5.0
}

#check if we can apply the update
#FOR THE OLDER ME -> Don't forget to modify the os detection if there is a 2.5.x release !!!
[[ $checking == '--checking' ]] && check_before_update && exit

echo '################################'
echo 'Starting standard update'
echo '################################'
update || { echo 'Update failed (update)' ; exit 1 ;} 
# calling specific update function. If we are using v2.2.5, it will call the function upd_2.2.5
echo 'Starting specific update'
upd_"${old_version/b*/b}" "$@"  || { echo 'Update failed (upd_release_number)' ; exit 1 ;} 
#note for older me:
#When dealing with beta version, "${oldversion/b*/b}" will call function 2.4b when we use a release 2.4b1 or 2.4b2 or 2.4beta99

# The new version numbers will be imported from settings.conf.default during the web server startup.
echo "Delete the line version= and checkpoint_version= in settings.conf"
sed -i '/^checkpoint_version=/d' ${destination_directory}/settings.conf
sed -i '/^version=/d' ${destination_directory}/settings.conf
echo 'Insert updated status in settings.conf'
sed -i '/^\[general\]/a updated=true' ${destination_directory}/settings.conf

#change rtkbase's content owner
chown -R ${standard_user}:${standard_user} ${destination_directory}

  #restart str2str if it was active before upgrading rtklib
  # restart not nedeed if RTKlib was not upgraded
  [ $str2str_active = 'active' ] && systemctl restart str2str_tcp 
  [ $str2str_file = 'active' ] && systemctl restart str2str_file 
  [ $rtkrcv_raw2nmea = 'active' ] && systemctl restart rtkbase_raw2nmea
  # restart previously running services
  # restart needed with all update to propagate the release number in the rtcm stream
  [ $str2str_ntrip_A_active = 'active' ] && systemctl restart str2str_ntrip_A
  [ $str2str_ntrip_B_active = 'active' ] && systemctl restart str2str_ntrip_B  
  [ $str2str_local_caster = 'active' ] && systemctl restart str2str_local_ntrip_caster
  [ $str2str_rtcm = 'active' ] && systemctl restart str2str_rtcm_svr
  [ $str2str_serial = 'active' ] && systemctl restart str2str_rtcm_serial
  

#if a reboot is needed
#systemctl reboot
echo 'RTKBase update ending...'
echo 'Restart web server'
systemctl restart rtkbase_web.service
