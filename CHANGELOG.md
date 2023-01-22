# Changelog

## [2.4.0] - not released
### Added
- GUI -> Settings: Added a 2nd NTRIP output. #240
- GUI -> Settings: Added features to backup, restore and reset RTKBase settings.
- GUI -> Settings: Added a button to detect and/or configure the gnss receiver. #70
- GUI -> Settings: Added a button to show/hide the Ntrip passwords. Thanks to @GwnDaan #208 
- GUI -> Settings: Added Gnss receiver informations (Model and firmware release).
- GUI -> Status: Added tooltip on the blue pin to explain that it's a coarse location. #247
- GUI -> Status: Added an alert if the main service isn't active.
- GUI -> Logs: Added 3 more Rinex presets, and modified rinex window layout. #43 #134 #190 #200
- More informations are available in the local caster source table. #183
- Port number for the web server is configurable in settings.conf
### Changed
- RTKLib upgrade to release b34g from rtklibexplorer. #222
- Command line: Many changes on install.sh arguments/options. See `install.sh --help`
- Flask upgraded to v2.2.2 and other dependencies upgraded too.
- SocketIO upgraded to v4.4.1
- Bootstrap upgraded to v4.6.1
- Bootstrap-table upgraded to v1.21.1
- Password for local caster isn't mandatory anymore. Thanks to @GwnDaan #210
### Fixed
- GUI -> Status: Sat. levels and coordinates are set to zero in case of a signal interruption. #164
- GUI -> Status: Sat. levels are left align. Thanks to @GwnDaan #72
- GUI -> Status: New provider for OpenStreetMap HOT tiles.
- GUI: After a RTKBase update, the browser won't use the old javascript files anymore (cache busting). #217
- Remaining space check could not work with non english shell. Thanks to @GwnDaan #213
- GUI -> Settings: No more "bounce" issues with the switches. Thanks to @GwnDaan
- Max Cpu temp was not updated when no user were connected. Thanks to @GwnDaan
- GUI -> Settings: Check update now display an error in case of a connection error. Thanks to @GwnDaan #221
- GUI -> Logs: Better logs table behaviour on mobile devices.

### Security

## [2.3.4] - 2022-04-01
### Fixed 
- Failure with some python dependancies. #215
- More fixes with Gpsd service restart. #94

## [2.3.3] - 2022-02-28
### Fixed
- Fix the Rinex conversion failure. #206
- Restart Ntrip/Rtcm services after an update. #171
- When the Main service restart, Gpsd service restart too #94

## [2.3.2] - 2022-02-22
### Added
- GUI -> Status: Added a new default map background : Osm "standard", from osm.org.
- GUI: The footer include a link to the github repo. #191
- GUI -> Settings : Board name is displayed in the System Settings section. #194
### Changed
- Leafletjs upgraded to release 1.7
- GUI -> Status: Ortho HR (aerial images) max zoom changed from 20 to 21.
### Fixed
- GUI -> Settings: "Save" buttons are disabled when a new setting is saved. #193
- The Rinex conversion is more robust and error message is more understandable.
- GUI -> Rinex conversion is now enabled only for zip files.

## [2.3.1] - 2021-07-25
### Fixed
- Local ntrip caster was not started with the right user/password syntax. #166
- Local ntrip caster service was not restarted after new settings were set. #167
- Psutil python requirement could not be installed on Os already including it (like Raspberry Pi Os with desktop). #165

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
- Rtkbase was deleting old archives when remaining space was lower than 5GB instead of 500MB. And now you can change this value inside `settings.conf`. #132
- rtkrcv configuration was hardcoded with ubx input, now it uses the format set on GUI -> Settings -> Main. #148
- Only .ubx files were archived. Now archive_and_clean.sh script check for all files format managed by str2str. #158
- The 2.1.x to 2.2.0 upgrade created a wrong path inside str2str_rtcm_serial.service (/var/tmp/rtkbase)
- rtkrcv didn't always stop after the 1O mn timeout. #35

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
- Gnss receiver (U-Blox): During the first installation, if a U-Blox receiver is detected, -TADJ=1 will be added for Rtcm and Ntrip outputs. See #80
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
