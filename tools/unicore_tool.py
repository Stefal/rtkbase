#! /usr/bin/env python3

import os
import sys
import argparse
import logging
from unicore.unicore_gnss.unicore_cmd import *
from enum import Enum
from operator import methodcaller

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('ERROR')

class CmdMapping(Enum):
    """Mapping human command to unicore_cmd methods"""

    get_model = 'get_receiver_model'
    get_firmware = 'get_receiver_firmware'
    reset = 'set_factory_default'
    send_config_file = 'send_config_file'

def arg_parse():
    """ Parse the command line you use to launch the script """
    
    parser= argparse.ArgumentParser(prog='Unicore tool', description="A tool to send comment to a Unicore GNSS receiver")
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--port", help="Port to connect to", type=str)
    parser.add_argument("-b", "--baudrate", help="port baudrate", default=115200, type=int)
    parser.add_argument("-c", "--command", nargs='+', help="Command to send to the gnss receiver.\nAvailable commands are: 'get_model' 'get_firmware' 'reset' 'send_config_file'", type=str)
    parser.add_argument("-s", "--store", action='store_true', help="Store settings as permanent", default=False)
    parser.add_argument("-r", "--retry", help="set a number of retry if the command fails", default=0, type=int)
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = arg_parse()
    if args.debug:
        log.setLevel('DEBUG')
        log.debug(f"Arguments: {args}")
    command = args.command[0]
    retries = 0
    retry_delay = 10
    while retries <= args.retry:
        try:
            with UnicoGnss(args.port, baudrate=args.baudrate, timeout=2, debug=False) as gnss:
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
                log.warning("Failed...retrying in {}s".format(retry_delay))
                time.sleep(retry_delay)
    if retries > args.retry:
        print("Command failed!")
        sys.exit(1)