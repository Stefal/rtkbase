# Changelog

## [2.2.1] - Not released
### Fixed
- Rtkbase was deleting old archive when remaining space was lower than 5GB instead of 500MB

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
