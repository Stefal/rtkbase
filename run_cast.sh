#!/bin/bash
#
# run_cast.sh: script to run NTRIP caster by STR2STR
# You can read the RTKLIB manual for more str2str informations:
# https://github.com/tomojitakasu/RTKLIB

BASEDIR=$(dirname "$0")
source <( grep = ${BASEDIR}/settings.conf )  #import settings


in_serial="serial://${serial_input}"
in_tcp="tcpcli://127.0.0.1:${tcp_port}#${receiver_format}"

out_caster="ntrips://:${svr_pwd}@${svr_addr}:${svr_port}/${mnt_name}#rtcm3 -msg ${rtcm_msg} -p ${position} -i ${receiver}"
out_tcp="tcpsvr://:${tcp_port}"
out_file="file://${datadir}/${file_name}::T::S=${file_rotate_time} -f ${file_overlap_time}"


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
        mkdir -p ${datadir}
        ${cast} -in ${!1} -out ${out_file} &
      fi
      ;;
      
    esac





