#!/bin/bash
connection_name='LTE Modem'
modem_name=A76XX

function man_help() {
    echo '####################################'
    echo 'LTE MODEM CONNECTION MANAGEMENT HELP'
    echo '####################################'
    echo 'Bash scripts to set LTE Modem connection name and priority (metric)'
    echo ''
    echo ''
    echo 'Options: '
    echo '        -c | --connection_rename'
    echo '                    Rename the LTE Modem connection to "LTE Modem"'
    echo ''
    echo '        -l | --lte_priority'
    echo '                    Set network connection priority to the LTE Modem'
    echo ''
    echo '        -o | --other_priority'
    echo '                    Set network connection priority to other connection than LTE Modem'
    echo ''
    echo '        -h | --help'
    echo '                    Display this help message.'
    exit 0
}
function _nm_connection_of() {
    # $1 = name of network interface to query
    con_name=$(nmcli -g GENERAL.CONNECTION device show "$1")
    if [ "$con_name" = "" ]; then
        echo "ERROR: no connection associated with $1" >&2
        return 1
    fi
    echo "$con_name"
}

function get_lte_interface_name() {
    #echo 'modem name' $1
    for dev in /sys/class/net/*/ 
    do
        lte_device_interface_name=$(udevadm info $dev | grep -q "${1}" && echo "$(basename $dev)" && exit 0)
        [[ ! -z $lte_device_interface_name ]] && echo $lte_device_interface_name && break
    done
    
    #echo 'interface_name ' $2
	#udevadm info $2 | grep -q "${1}" && echo "$(basename $2)" && exit 0
}

#export -f _filter_interface

function connection_rename() {
    #echo 'MODEM: ' "${modem_name}"
    #lte_device_if_name=$(find /sys/class/net/ -type l -exec bash -c '_filter_interface A76XX {}' \;)
    #lte_device_if_name=$(find /sys/class/net/ -type l | while read dir; do _filter_interface "${modem_name}" "${dir}"; done)
    lte_device_if_name=$(get_lte_interface_name "${modem_name}")
    if [[ ! -z "${lte_device_if_name}" ]]
    then
        nmcli connection modify "$(_nm_connection_of "${lte_device_if_name}")" connection.id "${connection_name}" && \
        echo 'Connection renamed to' "${connection_name}"                                                         && \
        nmcli connection up "${connection_name}"
    else
        echo "No connection found!"
        return 1
    fi
}

function set_lte_priority() {
    lte_device_if_name=$(get_lte_interface_name "${modem_name}")
    nmcli connection modify  "$(_nm_connection_of "${lte_device_if_name}")" ipv4.route-metric 50 ipv6.route-metric 50
    nmcli connection up "$(_nm_connection_of "${lte_device_if_name}")"
}

function set_other_priority() {
    lte_device_if_name=$(get_lte_interface_name "${modem_name}")
    nmcli connection modify  "$(_nm_connection_of "${lte_device_if_name}")" ipv4.route-metric 900 ipv6.route-metric 900
    nmcli connection up "$(_nm_connection_of "${lte_device_if_name}")"
}

function informations() {
    echo 'TODO'
}

function main() {
ARG_HELP=0
ARG_CON_RENAME=0
ARG_LTE_PRIORITY=0
ARG_OTHER_PRIORITY=0
ARG_INFORMATIONS=0

PARSED_ARGUMENTS=$(getopt --name lte_network_mgmt --options cloih --longoptions connection_rename,lte_priority,other_priority,informations,help -- "$@")
VALID_ARGUMENTS=$?
if [ "$VALID_ARGUMENTS" != "0" ]; then
    #man_help
    echo 'Try '\''--help'\'' for more information'
    exit 1
fi

#echo "PARSED_ARGUMENTS is $PARSED_ARGUMENTS"
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
        -c | --connection_rename) ARG_CON_RENAME=1     ; shift   ;;
        -l | --lte_priority) ARG_LTE_PRIORITY=1        ; shift   ;;
        -o | --other_priority) ARG_OTHER_PRIORITY=1    ; shift   ;;
        -i | --informations) ARG_INFORMATIONS=1        ; shift   ;;
        -h | --help)   ARG_HELP=1                      ; shift   ;;
        # -- means the end of the arguments; drop this, and break out of the while loop
        --) shift; break ;;
        # If invalid options were passed, then getopt should have reported an error,
        # which we checked as VALID_ARGUMENTS when getopt was called...
        *) echo "Unexpected option: $1"
        usage ;;
    esac
done

[ $ARG_HELP -eq 1 ] && man_help
[ $ARG_CON_RENAME -eq 1 ] && connection_rename
[ $ARG_LTE_PRIORITY -eq 1 ] && set_lte_priority
[ $ARG_OTHER_PRIORITY -eq 1 ] && set_other_priority
[ $ARG_INFORMATIONS -eq 1 ] && informations
}

main "$@"
