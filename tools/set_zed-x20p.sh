#!/bin/bash

# RTKBase 2.8.0 - u-blox ZED-X20P configurator

set -u

BASEDIR=$(cd "$(dirname "$0")" && pwd)

GPS="${1:-}"
DEVICE_SPEED="${2:-}"
CONFIG="${3:-}"
POSITION="${4:-}"
# Persist to Flash without depending on the optional BBR layer. Layer 1 is
# available for a RAM-only test; the normal configuration action uses layer 5.
CONFIG_LAYER="${5:-5}"

UBXTOOL="${BASEDIR}/ubxtool"

ubx() {
    local -a args=("$@")
    if [[ "${args[0]:-}" == "-z" ]]; then
        [[ "${args[1]//[^,]/}" == "," ]] ||
            fail "expected configuration key,value: ${args[1]}"
        args[1]+=",${CONFIG_LAYER}"
    fi
    python3 "${UBXTOOL}" -f "${GPS}" -s "${DEVICE_SPEED}" -P 50.11 -v 0 "${args[@]}"
}

fail() {
    echo "GNSS Configuration: ERROR: $*" >&2
    exit 1
}

fixed_position_values() {
    python3 - "${POSITION}" <<'PYFIXED'
import sys
from decimal import Decimal, ROUND_DOWN

try:
    parts = sys.argv[1].split()
    if len(parts) != 3:
        raise ValueError

    lat, lon, height = map(Decimal, parts)

    if not (Decimal("-90") <= lat <= Decimal("90")):
        raise ValueError
    if not (Decimal("-180") <= lon <= Decimal("180")):
        raise ValueError

    # LAT/LON coarse resolution = 1e-7 degree
    # LAT_HP/LON_HP resolution = 1e-9 degree.
    lat_coarse = int((lat * Decimal("1e7")).to_integral_value(rounding=ROUND_DOWN))
    lon_coarse = int((lon * Decimal("1e7")).to_integral_value(rounding=ROUND_DOWN))

    lat_hp = int(((lat - Decimal(lat_coarse) * Decimal("1e-7")) *
                  Decimal("1e9")).to_integral_value())
    lon_hp = int(((lon - Decimal(lon_coarse) * Decimal("1e-7")) *
                  Decimal("1e9")).to_integral_value())

    # HEIGHT coarse resolution = 1 cm
    # HEIGHT_HP resolution = 0.1 mm.
    height_coarse = int((height * Decimal("100")).to_integral_value(rounding=ROUND_DOWN))
    height_hp = int(((height - Decimal(height_coarse) * Decimal("0.01")) *
                     Decimal("10000")).to_integral_value())

    print(lat_coarse, lat_hp, lon_coarse, lon_hp,
          height_coarse, height_hp)

except Exception:
    sys.exit(1)
PYFIXED
}

if [[ ! -c "${GPS}" ]]; then
    fail "invalid GNSS device: ${GPS}"
fi

if [[ ! "${DEVICE_SPEED}" =~ ^[0-9]+$ ]] || (( DEVICE_SPEED <= 0 )); then
    fail "invalid baudrate: ${DEVICE_SPEED}"
fi

if [[ ! -f "${CONFIG}" || ! -s "${CONFIG}" ]]; then
    fail "invalid configuration file: ${CONFIG}"
fi

if [[ "${CONFIG_LAYER}" != "1" && "${CONFIG_LAYER}" != "5" ]]; then
    fail "configuration layer must be 1 (RAM) or 5 (RAM + Flash)"
fi

echo "Checking receiver..."

MONVER=$(ubx -p MON-VER 2>&1 | grep -m1 'MOD=ZED-X20P')

if [[ -z "${MONVER}" ]]; then
    fail "u-blox ZED-X20P not detected"
fi

echo "u-blox ZED-X20P detected"
echo "Sending X20P configuration..."

