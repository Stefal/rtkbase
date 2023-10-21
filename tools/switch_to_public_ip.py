#! /usr/bin/env python3

import os
import sys
import nmcli
if os.getenv("SUDO_USER") is not None:
    homedir = os.path.join("/home", os.getenv("SUDO_USER"))
else:
    homedir = os.path.expanduser('~')

sys.path.insert(1, os.path.join(homedir, "sim-modem"))
from src.sim_modem import *

nmcli.disable_use_sudo()
CONN_NAME='Cellular Modem'

def sleep(timeout, retry=50):
    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    value = function(*args, **kwargs)
                    if value is not None:
                        return value
                except:
                    print(f'Sleeping for {timeout + retries*timeout} seconds')
                    time.sleep(timeout + retries*timeout)
                    retries += 1
                    
        return wrapper
    return the_real_decorator

@sleep(10)
def check_modem():
    nmcli.connection.show(CONN_NAME)
    if nmcli.connection.show(CONN_NAME).get("GENERAL.STATE") == 'activated':
        return True
    
@sleep(10)
def get_public_ip_address():
    return modem.get_ip_address()

@sleep(10)
def get_in_use_ip_address():
    return nmcli.connection.show(CONN_NAME)['IP4.ADDRESS[1]'].split('/')[0]

check_modem()
modem = Modem('/dev/ttymodemAT')
ip_in_use = get_in_use_ip_address()
public_ip = get_public_ip_address()

print("Ip address in use: ", ip_in_use)
print("Public Ip address: ", public_ip)

if ip_in_use != public_ip:
    modem.set_usbnetip_mode(1)
    print("Request to switch to public IP address done!")
    print("It could take a few minutes to be active")
else:
    print("We are already using the public Ip")

