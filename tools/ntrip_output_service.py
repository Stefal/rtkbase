"""Run one independently configured NTRIP output; never open a GNSS device."""
import argparse,configparser,os
from pathlib import Path
from ntrip_routing import resolve_route,ex_command,value

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--channel',choices=list('ABCDEF'),required=True);args=parser.parse_args()
    config=configparser.ConfigParser(interpolation=None);config.read([args.root/'settings.conf.default',args.root/'settings.conf'])
    route=resolve_route(config,args.channel)
    configured=value(config,'general','ntrip_ex_binary') or value(config,'general','cast')
    binary=Path(configured)
    if not binary.is_absolute() or not binary.is_file() or not os.access(binary,os.X_OK):raise ValueError('Configure an executable str2str binary path')
    command=ex_command(binary,route,value(config,'main','position'))
    antenna=value(config,'main','antenna_info')
    if antenna:command.extend(['-a',antenna])
    command.extend(['-i','RTKBase '+route.source.label])
    os.execv(str(binary),command)

if __name__=='__main__':main()
