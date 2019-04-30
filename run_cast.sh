#!/bin/bash
#
# run_cast.sh: script to run NTRIP caster by STR2STR
# You can read the RTKLIB manual for more str2str informations:
# https://github.com/tomojitakasu/RTKLIB


# NTRIP caster program
BASEDIR=$(dirname "$0")
cast=/usr/local/bin/str2str

# General options
position='47.034 -1.251 36.4'			#base coordinates: lat long height
com_port='ttyS1:115200:8:n:1'			#gnss receiver com port and settings
receiver_format='ubx'				#gnss receiver format
serial_input="${com_port}#${receiver_format}"

# File options
datadir=$BASEDIR/data				#gnss data directory
file_name="%Y-%m-%d-%h:%M:%S-GNSS-1.ubx"	#gnss data filename
file_rotate_time=24				#file rotate time in hour
file_overlap_time=30				#file overlap time in seconds

# TCP options
tcp_port=5015

# NTRIP caster options
svr_addr=rtk2go.com				#ntrip caster url
svr_port=2101					#ntrip caster port
svr_pwd=BETATEST				#ntrip caster password
mnt_name=Your_mount_name			#Mount name
receiver=Ublox_neo-m8t				#receiver model
rtcm_msg='1004,1005,1019,1042,1045,1046,1077,1097,1107,1127'

logdir=$BASEDIR/log				#log directory
level=0						#trace level (0: no trace)

in_serial="serial://${serial_input}"
in_tcp="tcpcli://127.0.0.1:${tcp_port}#${receiver_format}"

out_caster="ntrips://:${svr_pwd}@${svr_addr}:${svr_port}/${mnt_name}#rtcm3 -msg ${rtcm_msg} -p ${position} -i ${receiver}"
out_tcp="tcpsvr://:${tcp_port}"
out_file="file://${datadir}/${file_name}::T::S=${file_rotate_time} -f ${file_overlap_time}"

# NTRIP caster logs
log1=$logdir/cast_trac_`date -u +%Y%m%d_%H%M%S`.log
log2=$logdir/cast_stat_`date -u +%Y%m%d_%H%M%S`.log
log3=$logdir/ifconfig_`date -u +%Y%m%d_%H%M%S`.log
# start NTRIP caster


    mkdir -p ${logdir} ${datadir}
    
    case "$2" in
      out_tcp)
      #echo ${cast} -in ${!1} -out $out_tcp
      ${cast} -in ${!1} -out ${out_tcp} &
      ;;

    out_caster)
      #echo ${cast} -in ${!1} -out $out_caster
      ${cast} -in ${!1} -out ${out_caster} &
      ;;

    out_file)
      #echo ${cast} -in ${!1} -out $out_caster
      ${BASEDIR}/check_timesync.sh  #wait for a correct date/time before starting to write files
      ret=$?
      if [ ${ret} -eq 0 ]
      then
        ${cast} -in ${!1} -out ${out_file}
      fi
      ;;
      
    esac





