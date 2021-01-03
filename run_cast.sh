#!/bin/bash
#
# run_cast.sh: script to run NTRIP caster by STR2STR
# You can read the RTKLIB manual for more str2str informations:
# https://github.com/tomojitakasu/RTKLIB

BASEDIR=$(dirname "$0")
source <( grep = ${BASEDIR}/settings.conf )  #import settings


in_serial="serial://${com_port}:${com_port_settings}#${receiver_format}"
in_tcp="tcpcli://127.0.0.1:${tcp_port}#${receiver_format}"

out_caster="ntrips://:${svr_pwd}@${svr_addr}:${svr_port}/${mnt_name}#rtcm3 -msg ${rtcm_msg} -p ${position} -i ${receiver}"
#add receiver options if it exists
[[ ! -z "${ntrip_receiver_options}" ]] && out_caster=""${out_caster}" -opt "${ntrip_receiver_options}""

out_tcp="tcpsvr://:${tcp_port}"

out_file="file://${datadir}/${file_name}.${receiver_format}::T::S=${file_rotate_time} -f ${file_overlap_time}"

out_rtcm_svr="tcpsvr://:${rtcm_svr_port}#rtcm3 -msg ${rtcm_svr_msg} -p ${position}"
#add receiver options if it exists
[[ ! -z "${rtcm_receiver_options}" ]] && out_rtcm_svr=""${out_rtcm_svr}" -opt "${rtcm_receiver_options}""

out_serial_rtcm="serial://${out_com_port}:${out_com_port_settings}#rtcm3 -msg ${serial_rtcm_msg} -p ${position}"
#add receiver options if it exists
[[ ! -z "${serial_rtcm_receiver_options}" ]] && out_serial_rtcm=""${out_serial_rtcm}" -opt "${serial_rtcm_receiver_options}""

mkdir -p ${logdir}
    
  case "$2" in
    out_tcp)
    #echo ${cast} -in ${!1} -out $out_tcp
    # What is this ${!1} ? It's variable indirection
    ${cast} -in ${!1} -out ${out_tcp} -t ${level} &
    ;;

  out_caster)
    #echo ${cast} -in ${!1} -out $out_caster
    ${cast} -in ${!1} -out ${out_caster} -t ${level} &
    ;;

  out_rtcm_svr)
    #echo ${cast} -in ${!1} -out $out_rtcm_svr
    ${cast} -in ${!1} -out ${out_rtcm_svr} -t ${level} &
    ;;

  out_serial_rtcm)
    #echo ${cast} -in ${!1} -out $out_serial_rtcm
    ${cast} -in ${!1} -out ${out_serial_rtcm} -t ${level} &
    ;;

  out_file)
    #echo ${cast} -in ${!1} -out $out_caster
    ${BASEDIR}/check_timesync.sh  #wait for a correct date/time before starting to write files
    ret=$?
    if [ ${ret} -eq 0 ]
    then
      mkdir -p ${datadir}
      ${cast} -in ${!1} -out ${out_file} -t ${level} &
    fi
    ;;
    
  esac





