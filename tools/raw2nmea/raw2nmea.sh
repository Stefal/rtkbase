#!/bin/bash

#Script to get raw data from the gnss receiver, compute it with rtkrcv, and output to nmea on tcp port 5014, for feeding gpsd.
#Unuseful with a U-Blox receiver
#Useful with other receivers to get date time when there is no internet connection

if [[ -z ${rtkbase_path} ]]
  then
    if grep -q '^rtkbase_path=' /etc/environment
    then
      source /etc/environment
    else 
      echo 'Error, missing rtkbase_path variable'
      exit 1
    fi
  fi

RAW_PORT=$(grep ^tcp_port= "${rtkbase_path}"/settings.conf | awk -F"'" '{print $2}')
RAW_FORMAT=$(grep ^receiver_format= "${rtkbase_path}"/settings.conf | awk -F"'" '{print $2}')
NMEA_PORT=$(grep ^nmea_port= "${rtkbase_path}"/settings.conf | awk -F"'" '{print $2}')
if [[ $RAW_FORMAT == ubx ]]
  then
   echo "Service not needed with ubx format"
   exit
fi

sed -i s/^inpstr1-path.*/inpstr1-path\ \ =localhost:$RAW_PORT/ "${rtkbase_path}"/tools/raw2nmea/nmea_out.conf
sed -i s/^inpstr1-format.*/inpstr1-format\ \ =$RAW_FORMAT/ "${rtkbase_path}"/tools/raw2nmea/nmea_out.conf
sed -i s/^outstr1-path.*/outstr1-path\ \ =localhost:$NMEA_PORT/ "${rtkbase_path}"/tools/raw2nmea/nmea_out.conf
sed -i 's/^DEVICES=.*/DEVICES="tcp:\/\/localhost:'$NMEA_PORT'"/' /etc/default/gpsd

{ sleep 20 ; systemctl restart gpsd ;} &
rtkrcv -o "${rtkbase_path}"/tools/raw2nmea/nmea_out.conf -nc
