#!/bin/bash
#
# run_cast.sh: script to run NTRIP caster by STR2STR
# You can read the RTKLIB manual for more str2str informations:
# https://github.com/tomojitakasu/RTKLIB

BASEDIR=$(dirname "$0")
source <( grep = ${BASEDIR}/settings.conf )  #import settings


in_serial="serial://${com_port}:${com_port_settings}#${receiver_format}"
in_tcp="tcpcli://127.0.0.1:${tcp_port}#${receiver_format}"
#in_ext_tcp is mainly for dev purpose to receive a raw stream from another base
in_ext_tcp="tcpcli://192.168.1.60:${tcp_port}#${receiver_format}"

out_caster="ntrips://:${svr_pwd}@${svr_addr}:${svr_port}/${mnt_name}#rtcm3 -msg ${rtcm_msg} -p ${position} -i RTKBase_v${version}_${receiver} -a ${antenna_info}"
#add receiver options if it exists
[[ ! -z "${ntrip_receiver_options}" ]] && out_caster=""${out_caster}" -opt "${ntrip_receiver_options}""

out_tcp="tcpsvr://:${tcp_port}"

out_file="file://${datadir}/${file_name}.${receiver_format}::T::S=${file_rotate_time} -f ${file_overlap_time}"

out_rtcm_svr="tcpsvr://:${rtcm_svr_port}#rtcm3 -msg ${rtcm_svr_msg} -p ${position} -i RTKBase_v${version}_${receiver} -a ${antenna_info}"
#add receiver options if it exists
[[ ! -z "${rtcm_receiver_options}" ]] && out_rtcm_svr=""${out_rtcm_svr}" -opt "${rtcm_receiver_options}""

out_rtcm_serial="serial://${out_com_port}:${out_com_port_settings}#rtcm3 -msg ${rtcm_serial_msg} -p ${position} -i RTKBase_v${version}_${receiver} -a ${antenna_info}"
#add receiver options if it exists
[[ ! -z "${rtcm_serial_receiver_options}" ]] && out_rtcm_serial=""${out_rtcm_serial}" -opt "${rtcm_serial_receiver_options}""

mkdir -p ${logdir}
    
  case "$2" in
    out_tcp)
    #echo ${cast} -in ${!1} -out $out_tcp
    # What is this ${!1} ? It's variable indirection
    ${cast} -in ${!1} -out ${out_tcp} -t ${level} -fl ${logdir}/str2str_tcp.log &
    ;;

  out_caster)
    #echo ${cast} -in ${!1} -out $out_caster
    ${cast} -in ${!1} -out ${out_caster} -t ${level} -fl ${logdir}/str2str_ntrip.log &
    ;;

  out_rtcm_svr)
    #echo ${cast} -in ${!1} -out $out_rtcm_svr
    ${cast} -in ${!1} -out ${out_rtcm_svr} -t ${level} -fl ${logdir}/str2str_rtcm_svr.log &
    ;;

  out_rtcm_serial)
    #echo ${cast} -in ${!1} -out $out_rtcm_serial
    ${cast} -in ${!1} -out ${out_rtcm_serial} -t ${level} -fl ${logdir}/str2str_rtcm_serial.log &
    ;;

  out_file)
    #echo ${cast} -in ${!1} -out $out_caster
    ${BASEDIR}/check_timesync.sh  #wait for a correct date/time before starting to write files
    ret=$?
    if [ ${ret} -eq 0 ]
    then
      mkdir -p ${datadir}
      ${cast} -in ${!1} -out ${out_file} -t ${level} -fl ${logdir}/str2str_file.log &
    fi
    ;;
    
  esac





