# Yocto Fresh-Install Plan: Olimex i.MX8MP and LG290P Time Server

**Updated:** 2026-10-26  
**Scope:** Plan a clean Yocto-based image for the **Olimex iMX8MP-SOM-4GB-IND Rev. B + iMX8MP-SOM-EVB Rev. B** (with `Flash-e32Gs16M` on `Flash_Con1`) hosting the **RTKBase / Waveshare LG290P (`LG290P03`)** RTK GNSS base station and stratum-1 time server.

## Architectural Decision

1. **Standardize directly on NXP's latest upstream BSP & kernel (`linux-imx`):**
   - Base the build on NXP's latest official i.MX Linux BSP release: **`6.18.37-2.1.0`**, manifest branch `imx-linux-wrynose`, manifest file `imx-6.18.37-2.1.0.xml` (kernel `linux-imx` `lf-6.18.y`), tracking updates directly from NXP upstream (`nxp-imx`).
   - Do **not** use the `linux-fslc` kernel default from `meta-freescale-3rdparty`. Instead, keep NXP's upstream `linux-imx` kernel and BSP recipes unmodified, and apply only the **Olimex-specific hardware customizations** (4 GB LPDDR4 U-Boot/SPL config, `imx8mp-olimex.dts` ported to `lf-6.18.y`, and `rtkbase`/GNSS/PPS integration) in a dedicated layer (`meta-olimex`).
2. **Standardize on `UEXT1` (3.3 V native) for future LG290P UART + PPS transition:**
   - Keep USB (`/dev/ttyACM0` at 460800 bps) as the initial baseline, while configuring the device tree for the EVB's `UEXT1` header (`UART3` on pins 3/4 + `pps-gpio` on pin 7 `UEXT_MISO` → `GPIO5_IO12` via onboard `SN74LVC2T45` 3.3 V ↔ 1.8 V translators).

## Hardware & Board-Specific Configuration

