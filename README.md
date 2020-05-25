# RTKBase

An easy to use and easy to install web frontend with some bash scripts and services for a simple gnss base station.

### FrontEnd:
|<img src="/images/web_status.png" alt="status" width="250"/>|<img src="/images/web_settings.png" alt="settings" width="250"/>|<img src="/images/web_logs.png" alt="logs" width="250"/>|

Frontend's features are:

+ View the satellites signal levels
+ View the base location on a map
+ Start/stop various services (Sending data to a Ntrip caster, Rtcm server, Log raw data to files
+ Edit the services settings
+ Download/delete raw data

### Base example:
<img src="/images/base_f9p.jpg" alt="status" width="550" />

+ Enclosure: GentleBOX JE-200
+ SBC: Orange Pi Zero (512MB)
+ Gnss Receiver: U-Blox F9P (from Drotek)
+ Power: Trendnet TPE-113GI POE injector + Trendnet POE TPE-104GS Extractor/Splitter + DC Barrel to Micro Usb adapter

## Automated installation (with a usb ZED-F9P):

+ Connect your gnss receiver to your raspberry pi/orange pi/.... with a usb cable.

+ Open a terminal and:

   ```bash
   $ cd ~
   $ wget https://raw.githubusercontent.com/stefal/rtkbase/web_gui/tools/install.sh
   $ chmod +x install.sh
   $ sudo ./install.sh --all
   ```

+ Go grab a coffee, it's gonna take a while. The script will install the needed softwares, find your F9P receiver and set it to works as a base station.
+ Open a web browser to `http://ip_of_your_sbc`. Default password is `admin`.

## Installation: 

+ Connect your gnss receiver to raspberry pi/orange pi/.... with usb or uart, and check which com port it uses (ttyS1, ttyAMA0, something else...)

+ Set your gnss receiver to output raw data. If you need to use U-center from another computer, you can use `socat`:

   ``$ sudo socat tcp-listen:128,reuseaddr /dev/ttyS1,b115200,raw,echo=0``
   
   Change the ttyS1 and 115200 value if needed. Then you can use a network connection in U-center with the base station ip address and the port n°128.

+ clone [RTKlib](https://github.com/tomojitakasu/RTKLIB/tree/rtklib_2.4.3)

   ```bash
   $ cd ~
   $ git clone -b rtklib_2.4.3 https://github.com/tomojitakasu/RTKLIB/rtklib_2.4.3
   ```

+ compile and install str2str:

   Edit the CTARGET line in makefile in RTKLIB/app/str2str/gcc
   
   ```bash
   $ cd RTKLIB/app/str2str/gcc
   $ nano makefile
   ```
   
   For an Orange Pi Zero SBC, i use:
   
   ``CTARGET = -mcpu=cortex-a7 -mfpu=neon-vfpv4 -funsafe-math-optimizations``
   
   Then you can compile and install str2str:
   
   ```bash  
   $ make
   $ sudo make install
   ```

+ clone this repository:

   ```bash
   $ cd ~
   $ git clone https://github.com/Stefal/rtkbase.git
   ```

+ Edit settings.conf:

   ```bash
   $ cd rtkbase
   $ nano settings.conf
   ```

   The main parameters you should edit are `com_port`, `position`, and the NTRIP section if you send the stream to a caster.

+ If the U-blox gnss receiver is sets to its default settings (Raw output is disabled) you can permanently configure the receiver with `ubxconfig.sh`. For the ZED-F9P use

   ```bash
   $ ./ubxconfig.sh /dev/your_com_port receiver_cfg/U-Blox_ZED-F9P_rtkbase.txt
   ```
   This script will send the settings only if the firmware is the same release on the receiver and in the file. If your receiver use a more recent firmware, you can add the `--force` settings on the command line.
   ```bash
   $ ./ubxconfig.sh /dev/your_com_port receiver_cfg/U-Blox_ZED-F9P_rtkbase.txt --force
   ```
   
+ Do a quick test with ``$ ./run_cast.sh in_serial out_tcp`` you should see some data like this:
   ```
   2019/10/09 15:42:53 [CW---]      14020 B   19776 bps (0) /dev/ttyS1 (1) waiting...
   2019/10/09 15:42:58 [CW---]      26244 B   19558 bps (0) /dev/ttyS1 (1) waiting...
   2019/10/09 15:43:03 [CW---]      37956 B   19289 bps (0) /dev/ttyS1 (1) waiting...
   2019/10/09 15:43:08 [CW---]      49684 B   19551 bps (0) /dev/ttyS1 (1) waiting...
   2019/10/09 15:43:13 [CW---]      61488 B   17232 bps (0) /dev/ttyS1 (1) waiting...
   2019/10/09 15:43:18 [CW---]      73076 B   17646 bps (0) /dev/ttyS1 (1) waiting...
   ```
   Stop the stream with 
   
   ```bash
   $ sudo killall str2str
   ```
   
+ If everything is ok, you can copy the unit files for systemd with this script:

   ```bash
   $ sudo ./copy_unit.sh
   ```

+ Then you can enable these services to autostart during boot:  

   ``$ sudo systemctl enable str2str_tcp.service``  <-- mandatory  
   ``$ sudo systemctl enable str2str_file.service`` <-- log data locally  
   ``$ sudo systemctl enable str2str_ntrip.service`` <-- send ntrip data to a caster
   
+ You can start the services right now (ntrip and/or file), str2str_tcp.service will autostart as it is a dependency :

  ``$ sudo systemctl start str2str_file.service``  
  ``$ sudo systemctl start str2str_ntrip.service``  
  
+ If you use `str2str_file` to log the data inside the base station, you may want to compress these data and delete the too old archives. For these 2 tasks, you can use `archive_and_clean.sh`. The default settings compress the previous day data and delete all archives older than 30 days. Edit your crontab with ``$ crontab -e`` and add these lines:
   ```bash
   SHELL=/bin/bash
   0 4 * * * /home/YOUR_USER_NAME/PATH_TO_RTKBASE/archive_and_clean.sh
   ```
   Cron will run this script everyday at 4H00.

## License:
RTKBase is licensed under AGPL 3 (see LICENSE file).

RTKBase use some parts of others software:
+ [RTKLIB](https://github.com/tomojitakasu/RTKLIB) (BSD-2-Clause)
+ [ReachView](https://github.com/emlid/ReachView) (GPL v3)
+ [Flask](https://palletsprojects.com/p/flask/) [Jinja](https://palletsprojects.com/p/jinja/) [Werkzeug](https://palletsprojects.com/p/werkzeug/) (BSD-3-Clause)
+ [Flask SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO) (MIT)
+ [Bootstrap](https://getbootstrap.com/) [Bootstrap Flask](https://github.com/greyli/bootstrap-flask) [Bootstrap 4 Toggle](https://gitbrent.github.io/bootstrap4-toggle/) [Bootstrap Table](https://bootstrap-table.com/) (MIT)
+ [wtforms](https://github.com/wtforms/wtforms/) (BSD-3-Clause) [Flask WTF](https://github.com/lepture/flask-wtf) (BSD)
+ [pystemd](https://github.com/facebookincubator/pystemd) (L-GPL 2.1)
+ [gpsd](https://gitlab.com/gpsd/gpsd) (BSD-2-Clause)

RTKBase use OpenStreetMap tiles, courtesy of [Empreinte digitale](cloud.empreintedigitale.fr).
