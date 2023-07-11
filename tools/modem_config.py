#! /usr/bin/env python3

import sys
sys.path.insert(1, '/home/basegnss/sim-modem/src/')
import argparse
from sim_modem import *

def arg_parse():
    parser=argparse.ArgumentParser(
        description="SIMCom 76XX LTE modem configuration and informations",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--device",
        default='/dev/ttymodemAT',
        type=str,
        help="device path"
    )
    parser.add_argument(
        "-i",
        "--informations",
        action="store_true",
        default=True,
        help="Display various modem informations"
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store_true",
        default=False,
        help="Configure the modem in ECM Mode"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug mode"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="release 0.1"
    )
    args = parser.parse_args()
    print(args)
    return args

if __name__ == '__main__':
    args=arg_parse()
    modem=modem = Modem(args.device, debug=args.debug)
    if args.informations:
        #modem=modem = Modem('/dev/ttymodemAT', debug=True)
        print("Manufacturer: ",modem.get_manufacturer_identification())
        print("Model: ", modem.get_model_identification())
        print("Sim status: ", modem.get_sim_status())
        print("Signal Quality: ",modem.get_signal_quality())
        print("Signal Quality: ", modem.get_signal_quality_range().name)
        print("Network registration: ", modem.get_network_registration_status())
        print("Data network registration", modem.get_eps_network_registration_status())
        print("Network mode selection: ", modem.get_network_mode())
        print("Current network mode: ", modem.get_current_network_mode().name)
        print("EU system information: ",modem.get_eu_system_informations())

    if args.config:
        print("Configuring the modem in ECM Mode")
        print("It will reboot the modem !")
        modem.set_autodial_mode(0)
        modem.set_data_connection_mode(DataMode["ECM"])
        print("Done!")
        print("Please wait a few minutes before trying to use it")
