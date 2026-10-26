# LG290P on Olimex i.MX8MPlus: Serial and Timing Wiring

This note records the current USB setup for the **Waveshare LG290P** (Quectel `LG290P03`) RTK GNSS module on the **Olimex iMX8MP-SOM-4GB-IND Rev. B + iMX8MP-SOM-EVB Rev. B**, and the planned transitions to PPS timing, direct UART, or both. All header pin numbers and voltage levels below have been verified against the Olimex Rev. B SOM and EVB schematics.

## Current software profile

The proven baseline connection is the LG290P USB serial interface at `/dev/ttyACM0` (or `/dev/ttyUSB0`), 460800 baud. RTKBase streams receiver data; GPSD reads the mixed NMEA/RTCM stream from the local RTKBase TCP feed. Chrony receives GNSS time but should not be considered PPS-disciplined until the PPS path is wired, enabled, and verified.

Keep this USB configuration as the recovery baseline when adding header signals. Make one hardware/software change at a time and preserve a known-good receiver configuration.

## Verified Olimex EVB Rev. B expansion headers & voltage levels

The Waveshare LG290P breakout operates its UART (`TXD`/`RXD`) and `PPS` output at **3.3 V logic**.

> **CRITICAL VOLTAGE WARNING:** On the Olimex `iMX8MP-SOM-EVB` Rev. B, only **`UEXT1`** includes onboard 3.3 V ↔ 1.8 V level translators (`SN74LVC2T45DCUR` `U15`, `U16`, `U17`). Almost all SoC UART and GPIO signals on **`EXT1`** and **`EXT2`** are **1.8 V only (`VDD_1V8`)** directly connected to the i.MX8MP SoC pads. Do **not** connect the LG290P's 3.3 V `TXD` or 3.3 V `PPS` directly to `EXT1` or `EXT2` without an external 3.3 V ↔ 1.8 V level translator.

### UEXT1 (10-pin 0.1" header — Primary Recommended 3.3 V Interface)

`UEXT1` provides native **3.3 V** signals via onboard `SN74LVC2T45DCUR` level translators (`U15`, `U16`, `U17` wired with `DIR=GND`, `B -> A`):

| Pin | EVB Net Name | SoC Ball / Signal | Direction & Voltage at `UEXT1` Pin | Recommended LG290P Connection |
| ---: | --- | --- | --- | --- |
| 1 | `VDD_3V3` | — | 3.3 V Power Supply | `VCC` (or leave unconnected if USB-powered) |
| 2 | `GND` | `GND` | Ground | `GND` (Required common ground) |
| 3 | `UEXT_TXD` | `AJ4` / `UART3_TXD` | **3.3 V Output** (translated from 1.8 V via `U17`) | LG290P `RXD` |
| 4 | `UEXT_RXD` | `AE6` / `UART3_RXD` | **3.3 V Input** (translated to 1.8 V via `U17`) | LG290P `TXD` |
| 5 | `I2C2_SCL_3V3` | `AH6` / `I2C2_SCL` | 3.3 V I2C Clock (via `FET4` level shifter) | Unused |
| 6 | `I2C2_SDA_3V3` | `AE8` / `I2C2_SDA` | 3.3 V I2C Data (via `FET3` level shifter) | Unused |
| 7 | `UEXT_MISO` | `AH20` / `ECSPI2_MISO` (`GPIO5_IO12`) | **3.3 V Input** (translated to 1.8 V via `U15`) | **LG290P `PPS` Output** (via `pps-gpio` on `GPIO5_IO12` when SPI2 is disabled) |
| 8 | `UEXT_MOSI` | `AJ21` / `ECSPI2_MOSI` | 3.3 V Output (translated from 1.8 V via `U16`) | Unused |
| 9 | `UEXT_SCLK` | `AH21` / `ECSPI2_SCLK` | 3.3 V Output (translated from 1.8 V via `U15`) | Unused |
| 10 | `UEXT_CSn` | `AJ22` / `ECSPI2_SS0` | 3.3 V Output (translated from 1.8 V via `U16`) | Unused |

