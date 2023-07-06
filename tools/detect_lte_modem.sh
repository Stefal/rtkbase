#!/bin/bash

detect_usb_lte_simcom_modem() {
    echo '################################'
    echo 'SIMCOM A76XX LTE MODEM DETECTION'
    echo '################################'
      #This function try to detect a simcom lte modem (A76XX serie) and write the port inside settings.conf
for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
          ID_MODEL=''
          syspath="${sysdevpath%/dev}"
          devname="$(udevadm info -q name -p "${syspath}")"
          if [[ "$devname" == "bus/"* ]]; then continue; fi
          eval "$(udevadm info -q property --export -p "${syspath}")"
          #if [[ $MINOR != 1 ]]; then continue; fi
          if [[ -z "$ID_MODEL" ]]; then continue; fi
          if [[ "$ID_MODEL" =~ 'A76XX' ]]
          then
            detected_modem[0]=$devname
            detected_modem[1]=$ID_SERIAL
            echo '/dev/'"${detected_modem[0]}" ' - ' "${detected_modem[1]}"
            #return 0
          fi
      done
      return $?
    }

detect_with_lsusb() {
          vendor_and_product_ids=$(lsusb | grep -i "A76XX" | grep -Eo "[0-9A-Za-z]+:[0-9A-Za-z]+")
          #echo 'vendor and product ids: ' "${vendor_and_product_ids}"
          if [[ -z "$vendor_and_product_ids" ]]; then 
            echo 'NO LTE MODEM DETECTED'
            return 1
          fi
          devname=$(_get_device_path "$vendor_and_product_ids")
          echo 'devname: ' $devname
          detected_gnss[0]=$devname
          detected_gnss[1]='-'
          echo '/dev/'${detected_gnss[0]} ' - ' ${detected_gnss[1]}
}

_get_device_path() {
    id_Vendor=${1%:*}
    id_Product=${1#*:}
    for path in $(find /sys/devices/ -name idVendor | rev | cut -d/ -f 2- | rev); do
        echo "${path}"
        if grep -q "$id_Vendor" "$path"/idVendor; then
            if grep -q "$id_Product" "$path"/idProduct; then
		#if grep -q 'net' "${path}"/idProduct; then
                 find "$path" -name 'device' | rev | cut -d / -f 2 | rev
		#fi
            fi
        fi
    done
}

function add_modem_port(){
  if [[ -f "${rtkbase_path}/settings.conf" ]]  && grep -qE "^modem_at_port=.*" "${rtkbase_path}"/settings.conf #check if settings.conf exists
  then
    #change the com port value/settings inside settings.conf
    sudo -u "${RTKBASE_USER}" sed -i s\!^modem_at_port=.*\!modem_at_port=\'${modem_at_port}\'! "${rtkbase_path}"/settings.conf
  elif [[ -f "${rtkbase_path}/settings.conf" ]]  && ! grep -qE "^modem_at_port=.*" "${rtkbase_path}"/settings.conf #check if settings.conf exists without modem_at_port entry
  then
    sudo -u "${RTKBASE_USER}" printf "[network]\nmodem_at_port='"${modem_at_port}"'" >> "${rtkbase_path}"/settings.conf
  elif [[ ! -f "${rtkbase_path}/settings.conf" ]]
  then
    #create settings.conf with the modem_at_port setting
    sudo -u "${RTKBASE_USER}" printf "[network]\nmodem_at_port='"${modem_at_port}"'" > "${rtkbase_path}"/settings.conf
  fi
}

modem_at_port=/dev/ttyAT

RTKBASE_USER=basegnss

detect_usb_lte_simcom_modem
add_modem_port