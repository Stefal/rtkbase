#!/usr/bin/python

import psutil
import nmcli
from dataclasses import dataclass

nmcli.disable_use_sudo()

def get_up_if():
    #filtering available interface
    if_stats = psutil.net_if_stats()
    if_stats.pop('lo')
    if_stats = {k:v for (k,v) in if_stats.items() if if_stats[k].isup} # keep only up interface
    if_stats = {k:v for (k,v) in if_stats.items() if if_stats[k].speed > 0} # keep only interface with speed > 0
    if_stats = {k:v for (k,v) in if_stats.items() if not k.startswith('docker')} # remove docker interface
    return if_stats

def get_conn_name(device):
    try:
        device_infos = nmcli.device.show(device)
        return device_infos["GENERAL.CONNECTION"]
    except NotExistException:
        return None 

def get_interfaces_infos():

    #print(get_up_if())
    up_interface = get_up_if()
    #then filter psutil.net_if_addrs()
    if_addrs = psutil.net_if_addrs()
    up_interface = {k:if_addrs[k] for (k,v) in up_interface.items() if if_addrs[k]}
    #then filter to keep only AF_INET and AF_INET6
    for k,v in up_interface.items():
        up_interface[k] = [ x for x in v if x.family.name == 'AF_INET' or x.family.name == 'AF_INET6']
    #then filter ipv6 link local address
    for k,v in up_interface.items():
        up_interface[k] = [ x for x in v if not x.address.startswith('fe80')]

    interfaces_infos = []
    for k,v in up_interface.items():
        #print('key: ', k)
        #print('value: ', v)
        device_info = {"device" : k}
        ipv4 = []
        ipv6 = []
        for part in v:
            if part.family.name == 'AF_INET6':
                ipv6.append(part.address)
            elif part.family.name == 'AF_INET':
                ipv4.append(part.address)
            #print("{} : {} : {}".format(k, part.family.name, part.address))
        device_info["ipv4"] = ipv4
        device_info["ipv6"] = ipv6
        conn_name = get_conn_name(k)
        if conn_name:
            device_info["conn_name"] = conn_name
        interfaces_infos.append(device_info)
    return interfaces_infos