### EXT1 (26-pin 0.1" header — 1.8 V Logic Only; Requires External Level Shifter)

| Pin | EVB Schematic Signal | Logic Level | Notes |
| ---: | --- | --- | --- |
| 1 | `+5V` | 5 V Supply | Power rail |
| 2, 4 | `GND` | Ground | Common ground |
| 3 | `VDD_3V3` | 3.3 V Supply | Reference rail for external level translator `VCCB` |
| 5 | `VDD_1V8` | 1.8 V Supply | Reference rail for external level translator `VCCA` |
| 20 | `UART1_RXD` (ball `AD6`) | **1.8 V Input** | Requires external 3.3 V → 1.8 V level shifter from LG290P `TXD` |
| 22 | `UART1_TXD` (ball `AJ3`) | **1.8 V Output** | Requires external 1.8 V → 3.3 V level shifter to LG290P `RXD` |
| 24 | `UART1_CTS` | **1.8 V** | Leave disconnected unless hardware flow control is used |
| 26 | `UART1_RTS` | **1.8 V** | Leave disconnected unless hardware flow control is used |

### EXT2 (40-pin 0.1" header — 1.8 V GPIO Logic; Requires External Level Shifter)

| Pin | EVB Schematic Signal | Logic Level | Notes |
| ---: | --- | --- | --- |
| 1 | `VDD_3V3` | 3.3 V Supply | Reference rail for external level translator `VCCB` |
| 2, 4 | `GND` | Ground | Common ground |
| 3 | `VDD_1V8` | 1.8 V Supply | Reference rail for external level translator `VCCA` |
| 5 | `GPIO1_IO00` (ball `A7`) | **1.8 V GPIO** | Candidate PPS input **only** with external 3.3 V → 1.8 V level translator |
| 6 | `SAI5_RXFS` (ball `AC14`) | **1.8 V** | **Not** `GPIO1_IO01` (even row is SAI5/I2C/SAI2/SAI3) |
| 7 | `GPIO1_IO01` (ball `E8`) | **1.8 V GPIO** | Candidate PPS input **only** with external 3.3 V → 1.8 V level translator |
| 39 | `UART3_RTS` | **1.8 V** | `UART3` RTS (not `UART2`) |
| 40 | `UART3_CTS` | **1.8 V** | `UART3` CTS (not `UART2`) |

## Electrical and pin-mux checks before connecting anything

- **Use `UEXT1` as the primary header** for direct 3.3 V UART (`UART3` on pins 3/4) and 3.3 V PPS (`UEXT_MISO` on pin 7 → `ECSPI2_MISO` muxed as `GPIO5_IO12`), as `U15` and `U17` (`SN74LVC2T45DCUR`) already perform 3.3 V ↔ 1.8 V translation on the EVB.
- If `EXT1` (`UART1`) or `EXT2` (`GPIO1_IO00`/`GPIO1_IO01`) is used instead, an external bidirectional/unidirectional 3.3 V ↔ 1.8 V level translator referenced to `VDD_3V3` (Pin 1/3) and `VDD_1V8` (Pin 3/5) is mandatory.
- The Linux serial console is on `A53_DBG1` (`UART2` / `ttymxc1`). Keep `UART2` dedicated to the boot/debug console.
- Do not assume UART hardware flow control is needed; leave CTS/RTS disconnected unless explicitly configured.

## Profile A: USB serial, no PPS (current baseline)

- Connect through the LG290P USB interface to `USB3.0 HOST1` or `USB3.0 HOST2`.
- RTKBase serial input: USB device (currently `ttyACM0`) at `460800:8:n:1`, receiver `quectel_LG290P03`, format `rtcm3`.
- Keep the configured NMEA output (`GGA`, `RMC`, `ZDA`) available in the RTKBase stream for GPSD and Chrony.
- Leave the Chrony PPS refclock disabled. NMEA time provides a coarse GNSS clock source, not a PPS-disciplined clock.

