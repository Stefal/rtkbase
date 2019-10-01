# rtkbase

Some bash scripts for a simple gnss base station

Usage: 
- Connect your gnss receiver to raspberry pi/orange pi/.... with usb or uart.
- Set your gnss receiver to output raw data
- clone rtklib
- compile and install str2str
- clone this repository
- Check which tty your receiver is connected to
- Edit settings.conf
- Do a quick test with ``./run_cast.sh in_serial out_tcp``   (you should see some data "10972 B   17117 bps (0) /dev/ttyS1 (1) waiting...")
- If everything is ok, you can run ``./copy_unit.sh`` to copy unit files for systemd
- Then you can enable these services to autostart:
``sudo systemctl enable str2str_tcp.service``  <-- mandatory
``sudo systemctl enable str2str_file.service`` <-- log data locally
``sudo systemctl enable str2str_ntrip.service`` <-- send ntrip data to a caster
