#! /usr/bin/env python3

import os
import sys
import argparse
import logging
from septentrio.septentrio_cmd import *
from enum import Enum
from operator import methodcaller

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('ERROR')

class CmdMapping(Enum):
    """Mapping human command to septentrio_cmd methods"""

    get_model = 'get_receiver_model'
    get_firmware = 'get_receiver_firmware'
    get_ip = 'get_receiver_ip'
    reset = 'set_factory_default'
    send_config_file = 'send_config_file'

def arg_parse():
    """ Parse the command line you use to launch the script """
    
    parser= argparse.ArgumentParser(prog='Septentrio tool', description="A tool to send comment to a Septentrio GNSS receiver")
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--port", help="Port to connect to", type=str)
    parser.add_argument("-b", "--baudrate", help="port baudrate", default=115200, type=int)
    parser.add_argument("-c", "--command", nargs='+', help="Command to send to the gnss receiver.\nAvailable commands are: 'get_model' 'get_firmware' 'reset' 'send_config_file'", type=str)
    parser.add_argument("-s", "--store", action='store_true', help="Store settings as permanent", default=False)
    parser.add_argument("-r", "--retry", help="set a number of retry if the command fails", default=0, type=int)
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--version", action="version", version="%(prog)s 1.1")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = arg_parse()
    if args.debug:
        log.setLevel('DEBUG')
        log.debug(f"Arguments: {args}")
    command = args.command[0]
    retries = 0
    retry_delay = 2
    while retries <= args.retry:
        try:
            with SeptGnss(args.port, baudrate=args.baudrate, timeout=30, debug=args.debug) as gnss:
                res = methodcaller(CmdMapping[command].value, *args.command[1:])(gnss)
                if type(res) is str:
                    print(res)
                if args.store:
                    gnss.set_config_permanent()
            break
        except Exception as e:
            log.debug("Exception: ",e)
            retries += 1
            if retries <= args.retry:
                print("Failed...retrying in {}s".format(retry_delay))
                time.sleep(retry_delay)
    if retries > args.retry:
        print("Command failed!")
        sys.exit(1)