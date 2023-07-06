#!/bin/bash

detect_usb_lte_simcom_modem() {
    echo '################################'
    echo 'SIMCOM LTE MODEM DETECTION'
    echo '################################'
      #This function try to detect a simcom lte modem (A76XX serie) and write the port inside settings.conf
for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
          ID_SERIAL=''
          MINOR=''
          syspath="${sysdevpath%/dev}"
          devname="$(udevadm info -q name -p "${syspath}")"
          if [[ "$devname" == "bus/"* ]]; then continue; fi
          eval "$(udevadm info -q property --export -p "${syspath}")"
          if [[ $MINOR != 1 ]]; then continue; fi
          if [[ -z "$ID_SERIAL" ]]; then continue; fi
          if [[ "$ID_SERIAL" =~ 'SIMCom' ]]
          then
            detected_modem[0]=$devname
            detected_modem[1]=$ID_SERIAL
            echo '/dev/'"${detected_modem[0]}" ' - ' "${detected_modem[1]}"
          fi
      done
    }

detect_with_lsusb() {
          vendor_and_product_ids=$(lsusb | grep -i "A76XX" | grep -Eo "[0-9A-Za-z]+:[0-9A-Za-z]+")
          #echo 'vendor and product ids: ' "${vendor_and_product_ids}"
          if [[ -z "$vendor_and_product_ids" ]]; then 
            echo 'NO GNSS RECEIVER DETECTED'
            echo 'YOU CAN REDETECT IT FROM THE WEB UI'
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

#detect_usb_lte_simcom_modem
detect_with_lsusb
