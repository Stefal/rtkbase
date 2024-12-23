#!/usr/bin/python
""" Module to get up network interfaces with their ip address and connection name
    These informations are then displayed inside the RTKBase web GUI.
"""

import logging
import psutil
import nmcli
import argparse

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('ERROR')

nmcli.disable_use_sudo()


def get_conn_name(device):
    """
        Get the connection name for the device 
        (e.g. Wired Connection 1)
        
        Parameter:
            device(str): the network device name
        Return:
            str: connection name
    """
    try:
        device_infos = nmcli.device.show(device)
        return device_infos["GENERAL.CONNECTION"]
    except nmcli.NotExistException:
        log.debug("No connection name for {}".format(device))
        return None

def get_up_if():
    """
        Get the up network interface

        Return:
            list: up interfaces
    """
    #filtering available interface
    if_stats = psutil.net_if_stats()
    if_stats.pop('lo')
    log.debug(if_stats)
    if_stats = {k:v for (k,v) in if_stats.items() if if_stats[k].isup} # keep only up interface
    if_stats = {k:v for (k,v) in if_stats.items() if if_stats[k].speed > 0 or 'pointopoint' in if_stats[k].flags} # keep only interface with speed > 0
    if_stats = {k:v for (k,v) in if_stats.items() if not k.startswith('docker')} # remove docker interface
    return if_stats

def get_interfaces_infos():
    """
        Get all up network interfaces with their ip v4/v6 addresses
        and the connection name.
        It returns a list of dict
        e.g. [{'device': 'end0', 'ipv4': ['192.168.1.135'], 'ipv6': [], 'conn_name': 'Wired connection 1'}]

        Return:
            list: all up network interfaces as dict
    """
    up_interface = get_up_if()
    log.debug("up interfaces: {}".format(up_interface))
    #then filter psutil.net_if_addrs()
    if_addrs = psutil.net_if_addrs()
    up_interface = {k:if_addrs[k] for (k,v) in up_interface.items() if if_addrs.get(k)}
    #then filter to keep only AF_INET and AF_INET6
    for k,v in up_interface.items():
        up_interface[k] = [ x for x in v if x.family.name == 'AF_INET' or x.family.name == 'AF_INET6']
    #then filter ipv6 link local address
    for k,v in up_interface.items():
        up_interface[k] = [ x for x in v if not x.address.startswith('fe80')]

    interfaces_infos = []
    for k,v in up_interface.items():
        device_info = {"device" : k}
        ipv4 = []
        ipv6 = []
        for part in v:
            if part.family.name == 'AF_INET6':
                ipv6.append(part.address)
            elif part.family.name == 'AF_INET':
                ipv4.append(part.address)
            log.debug("{} : {} : {}".format(k, part.family.name, part.address))
        device_info["ipv4"] = ipv4 if len(ipv4) > 0 else None
        device_info["ipv6"] = ipv6 if len(ipv6) > 0 else None
        conn_name = get_conn_name(k)
        if conn_name:
            device_info["conn_name"] = conn_name
        interfaces_infos.append(device_info)
    return interfaces_infos

def arg_parse():
    """ Parse the command line you use to launch the script """
    
    parser= argparse.ArgumentParser(prog='network_infos', description="Module to get up network interfaces with their ip address and connection name")
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--debug", action='store_true')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = arg_parse()
    if args.debug:
        log.setLevel('DEBUG')
    print(get_interfaces_infos())
