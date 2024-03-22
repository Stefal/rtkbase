#! /usr/bin/env python3

import os
import sys
import time
import nmcli

if os.getenv("SUDO_USER") is not None:
    homedir = os.path.join("/home", os.getenv("SUDO_USER"))
else:
    homedir = os.path.expanduser('~')

sys.path.insert(1, os.path.join(homedir, "sim-modem"))
from src.sim_modem import *

nmcli.disable_use_sudo()
CONN_NAME='Cellular Modem'
MODEM_PORT='/dev/ttymodemAT'

def sleep(timeout, retry=10):
    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    value = function(*args, **kwargs)
                    if value is not None:
                        return value
                except:
                    print(f'{function.__name__}: Sleeping for {timeout + retries*timeout} seconds')
                    time.sleep(timeout + retries*timeout)
                    retries += 1
                    
        return wrapper
    return the_real_decorator

@sleep(10)
def check_modem():
    nmcli.connection.show(CONN_NAME)
    if nmcli.connection.show(CONN_NAME).get("GENERAL.STATE") == 'activated':
        return True

@sleep(10, retry=2)
def check_network_registration():
    try:
        modem = Modem(MODEM_PORT)
        network_reg = int(modem.get_network_registration_status().split(",")[1])
        if network_reg == 1 or network_reg == 2 or network_reg == 5:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        raise Exception
    finally:
        modem.close()

@sleep(10)
def get_public_ip_address():
    try:
        modem = Modem(MODEM_PORT)
        public_ip = modem.get_ip_address()
        
    except Exception as e:
        print (e)
        raise Exception
    finally:
        print("closing modem connexion")
        modem.close()
    return public_ip

@sleep(10)
def get_in_use_ip_address():
    return nmcli.connection.show(CONN_NAME)['IP4.ADDRESS[1]'].split('/')[0]

@sleep(10)
def ping(host):
    res = os.system("ping -c 4 " + host + ' >/dev/null')
    return res == 0

check_modem()
network_reg = check_network_registration()
ip_in_use = get_in_use_ip_address()
public_ip = get_public_ip_address()
ping_host = ping('caster.centipede.fr') or ping('pch.net')
print("Internal Ip address in use: ", ip_in_use)
print("Modem public Ip address: ", public_ip)
print("Ping caster.centipede.fr or pch.net", ping_host)


if ip_in_use == None or public_ip == None or network_reg == False or ping_host == False:
    print("Modem problem. Switching to airplane mode and back to normal")
    try:
        print("Connecting to modem...")
        modem = Modem(MODEM_PORT)
        print("Sending AT+CFUN=0")
        modem.custom_read_lines('AT+CFUN=0')
        time.sleep(20)
        print("Sending AT+CFUN=1")
        modem.custom_read_lines('AT+CFUN=1')
    except Exception as e:
        print(e)
    finally:
        modem.close()

elif ip_in_use != public_ip:
    try:
        modem = Modem(MODEM_PORT)
        modem.set_usbnetip_mode(1)
        print("Request to switch to public IP address done!")
        print("It could take a few minutes to be active")
    except Exception as e:
        print(e)
    finally:
        print("closing modem connexion")
        modem.close()
else:
    print("We are already using the public Ip")

