### What is GPSView?

GPSView is a fork of Emlid's ReadhView.

GPSView is a web-interface for RTKLIB hosted on u-blox M8T (and maybe other) receivers and non-Intel Edison SBCs.

### Running/testing/debugging instructions

At the moment GPSView has been tested on an Orange Pi Zero running Armbian 5.27. There is a lot of setup that is not documented yet.

GPSView is started on device power up.

To disable that, disable systemd service **reach-setup.service** with:  --> FixMe
`systemctl disable reach-setup.service` --> FixMe

You can launch GPSView by running `sudo ./server.py` from the app directory at `/home/reach`.

It depends on the RTKLIB repository in the same directory, so you can substitute it with another version, as long as the directory structure stays the same and default configuration files are present.

### Reporting bugs and requesting features

Bug reports and feature requests are welcome either here as issues.

## Contributing

Fork this project and play to your hearts content...

### Authors

ReachView is created by Egor Fedorov and Danil Kramorov working at [Emlid](https://emlid.com/).
GPSView has been heavily modified from the above code to allow it to run on other platforms. The Orange Pi Zero is only an example, other SBC's can be used as well.