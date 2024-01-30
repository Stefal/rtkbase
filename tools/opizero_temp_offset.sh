#!/bin/bash

detect_sbc_temp_offset(){
  #Detect if the computer is a Orange Pi Zero, and if the cpu temps is lower than 30°C, it looks like it's a Orange Pi zero LTS with a 30°C offset
  computer_model=$(tr -d '\0' < /sys/firmware/devicetree/base/model)
  cpu_temp=$(($(cat /sys/class/thermal/thermal_zone0/temp)/1000))
  if [[ $computer_model = 'Xunlong Orange Pi Zero' ]] && [[ cpu_temp -lt 30 ]]
  then
    echo 'Adding 30°C offset'
    if [[ -f "${rtkbase_path}/settings.conf" ]]  && grep -qE "^cpu_temp_offset=.*" "${rtkbase_path}"/settings.conf #check if settings.conf exists
          then
            #change the cpu_temp_offset value/settings inside settings.conf
            sed -i s/^cpu_temp_offset=.*/cpu_temp_offset=30/ "${rtkbase_path}"/settings.conf
    elif [[ -f "${rtkbase_path}/settings.conf" ]]
          then
            sed -i '/^\[general\]/a cpu_temp_offset=30' "${rtkbase_path}"/settings.conf
    else
           #create settings.conf with the cpu_temp_offset setting
           #as it could start before the web server merge settings.conf.default and settings.conf
            printf "[general]\ncpu_temp_offset=30" > "${rtkbase_path}"/settings.conf
    fi
  fi
}

if [[ -n "${rtkbase_path}" ]]
    then
      detect_sbc_temp_offset
    else
      echo 'RTKBase path unknown. Exiting'
      exit 1
fi