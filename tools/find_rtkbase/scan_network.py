#! /usr/bin/env python3
import time
import logging
import argparse
import requests
import scapy.all as scapy
scapy.load_layer("http")
from zeroconf import Zeroconf
from zeroconf import ServiceBrowser
logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('ERROR')

class MyZeroConfListener:
    def __init__(self):
        self.services = []

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        log.debug(f"Service found: {name}")
        self.services.append(info)
    
    def update_service(self, *args, **kwargs):
        pass

def zeroconf_scan(name, prot_type, timeout=5):
    log.debug("Scanning with zeroconf")
    service_list = []
    zeroconf = Zeroconf()
    listener = MyZeroConfListener()
    browser = ServiceBrowser(zeroconf, prot_type, listener)
    time.sleep(timeout)
    for service in listener.services:
        if name.lower() in service.name.lower():
            service_list.append({'NAME' : service.name,
                                'PORTS' : [service.port],
                                'SERVER' : service.server.rstrip('.'),
                                'IP' : '.'.join(str(byte) for byte in service.addresses[0])})
    log.debug(f"filtered list for {name}")
    log.debug(service_list)
    return service_list



def arp_scan(ip, interface=conf.iface):
    arp_request = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    log.debug(f"{interface} : {ip}")
    try:
        answered_list = []
        answered_list = scapy.srp(arp_request_broadcast, iface=interface, timeout=1, verbose=False)[0]
    except (PermissionError) as e:
        log.debug(f"{interface} - {ip} : {e}")
        pass
    results = []

    for element in answered_list:
        result = {"IP": element[1].psrc, "MAC": element[1].hwsrc}
        results.append(result)
    return results

def ping_scan(ip):
    """ Not in use, it doesn't work on windows"""
    TIMEOUT=2
    conf.verb = 0
    for ip in range(0, 256):
        packet = scapy.IP(dst="192.168.1." + str(ip), ttl=20)/scapy.ICMP()
        reply = scapy.sr1(packet, timeout=TIMEOUT)
    if not (reply is None):
         print(reply.dst, "is online")
    else:
         print("Timeout waiting for %s" % packet[IP].dst)

def tcp_scan(ip, ports):
    """
    Performs a TCP scan by sending SYN packets to <ports>.
    Args:
        ip (str): An IP address or hostname to target.
        ports (list or tuple of int): A list or tuple of ports to scan.
    Returns:
        A list of ports that are open.
    """

    try:

        syn = scapy.IP(dst=ip) / scapy.TCP(dport=ports, flags="S")
    except scapy.socket.gaierror:
        raise ValueError('Hostname {} could not be resolved.'.format(ip))


    ans, unans = scapy.sr(syn, timeout=2, retry=1, verbose=False)
    result = []
    
    for sent, received in ans:
        if received[scapy.TCP].flags == "SA":
            result.append(received[scapy.TCP].sport)

    return result

def get_rtkbase_infos(host_list):
    available_rtkbase = []
    for result in host_list:
        if result.get('PORTS') and len(result.get('PORTS')) > 0:
            try:
                for port in result.get('PORTS'):
                    #try with mDns server name at first, then with the ip address if it fails
                    for address in (result.get('SERVER'), result.get('IP')):
                        try:
                            ans = None
                            if address is None:
                                continue
                            log.debug(f"{address}:{port} Api request")
                            res = requests.get(f"http://{address}:{port}/api/v1/infos", timeout=10)
                            log.debug(f"{address}:{port} Api response: {res}")
                            ans = res.json() if res is not None and res.status_code == 200 else None
                            if ans:
                                break
                        except (TimeoutError, TypeError, requests.exceptions.ConnectionError) as e:
                            log.debug(f"{address}:{port} - {e}")

                    if ans and ans.get('app') == 'RTKBase':
                        available_rtkbase.append({'ip' : result.get('IP'),
                                                 'port' : port,
                                                 'app_version' : ans.get('app_version'),
                                                 'fqdn' : ans.get('fqdn'),
                                                 'server' : result.get('SERVER')})
            except (AttributeError, ValueError) as e:
                log.debug(e)
                pass
            #except Exception as e:
            #    print(result.get('IP'), result.get('PORTS'), e)
    return available_rtkbase

def display_results(results):
    print("IP Address\t\tMAC Address\t\tOPEN PORT(S)")
    print("-----------------------------------------")
    for result in results:
        print("{}\t\t{}\t\t{}".format(result.get("IP"), result.get("MAC"), str(result.get('PORTS'))))

def remove_duplicate_hosts(hosts_list):
    """ take a list of dicts containing rtkbase hosts to remove
        the duplicates
        It keeps at least one entry per hosts, if possible the one
        which contains a server key/value
    """
    duplicate_groups = {}
    for d in hosts_list:
        key = (d['ip'], d['port'])
        if key not in duplicate_groups:
            duplicate_groups[key] = []
        duplicate_groups[key].append(d)

    filtered_list = []
    for group in duplicate_groups.values():
        valid_servers = [d for d in group if d['server'] and d['server'] != 'None']
        if valid_servers:
            filtered_list.extend(valid_servers)
        else:
            filtered_list.append(group[0])

    return filtered_list

def arg_parse():
    """ Parse the command line you use to launch the script """
    
    parser= argparse.ArgumentParser(prog='Scan for RTKBase', description="A tool to scan network and find Rtkbase Gnss base station")
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--ports", nargs='+', help="Port(s) used to find the web server. Default value is 80 and 443", default=[80, 443], type=int)
    parser.add_argument("-a", "--allscan", help="force scan with mDns AND ip range", action='store_true')
    parser.add_argument("-i", "--iprange", help="ip range to scan eg 192.168.1.0/24", type=str)
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    arguments = parser.parse_args()
    return arguments


def main(ports, allscan=False, iprange=None):

    #interfaces = scapy.get_working_ifaces()
    scan_results = []
    scan_results.extend(zeroconf_scan('RTKBase Web Server', '_http._tcp.local.'))
    arp_results=[]
    if allscan or len(scan_results) == 0:
        log.debug("No result with zeroconf (or --allscan). Trying with ip range")
        if iprange:
            #log.debug(f"{conf.iface} : {iprange}")
            arp_results.extend(arp_scan(iprange, conf.iface))
        interfaces = {value.name : scapy.get_if_addr(value.name) for value in scapy.get_working_ifaces() if not 
                            (scapy.get_if_addr(value.name).startswith('0.0') or 
                            scapy.get_if_addr(value.name).startswith('169.254') or
                            scapy.get_if_addr(value.name).startswith('127.0.0.1')
                            )}        
        for iface, ip in interfaces.items():
            #log.debug(f"{iface} : {ip}/24")
            arp_results.extend(arp_scan(ip + '/24', iface))
        for result in arp_results:
            result['PORTS']=tcp_scan(result['IP'], ports)
    scan_results.extend(arp_results)
    log.debug("Potential available addresses:")
    log.debug(scan_results)
    available_rtkbase = get_rtkbase_infos(scan_results)
    #remove duplicate
    available_rtkbase = remove_duplicate_hosts(available_rtkbase)
    log.debug("RTKBase station found: ")
    log.debug(available_rtkbase)
    return available_rtkbase

if __name__ == "__main__":
    args = arg_parse()
    if args.debug:
        log.setLevel('DEBUG')
        log.debug(f"Arguments: {args}")
    print(main(args.ports, args.allscan, args.iprange))