## Profile B: USB serial plus PPS

Keep USB as the receiver's data/configuration interface and connect the LG290P's 3.3 V `PPS` output and `GND` to:
- **Primary (`UEXT1`, no external components needed):** `UEXT1` Pin 7 (`UEXT_MISO`, translated from 3.3 V to 1.8 V via `U15` into ball `AH20` `ECSPI2_MISO` / `GPIO5_IO12`) and `UEXT1` Pin 2 (`GND`).
- **Alternative (`EXT2` with external 3.3 V → 1.8 V level translator):** `EXT2` Pin 5 (`GPIO1_IO00`) or Pin 7 (`GPIO1_IO01`).

Software work:
1. Configure the chosen pin (`MX8MP_IOMUXC_ECSPI2_MISO__GPIO5_IO12` for `UEXT1` Pin 7, with `ecspi2` disabled) in the device tree and bind the Linux `pps-gpio` client driver. Confirm a stable `/dev/ppsN` node (note: `eqos` PTP may register `/dev/pps0`, making `pps-gpio` `/dev/pps1`—verify via `/sys/class/pps/pps*/name`) and test events using `ppstest`.
2. Keep the receiver's NMEA time feed active so Chrony/GPSD can associate the UTC second with the PPS edge.
3. Configure GPSD/Chrony to use the verified `/dev/ppsN` device and GNSS time source (e.g., `refclock PPS /dev/pps1 refid PPS lock GNSS`).
4. Check `chronyc sources -v`, `chronyc sourcestats`, and `chronyc tracking`. Confirm PPS is reachable, locked, and selected with sub-millisecond offset.

## Profile C: direct UART serial, no PPS

Use this profile to move receiver data/control from USB to `UEXT1` (`UART3`, 3.3 V native):

- Wire LG290P `TXD` (3.3 V) to **`UEXT1` Pin 4 (`UEXT_RXD`)**, LG290P `RXD` (3.3 V) to **`UEXT1` Pin 3 (`UEXT_TXD`)**, and common ground to **`UEXT1` Pin 2 (`GND`)**. (If using `EXT1` Pin 20 `UART1_RXD` and Pin 22 `UART1_TXD`, insert a 3.3 V ↔ 1.8 V level translator.)
- Enable `uart3` (`ttymxc2`) in the device tree without RTS/CTS flow control, and verify no systemd `getty` is bound to `ttymxc2`.
- Configure RTKBase to use `ttymxc2` at `460800:8:n:1` with receiver `quectel_LG290P03` and format `rtcm3`.
- Avoid having RTKBase streaming, GPSD, and `quectel_tool.py` open the same UART concurrently. Stop `str2str_tcp.service` before running `quectel_tool.py`.
- Confirm the LG290P UART1 output includes the expected RTCM3 and NMEA (`GGA`, `RMC`, `ZDA`) sentences and persists across receiver reboot.

## Profile D: direct UART serial plus PPS

Combine Profile C's `UEXT1` UART wiring (`UEXT1` Pin 3 `UEXT_TXD`, Pin 4 `UEXT_RXD`, Pin 2 `GND`) with Profile B's `UEXT1` Pin 7 PPS input (`UEXT_MISO` → `GPIO5_IO12` via `pps-gpio`). Test UART data and PPS independently first, then together.

## Acceptance checks for every profile

- Reboot and confirm receiver port identity, baud rate, receiver mode, survey state, message output, and RTKBase service recovery.
- Confirm GPSD reports valid NMEA time and fix/satellite information from the intended feed.
- Validate RTCM frame CRCs and expected observation/station message types (`1005`, MSM4).
- For PPS profiles, confirm regular kernel PPS events (`ppstest`), correct edge/polarity, PPS/GNSS lock, and Chrony reachability/source selection.
- Check that network NTP fallback policy is explicit.
- Keep the USB profile and a bootable microSD backup until the new profile passes a sustained soak test.
