# rtkbase

Some bash scripts for a simple gnss base station

## Installation: 

+ Connect your gnss receiver to raspberry pi/orange pi/.... with usb or uart, and check which com port it uses (ttyS1, ttyAMA0, something else...)

+ Set your gnss receiver to output raw data. If you need to use U-center from another computer, you can use `socat`:

   ``sudo socat tcp-listen:128,reuseaddr /dev/ttyS1,b115200,raw,echo=0``
   
   Change the ttyS1 and 115200 value if needed. Then you can use a network connection in U-center with the base station ip address and the port n°128.

+ clone [RTKlib](https://github.com/tomojitakasu/RTKLIB/tree/rtklib_2.4.3)

   ```
   cd ~
   git clone https://github.com/tomojitakasu/RTKLIB/tree/rtklib_2.4.3
   ```

+ compile and install str2str:

   Edit the CTARGET line in makefile in RTKLIB/app/str2str/gcc
   
   ```
   cd RTKLIB/app/str2str/gcc
   nano makefile
   ```
   
   For an Orange Pi Zero SBC, i use:
   
   ``CTARGET = -mcpu=cortex-a7 -mfpu=neon-vfpv4 -funsafe-math-optimizations``
   
   Then you can compile and install str2str:
   
   ```  
   make
   sudo make install
   ```

+ clone this repository:

   ```
   cd ~
   git clone https://github.com/Stefal/rtkbase.git
   ```

+ Edit settings.conf:

   ```
   cd rtkbase
   nano settings.conf
   ```

   The main parameters you should edit are `com_port`, `position`, and the NTRIP section if you send the stream to a caster.

+ Do a quick test with ``./run_cast.sh in_serial out_tcp``   (you should see some data "10972 B   17117 bps (0) /dev/ttyS1 (1) waiting...")

+ If everything is ok, you can run ``sudo ./copy_unit.sh`` to copy unit files for systemd

+ Then you can enable these services to autostart during boot:  

   ``sudo systemctl enable str2str_tcp.service``  <-- mandatory  
   ``sudo systemctl enable str2str_file.service`` <-- log data locally  
   ``sudo systemctl enable str2str_ntrip.service`` <-- send ntrip data to a caster
   
+ You can start the services right now (ntrip and/or file), str2str_tcp.service will autostart as it is a dependency :

  ``sudo systemctl start str2str_file.service``  
  ``sudo systemctl start str2str_file.service``  
