#!/bin/bash
#
# configure_gps.sh: script to provide GPS modules with commands
# that are not saved in flash on the module (ie. they must be provided
# each time the module is started).


BASEDIR="$(dirname "$0")"
source <( grep -v '^#' "${BASEDIR}"/settings.conf | grep '=' ) #import settings

if [[ "${receiver}" = "Quectel LC29HBS" ]]; then
  speed="${com_port_settings%%:*}"
  python3 "${BASEDIR}"/tools/nmea.py --file "${BASEDIR}"/receiver_cfg/LC29HBS_Configure.txt /dev/"${com_port}" "${speed}" 3
  echo Configuring Quectel LC29HBS on /dev/"${com_port}" at speed "${speed}"
fi