while IFS= read -r setting || [[ -n "${setting}" ]]; do

    # Remove CR from CRLF files
    setting="${setting%$'\r'}"

    # Ignore empty lines and comments
    [[ -z "${setting}" ]] && continue
    [[ "${setting}" =~ ^[[:space:]]*# ]] && continue

    case "${setting}" in

        UBX-FRESET)
            echo "Reset configuration to defaults..."
            ubx -p RESET >/dev/null ||
                fail "UBX-FRESET failed"

            sleep 5

            ubx -p MON-VER 2>&1 | grep -qm1 'MOD=ZED-X20P' ||
                fail "ZED-X20P did not respond after reset"
            ;;

        UBX-SURVEY,*)
            args="${setting#UBX-SURVEY,}"

            duration="${args%% *}"
            accuracy="${args#* }"

            if [[ "${duration}" == "${args}" || -z "${accuracy}" ]]; then
                fail "invalid UBX-SURVEY syntax: ${setting}"
            fi

            # Always disable TMODE before changing base coordinates/mode.
            ubx -z CFG-TMODE-MODE,0 >/dev/null ||
                fail "unable to disable TMODE"

            if [[ -n "${POSITION}" ]]; then
                echo "Configure fixed base position: ${POSITION}"

                values=$(fixed_position_values) ||
                    fail "invalid fixed position: ${POSITION}"

                read -r lat lat_hp lon lon_hp height height_hp <<< "${values}"

                ubx -z CFG-TMODE-POS_TYPE,1 >/dev/null ||
                    fail "unable to set TMODE position type"

                ubx -z "CFG-TMODE-LAT,${lat}" >/dev/null ||
                    fail "unable to set latitude"

                ubx -z "CFG-TMODE-LAT_HP,${lat_hp}" >/dev/null ||
                    fail "unable to set high precision latitude"

                ubx -z "CFG-TMODE-LON,${lon}" >/dev/null ||
                    fail "unable to set longitude"

                ubx -z "CFG-TMODE-LON_HP,${lon_hp}" >/dev/null ||
                    fail "unable to set high precision longitude"

                ubx -z "CFG-TMODE-HEIGHT,${height}" >/dev/null ||
                    fail "unable to set height"

                ubx -z "CFG-TMODE-HEIGHT_HP,${height_hp}" >/dev/null ||
                    fail "unable to set high precision height"

                # Conservative accuracy: use the profile Survey-In target.
                ubx -z "CFG-TMODE-FIXED_POS_ACC,${accuracy}" >/dev/null ||
                    fail "unable to set fixed position accuracy"

                # Activate Fixed mode only after all coordinates are written.
                ubx -z CFG-TMODE-MODE,2 >/dev/null ||
                    fail "unable to enable fixed base mode"

                echo "Fixed base mode enabled"

                # Verify that the receiver really entered Fixed mode.
                ubx -g CFG-TMODE-MODE 2>&1 |
                    grep -qm1 'CFG-TMODE-MODE.*val 2' ||
                    fail "fixed base mode verification failed"

                echo "Fixed base mode verified"

            else
                echo "No fixed position supplied."
                echo "Configure Survey-In: ${duration}s / ${accuracy} (0.1 mm)"

                ubx -z "CFG-TMODE-SVIN_MIN_DUR,${duration}" >/dev/null ||
                    fail "unable to set Survey-In duration"

                ubx -z "CFG-TMODE-SVIN_ACC_LIMIT,${accuracy}" >/dev/null ||
                    fail "unable to set Survey-In accuracy"

                ubx -z CFG-TMODE-MODE,1 >/dev/null ||
                    fail "unable to enable Survey-In"

                echo "Survey-In mode enabled"
            fi
            ;;

        CFG-*)
            ubx -z "${setting}" >/dev/null ||
                fail "configuration command failed: ${setting}"
            ;;

        *)
            fail "unsupported configuration command: ${setting}"
            ;;
    esac

done < "${CONFIG}"

sleep 2

echo "GNSS Configuration: done"
exit 0
