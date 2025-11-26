# Changelog

## [2.6.4] - 2025-11-26
### Fixed
- GUI -> Diagnostic: Fix missing line return. [#480](https://github.com/Stefal/rtkbase/issues/480)
- Install missing Avahi-daemon service and settings

## [2.6.3] - 2025-02-16
### Added
- New [Linux/Windows Gui](https://github.com/Stefal/rtkbase/tree/master/tools/find_rtkbase/dist) to detect online Station.
- Add Unicore UM980/UM982 support (rtcm3 mode). [#351](https://github.com/Stefal/rtkbase/issues/351)
- Add api to get basics informations about the base station (/api/v1/infos)
- Add Zeroconf/Avahi service definition to get a fast online Rtkbase station detection.
- Detect Gnss receiver firmware version during receiver detection. [#428](https://github.com/Stefal/rtkbase/issues/428)
- GUI -> Logs: Non-zipped files can be convert to rinex. [#348](https://github.com/Stefal/rtkbase/issues/348)
- GUI -> Settings: Display network informations.
- GUI -> Settings: Better changelog display (Convert markdown to html).
### Changed
- Faster Septentrio Mosaic-X5 detection
### Fixed
- Fix some services were not restarted after saving new settings in the main service.
- Fix pystemd result request for timer services. [#162](https://github.com/Stefal/rtkbase/issues/162) [#445](https://github.com/Stefal/rtkbase/issues/445)
- Increase free space for archiving Mosaic-X5 data. [#369](https://github.com/Stefal/rtkbase/issues/369)
- Various fixes [#441](https://github.com/Stefal/rtkbase/issues/441) [#443](https://github.com/Stefal/rtkbase/issues/443) [#450](https://github.com/Stefal/rtkbase/issues/450)
### Security
- GUI -> Logs: Fix path traversal vulnerability.

## [2.6.2] - 2024-10-06
### Added
- Added Rtkbase gnss reverse proxy service in the diagnostic view. [#421](https://github.com/Stefal/rtkbase/issues/421)
### Fixed
- Remove firstboot service on Raspberry Pi image >= 2.5 which was causing services to stay stopped after a reboot. [#436](https://github.com/Stefal/rtkbase/issues/436)
- Reboot autorefresh timeout is now 90s. [#426](https://github.com/Stefal/rtkbase/issues/426)
 
## [2.6.1] - 2024-08-26
### Changed
- More tests before installing prebuilt RTKLib cli tools.
### Fixed
- Build rtklib if previous installed release is not working. [#418](https://github.com/Stefal/rtkbase/issues/418)
- Insert new release number into settings.conf before restarting services. [#411](https://github.com/Stefal/rtkbase/issues/411)
- Custom web_port setting was not used. [#419](https://github.com/Stefal/rtkbase/issues/419)
- Cellular modem: nmcli connection was not updated after a switch to public ip address.

## [2.6.0] - 2024-07-05
### Added
- Septentrio Mosaic-X5 detection and configuration
- Reverse proxy server with Rtkbase authentication, for Mosaic-X5 web interface
- Added description below form input. [#381](https://github.com/Stefal/rtkbase/issues/381)
- New optional service, rtkbase_raw2nmea.service, to get date and time with a gnss receiver unknown to gpsd. (CLI only) [#394](https://github.com/Stefal/rtkbase/issues/394)
### Changed
- RTKLib upgraded to release b34j from rtklibexplorer.
- Switch server from eventlet to gevent + Gunicorn server.
### Deprecated
- Operating systems older than Debian 11 / Ubuntu 22.04 can't update RTKBase anymore.
- Python release < 3.8 deprecated
### Removed
- Eventlet python module is not needed anymore.
### Fixed
- Remove Sbas rtcm message (1107) after F9P configuration. [#391](https://github.com/Stefal/rtkbase/issues/391)
- Tooltips buttons were a link to top page. [#387](https://github.com/Stefal/rtkbase/issues/387)
- Fix armbian ramlog bug with log older than 1 day. https://github.com/Stefal/build/issues/16
- Archive service will compress .sbf files too.
- Fix duplicates in .sbf to rinex conversion : https://github.com/rtklibexplorer/RTKLIB/issues/186
- Various fixes : [#374](https://github.com/Stefal/rtkbase/issues/374)
### Security
- Update various python modules.

## [2.5.0] - 2024-01-30
### Added
- udev rules to create ttyGNSS port for usb connected F9P.
- Added UART connected F9P detection and configuration.
- Some scripts for using a base with a 4G Simcom A76XX modem. (Beta).
- Rules to manage rtkbase services without sudo (Bookworm or newer).
- Trying to detect the wrong cpu temp on Orange Pi Zero. [#224](https://github.com/Stefal/rtkbase/issues/224)
- Buttons and collapsing informations on the diagnostic page.
### Changed
- RTKLib upgraded to release b34i from rtklibexplorer.
- RTKBase now use a virtual environnement for the python environnement
- install.sh -> --detect-usb-gnss renamed to --detect-gnss
- Rinex conversion -> limit to 2 frequencies removed in "full" presets
- Rinex conversion -> receiver option (-TADJ=1 for ubx) is sourced from settings.conf
- Logs -> default time overlap changed from 30s to 0s
### Fixed
- More tests before copying RTKLib binaries. [#313](https://github.com/Stefal/rtkbase/issues/313)
- Skip unknown section or key when restoring settings. [#336](https://github.com/Stefal/rtkbase/issues/336)
- Fix space detection in various forms inputs.
- Fix broken form input validation patterns. [#353](https://github.com/Stefal/rtkbase/issues/353)
- Fix some issues with Orange Pi Zero images. [#361](https://github.com/Stefal/rtkbase/issues/361)
### Security
- Update of various python modules.
- Apply some restrictions on RTKBase services. [#341](https://github.com/Stefal/rtkbase/issues/341)

## [2.4.2] - 2023-11-10
### Fixed
- Pin Werkzeug module to v2.2.2 to fix dependencie failure. [#330](https://github.com/Stefal/rtkbase/issues/330)
 
## [2.4.1] - 2023-02-26
### Fixed
- GUI -> Settings: Fixed GNSS detect & configure. [#303](https://github.com/Stefal/rtkbase/issues/303)

## [2.4.0] - 2023-02-20
### Added
- GUI -> Settings: Added a 2nd NTRIP output. [#240](https://github.com/Stefal/rtkbase/issues/240)
- GUI -> Settings: Added features to backup, restore and reset RTKBase settings.
- GUI -> Settings: Added a button to detect and/or configure the gnss receiver. [#70](https://github.com/Stefal/rtkbase/issues/70)
- GUI -> Settings: Added a button to show/hide the Ntrip passwords. Thanks to @GwnDaan [#208](https://github.com/Stefal/rtkbase/issues/208) 
- GUI -> Settings: Added Gnss receiver informations (Model and firmware release).
- GUI -> Settings: Added Operating system informations.
- GUI -> Settings: Alert when user wants to leave the page with unsaved settings. [#235](https://github.com/Stefal/rtkbase/issues/235)
- GUI -> Status: Added tooltip on the blue pin to explain that it's a coarse location. [#247](https://github.com/Stefal/rtkbase/issues/247)
- GUI -> Status: Added an alert if the main service isn't active.
- GUI -> Logs: Added 3 more Rinex presets, and modified rinex window layout. [#43](https://github.com/Stefal/rtkbase/issues/43) [#134](https://github.com/Stefal/rtkbase/issues/134) [#190](https://github.com/Stefal/rtkbase/issues/190) [#200](https://github.com/Stefal/rtkbase/issues/200)
- Bidirectionnal communication with the gnss receiver is enabled. [#277](https://github.com/Stefal/rtkbase/issues/277)
- More informations are available in the local caster source table. [#183](https://github.com/Stefal/rtkbase/issues/183)
- Port number for the web server is configurable in settings.conf
### Changed
- RTKLib upgraded to release b34g from rtklibexplorer. [#222](https://github.com/Stefal/rtkbase/issues/222)
- RTKLib binaries are bundled for armv6l, armv7l, aarch64, x86. Compilation from source isn't needed anymore for these platforms.
- Command line: Many changes on install.sh arguments/options. See `install.sh --help`
- Flask upgraded to v2.2.2 and other dependencies upgraded too.
- SocketIO upgraded to v4.4.1
- Bootstrap upgraded to v4.6.1
- Bootstrap-table upgraded to v1.21.1
- Password for local caster isn't mandatory anymore. Thanks to @GwnDaan [#210](https://github.com/Stefal/rtkbase/issues/210)
- Change socketio connection method. Thanks to @jaapvandenhandel
- Change 127.0.0.1 to localhost for better ipv6 support. Thanks to @by
### Fixed
- GUI -> Status: Sat. levels and coordinates are set to zero in case of a signal interruption. [#164](https://github.com/Stefal/rtkbase/issues/164)
- GUI -> Status: Sat. levels are left align. Thanks to @GwnDaan [#72](https://github.com/Stefal/rtkbase/issues/72)
- GUI -> Status: New provider for OpenStreetMap HOT tiles.
- GUI: After a RTKBase update, the browser won't use the old javascript files anymore (cache busting). [#217](https://github.com/Stefal/rtkbase/issues/217)
- Remaining space check could not work with non english shell. Thanks to @GwnDaan [#213](https://github.com/Stefal/rtkbase/issues/213)
- GUI -> Settings: No more "bounce" issues with the switches. Thanks to @GwnDaan
- Max Cpu temp was not updated when no user were connected. Thanks to @GwnDaan
- GUI -> Settings: Check update now display an error in case of a connection error. Thanks to @GwnDaan [#221](https://github.com/Stefal/rtkbase/issues/221)
- GUI -> Logs: Better logs table behaviour on mobile devices.
- Grep pattern fixed on PPS example. Thanks to @by.

### Security

## [2.3.4] - 2022-04-01
### Fixed 
- Failure with some python dependancies. [#215](https://github.com/Stefal/rtkbase/issues/215)
- More fixes with Gpsd service restart. [#94](https://github.com/Stefal/rtkbase/issues/94)

## [2.3.3] - 2022-02-28
### Fixed
- Fix the Rinex conversion failure. [#206](https://github.com/Stefal/rtkbase/issues/206)
- Restart Ntrip/Rtcm services after an update. [#171](https://github.com/Stefal/rtkbase/issues/171)
- When the Main service restart, Gpsd service restart too [#94](https://github.com/Stefal/rtkbase/issues/94)

## [2.3.2] - 2022-02-22
### Added
- GUI -> Status: Added a new default map background : Osm "standard", from osm.org.
- GUI: The footer include a link to the github repo. [#191](https://github.com/Stefal/rtkbase/issues/191)
- GUI -> Settings : Board name is displayed in the System Settings section. [#194](https://github.com/Stefal/rtkbase/issues/194)
### Changed
- Leafletjs upgraded to release 1.7
- GUI -> Status: Ortho HR (aerial images) max zoom changed from 20 to 21.
### Fixed
- GUI -> Settings: "Save" buttons are disabled when a new setting is saved. [#193](https://github.com/Stefal/rtkbase/issues/193)
- Rtcm and Ntrip services are restarded after a RTKBase update. [#171](https://github.com/Stefal/rtkbase/issues/171)
- The Rinex conversion is more robust and error message is more understandable.
- GUI -> Rinex conversion is now enabled only for zip files.

## [2.3.1] - 2021-07-25
### Fixed
- Local ntrip caster was not started with the right user/password syntax. [#166](https://github.com/Stefal/rtkbase/issues/166)
- Local ntrip caster service was not restarted after new settings were set. [#167](https://github.com/Stefal/rtkbase/issues/167)
- Psutil python requirement could not be installed on Os already including it (like Raspberry Pi Os with desktop). [#165](https://github.com/Stefal/rtkbase/issues/165)

## [2.3.0] - 2021-07-08
### Added
- New local Ntrip Caster service to use RTKBase as a standalone NTRIP Caster.
- GUI -> Status: New OrthoHR aerial imagery layer, covering France only.
- GUI -> Status: Realtime and static base position stay both visible on the map.
- GUI -> Status: Solution status is displayed next to coordinates.
- GUI -> Settings: Service status are updated in realtime, and painted with orange/red in case of restart/failure.
- GUI -> Settings: Display Cpu temperature.
- GUI -> Settings: Display uptime.
- GUI -> Settings: Display storage informations.
- GUI -> Settings: Tooltips to display some help about each services.
- GUI : Auto reconnection with the web server after a RTKBase update or a server (SBC) reboot.

### Changed
- Default antenna value sets to 'ADVNULLANTENNA' instead of 'NULLANTENNA'.

### Fixed
- Rtkbase was deleting old archives when remaining space was lower than 5GB instead of 500MB. And now you can change this value inside `settings.conf`. [#132](https://github.com/Stefal/rtkbase/issues/132)
- rtkrcv configuration was hardcoded with ubx input, now it uses the format set on GUI -> Settings -> Main. [#148](https://github.com/Stefal/rtkbase/issues/148)
- Only .ubx files were archived. Now archive_and_clean.sh script check for all files format managed by str2str. [#158](https://github.com/Stefal/rtkbase/issues/158)
- The 2.1.x to 2.2.0 upgrade created a wrong path inside str2str_rtcm_serial.service (/var/tmp/rtkbase)
- rtkrcv didn't always stop after the 1O mn timeout. [#35](https://github.com/Stefal/rtkbase/issues/35)

### Security
- Cryptography module updated to 3.3.2
- Eventlet module updated to 0.31.0

## [2.2.0] - 2021-01-12
### Added
- New Rtcm serial service to send a rtcm stream on a serial output, like a radio module
- RTKBase release number, receiver model, and antenna information are sent on RTCM stream (message 1008 and 1033 added)
- GUI->Status: Button to copy realtime coordinates to the clipboard
- GUI->Settings: You can edit the antenna info in the Main service options
- GUI->Settings: Spinners and countdown added on reboot modal window
- GUI->Settings: Auto refresh the webpage after a reboot (fixed time duration)
- The archive_and_clean script delete oldest archives if there is less than 500MB available.
- The install script check if there is enough space before starting

### Changed
- Upgrade to RTKLib v2.4.3-b34
- Pystemd updated to 0.8.0
- Pystemd is now installed from Pypi
- Some python module updates
- More dependencies are installed for aarch64 platform
- The realtime base location calculation is now using dual-frequency ionosphere correction. You won't see the location anymore if you use a single frequency receiver.
- Default value for archive rotation lowered to 60 days.

### Fixed
- Cleaning update modal box when closing it
- writing absolute path to python3 in rtkbase_web unit file

### Security
- Cryptography module updated to 3.3.1

## [2.1.1] - 2020-07-30
### Fixed
- rtcm services was sending data to the ntrip caster.

## [2.1.0] - 2020-07-22
### Added
- GUI -> Status: Marker on the map with the fixed base's coordinates.
- GUI -> Status: Optional Maptiler aerial image layer on the map (see 'Advanced' section in README.md)
- GUI -> Settings: Receiver dependent options on Rtcm and Ntrip output
- GUI -> Settings: Services diagnostic
- GUI -> Logs: Option to convert a zipped ubx archive to Rinex (for the IGN "Calculs GNSS Réseau en ligne")
- Miscellaneous: You can run install.sh from anywhere
- Miscellaneous: Freeze python modules inside requirements

### Changed
- Gnss receiver (ZED-F9P): Disabling SBAS during configuration
- Gnss receiver (U-Blox): During the first installation, if a U-Blox receiver is detected, -TADJ=1 will be added for Rtcm and Ntrip outputs. See [#80](https://github.com/Stefal/rtkbase/issues/80)
- Gnss receiver: The config files extension is now .cfg

### Fixed
- install.sh: Check if logname return a correct value
- install.sh: Add dialout group to user
- various bugfixes

## [2.0.2] - 2020-06-09
### Added
- Web interface
- Satellite levels
- Map
- Setting configuration from the webpage
- Download/Delete raw data
- Automatic installation
- Automatic setup for usb connected Ublox Zed-F9P
- Multiple simultaneous streams (Raw/Rtcm/Ntrip)

## [1.0.0] - 2019-12-19
### Added
- First official Release

## [0.0.1] - 2019-03-02
### Added
- First beta release

### Changed
### Deprecated
### Removed
### Fixed
### Security