- **Target Hardware:** Olimex `iMX8MP-SOM-4GB-IND` Rev. B (**4 GB LPDDR4**) on `iMX8MP-SOM-EVB` Rev. B, with `Flash-e32Gs16M` eMMC/SPI flash module installed on `Flash_Con1`.
- **Current Running System (Rollback Baseline):** Vendor-built Armbian image (kernel 5.10.72, `imx8mp-olimex.dtb`). Preserve the existing boot media intact during bring-up.
- **Community Reference Inputs (for porting into `meta-olimex`):**
  - Machine & U-Boot reference from [`Freescale/meta-freescale-3rdparty`](https://github.com/Freescale/meta-freescale-3rdparty): `olimex-imx8mp-evb.conf` and `u-boot-olimex` 4 GB LPDDR4 SPL/DDR timing patches (needed because NXP's `imx8mp-lpddr4-evk` assumes 6 GB LPDDR4).
  - Device tree reference from [`Freescale/linux-fslc`](https://github.com/Freescale/linux-fslc): `imx8mp-olimex.dts`, forward-ported to NXP `linux-imx` `lf-6.18.y` and verified against the Rev. B schematics:
    - **Dual Gigabit Ethernet:** `LAN1` (`eqos` TSN MAC + `KSZ9031RNX` `U4` at PHY addr `3`, reset `SAI2_RXC`, IRQ `SAI2_RXFS`) and `LAN2` (`fec` MAC on `SAI1` balls + `KSZ9031RNX` `U9` at PHY addr `7`, reset `SAI1_RXD0`, IRQ `SAI1_RXD1`).
    - **Dual USB 3.0 Type-A Host:** `USB3.0 HOST1` (`usb3_0`, VBUS switch `U12` enabled by active-low `SD2_WP\USB1_PWR_EN` via `FET12`) and `USB3.0 HOST2` (`usb3_1`, VBUS switch `U8` enabled by active-low `GPIO1_IO14\USB2_PWR_EN` via `FET5`).
    - **Boot Storage:** microSD on `MICRO_SD1` (`USDHC2`, `BOOT_SWITCH1 = 0011`) and 8-bit eMMC on `Flash_Con1` (`USDHC3`, reset `QSPIA_DQS\eMMC_RSTn`, `BOOT_SWITCH1 = 0010`).
    - **Console & GNSS/PPS:** Linux console on `A53_DBG1` (`UART2` / `ttymxc1`, 3.3 V); GNSS UART on `UEXT1` pins 3/4 (`UART3` / `ttymxc2`, 3.3 V via `U17`); GNSS PPS input on `UEXT1` pin 7 (`UEXT_MISO` → `ECSPI2_MISO` / `GPIO5_IO12`, 3.3 V → 1.8 V via `U15`, bound to `pps-gpio`).

## Fresh-Image Scope

Build a minimal headless image on top of NXP's `imx-image-core` (or minimal product image) including:

- OpenSSH server for remote administration
- RTKBase application, Python runtime dependencies (`pyserial`, `flask`, `flask-socketio`, `packaging`, etc.), `quectel_tool.py`, and `str2str`/`convbin`/`rtkrcv` (RTKLIB)
- `gpsd` and `chrony` for GNSS/PPS time service
- Kernel drivers: `CONFIG_USB_ACM` (`cdc_acm`), `CONFIG_USB_SERIAL_CH341`, `CONFIG_USB_SERIAL_CP210X`, `CONFIG_USB_SERIAL_FTDI_SIO`, `CONFIG_PPS`, `CONFIG_PPS_CLIENT_GPIO` (`pps-gpio`)
- `gpiod-tools` (`libgpiod`), `pps-tools` (`ppstest`), and `mmc-utils`

## Implementation Plan

### 1. Preserve the current system and capture a baseline

1. Record the current U-Boot environment, storage layout, `settings.conf`, LG290P firmware (`PQTMVERNO`), and survey-in/base coordinates.
2. Keep the existing microSD / eMMC installation untouched while validating the new Yocto build on a separate microSD card (`BOOT_SWITCH1 = 0011`).

### 2. Initialize NXP upstream BSP (`6.18.37-2.1.0`)

1. Fetch the pinned NXP release on a Linux build host:
   ```sh
   repo init -u https://github.com/nxp-imx/imx-manifest \
     -b imx-linux-wrynose -m imx-6.18.37-2.1.0.xml
   repo sync
   ```
2. Build `imx-image-core` for `imx8mp-lpddr4-evk` first to verify the upstream NXP toolchain and host environment.

### 3. Layer Olimex & RTKBase customizations (`meta-olimex`)

1. Create `meta-olimex` pinning `PREFERRED_PROVIDER_virtual/kernel = "linux-imx"` (NXP's `lf-6.18.y` kernel directly).
2. Port the Olimex 4 GB LPDDR4 U-Boot/SPL configuration and `imx8mp-olimex.dts` (with `LAN1` + `LAN2`, `USB3.0 HOST1` + `HOST2`, `USDHC2` + `USDHC3`, and `UEXT1` `UART3` + `pps-gpio`).
3. Add recipes for RTKLIB (`str2str`, `convbin`, `rtkrcv`), RTKBase (from the `lg290` branch), `gpsd`, and `chrony`, along with systemd service units.
4. Verify with `bitbake -e virtual/kernel` and `bitbake -e virtual/bootloader` that NXP's `linux-imx` 6.18.x kernel and the 4 GB Olimex U-Boot configuration are selected.

### 4. Validate hardware, USB GNSS, and `UEXT1` UART + PPS

1. Boot from microSD (`BOOT_SWITCH1 = 0011`) with serial console attached to `A53_DBG1` (Pin 1 `GND`, Pin 2 `RXD`, Pin 3 `TXD`, 115200 8N1, 3.3 V).
2. Confirm U-Boot and Linux report 4 GB RAM, `imx8mp-olimex.dtb`, both Gigabit Ethernet interfaces (`LAN1` PHY 3 and `LAN2` PHY 7), both USB 3.0 host ports, and `Flash_Con1` eMMC (`mmcblk2`).
3. Validate Profile A (LG290P over USB at `/dev/ttyACM0`, 460800 bps) with `quectel_tool.py`, RTKBase `str2str_tcp.service`, `gpsd`, and `chrony`.
4. Validate Profile B / D using `UEXT1` Pin 7 (`PPS` → `GPIO5_IO12` via `pps-gpio`) and `UEXT1` Pins 3/4 (`UART3` / `ttymxc2`), verifying PPS pulses with `ppstest` and Chrony lock (`chronyc sources -v`).
5. Provision and test independent eMMC boot on `Flash_Con1` (`BOOT_SWITCH1 = 0010`).

## References

- [Companion Hardware & Yocto Plan (`ipkh/Olimex-iMX8PLUS`)](https://github.com/ipkh/Olimex-iMX8PLUS)
- [LG290P on Olimex i.MX8MPlus Wiring & Timing Profiles](./lg290-olimex-wiring.md)
- [NXP i.MX Manifest (`imx-linux-wrynose` / `imx-6.18.37-2.1.0.xml`)](https://github.com/nxp-imx/imx-manifest)
- [NXP `meta-imx` layer](https://github.com/nxp-imx/meta-imx)
- [NXP `linux-imx` repository (`lf-6.18.y`)](https://github.com/nxp-imx/linux-imx)
- [Community `meta-freescale-3rdparty` (`olimex-imx8mp-evb.conf`)](https://github.com/Freescale/meta-freescale-3rdparty/blob/master/conf/machine/olimex-imx8mp-evb.conf)
