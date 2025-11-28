#! /usr/bin/env python3

import tkinter as tk
import tkinter.font
import tkinter.ttk as ttk
import webbrowser
import threading
import scan_network
import tkinter as tk
from tkinter import ttk
import logging
import argparse
import os
logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel('ERROR')


class MyApp:
    def __init__(self, master, ports=[80, 443], allscan=False):
        self.master = master
        self.ports = ports
        self.allscan = allscan
        master.title("Find RTKBase v0.2")
        master.geometry("400x200")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        self._create_gui()
        self.available_base = None
        if os.name == 'nt':
            log.debug('"False" scan to pop up the windows firewall window')
            scan_network.zeroconf_scan('RTKBase Web Server', '_http._tcp.local.', timeout=0)

    def _create_gui(self):

        #Scanning and results frame
        self.top_frame = ttk.Frame(self.master, padding="10")
        self.top_frame.grid(row=0, column=0, sticky="nsew")
        self.top_frame.columnconfigure(0, weight=1)
        self.top_frame.rowconfigure(97, weight=1)
        self.intro_label = ttk.Label(self.top_frame, text="Click 'Find' to search for RTKBase")
        self.intro_label.grid(column=0, row=0, pady=10)
        self.scanninglabel = ttk.Label(self.top_frame, text="Searching....")
        self.scanninglabel.grid(column=0, row=0, pady=10)
        self.scanninglabel.grid_remove()
        self.progress_bar = ttk.Progressbar(self.top_frame,mode='indeterminate')
        self.progress_bar.grid(column=2, columnspan=2, row=0, pady=10)
        self.progress_bar.grid_remove()
        self.nobase_label = ttk.Label(self.top_frame, text="No base station detected")
        self.nobase_label.grid(column=0, row=0, columnspan=2, pady=10)
        self.nobase_label.grid_remove()
        self.error_label = ttk.Label(self.top_frame, text="Error")
        self.error_label.grid(column=0, row=0, columnspan=2, pady=10)
        self.error_label.grid_remove()

       
        # Scan/Quit Frame
        self.bottom_frame = ttk.Frame(self.top_frame)
        self.bottom_frame.grid(column=0, row=99, columnspan=4, sticky="ew")
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.scanButton = ttk.Button(self.bottom_frame, text="Find", command=self.scan_network)
        self.scanButton.grid(column=0, row=0, padx=(0, 5), sticky="e")
        self.quitButton = ttk.Button(self.bottom_frame, text="Quit", command=self.master.quit)
        self.quitButton.grid(column=1, row=0, padx=(5, 0), sticky="w")

         # info Frame
        """ self.info_frame = ttk.Frame(self.top_frame)
        self.info_frame.grid(column=3, row=99, sticky="ew")
        self.version_label = ttk.Label(self.info_frame, text="v0.1")
        self.version_label.grid(sticky="e") """

    def scan_network(self):
        
        #Cleaning GUI
        try:
            self.intro_label.grid_remove()
            self.error_label.grid_remove()
            for label in self.base_labels_list:
                label.destroy()
            for button in self.base_buttons_list:
                button.destroy()
        except AttributeError:
            pass
        self.nobase_label.grid_remove()
        self.scanButton.config(state=tk.DISABLED)
        self.scanninglabel.grid()
        self.progress_bar.grid()
        self.progress_bar.start()

        #Launch scan
        thread = threading.Thread(target=self._scan_thread)
        thread.start()
        
    def _scan_thread(self):
        log.debug(f"Start Scanning (ports {self.ports})")
        try:
            self.available_base = scan_network.main(self.ports, self.allscan)
        #self.available_base = [{'ip': '192.168.1.23', 'port' : 80, 'fqdn' : 'rtkbase.home'},
        #                   {'ip': '192.168.1.124', 'port' : 80, 'fqdn' : 'localhost'},
        #                   {'ip': '192.168.1.199', 'port' : 443, 'fqdn' : 'basegnss'} ]
        #self.available_base = [{'ip': '192.168.1.123', 'port' : 80, 'fqdn' : 'localhost'},]
        except Exception as e:
            log.debug(f"Error during network scan: {e}")
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.scanninglabel.grid_remove()
            self.error_label.grid()
            self.scanButton.config(state=tk.NORMAL)
            return
            
        log.debug("Scan terminated")
        self._after_scan_thread()

    def _after_scan_thread(self):
        log.debug(f"available_base: {self.available_base}")
        self.scanninglabel.grid_remove()
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.base_labels_list = ["base" + str(i) + "Label" for i, j in enumerate(self.available_base)]
        self.base_buttons_list = ["base" + str(i) + "Button" for i, j in enumerate(self.available_base)]
        if len(self.available_base)>0:
            for i, base in enumerate(self.available_base):
                def browser_fqdn(event, ip = (base.get('server') or base.get('ip')), port = base.get('port')):
                    self.launch_browser(ip, port)
                def browser_ip(event, ip = (base.get('ip')), port = base.get('port')):
                    self.launch_browser(ip, port)

                self.base_labels_list[i] = ttk.Label(self.top_frame, text=f"{base.get('server') or base.get('fqdn')} ({base.get('ip')})")
                self.base_labels_list[i].grid(column=0, row=i)
                self.base_buttons_list[i] = ttk.Button(self.top_frame, text='Open')
                self.base_buttons_list[i].bind("<Button-1>", browser_fqdn)
                self.base_buttons_list[i].bind("<Shift-Button-1>", browser_ip)
                self.base_buttons_list[i].grid(column=3, row=i)
        else:
            self.nobase_label.grid()
        self.scanButton.config(state=tk.NORMAL)

    def launch_browser(self, ip, port):
        print('{} port {}'.format(ip, port))
        webbrowser.open(f"http://{ip}:{port}")

def arg_parse():
    """ Parse the command line you use to launch the script """
    
    parser= argparse.ArgumentParser(prog='Scan for RTKBase', description="A tool to scan network and find Rtkbase Gnss base station")
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--ports", nargs='+', help="Port(s) used to find the web server. Default value is 80 and 443", default=[80, 443], type=int)
    parser.add_argument("-a", "--allscan", help="force scan with mDns AND ip range", action='store_true')
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = arg_parse()
    if args.debug:
        log.setLevel('DEBUG')
        log.debug(f"Arguments: {args}")
    root = tk.Tk()
    iconpath = os.path.join(os.path.dirname(__file__), 'rtkbase_icon.png')
    icon = tk.PhotoImage(file=iconpath)
    root.wm_iconphoto(False, icon)
    app = MyApp(root, args.ports, args.allscan)
    root.mainloop()
