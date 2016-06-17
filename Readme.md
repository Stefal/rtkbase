### What is ReachView?

ReachView is a web-interface for RTKLIB hosted on Emlid Reach receivers. For more details on using Reach and ReachView check out our [docs](https://docs.emlid.com/reach/).

### Running/testing/debugging instructions

At the moment ReachView will only run on a Reach/Intel Edison flashed with our pre-built image. Flashing instructions and the image can be found [here](https://docs.emlid.com/reach/firmware-reflashing/).

ReachView is started on device power up.

To disable that, disable systemd service **reach-setup.service** with:
`systemctl disable reach-setup.service`

You can launch ReachView by running `sudo ./server.py` from the app directory at `/home/reach/ReachView`.

It depends on the RTKLIB repository in the same directory, so you can substitute it with another version, as long as the directory structure stays the same and default configuration files are present.

### Reporting bugs and requesting features

Bug reports and feature requests are welcome either here as issues, or at our active [community forum](https://community.emlid.com/).

### Contributing

Any contributions with a pull request are highly appreciated.

### Authors

ReachView is created by Egor Fedorov and Danil Kramorov working at [Emlid](https://emlid.com/).