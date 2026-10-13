# Proposed receiver, interface and system update changes

This contribution is based on Stefal/rtkbase master at `2ce7ce0`. It ports selected changes from local development, rather than importing the experimental release branch.

## Included

- Explicit ZED-X20P configuration and configuration key definitions. The final receiver profile preserves the station mode and coordinates; it does not start a new survey-in.
- Passive USB source discovery, independent registration and NTRIP A–F routing. USB serial identifiers identify adapters, not antenna positions or firmware. Serial-less devices use a physical USB path. Two identical UM980 models or firmwares do not imply one receiver. The existing single-receiver detection/configuration dialog is retained; experimental group preparation, group application, rollback adapters and standalone hardware trial tools are excluded.
- A shared serial input per registered receiver, independent localhost output ports, slow consumer isolation and input recovery. Stopping the legacy main input no longer requires stopping independently sourced NTRIP outputs.
- A pinned RTKLIB EX 2.5.1 source build, archive fingerprint checking and `--version` verification of str2str, rtkrcv and convbin before installation. Build failures leave installed tools unchanged. Replacement of the three binaries is sequential, not an atomic rollback transaction. Use the complete source checkout containing the builder; standalone bootstrap installation from only install.sh is not validated.
- An initial common visual shell, Light/Dark/System preferences and a persisted French/English selector. This is a translation foundation for common authored labels, not a complete translation of all generated forms, messages or third-party widgets. Receiver names, measurements and logs remain untouched.
- An authenticated and CSRF-protected system package update action in Settings. Fixed APT commands run in a separate root worker, with private state, progress/error handling and a last successful update date. This upgrades packages within the configured distribution; it does not upgrade Debian releases. Package scripts may restart services, and updates are not automatically reversible. Reboot remains manual.

## Checks on the adapted proposal

- 61 local Python tests for X20P, routing, passive discovery, serial fanout, coordinator, EX builder and system package updates.
- JavaScript fixture checks for theme changes and language persistence, including storage failure and cross-tab updates. Settings JavaScript syntax is checked after restoring the existing single-receiver dialog.
- The actual Settings route was rendered with strict template checking: unique control IDs, six NTRIP channels, language selector and system update controls. Preview controls were disabled and used no station data.
- Python syntax checks and shell syntax checks for install.sh and set_zed-x20p.sh.

These checks used fixtures on Windows; serial fanout tests used localhost sockets. They did not open receiver ports, execute APT, install units or change a station. Earlier Linux and hardware checks of the original development components do not validate installation of this adapted upstream proposal. Full Linux deployment, migration of existing units/settings, service lifecycle and hardware configuration require review and validation before release.

No new PPP, position correction, drift/attitude monitoring, Galileo HAS, long recording workflow or tutorial subsystem is included. No credentials, recorded observations, real station coordinates or private diagnostic reports are part of this contribution.
