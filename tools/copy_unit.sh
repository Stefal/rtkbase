#!/bin/bash
#
# Script to add the user name and user path in unit file
# then copy these services to the correct location.

man_help() {
 echo 'Options:'
 echo '        -h | --help'
 echo '        -u | --user  <username>'
 echo '                        Specify user used in the service unit. Without this argument'
 echo '                        the user return by the logname command will be used.'
 exit 0
}

BASEDIR=$(dirname "$0")
ARG_HELP=0
ARG_USER=0
PARSED_ARGUMENTS=$(getopt --name copy_unit --options hu: --longoptions help,user: -- "$@")
VALID_ARGUMENTS=$?
if [ "$VALID_ARGUMENTS" != "0" ]; then
    #man_help
    echo 'Try '\''copy_unit.sh --help'\'' for more information'
    exit 1
  fi
#echo "PARSED_ARGUMENTS is $PARSED_ARGUMENTS"
  eval set -- "$PARSED_ARGUMENTS"
  while :
    do
      case "$1" in
        -h | --help)   ARG_HELP=1                     ; shift   ;;
        -u | --user)   ARG_USER="${2}"                ; shift 2 ;;
        # -- means the end of the arguments; drop this, and break out of the while loop
        --) shift; break ;;
        # If invalid options were passed, then getopt should have reported an error,
        # which we checked as VALID_ARGUMENTS when getopt was called...
        *) echo "Unexpected option: $1 - this should not happen."
          usage ;;
      esac
    done
[ $ARG_HELP -eq 1 ] && man_help
[ "${ARG_USER}" == 0 ] && ARG_USER=$(logname)
#echo 'user=' "${ARG_USER}"

if ! [ $(id -u) = 0 ]; then
   echo "This script needs root/sudo"
   exit 1
fi

for file_path in "${BASEDIR}"/../unit/*.service "${BASEDIR}"/../unit/*.timer
    do
        file_name=$(basename "${file_path}")
        echo copying "${file_name}"
        sed -e 's|{script_path}|'"$(dirname "$(dirname "$(readlink -f "$0")")")"'|' -e 's|{user}|'"${ARG_USER}"'|' -e 's|{python_path}|'"$(which python3)"'|' "${file_path}" > /etc/systemd/system/"${file_name}"
    done

systemctl daemon-reload
