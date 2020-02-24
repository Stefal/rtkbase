# rtkbase

Some bash scripts for a simple gnss base station

## Installation: 

+ Connect your gnss receiver to raspberry pi/orange pi/.... with usb or uart, and check which com port it uses (ttyS1, ttyAMA0, something else...)

+ Set your gnss receiver to output raw data. If you need to use U-center from another computer, you can use `socat`:

   ``$ sudo socat tcp-listen:128,reuseaddr /dev/ttyS1,b115200,raw,echo=0``
   
   Change the ttyS1 and 115200 value if needed. Then you can use a network connection in U-center with the base station ip address and the port n°128.

+ clone [RTKlib](https://github.com/tomojitakasu/RTKLIB/tree/rtklib_2.4.3)

   ```
   $ cd ~
   $ git clone -b rtklib_2.4.3 https://github.com/tomojitakasu/RTKLIB/tree/rtklib_2.4.3
   ```

+ compile and install str2str:

   Edit the CTARGET line in makefile in RTKLIB/app/str2str/gcc
   
   ```
   $ cd RTKLIB/app/str2str/gcc
   $ nano makefile
   ```
   
   For an Orange Pi Zero SBC, i use:
   
   ``CTARGET = -mcpu=cortex-a7 -mfpu=neon-vfpv4 -funsafe-math-optimizations``
   
   Then you can compile and install str2str:
   
   ```  
   $ make
   $ sudo make install
   ```

+ clone this repository:

   ```
   $ cd ~
   $ git clone https://github.com/Stefal/rtkbase.git
   ```

+ Edit settings.conf:

   ```
   $ cd rtkbase
   $ nano settings.conf
   ```

   The main parameters you should edit are `com_port`, `position`, and the NTRIP section if you send the stream to a caster.

+ If the U-blox gnss receiver is sets to its default settings (Raw output is disabled) you can permanently configure the receiver with `ubxconfig.sh`. For the ZED-F9P use

   ```
   $ ./ubxconfig.sh /dev/your_com_port receiver_cfg/U-Blox_ZED-F9P_rtkbase.txt
   ```
   This script will send the settings only if the firmware is the same release on the receiver and in the file. If your receiver use a more recent firmware, you can add the `--force` settings on the command line.
   ```
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
   
   ```
   $ sudo killall str2str
   ```
   
+ If everything is ok, you can copy the unit files for systemd with this script:

   ```
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
   ```
   SHELL=/bin/bash
   0 4 * * * /home/YOUR_USER_NAME/PATH_TO_RTKBASE/archive_and_clean.sh
   ```
   Cron will run this script everyday at 4H00.
