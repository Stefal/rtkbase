'''
class ubx
'''

# This file is Copyright 2020 by the GPSD project
# SPDX-License-Identifier: BSD-2-clause
#
# This code runs compatibly under Python 2 and 3.x for x >= 2.
# Preserve this property!

from __future__ import absolute_import, print_function, division

import binascii      # for binascii.hexlify()
import string        # for string.printable
import struct        # for pack()
import sys
import time

try:
    import gps
except ImportError:
    # PEP8 says local imports last
    sys.stderr.write("gps/ubx: failed to import gps, check PYTHONPATH\n")
    sys.exit(2)


def erd_s(erd):
    """convert 6 bits of subframe 4, page 13 (NMCT) ERD to string"""
    if erd & 0x20:
        if erd == 0x20:
            return "n/a"
        # else
        erd = 1 - erd
    # else
    return "%3s" % erd


# I'd like to use pypy module bitstring or bitarray, but
# people complain when non stock python modules are used here.
def unpack_s11(word, pos):
    """Grab a signed 11 bits from offset pos of word"""

    ubytes = bytearray(2)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0x07
    if 0x04 & ubytes[1]:
        # extend the sign
        ubytes[1] |= 0xf8
    u = struct.unpack_from('<h', ubytes, 0)
    return u[0]


def unpack_s11s(word):
    """Grab the weird split signed 11 bits from word"""

    newword = (word >> 22) & 0xff
    newword <<= 3
    newword |= (word >> 8) & 0x07
    return unpack_s11(newword, 0)


def unpack_s14(word, pos):
    """Grab a signed 14 bits from offset pos of word"""

    ubytes = bytearray(2)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0x3f
    if 0x20 & ubytes[1]:
        # extend the sign
        ubytes[1] |= 0xc0
    u = struct.unpack_from('<h', ubytes, 0)
    return u[0]


def unpack_s16(word, pos):
    """Grab a signed two bytes from offset pos of word"""

    ubytes = bytearray(2)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0xff
    u = struct.unpack_from('<h', ubytes, 0)
    return u[0]


def unpack_u16(word, pos):
    """Grab a unsigned two bytes from offset pos of word"""

    ubytes = bytearray(2)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0xff
    u = struct.unpack_from('<H', ubytes, 0)
    return u[0]


def unpack_u17(word, pos):
    """Grab an unsigned 17 bits from offset pos of word"""

    return unpack_u24(word, pos) & 0x01ffff


def unpack_s22(word, pos):
    """Grab a signed 22 bits from offset pos of word"""

    ubytes = bytearray(4)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0xff
    ubytes[2] = (word >> (pos + 16)) & 0x3f
    ubytes[3] = 0
    if 0x20 & ubytes[2]:
        # extend the sign
        ubytes[2] |= 0xc0
        ubytes[3] = 0xff

    u = struct.unpack_from('<l', ubytes, 0)
    return u[0]


def unpack_s24(word, pos):
    """Grab a signed 24 bits from offset pos of word"""

    ubytes = bytearray(4)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0xff
    ubytes[2] = (word >> (pos + 16)) & 0xff
    ubytes[3] = 0
    if 0x80 & ubytes[2]:
        # extend the sign
        ubytes[3] = 0xff

    u = struct.unpack_from('<l', ubytes, 0)
    return u[0]


def unpack_u24(word, pos):
    """Grab an unsigned 24 bits from offset pos of word"""

    ubytes = bytearray(4)
    ubytes[0] = (word >> pos) & 0xff
    ubytes[1] = (word >> (pos + 8)) & 0xff
    ubytes[2] = (word >> (pos + 16)) & 0xff
    ubytes[3] = 0

    u = struct.unpack_from('<L', ubytes, 0)
    return u[0]


def unpack_s32s(word, word1):
    """Grab an signed 32 bits from weird split word, word1"""

    ubytes = bytearray(4)
    ubytes[0] = (word >> 6) & 0xff
    ubytes[1] = (word >> 14) & 0xff
    ubytes[2] = (word >> 22) & 0xff
    ubytes[3] = (word1 >> 6) & 0xff

    u = struct.unpack_from('<l', ubytes, 0)
    return u[0]


def unpack_u32s(word, word1):
    """Grab an unsigned 32 bits from weird split word, word1"""

    ubytes = bytearray(4)
    ubytes[0] = (word >> 6) & 0xff
    ubytes[1] = (word >> 14) & 0xff
    ubytes[2] = (word >> 22) & 0xff
    ubytes[3] = (word1 >> 6) & 0xff

    u = struct.unpack_from('<L', ubytes, 0)
    return u[0]


def unpack_s8(word, pos):
    """Grab a signed byte from offset pos of word"""

    ubytes = bytearray(1)
    ubytes[0] = (word >> pos) & 0xff
    u = struct.unpack_from('<b', ubytes, 0)
    return u[0]


def unpack_u8(word, pos):
    """Grab an unsigned byte from offset pos of word"""

    ubytes = bytearray(1)
    ubytes[0] = (word >> pos) & 0xff
    u = struct.unpack_from('<B', ubytes, 0)
    return u[0]


def flag_s(flag, descs):
    """Decode flag using descs, return a string.  Ignores unknown bits."""

    s = ''
    for key, value in sorted(descs.items()):
        if key == (key & flag):
            s += value
            s += ' '

    return s.strip()


def index_s(index, descs, nf="Unk"):
    """Decode flag using descs, return a string.  Otherwise Unk"""

    if index in descs:
        s = descs[index]
    else:
        s = nf

    return s


def timestamp(timestamp_opts):
    """Print current time as a timestamp.

UNIX epoch for timestamp_opts == 1, UTC when timestamp_opts == 2
"""

    now = time.time()
    if 1 == timestamp_opts:
        print("%.4f" % now)
    elif 2 == timestamp_opts:
        print("%.4f %s" % (now, time.asctime(time.gmtime(now))))


class ubx(object):
    """Class to hold u-blox stuff."""

    # expected statement identifier.
    expect_statement_identifier = False
    io_handle = None
    # when a statement identifier is received, it is stored here
    last_statement_identifier = None
    read_only = False
    protver = 10.0
    timestamp = None
    verbosity = gps.VERB_NONE

    def __init__(self):
        pass

    # allowable speeds
    speeds = (921600, 460800, 230400, 153600, 115200, 57600, 38400, 19200,
              9600, 4800)

    # UBX Satellite Numbering
    gnss_id = {0: 'GPS',
               1: 'SBAS',
               2: 'Galileo',
               3: 'BeiDou',
               4: 'IMES',
               5: 'QZSS',
               6: 'GLONASS'}

    # Names for portID values in UBX-CFG-PRT, UBX-MON-IO, etc.
    port_ids = {0: 'DDC',  # The license free name for i2c used in the spec
                1: 'UART1',
                2: 'UART2',
                3: 'USB',
                4: 'SPI',
                }
    port_id_map = dict([(v, k) for (k, v) in port_ids.items()])
    port_id_map['UART'] = port_id_map['UART1']  # Accept synonym
    port_ids[5] = 'Reserved'  # Don't include this in port_id_map

    # Names for portID values in UBX-CFG-COMMS
    # the doc does not match what is seen
    port_ids1 = {0: 'DDC',
                 0x001: 'UART1',     # as documented on ZED-M9
                 0x003: 'USB',       # as documented on ZED-M9
                 0x004: 'SPI',       # as documented on ZED-M9
                 0x100: 'UART1',     # seen on ZED-M9, documented
                 0x101: 'UNKa',      # seen on ZED-M9T, undocumented
                 0x102: 'UART2',     # as documented on ZED-M9
                 0x200: 'UNKb',      # seen on ZED-M9T, undocumented
                 0x201: 'UART2',
                 0x300: 'USB',       # seen on ZED-M9, undocumented
                 0x400: 'SPI',
                 }
    # u-blox 9 cfg items as a 5-tuple
    # 1 - Name
    # 2 - key id
    # 3 - value type
    # 4 - scale
    # 5 - Unit
    # 6 - Description
    cfgs = (
        # CFG--
        ("CFG", 0x1FFFFFFF, "", 0, "",
         "get all CFG"),
        # CFG-ANA-
        ("CFG-ANA", 0x1023FFFF, "", 0, "",
         "get all CFG-ANA"),
        ("CFG-ANA-USE_ANA", 0x10230001, "L", 1, "",
         "Use AssistNow Autonomous"),
        ("CFG-ANA-ORBMAXERR", 0x30230002, "U2", 1, "m",
         "Maximum acceptable (modeled) orbit error"),
        # CFG-BATCH-
        ("CFG-BATCH", 0x1026FFFF, "", 0, "",
         "get all CFG-BATCH"),
        ("CFG-BATCH-ENABLE", 0x10260013, "L", 1, "",
         "Enable the feature. Needs further configuration."),
        ("CFG-BATCH-PIOENABLE", 0x10260014, "L", 1, "",
         "Enable PIO notification when buffer fill level exceeds WARNTHRS."),
        ("CFG-BATCH-MAXENTRIES", 0x30260015, "U2", 1, "",
         "Size of buffer in number of epochs to store."),
        ("CFG-BATCH-WARNTHRS", 0x30260016, "U2", 1, "",
         "Fill level to trigger PIO notification, number of epochs stored."),
        ("CFG-BATCH-PIOACTIVELOW", 0x10260018, "L", 1, "",
         "Drive CFG-BATCH-PIOID low when buffer fill level reaches WARNTHRS"),
        ("CFG-BATCH-PIOPID", 0x20260019, "U1", 1, "",
         "PIO that is used for buffer fill level notification"),
        ("CFG-BATCH-EXTRAPVT", 0x1026001a, "L", 1, "",
         "Include additional PVT information in UBX-LOG-BATCH messages"),
        ("CFG-BATCH-EXTRAODO", 0x1026001b, "L", 1, "",
         "Include additional ODO information in UBX-LOG-BATCH messages"),
        # CFG-GEOFENCE-
        ("CFG-GEOFENCE", 0x2024FFFF, "", 0, "",
         "get all CFG-GEOFENCE"),
        ("CFG-GEOFENCE-CONFLVL", 0x20240011, "E1", 1, "",
         "Required confidence level for state evaluation"),
        ("CFG-GEOFENCE-USE_PIO", 0x10240012, "L", 1, "",
         "Use PIO combined fence state output"),
        ("CFG-GEOFENCE-PINPOL", 0x20240013, "E1", 1, "",
         "PIO pin polarity"),
        ("CFG-GEOFENCE-PIN", 0x20240014, "U1", 1, "",
         "PIO pin number"),
        ("CFG-GEOFENCE-USE_FENCE1", 0x10240020, "L", 1, "",
         "Use first geofence"),
        ("CFG-GEOFENCE-FENCE1_LAT", 0x40240021, "I4", 1e-7, "deg",
         "Latitude of the first geofence circle center"),
        ("CFG-GEOFENCE-FENCE1_LON", 0x40240022, "I4", 1e-7, "deg",
         "Longitude of the first geofence circle center"),
        ("CFG-GEOFENCE-FENCE1_RAD", 0x40240023, "U4", 0.01, "m",
         "Radius of the first geofence circle"),
        ("CFG-GEOFENCE-USE_FENCE2", 0x10240030, "L", 1, "",
         "Use second geofence"),
        ("CFG-GEOFENCE-FENCE2_LAT", 0x40240031, "I4", 1e-7, "deg",
         "Latitude of the second geofence circle center"),
        ("CFG-GEOFENCE-FENCE2_LON", 0x40240032, "I4", 1e-7, "deg",
         "Longitude of the second geofence circle center"),
        ("CFG-GEOFENCE-FENCE2_RAD", 0x40240033, "U4", 0.01, "m",
         "Radius of the second geofence circle"),
        ("CFG-GEOFENCE-USE_FENCE3", 0x10240040, "L", 1, "",
         "Use third geofence"),
        ("CFG-GEOFENCE-FENCE3_LAT", 0x40240041, "I4", 1e-7, "deg",
         "Latitude of the third geofence circle center"),
        ("CFG-GEOFENCE-FENCE3_LON", 0x40240042, "I4", 1e-7, "deg",
         "Longitude of the third geofence circle center"),
        ("CFG-GEOFENCE-FENCE3_RAD", 0x40240043, "U4", 0.01, "m",
         "Radius of the third geofence circle"),
        ("CFG-GEOFENCE-USE_FENCE4", 0x10240050, "L", 1, "",
         "Use fourth geofence"),
        ("CFG-GEOFENCE-FENCE4_LAT", 0x40240051, "I4", 1e-7, "deg",
         "Latitude of the fourth geofence circle center"),
        ("CFG-GEOFENCE-FENCE4_LON", 0x40240052, "I4", 1e-7, "deg",
         "Longitude of the fourth geofence circle center"),
        ("CFG-GEOFENCE-FENCE4_RAD", 0x40240053, "U4", 0.01, "m",
         "Radius of the fourth geofence circle"),
        # CFG-HW
        ("CFG-HW", 0x10a3FFFF, "", 0, "",
         "get all CFG-HW"),
        ("CFG-HW-ANT_CFG_VOLTCTRL", 0x10a3002e, "L", 1, "",
         "Active antenna voltage control flag"),
        ("CFG-HW-ANT_CFG_SHORTDET", 0x10a3002f, "L", 1, "",
         "Short antenna detection flag"),
        ("CFG-HW-ANT_CFG_SHORTDET_POL", 0x10a30030, "L", 1, "",
         "Short antenna detection polarity"),
        ("CFG-HW-ANT_CFG_OPENDET", 0x10a30031, "L", 1, "",
         "Open antenna detection flag"),
        ("CFG-HW-ANT_CFG_OPENDET_POL", 0x10a30032, "L", 1, "",
         "Open antenna detection polarity"),
        ("CFG-HW-ANT_CFG_PWRDOWN", 0x10a30033, "L", 1, "",
         "Power down antenna flag"),
        ("CFG-HW-ANT_CFG_PWRDOWN_POL", 0x10a30034, "L", 1, "",
         "Power down antenna logic polarity"),
        ("CFG-HW-ANT_CFG_RECOVER", 0x10a30035, "L", 1, "",
         "Automatic recovery from short state flag"),
        ("CFG-HW-ANT_SUP_SWITCH_PIN", 0x20a30036, "U1", 1, "",
         "ANT1 PIO number"),
        ("CFG-HW-ANT_SUP_SHORT_PIN", 0x20a30037, "U1", 1, "",
         "ANT0 PIO number"),
        ("CFG-HW-ANT_SUP_OPEN_PIN", 0x20a30038, "U1", 1, "",
         "ANT2 PIO number"),
        # CFG-I2C
        ("CFG-I2C", 0x2051ffff, "", 0, "",
         "get all CFG-I2C"),
        ("CFG-I2C-ADDRESS", 0x20510001, "U1", 1, "",
         "I2C slave address of the receiver"),
        ("CFG-I2C-EXTENDEDTIMEOUT", 0x10510002, "L", 1, "",
         "Flag to disable timeouting the interface after 1.5 s"),
        ("CFG-I2C-ENABLED", 0x10510003, "L", 1, "",
         "Flag to indicate if the I2C interface should be enabled"),
        # CFG-I2CINPROT
        ("CFG-I2CINPROT", 0x1071ffff, "", 0, "",
         "get all CFG-I2CINPROT"),
        ("CFG-I2CINPROT-UBX", 0x10710001, "L", 1, "",
         "Flag to indicate if UBX should be an input on I2C"),
        ("CFG-I2CINPROT-NMEA", 0x10710002, "L", 1, "",
         "Flag to indicate if NMEA should be an input on I2C"),
        ("CFG-I2CINPROT-RTCM2X", 0x10710003, "L", 1, "",
         "Flag to indicate if RTCM2X should be an input on I2C"),
        ("CFG-I2CINPROT-RTCM3X", 0x10710004, "L", 1, "",
         "Flag to indicate if RTCM3X should be input on I2C"),
        # CFG-I2COUTPROT
        ("CFG-I2COUTPROT", 0x1072ffff, "", 0, "",
         "get all CFG-I2COUTPROT"),
        ("CFG-I2COUTPROT-UBX", 0x10720001, "L", 1, "",
         "Flag to indicate if UBX should be an output on I2C"),
        ("CFG-I2COUTPROT-NMEA", 0x10720002, "L", 1, "",
         "Flag to indicate if NMEA should be an output on I2C"),
        ("CFG-I2COUTPROT-RTCM3X", 0x10720004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an output on I2C"),
        # CFG-INFMSG-
        ("CFG-INFMSG", 0x2092ffff, "", 0, "",
         "get all CFG-INFMSG"),
        ("CFG-INFMSG-UBX_I2C", 0x20920001, "X1", 1, "",
         "Information message enable flags for UBX protocol on I2C"),
        ("CFG-INFMSG-UBX_UART1", 0x20920002, "X1", 1, "",
         "Information message enable flags for UBX protocol on UART1"),
        ("CFG-INFMSG-UBX_UART2", 0x20920003, "X1", 1, "",
         "Information message enable flags for UBX protocol on UART2"),
        ("CFG-INFMSG-UBX_USB", 0x20920004, "X1", 1, "",
         "Information message enable flags for UBX protocol on USB"),
        ("CFG-INFMSG-UBX_SPI", 0x20920005, "X1", 1, "",
         "Information message enable flags for UBX protocol on SPI"),
        ("CFG-INFMSG-NMEA_I2C", 0x20920006, "X1", 1, "",
         "Information message enable flags for NMEA protocol on I2C"),
        ("CFG-INFMSG-NMEA_UART1", 0x20920007, "X1", 1, "",
         "Information message enable flags for NMEA protocol on UART1"),
        ("CFG-INFMSG-NMEA_UART2", 0x20920008, "X1", 1, "",
         "Information message enable flags for NMEA protocol on UART2"),
        ("CFG-INFMSG-NMEA_USB", 0x20920009, "X1", 1, "",
         "Information message enable flags for NMEA protocol on USB"),
        ("CFG-INFMSG-NMEA_SPI", 0x2092000a, "X1", 1, "",
         "Information message enable flags for NMEA protocol on SPI"),
        # CFG-ITFM-
        ("CFG-ITFM", 0x2041ffff, "", 0, "",
         "get all CFG-ITFM"),
        ("CFG-ITFM-BBTHRESHOLD", 0x20410001, "U1", 1, "",
         "Broadband jamming detection threshold"),
        ("CFG-ITFM-CWTHRESHOLD", 0x20410002, "U1", 1, "",
         "CW jamming detection threshold"),
        ("CFG-ITFM-ENABLE", 0x1041000d, "L", 1, "",
         "Enable interference detection"),
        ("CFG-ITFM-ANTSETTING", 0x20410010, "E1", 1, "",
         "Antenna setting"),
        ("CFG-ITFM-ENABLE_AUX", 0x10410013, "L", 1, "",
         "Set to true to scan auxiliary bands"),
        # CFG-LOGFILTER-
        ("CFG-LOGFILTER", 0x10deffff, "", 0, "",
         "get all CFG-LOGFILTER"),
        ("CFG-LOGFILTER-RECORD_ENA", 0x10de0002, "L", 1, "",
         "Recording enabled"),
        ("CFG-LOGFILTER-ONCE_PER_WAKE_UP_ENA", 0x10de0003, "L", 1, "",
         "Once per wakeup"),
        ("CFG-LOGFILTER-APPLY_ALL_FILTERS", 0x10de0004, "L", 1, "",
         "Apply all filter settings"),
        ("CFG-LOGFILTER-MIN_INTERVAL", 0x30de0005, "U2", 1, "s",
         "Minimum time interval between logged positions"),
        ("CFG-LOGFILTER-TIME_THRS", 0x30de0006, "U2", 1, "s",
         "Time threshold"),
        ("CFG-LOGFILTER-SPEED_THRS", 0x30de0007, "U2", 1, "m/s",
         "Speed threshold"),
        ("CFG-LOGFILTER-POSITION_THRS", 0x40de0008, "U4", 1, "m",
         "Position threshold"),
        # CFG-MOT-
        ("CFG-MOT", 0x3025ffff, "", 0, "",
         "get all CFG-MOT"),
        ("CFG-MOT-GNSSSPEED_THRS", 0x20250038, "U1", 0.01, "m/s",
         "GNSS speed threshold below which platform is considered "
         "as stationary"),
        ("CFG-MOT-GNSSDIST_THRS", 0x3025003b, "U2", 1, "",
         "Distance above which GNSS-based stationary motion is exit"),
        # CFG-MSGOUT-NMEA
        ("CFG-MSGOUT", 0x2091ffff, "", 0, "",
         "get all CFG-MSGOUT"),
        ("CFG-MSGOUT-NMEA_ID_DTM_I2C", 0x209100a6, "U1", 1, "",
         "Output rate of the NMEA-GX-DTM message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_DTM_SPI", 0x209100aa, "U1", 1, "",
         "Output rate of the NMEA-GX-DTM message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_DTM_UART1", 0x209100a7, "U1", 1, "",
         "Output rate of the NMEA-GX-DTM message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_DTM_UART2", 0x209100a8, "U1", 1, "",
         "Output rate of the NMEA-GX-DTM message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_DTM_USB", 0x209100a9, "U1", 1, "",
         "Output rate of the NMEA-GX-DTM message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GBS_I2C", 0x209100dd, "U1", 1, "",
         "Output rate of the NMEA-GX-GBS message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GBS_SPI", 0x209100e1, "U1", 1, "",
         "Output rate of the NMEA-GX-GBS message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GBS_UART1", 0x209100de, "U1", 1, "",
         "Output rate of the NMEA-GX-GBS message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GBS_UART2", 0x209100df, "U1", 1, "",
         "Output rate of the NMEA-GX-GBS message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GBS_USB", 0x209100e0, "U1", 1, "",
         "Output rate of the NMEA-GX-GBS message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GGA_I2C", 0x209100ba, "U1", 1, "",
         "Output rate of the NMEA-GX-GGA message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GGA_SPI", 0x209100be, "U1", 1, "",
         "Output rate of the NMEA-GX-GGA message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GGA_UART1", 0x209100bb, "U1", 1, "",
         "Output rate of the NMEA-GX-GGA message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GGA_UART2", 0x209100bc, "U1", 1, "",
         "Output rate of the NMEA-GX-GGA message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GGA_USB", 0x209100bd, "U1", 1, "",
         "Output rate of the NMEA-GX-GGA message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GLL_I2C", 0x209100c9, "U1", 1, "",
         "Output rate of the NMEA-GX-GLL message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GLL_SPI", 0x209100cd, "U1", 1, "",
         "Output rate of the NMEA-GX-GLL message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GLL_UART1", 0x209100ca, "U1", 1, "",
         "Output rate of the NMEA-GX-GLL message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GLL_UART2", 0x209100cb, "U1", 1, "",
         "Output rate of the NMEA-GX-GLL message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GLL_USB", 0x209100cc, "U1", 1, "",
         "Output rate of the NMEA-GX-GLL message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GNS_I2C", 0x209100b5, "U1", 1, "",
         "Output rate of the NMEA-GX-GNS message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GNS_SPI", 0x209100b9, "U1", 1, "",
         "Output rate of the NMEA-GX-GNS message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GNS_UART1", 0x209100b6, "U1", 1, "",
         "Output rate of the NMEA-GX-GNS message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GNS_UART2", 0x209100b7, "U1", 1, "",
         "Output rate of the NMEA-GX-GNS message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GNS_USB", 0x209100b8, "U1", 1, "",
         "Output rate of the NMEA-GX-GNS message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GRS_I2C", 0x209100ce, "U1", 1, "",
         "Output rate of the NMEA-GX-GRS message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GRS_SPI", 0x209100d2, "U1", 1, "",
         "Output rate of the NMEA-GX-GRS message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GRS_UART1", 0x209100cf, "U1", 1, "",
         "Output rate of the NMEA-GX-GRS message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GRS_UART2", 0x209100d0, "U1", 1, "",
         "Output rate of the NMEA-GX-GRS message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GRS_USB", 0x209100d1, "U1", 1, "",
         "Output rate of the NMEA-GX-GRS message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GSA_I2C", 0x209100bf, "U1", 1, "",
         "Output rate of the NMEA-GX-GSA message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GSA_SPI", 0x209100c3, "U1", 1, "",
         "Output rate of the NMEA-GX-GSA message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GSA_UART1", 0x209100c0, "U1", 1, "",
         "Output rate of the NMEA-GX-GSA message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GSA_UART2", 0x209100c1, "U1", 1, "",
         "Output rate of the NMEA-GX-GSA message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GSA_USB", 0x209100c2, "U1", 1, "",
         "Output rate of the NMEA-GX-GSA message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GST_I2C", 0x209100d3, "U1", 1, "",
         "Output rate of the NMEA-GX-GST message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GST_SPI", 0x209100d7, "U1", 1, "",
         "Output rate of the NMEA-GX-GST message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GST_UART1", 0x209100d4, "U1", 1, "",
         "Output rate of the NMEA-GX-GST message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GST_UART2", 0x209100d5, "U1", 1, "",
         "Output rate of the NMEA-GX-GST message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_GST_USB", 0x209100d6, "U1", 1, "",
         "Output rate of the NMEA-GX-GST message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_GSV_I2C", 0x209100c4, "U1", 1, "",
         "Output rate of the NMEA-GX-GSV message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_GSV_SPI", 0x209100c8, "U1", 1, "",
         "Output rate of the NMEA-GX-GSV message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_GSV_UART1", 0x209100c5, "U1", 1, "",
         "Output rate of the NMEA-GX-GSV message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_GSV_UART2", 0x209100c6, "U1", 1, "",
         "Output rate of the NMEA-GX-GSV message on port UART"),
        ("CFG-MSGOUT-NMEA_ID_GSV_USB", 0x209100c7, "U1", 1, "",
         "Output rate of the NMEA-GX-GSV message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_RLM_I2C", 0x20910400, "U1", 1, "",
         "Output rate of the NMEA-GX-RLM message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_RLM_SPI", 0x20910404, "U1", 1, "",
         "Output rate of the NMEA-GX-RLM message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_RLM_UART1", 0x20910401, "U1", 1, "",
         "Output rate of the NMEA-GX-RLM message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_RLM_UART2", 0x20910402, "U1", 1, "",
         "Output rate of the NMEA-GX-RLM message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_RLM_USB", 0x20910403, "U1", 1, "",
         "Output rate of the NMEA-GX-RLM message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_RMC_I2C", 0x209100ab, "U1", 1, "",
         "Output rate of the NMEA-GX-RMC message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_RMC_SPI", 0x209100af, "U1", 1, "",
         "Output rate of the NMEA-GX-RMC message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_RMC_UART1", 0x209100ac, "U1", 1, "",
         "Output rate of the NMEA-GX-RMC message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_RMC_UART2", 0x209100ad, "U1", 1, "",
         "Output rate of the NMEA-GX-RMC message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_RMC_USB", 0x209100ae, "U1", 1, "",
         "Output rate of the NMEA-GX-RMC message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_VLW_I2C", 0x209100e7, "U1", 1, "",
         "Output rate of the NMEA-GX-VLW message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_VLW_SPI", 0x209100eb, "U1", 1, "",
         "Output rate of the NMEA-GX-VLW message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_VLW_UART1", 0x209100e8, "U1", 1, "",
         "Output rate of the NMEA-GX-VLW message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_VLW_UART2", 0x209100e9, "U1", 1, "",
         "Output rate of the NMEA-GX-VLW message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_VLW_USB", 0x209100ea, "U1", 1, "",
         "Output rate of the NMEA-GX-VLW message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_VTG_I2C", 0x209100b0, "U1", 1, "",
         "Output rate of the NMEA-GX-VTG message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_VTG_SPI", 0x209100b4, "U1", 1, "",
         "Output rate of the NMEA-GX-VTG message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_VTG_UART1", 0x209100b1, "U1", 1, "",
         "Output rate of the NMEA-GX-VTG message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_VTG_UART2", 0x209100b2, "U1", 1, "",
         "Output rate of the NMEA-GX-VTG message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_VTG_USB", 0x209100b3, "U1", 1, "",
         "Output rate of the NMEA-GX-VTG message on port USB"),
        ("CFG-MSGOUT-NMEA_ID_ZDA_I2C", 0x209100d8, "U1", 1, "",
         "Output rate of the NMEA-GX-ZDA message on port I2C"),
        ("CFG-MSGOUT-NMEA_ID_ZDA_SPI", 0x209100dc, "U1", 1, "",
         "Output rate of the NMEA-GX-ZDA message on port SPI"),
        ("CFG-MSGOUT-NMEA_ID_ZDA_UART1", 0x209100d9, "U1", 1, "",
         "Output rate of the NMEA-GX-ZDA message on port UART1"),
        ("CFG-MSGOUT-NMEA_ID_ZDA_UART2", 0x209100da, "U1", 1, "",
         "Output rate of the NMEA-GX-ZDA message on port UART2"),
        ("CFG-MSGOUT-NMEA_ID_ZDA_USB", 0x209100db, "U1", 1, "",
         "Output rate of the NMEA-GX-ZDA message on port USB"),
        # CFG-MSGOUT-PUBX
        ("CFG-MSGOUT-PUBX_ID_POLYP_I2C", 0x209100ec, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX00 message on port I2C"),
        ("CFG-MSGOUT-PUBX_ID_POLYP_SPI", 0x209100f0, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX00 message on port SPI"),
        ("CFG-MSGOUT-PUBX_ID_POLYP_UART1", 0x209100ed, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX00 message on port UART1"),
        ("CFG-MSGOUT-PUBX_ID_POLYP_UART2", 0x209100ee, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX00 message on port UART2"),
        ("CFG-MSGOUT-PUBX_ID_POLYP_USB", 0x209100ef, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX00 message on port USB"),
        ("CFG-MSGOUT-PUBX_ID_POLYS_I2C", 0x209100f1, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX03 message on port I2C"),
        ("CFG-MSGOUT-PUBX_ID_POLYS_SPI", 0x209100f5, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX03 message on port SPI"),
        ("CFG-MSGOUT-PUBX_ID_POLYS_UART1", 0x209100f2, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX03 message on port UART1"),
        ("CFG-MSGOUT-PUBX_ID_POLYS_UART2", 0x209100f3, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX03 message on port UART2"),
        ("CFG-MSGOUT-PUBX_ID_POLYS_USB", 0x209100f4, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX03 message on port USB"),
        ("CFG-MSGOUT-PUBX_ID_POLYT_I2C", 0x209100f6, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX04 message on port I2C"),
        ("CFG-MSGOUT-PUBX_ID_POLYT_SPI", 0x209100fa, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX04 message on port SPI"),
        ("CFG-MSGOUT-PUBX_ID_POLYT_UART1", 0x209100f7, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX04 message on port UART1"),
        ("CFG-MSGOUT-PUBX_ID_POLYT_UART2", 0x209100f8, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX04 message on port UART2"),
        ("CFG-MSGOUT-PUBX_ID_POLYT_USB", 0x209100f9, "U1", 1, "",
         "Output rate of the NMEA-GX-PUBX04 message on port USB"),
        # CFG-MSGOUT-RTCM_3X
        ("CFG-MSGOUT-RTCM_3X_TYPE1005_I2C", 0x209102bd, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1005 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1005_SPI", 0x209102c1, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1005 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1005_UART1", 0x209102be, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1005 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1005_UART2", 0x209102bf, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1005 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1005_USB", 0x209102c0, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1005 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1074_I2C", 0x2091035e, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1074 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1074_SPI", 0x20910362, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1074 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1074_UART1", 0x2091035f, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1074 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1074_UART2", 0x20910360, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1074 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1074_USB", 0x20910361, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1074 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1077_I2C", 0x209102cc, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1077 message on port I2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1077_SPI", 0x209102d0, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1077 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1077_UART1", 0x209102cd, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1077 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1077_UART2", 0x209102ce, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1077 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1077_USB", 0x209102cf, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1077 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1087_I2C", 0x209102d1, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1087 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1084_SPI", 0x20910367, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1084 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1084_UART1", 0x20910364, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1084 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1084_UART2", 0x20910365, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1084 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1084_USB", 0x20910366, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1084 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1087_SPI", 0x209102d5, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1087 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1087_UART1", 0x209102d2, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1087 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1087_UART2", 0x209102d3, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1087 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1087_USB", 0x209102d4, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1087 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1094_I2C", 0x20910368, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1094 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1094_SPI", 0x2091036c, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1094 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1094_UART1", 0x20910369, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1094 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1094_UART2", 0x2091036a, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1094 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1094_USB", 0x2091036b, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1094 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1097_I2C", 0x20910318, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1097 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1097_SPI", 0x2091031c, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1097 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1097_UART1", 0x20910319, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1097 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1097_UART2", 0x2091031a, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1097 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1097_USB", 0x2091031b, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1097 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1124_I2C", 0x2091036d, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1124 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1124_SPI", 0x20910371, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1124 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1124_UART1", 0x2091036e, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1124 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1124_UART2", 0x2091036f, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1124 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1124_USB", 0x20910370, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1124 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1127_I2C", 0x209102d6, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1127 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1127_SPI", 0x209102da, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1127 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1127_UART1", 0x209102d7, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1127 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1127_UART2", 0x209102d8, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1127 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1127_USB", 0x209102d9, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1127 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1230_I2C", 0x20910303, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1230 message on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1230_SPI", 0x20910307, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1230 message on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1230_UART1", 0x20910304, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1230 message on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1230_UART2", 0x20910305, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1230 message on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE1230_USB", 0x20910306, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE1230 message on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_0_I2C", 0x209102fe, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 0 message "
         "on port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_0_SPI", 0x20910302, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 0 message "
         "on port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_0_UART1", 0x209102ff, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 0 message "
         "on port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_0_UART2", 0x20910300, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 0 message "
         "on port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_0_USB", 0x20910301, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 0 message "
         "on port USB"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_1_I2C", 0x20910381, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 1 message on  "
         "port I2C"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_1_SPI", 0x20910385, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 1 message on  "
         "port SPI"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_1_UART1", 0x20910382, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 1 message on  "
         "port UART1"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_1_UART2", 0x20910383, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 1 message on "
         " port UART2"),
        ("CFG-MSGOUT-RTCM_3X_TYPE4072_1_USB", 0x20910384, "U1", 1, "",
         "Output rate of the RTCM-3X-TYPE4072, sub-type 1 message "
         "on port USB"),
        # CFG-MSGOUT-UBX_LOG
        ("CFG-MSGOUT-UBX_LOG_INFO_I2C", 0x20910259, "U1", 1, "",
         "Output rate of the UBX-LOG-INFO message on port I2C"),
        ("CFG-MSGOUT-UBX_LOG_INFO_SPI", 0x2091025d, "U1", 1, "",
         "Output rate of the UBX-LOG-INFO message on port SPI"),
        ("CFG-MSGOUT-UBX_LOG_INFO_UART1", 0x2091025a, "U1", 1, "",
         "Output rate of the UBX-LOG-INFO message on port UART1"),
        ("CFG-MSGOUT-UBX_LOG_INFO_UART2", 0x2091025b, "U1", 1, "",
         "Output rate of the UBX-LOG-INFO message on port UART2"),
        ("CFG-MSGOUT-UBX_LOG_INFO_USB", 0x2091025c, "U1", 1, "",
         "Output rate of the UBX-LOG-INFO message on port USB"),
        # CFG-MSGOUT-UBX_MON
        ("CFG-MSGOUT-UBX_MON_COMMS_I2C", 0x2091034f, "U1", 1, "",
         "Output rate of the UBX-MON-COMMS message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_COMMS_SPI", 0x20910353, "U1", 1, "",
         "Output rate of the UBX-MON-COMMS message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_COMMS_UART1", 0x20910350, "U1", 1, "",
         "Output rate of the UBX-MON-COMMS message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_COMMS_UART2", 0x20910351, "U1", 1, "",
         "Output rate of the UBX-MON-COMMS message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_COMMS_USB", 0x20910352, "U1", 1, "",
         "Output rate of the UBX-MON-COMMS message on port USB"),
        ("CFG-MSGOUT-UBX_MON_HW2_I2C", 0x209101b9, "U1", 1, "",
         "Output rate of the UBX-MON-HW2 message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_HW2_SPI", 0x209101bd, "U1", 1, "",
         "Output rate of the UBX-MON-HW2 message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_HW2_UART1", 0x209101ba, "U1", 1, "",
         "Output rate of the UBX-MON-HW2 message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_HW2_UART2", 0x209101bb, "U1", 1, "",
         "Output rate of the UBX-MON-HW2 message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_HW2_USB", 0x209101bc, "U1", 1, "",
         "Output rate of the UBX-MON-HW2 message on port USB"),
        ("CFG-MSGOUT-UBX_MON_HW3_I2C", 0x20910354, "U1", 1, "",
         "Output rate of the UBX-MON-HW3 message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_HW3_SPI", 0x20910358, "U1", 1, "",
         "Output rate of the UBX-MON-HW3 message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_HW3_UART1", 0x20910355, "U1", 1, "",
         "Output rate of the UBX-MON-HW3 message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_HW3_UART2", 0x20910356, "U1", 1, "",
         "Output rate of the UBX-MON-HW3 message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_HW3_USB", 0x20910357, "U1", 1, "",
         "Output rate of the UBX-MON-HW3 message on port USB"),
        ("CFG-MSGOUT-UBX_MON_HW_I2C", 0x209101b4, "U1", 1, "",
         "Output rate of the UBX-MON-HW message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_HW_SPI", 0x209101b8, "U1", 1, "",
         "Output rate of the UBX-MON-HW message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_HW_UART1", 0x209101b5, "U1", 1, "",
         "Output rate of the UBX-MON-HW message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_HW_UART2", 0x209101b6, "U1", 1, "",
         "Output rate of the UBX-MON-HW message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_HW_USB", 0x209101b7, "U1", 1, "",
         "Output rate of the UBX-MON-HW message on port USB"),
        ("CFG-MSGOUT-UBX_MON_IO_I2C", 0x209101a5, "U1", 1, "",
         "Output rate of the UBX-MON-IO message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_IO_SPI", 0x209101a9, "U1", 1, "",
         "Output rate of the UBX-MON-IO message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_IO_UART1", 0x209101a6, "U1", 1, "",
         "Output rate of the UBX-MON-IO message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_IO_UART2", 0x209101a7, "U1", 1, "",
         "Output rate of the UBX-MON-IO message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_IO_USB", 0x209101a8, "U1", 1, "",
         "Output rate of the UBX-MON-IO message on port USB"),
        ("CFG-MSGOUT-UBX_MON_MSGPP_I2C", 0x20910196, "U1", 1, "",
         "Output rate of the UBX-MON-MSGPP message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_MSGPP_SPI", 0x2091019a, "U1", 1, "",
         "Output rate of the UBX-MON-MSGPP message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_MSGPP_UART1", 0x20910197, "U1", 1, "",
         "Output rate of the UBX-MON-MSGPP message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_MSGPP_UART2", 0x20910198, "U1", 1, "",
         "Output rate of the UBX-MON-MSGPP message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_MSGPP_USB", 0x20910199, "U1", 1, "",
         "Output rate of the UBX-MON-MSGPP message on port USB"),
        ("CFG-MSGOUT-UBX_MON_RF_I2C", 0x20910359, "U1", 1, "",
         "Output rate of the UBX-MON-RF message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_RF_SPI", 0x2091035d, "U1", 1, "",
         "Output rate of the UBX-MON-RF message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_RF_UART1", 0x2091035a, "U1", 1, "",
         "Output rate of the UBX-MON-RF message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_RF_UART2", 0x2091035b, "U1", 1, "",
         "Output rate of the UBX-MON-RF message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_RF_USB", 0x2091035c, "U1", 1, "",
         "Output rate of the UBX-MON-RF message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEQZSS_I2C", 0x20910386, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEQZSS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMEQZSS_SPI", 0x2091038a, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEQZSS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_TIMEQZSS_USB", 0x20910387, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEQZSS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEQZSS_UART1", 0x20910388, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEQZSS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMEQZSS_UART2", 0x20910389, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEQZSS message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_RXBUF_I2C", 0x209101a0, "U1", 1, "",
         "Output rate of the UBX-MON-RXBUF message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_RXBUF_SPI", 0x209101a4, "U1", 1, "",
         "Output rate of the UBX-MON-RXBUF message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_RXBUF_UART1", 0x209101a1, "U1", 1, "",
         "Output rate of the UBX-MON-RXBUF message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_RXBUF_UART2", 0x209101a2, "U1", 1, "",
         "Output rate of the UBX-MON-RXBUF message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_RXBUF_USB", 0x209101a3, "U1", 1, "",
         "Output rate of the UBX-MON-RXBUF message on port USB"),
        ("CFG-MSGOUT-UBX_MON_RXR_I2C", 0x20910187, "U1", 1, "",
         "Output rate of the UBX-MON-RXR message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_RXR_SPI", 0x2091018b, "U1", 1, "",
         "Output rate of the UBX-MON-RXR message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_RXR_UART1", 0x20910188, "U1", 1, "",
         "Output rate of the UBX-MON-RXR message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_RXR_UART2", 0x20910189, "U1", 1, "",
         "Output rate of the UBX-MON-RXR message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_RXR_USB", 0x2091018a, "U1", 1, "",
         "Output rate of the UBX-MON-RXR message on port USB"),
        ("CFG-MSGOUT-UBX_MON_SPAN_I2C", 0x2091038b, "U1", 1, "",
         "Output rate of the UBX-MON-SPAN message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_SPAN_SPI", 0x2091038f, "U1", 1, "",
         "Output rate of the UBX-MON-SPAN message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_SPAN_UART1", 0x2091038c, "U1", 1, "",
         "Output rate of the UBX-MON-SPAN message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_SPAN_UART2", 0x2091038d, "U1", 1, "",
         "Output rate of the UBX-MON-SPAN message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_SPAN_USB", 0x2091038e, "U1", 1, "",
         "Output rate of the UBX-MON-SPAN message on port USB"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_I2C", 0x2091019b, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_SPI", 0x2091019f, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_UART1", 0x2091019c, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_UART2", 0x2091019d, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_USB", 0x2091019e, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_AOPSTATUS_I2C", 0x20910079, "U1", 1, "",
         "Output rate of the UBX-MON-AOPSTATUS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_AOPSTATUS_SPI", 0x2091007d, "U1", 1, "",
         "Output rate of the UBX-MON-AOPSTATUS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_AOPSTATUS_UART1", 0x2091007a, "U1", 1, "",
         "Output rate of the UBX-MON-AOPSTATUS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_AOPSTATUS_UART2", 0x2091007b, "U1", 1, "",
         "Output rate of the UBX-MON-AOPSTATUS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_AOPSTATUS_USB", 0x2091007c, "U1", 1, "",
         "Output rate of the UBX-MON-AOPSTATUS message on port USB"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_I2C", 0x2091019b, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port I2C"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_SPI", 0x2091019f, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port SPI"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_UART1", 0x2091019c, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port UART1"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_UART2", 0x2091019d, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port UART2"),
        ("CFG-MSGOUT-UBX_MON_TXBUF_USB", 0x2091019e, "U1", 1, "",
         "Output rate of the UBX-MON-TXBUF message on port USB"),
        # CFG-MSGOUT-UBX_NAV
        ("CFG-MSGOUT-UBX_NAV_CLOCK_I2C", 0x20910065, "U1", 1, "",
         "Output rate of the UBX-NAV-CLOCK message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_CLOCK_SPI", 0x20910069, "U1", 1, "",
         "Output rate of the UBX-NAV-CLOCK message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_CLOCK_UART1", 0x20910066, "U1", 1, "",
         "Output rate of the UBX-NAV-CLOCK message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_CLOCK_UART2", 0x20910067, "U1", 1, "",
         "Output rate of the UBX-NAV-CLOCK message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_CLOCK_USB", 0x20910068, "U1", 1, "",
         "Output rate of the UBX-NAV- CLOCK message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_DOP_I2C", 0x20910038, "U1", 1, "",
         "Output rate of the UBX-NAV-DOP message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_DOP_SPI", 0x2091003c, "U1", 1, "",
         "Output rate of the UBX-NAV-DOP message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_DOP_UART1", 0x20910039, "U1", 1, "",
         "Output rate of the UBX-NAV-DOP message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_DOP_UART2", 0x2091003a, "U1", 1, "",
         "Output rate of the UBX-NAV-DOP message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_DOP_USB", 0x2091003b, "U1", 1, "",
         "Output rate of the UBX-NAV-DOP message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_EOE_I2C", 0x2091015f, "U1", 1, "",
         "Output rate of the UBX-NAV-EOE message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_EOE_SPI", 0x20910163, "U1", 1, "",
         "Output rate of the UBX-NAV-EOE message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_EOE_UART1", 0x20910160, "U1", 1, "",
         "Output rate of the UBX-NAV-EOE message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_EOE_UART2", 0x20910161, "U1", 1, "",
         "Output rate of the UBX-NAV-EOE message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_EOE_USB", 0x20910162, "U1", 1, "",
         "Output rate of the UBX-NAV-EOE message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_GEOFENCE_I2C", 0x209100a1, "U1", 1, "",
         "Output rate of the UBX-NAV-GEOFENCE message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_GEOFENCE_SPI", 0x209100a5, "U1", 1, "",
         "Output rate of the UBX-NAV-GEOFENCE message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_GEOFENCE_UART1", 0x209100a2, "U1", 1, "",
         "Output rate of the UBX-NAV-GEOFENCE message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_GEOFENCE_UART2", 0x209100a3, "U1", 1, "",
         "Output rate of the UBX-NAV-GEOFENCE message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_GEOFENCE_USB", 0x209100a4, "U1", 1, "",
         "Output rate of the UBX-NAV- GEOFENCE message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSECEF_I2C", 0x2091002e, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSECEF message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSECEF_SPI", 0x20910032, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSECEF message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSECEF_UART1", 0x2091002f, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSECEF message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSECEF_UART2", 0x20910030, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSECEF message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSECEF_USB", 0x20910031, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSECEF message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSLLH_I2C", 0x20910033, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSLLH message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSLLH_SPI", 0x20910037, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSLLH message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSLLH_UART1", 0x20910034, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSLLH message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSLLH_UART2", 0x20910035, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSLLH message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_HPPOSLLH_USB", 0x20910036, "U1", 1, "",
         "Output rate of the UBX-NAV-HPPOSLLH message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_ODO_I2C", 0x2091007e, "U1", 1, "",
         "Output rate of the UBX-NAV-ODO message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_ODO_SPI", 0x20910082, "U1", 1, "",
         "Output rate of the UBX-NAV-ODO message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_ODO_UART1", 0x2091007f, "U1", 1, "",
         "Output rate of the UBX-NAV-ODO message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_ODO_UART2", 0x20910080, "U1", 1, "",
         "Output rate of the UBX-NAV-ODO message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_ODO_USB", 0x20910081, "U1", 1, "",
         "Output rate of the UBX-NAV-ODO message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_ORB_I2C", 0x20910010, "U1", 1, "",
         "Output rate of the UBX-NAV-ORB message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_ORB_SPI", 0x20910014, "U1", 1, "",
         "Output rate of the UBX-NAV-ORB message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_ORB_UART1", 0x20910011, "U1", 1, "",
         "Output rate of the UBX-NAV-ORB message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_ORB_UART2", 0x20910012, "U1", 1, "",
         "Output rate of the UBX-NAV-ORB message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_ORB_USB", 0x20910013, "U1", 1, "",
         "Output rate of the UBX-NAV-ORB message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_POSECEF_I2C", 0x20910024, "U1", 1, "",
         "Output rate of the UBX-NAV-POSECEF message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_POSECEF_SPI", 0x20910028, "U1", 1, "",
         "Output rate of the UBX-NAV-POSECEF message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_POSECEF_UART1", 0x20910025, "U1", 1, "",
         "Output rate of the UBX-NAV-POSECEF message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_POSECEF_UART2", 0x20910026, "U1", 1, "",
         "Output rate of the UBX-NAV-POSECEF message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_POSECEF_USB", 0x20910027, "U1", 1, "",
         "Output rate of the UBX-NAV-POSECEF message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_POSLLH_I2C", 0x20910029, "U1", 1, "",
         "Output rate of the UBX-NAV-POSLLH message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_POSLLH_SPI", 0x2091002d, "U1", 1, "",
         "Output rate of the UBX-NAV-POSLLH message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_POSLLH_UART1", 0x2091002a, "U1", 1, "",
         "Output rate of the UBX-NAV-POSLLH message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_POSLLH_UART2", 0x2091002b, "U1", 1, "",
         "Output rate of the UBX-NAV-POSLLH message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_POSLLH_USB", 0x2091002c, "U1", 1, "",
         "Output rate of the UBX-NAV-POSLLH message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_PVT_I2C", 0x20910006, "U1", 1, "",
         "Output rate of the UBX-NAV-PVT message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_PVT_SPI", 0x2091000a, "U1", 1, "",
         "Output rate of the UBX-NAV-PVT message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_PVT_UART1", 0x20910007, "U1", 1, "",
         "Output rate of the UBX-NAV-PVT message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_PVT_UART2", 0x20910008, "U1", 1, "",
         "Output rate of the UBX-NAV-PVT message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_PVT_USB", 0x20910009, "U1", 1, "",
         "Output rate of the UBX-NAV-PVT message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_RELPOSNED_I2C", 0x2091008d, "U1", 1, "",
         "Output rate of the UBX-NAV-RELPOSNED message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_RELPOSNED_SPI", 0x20910091, "U1", 1, "",
         "Output rate of the UBX-NAV-RELPOSNED message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_RELPOSNED_UART1", 0x2091008e, "U1", 1, "",
         "Output rate of the UBX-NAV-RELPOSNED message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_RELPOSNED_UART2", 0x2091008f, "U1", 1, "",
         "Output rate of the UBX-NAV-RELPOSNED message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_RELPOSNED_USB", 0x20910090, "U1", 1, "",
         "Output rate of the UBX-NAV-RELPOSNED message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_SAT_I2C", 0x20910015, "U1", 1, "",
         "Output rate of the UBX-NAV-SAT message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_SAT_SPI", 0x20910019, "U1", 1, "",
         "Output rate of the UBX-NAV-SAT message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_SAT_UART1", 0x20910016, "U1", 1, "",
         "Output rate of the UBX-NAV-SAT message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_SAT_UART2", 0x20910017, "U1", 1, "",
         "Output rate of the UBX-NAV-SAT message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_SAT_USB", 0x20910018, "U1", 1, "",
         "Output rate of the UBX-NAV-SAT message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_SBAS_I2C", 0x2091006a, "U1", 1, "",
         "Output rate of the UBX-NAV-SBAS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_SBAS_SPI", 0x2091006e, "U1", 1, "",
         "Output rate of the UBX-NAV-SBAS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_SBAS_UART1", 0x2091006b, "U1", 1, "",
         "Output rate of the UBX-NAV-SBAS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_SBAS_UART2", 0x2091006c, "U1", 1, "",
         "Output rate of the UBX-NAV-SBAS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_SBAS_USB", 0x2091006d, "U1", 1, "",
         "Output rate of the UBX-NAV-SBAS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_SIG_I2C", 0x20910345, "U1", 1, "",
         "Output rate of the UBX-NAV-SIG message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_SIG_SPI", 0x20910349, "U1", 1, "",
         "Output rate of the UBX-NAV-SIG message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_SIG_UART1", 0x20910346, "U1", 1, "",
         "Output rate of the UBX-NAV-SIG message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_SIG_UART2", 0x20910347, "U1", 1, "",
         "Output rate of the UBX-NAV-SIG message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_SIG_USB", 0x20910348, "U1", 1, "",
         "Output rate of the UBX-NAV-SIG message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_SLAS_I2C", 0x20910336, "U1", 1, "",
         "Output rate of the UBX-NAV-SLAS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_SLAS_SPI", 0x2091033a, "U1", 1, "",
         "Output rate of the UBX-NAV-SLAS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_SLAS_UART1", 0x20910338, "U1", 1, "",
         "Output rate of the UBX-NAV-SLAS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_SLAS_UART2", 0x20910339, "U1", 1, "",
         "Output rate of the UBX-NAV-SLAS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_SLAS_USB", 0x20910348, "U1", 1, "",
         "Output rate of the UBX-NAV-SLAS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_STATUS_I2C", 0x2091001a, "U1", 1, "",
         "Output rate of the UBX-NAV-STATUS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_STATUS_SPI", 0x2091001e, "U1", 1, "",
         "Output rate of the UBX-NAV-STATUS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_STATUS_UART1", 0x2091001b, "U1", 1, "",
         "Output rate of the UBX-NAV-STATUS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_STATUS_UART2", 0x2091001c, "U1", 1, "",
         "Output rate of the UBX-NAV-STATUS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_STATUS_USB", 0x2091001d, "U1", 1, "",
         "Output rate of the UBX-NAV-STATUS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_SVIN_I2C", 0x20910088, "U1", 1, "",
         "Output rate of the UBX-NAV-SVIN message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_SVIN_SPI", 0x2091008c, "U1", 1, "",
         "Output rate of the UBX-NAV-SVIN message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_SVIN_UART1", 0x20910089, "U1", 1, "",
         "Output rate of the UBX-NAV-SVIN message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_SVIN_UART2", 0x2091008a, "U1", 1, "",
         "Output rate of the UBX-NAV-SVIN message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_SVIN_USB", 0x2091008b, "U1", 1, "",
         "Output rate of the UBX-NAV-SVIN message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEBDS_I2C", 0x20910051, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEBDS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMEBDS_SPI", 0x20910055, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEBDS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_TIMEBDS_UART1", 0x20910052, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEBDS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMEBDS_UART2", 0x20910053, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEBDS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_TIMEBDS_USB", 0x20910054, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEBDS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGAL_I2C", 0x20910056, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGAL message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGAL_SPI", 0x2091005a, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGAL message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGAL_UART1", 0x20910057, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGAL message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGAL_UART2", 0x20910058, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGAL message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGAL_USB", 0x20910059, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGAL message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGLO_I2C", 0x2091004c, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGLO message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGLO_SPI", 0x20910050, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGLO message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGLO_UART1", 0x2091004d, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGLO message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGLO_UART2", 0x2091004e, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGLO message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGLO_USB", 0x2091004f, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGLO message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGPS_I2C", 0x20910047, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGPS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGPS_SPI", 0x2091004b, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGPS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGPS_UART1", 0x20910048, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGPS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGPS_UART2", 0x20910049, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGPS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_TIMEGPS_USB", 0x2091004a, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEGPS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMELS_I2C", 0x20910060, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMELS message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMELS_SPI", 0x20910064, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMELS message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_TIMELS_UART1", 0x20910061, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMELS message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMELS_UART2", 0x20910062, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMELS message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_TIMELS_USB", 0x20910063, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMELS message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_TIMEUTC_I2C", 0x2091005b, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEUTC message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_TIMEUTC_SPI", 0x2091005f, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEUTC message on port S"),
        ("CFG-MSGOUT-UBX_NAV_TIMEUTC_UART1", 0x2091005c, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEUTC message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_TIMEUTC_UART2", 0x2091005d, "U1", 1, "",
         "Output rate of the UBX-NAV-TIMEUTC message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_TIMEUTC_USB", 0x2091005e, "U1", 1, "",
         "Output rate of the UBX-NAV- TIMEUTC message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_VELECEF_I2C", 0x2091003d, "U1", 1, "",
         "Output rate of the UBX-NAV-VELECEF message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_VELECEF_SPI", 0x20910041, "U1", 1, "",
         "Output rate of the UBX-NAV-VELECEF message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_VELECEF_UART1", 0x2091003e, "U1", 1, "",
         "Output rate of the UBX-NAV-VELECEF message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_VELECEF_UART2", 0x2091003f, "U1", 1, "",
         "Output rate of the UBX-NAV-VELECEF message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_VELECEF_USB", 0x20910040, "U1", 1, "",
         "Output rate of the UBX-NAV-VELECEF message on port USB"),
        ("CFG-MSGOUT-UBX_NAV_VELNED_I2C", 0x20910042, "U1", 1, "",
         "Output rate of the UBX-NAV-VELNED message on port I2C"),
        ("CFG-MSGOUT-UBX_NAV_VELNED_SPI", 0x20910046, "U1", 1, "",
         "Output rate of the UBX-NAV-VELNED message on port SPI"),
        ("CFG-MSGOUT-UBX_NAV_VELNED_UART1", 0x20910043, "U1", 1, "",
         "Output rate of the UBX-NAV-VELNED message on port UART1"),
        ("CFG-MSGOUT-UBX_NAV_VELNED_UART2", 0x20910044, "U1", 1, "",
         "Output rate of the UBX-NAV-VELNED message on port UART2"),
        ("CFG-MSGOUT-UBX_NAV_VELNED_USB", 0x20910045, "U1", 1, "",
         "Output rate of the UBX-NAV-VELNED message on port USB"),
        # CFG-MSGOUT-UBX_RXM
        ("CFG-MSGOUT-UBX_RXM_MEASX_I2C", 0x20910204, "U1", 1, "",
         "Output rate of the UBX-RXM-MEASX message on port I2C"),
        ("CFG-MSGOUT-UBX_RXM_MEASX_SPI", 0x20910208, "U1", 1, "",
         "Output rate of the UBX-RXM-MEASX message on port SPI"),
        ("CFG-MSGOUT-UBX_RXM_MEASX_UART1", 0x20910205, "U1", 1, "",
         "Output rate of the UBX-RXM-MEASX message on port UART1"),
        ("CFG-MSGOUT-UBX_RXM_MEASX_UART2", 0x20910206, "U1", 1, "",
         "Output rate of the UBX-RXM-MEASX message on port UART2"),
        ("CFG-MSGOUT-UBX_RXM_MEASX_USB", 0x20910207, "U1", 1, "",
         "Output rate of the UBX-RXM-MEASX message on port USB"),
        ("CFG-MSGOUT-UBX_RXM_RAWX_I2C", 0x209102a4, "U1", 1, "",
         "Output rate of the UBX-RXM-RAWX message on port I2C"),
        ("CFG-MSGOUT-UBX_RXM_RAWX_SPI", 0x209102a8, "U1", 1, "",
         "Output rate of the UBX-RXM-RAWX message on port SPI"),
        ("CFG-MSGOUT-UBX_RXM_RAWX_UART1", 0x209102a5, "U1", 1, "",
         "Output rate of the UBX-RXM-RAWX message on port UART1"),
        ("CFG-MSGOUT-UBX_RXM_RAWX_UART2", 0x209102a6, "U1", 1, "",
         "Output rate of the UBX-RXM-RAWX message on port UART2"),
        ("CFG-MSGOUT-UBX_RXM_RAWX_USB", 0x209102a7, "U1", 1, "",
         "Output rate of the UBX-RXM-RAWX message on port USB"),
        ("CFG-MSGOUT-UBX_RXM_RLM_I2C", 0x2091025e, "U1", 1, "",
         "Output rate of the UBX-RXM-RLM message on port I2C"),
        ("CFG-MSGOUT-UBX_RXM_RLM_SPI", 0x20910262, "U1", 1, "",
         "Output rate of the UBX-RXM-RLM message on port SPI"),
        ("CFG-MSGOUT-UBX_RXM_RLM_UART1", 0x2091025f, "U1", 1, "",
         "Output rate of the UBX-RXM-RLM message on port UART1"),
        ("CFG-MSGOUT-UBX_RXM_RLM_UART2", 0x20910260, "U1", 1, "",
         "Output rate of the UBX-RXM-RLM message on port UART2"),
        ("CFG-MSGOUT-UBX_RXM_RLM_USB", 0x20910261, "U1", 1, "",
         "Output rate of the UBX-RXM-RLM message on port USB"),
        ("CFG-MSGOUT-UBX_RXM_RTCM_I2C", 0x20910268, "U1", 1, "",
         "Output rate of the UBX-RXM-RTCM message on port I2C"),
        ("CFG-MSGOUT-UBX_RXM_RTCM_SPI", 0x2091026c, "U1", 1, "",
         "Output rate of the UBX-RXM-RTCM message on port SPI"),
        ("CFG-MSGOUT-UBX_RXM_RTCM_UART1", 0x20910269, "U1", 1, "",
         "Output rate of the UBX-RXM-RTCM message on port UART1"),
        ("CFG-MSGOUT-UBX_RXM_RTCM_UART2", 0x2091026a, "U1", 1, "",
         "Output rate of the UBX-RXM-RTCM message on port UART2"),
        ("CFG-MSGOUT-UBX_RXM_RTCM_USB", 0x2091026b, "U1", 1, "",
         "Output rate of the UBX-RXM-RTCM message on port USB"),
        ("CFG-MSGOUT-UBX_RXM_SFRBX_I2C", 0x20910231, "U1", 1, "",
         "Output rate of the UBX-RXM-SFRBX message on port I2C"),
        ("CFG-MSGOUT-UBX_RXM_SFRBX_SPI", 0x20910235, "U1", 1, "",
         "Output rate of the UBX-RXM-SFRBX message on port SPI"),
        ("CFG-MSGOUT-UBX_RXM_SFRBX_UART1", 0x20910232, "U1", 1, "",
         "Output rate of the UBX-RXM-SFRBX message on port UART1"),
        ("CFG-MSGOUT-UBX_RXM_SFRBX_UART2", 0x20910233, "U1", 1, "",
         "Output rate of the UBX-RXM-SFRBX message on port UART2"),
        ("CFG-MSGOUT-UBX_RXM_SFRBX_USB", 0x20910234, "U1", 1, "",
         "Output rate of the UBX-RXM-SFRBX message on port USB"),
        # CFG-MSGOUT-UBX_TIM
        ("CFG-MSGOUT-UBX_TIM_SVIN_I2C", 0x20910097, "U1", 1, "",
         "Output rate of the UBX-TIM-SVIN message on port I2C"),
        ("CFG-MSGOUT-UBX_TIM_SVIN_SPI", 0x2091009b, "U1", 1, "",
         "Output rate of the UBX-TIM-SVIN message on port SPI"),
        ("CFG-MSGOUT-UBX_TIM_SVIN_UART1", 0x20910098, "U1", 1, "",
         "Output rate of the UBX-TIM-SVIN message on port UART1"),
        ("CFG-MSGOUT-UBX_TIM_SVIN_UART2", 0x20910099, "U1", 1, "",
         "Output rate of the UBX-TIM-SVIN message on port UART2"),
        ("CFG-MSGOUT-UBX_TIM_SVIN_USB", 0x2091009a, "U1", 1, "",
         "Output rate of the UBX-TIM-SVIN message on port USB"),
        ("CFG-MSGOUT-UBX_TIM_TM2_I2C", 0x20910178, "U1", 1, "",
         "Output rate of the UBX-TIM-TM2 message on port I2C"),
        ("CFG-MSGOUT-UBX_TIM_TM2_SPI", 0x2091017c, "U1", 1, "",
         "Output rate of the UBX-TIM-TM2 message on port SPI"),
        ("CFG-MSGOUT-UBX_TIM_TM2_UART1", 0x20910179, "U1", 1, "",
         "Output rate of the UBX-TIM-TM2 message on port UART1"),
        ("CFG-MSGOUT-UBX_TIM_TM2_UART2", 0x2091017a, "U1", 1, "",
         "Output rate of the UBX-TIM-TM2 message on port UART2"),
        ("CFG-MSGOUT-UBX_TIM_TM2_USB", 0x2091017b, "U1", 1, "",
         "Output rate of the UBX-TIM-TM2 message on port USB"),
        ("CFG-MSGOUT-UBX_TIM_TP_I2C", 0x2091017d, "U1", 1, "",
         "Output rate of the UBX-TIM-TP message on port I2C"),
        ("CFG-MSGOUT-UBX_TIM_TP_SPI", 0x20910181, "U1", 1, "",
         "Output rate of the UBX-TIM-TP message on port SPI"),
        ("CFG-MSGOUT-UBX_TIM_TP_UART1", 0x2091017e, "U1", 1, "",
         "Output rate of the UBX-TIM-TP message on port UART1"),
        ("CFG-MSGOUT-UBX_TIM_TP_UART2", 0x2091017f, "U1", 1, "",
         "Output rate of the UBX-TIM-TP message on port UART2"),
        ("CFG-MSGOUT-UBX_TIM_TP_USB", 0x20910180, "U1", 1, "",
         "Output rate of the UBX-TIM-TP message on port USB"),
        ("CFG-MSGOUT-UBX_TIM_VRFY_I2C", 0x20910092, "U1", 1, "",
         "Output rate of the UBX-TIM-VRFY message on port I2C"),
        ("CFG-MSGOUT-UBX_TIM_VRFY_SPI", 0x20910096, "U1", 1, "",
         "Output rate of the UBX-TIM-VRFY message on port SPI"),
        ("CFG-MSGOUT-UBX_TIM_VRFY_UART1", 0x20910093, "U1", 1, "",
         "Output rate of the UBX-TIM-VRFY message on port UART1"),
        ("CFG-MSGOUT-UBX_TIM_VRFY_UART2", 0x20910094, "U1", 1, "",
         "Output rate of the UBX-TIM-VRFY message on port UART2"),
        ("CFG-MSGOUT-UBX_TIM_VRFY_USB", 0x20910095, "U1", 1, "",
         "Output rate of the UBX-TIM-VRFY message on port USB"),
        # CFG-NAVHPG-
        ("CFG-NAVHPG", 0x2014ffff, "", 0, "",
         "get all CFG-NAVHPG"),
        ("CFG-NAVHPG-DGNSSMODE", 0x20140011, "E1", 1, "",
         "Differential corrections mode"),
        # CFG-NAVSPG-
        ("CFG-NAVSPG", 0x2011ffff, "", 0, "",
         "get all CFG-NAVSPG"),
        ("CFG-NAVSPG-FIXMODE", 0x20110011, "E1", 1, "",
         "Position fix mode"),
        ("CFG-NAVSPG-INIFIX3D", 0x10110013, "L", 1, "",
         "Initial fix must be a 3d fix"),
        ("CFG-NAVSPG-WKNROLLOVER", 0x30110017, "U2", 1, "",
         "GPS week rollover number"),
        ("CFG-NAVSPG-USE_PPP", 0x10110019, "L", 1, "",
         "Use Precise Point Positioning"),
        ("CFG-NAVSPG-UTCSTANDARD", 0x2011001c, "E1", 1, "",
         "UTC standard to be used"),
        ("CFG-NAVSPG-DYNMODEL", 0x20110021, "E1", 1, "",
         "Dynamic platform model"),
        ("CFG-NAVSPG-ACKAIDING", 0x10110025, "L", 1, "",
         "Acknowledge assistance input messages"),
        ("CFG-NAVSPG-USE_USRDAT", 0x10110061, "L", 1, "",
         "Use user geodetic datum"),
        ("CFG-NAVSPG-USRDAT_MAJA", 0x50110062, "R8", 1, "m",
         "Geodetic datum semi-major axis"),
        ("CFG-NAVSPG-USRDAT_FLAT", 0x50110063, "R8", 1, "",
         "Geodetic datum 1.0 / flattening"),
        ("CFG-NAVSPG-USRDAT_DX", 0x40110064, "R4", 1, "m",
         "Geodetic datum X axis shift at the origin"),
        ("CFG-NAVSPG-USRDAT_DY", 0x40110065, "R4", 1, "m",
         "Geodetic datum Y axis shift at the origin"),
        ("CFG-NAVSPG-USRDAT_DZ", 0x40110066, "R4", 1, "m",
         "Geodetic datum Z axis shift at the origin"),
        ("CFG-NAVSPG-USRDAT_ROTX", 0x40110067, "R4", 1, "arcsec",
         "Geodetic datum rotation about the X axis"),
        ("CFG-NAVSPG-USRDAT_ROTY", 0x40110068, "R4", 1, "arcsec",
         "Geodetic datum rotation about the Y axis ()"),
        ("CFG-NAVSPG-USRDAT_ROTZ", 0x40110069, "R4", 1, "arcsec",
         "Geodetic datum rotation about the Z axis"),
        ("CFG-NAVSPG-USRDAT_SCALE", 0x4011006a, "R4", 1, "ppm",
         "Geodetic datum scale factor"),
        ("CFG-NAVSPG-INFIL_MINSVS", 0x201100a1, "U1", 1, "",
         "Minimum number of satellites for navigation"),
        ("CFG-NAVSPG-INFIL_MAXSVS", 0x201100a2, "U1", 1, "",
         "Maximum number of satellites for navigation"),
        ("CFG-NAVSPG-INFIL_MINCNO", 0x201100a3, "U1", 1, "dBHz",
         "Minimum satellite signal level for navigation"),
        ("CFG-NAVSPG-INFIL_MINELEV", 0x201100a4, "I1", 1, "deg",
         "Minimum elevation for a GNSS satellite to be used in navigation"),
        ("CFG-NAVSPG-INFIL_NCNOTHRS", 0x201100aa, "U1", 1, "",
         "Number of satellites required to have C/N0 above "
         "CFG-NAVSPG-INFIL_CNOTHRS for a fix to be attempted"),
        ("CFG-NAVSPG-INFIL_CNOTHRS", 0x201100ab, "U1", 1, "",
         "C/N0 threshold for deciding whether to attempt a fix"),
        ("CFG-NAVSPG-OUTFIL_PDOP", 0x301100b1, "U2", 0.1, "",
         "Output filter position DOP mask (threshold)"),
        ("CFG-NAVSPG-OUTFIL_TDOP", 0x301100b2, "U2", 0.11, "",
         "Output filter time DOP mask (threshold)"),
        ("CFG-NAVSPG-OUTFIL_PACC", 0x301100b3, "U2", 1, "m",
         "Output filter position accuracy mask (threshold)"),
        ("CFG-NAVSPG-OUTFIL_TACC", 0x301100b4, "U2", 1, "m",
         "Output filter time accuracy mask (threshold)"),
        ("CFG-NAVSPG-OUTFIL_FACC", 0x301100b5, "U2", 0.01, "m/s",
         "Output filter frequency accuracy mask (threshold)"),
        ("CFG-NAVSPG-CONSTR_ALT", 0x401100c1, "I4", 0.01, "m",
         "Fixed altitude (mean sea level) for 2D fix mode"),
        ("CFG-NAVSPG-CONSTR_ALTVAR", 0x401100c2, "U4", 0.0001, "M^2",
         "Fixed altitude variance for 2D mode"),
        ("CFG-NAVSPG-CONSTR_DGNSSTO", 0x201100c4, "U1", 1, "s",
         "DGNSS timeout"),
        ("CFG-NAVSPG-SIGATTCOMP", 0x201100d6, "E1", 1, "",
         "Permanently attenuated signal compensation mode"),
        # CFG-NMEA-
        ("CFG-NMEA", 0x2093ffff, "", 0, "",
         "get all CFG-NMEA"),
        ("CFG-NMEA-PROTVER", 0x20930001, "E1", 1, "",
         "NMEA protocol version"),
        ("CFG-NMEA-MAXSVS", 0x20930002, "E1", 1, "",
         "Maximum number of SVs to report per Talker ID"),
        ("CFG-NMEA-COMPAT", 0x10930003, "L", 1, "",
         "Enable compatibility mode"),
        ("CFG-NMEA-CONSIDER", 0x10930004, "L", 1, "",
         "Enable considering mode"),
        ("CFG-NMEA-LIMIT82", 0x10930005, "L", 1, "",
         "Enable strict limit to 82 characters maximum NMEA message length"),
        ("CFG-NMEA-HIGHPREC", 0x10930006, "L", 1, "",
         "Enable high precision mode"),
        ("CFG-NMEA-SVNUMBERING", 0x20930007, "E1", 1, "",
         "Display configuration for SVs that have no value defined in NMEA"),
        ("CFG-NMEA-FILT_GPS", 0x10930011, "L", 1, "",
         "Disable reporting of GPS satellites"),
        ("CFG-NMEA-FILT_SBAS", 0x10930012, "L", 1, "",
         "Disable reporting of SBAS satellites"),
        ("CFG-NMEA-FILT_GAL", 0x10930013, "L", 1, "",
         "Disable reporting of GALILEO satellites"),
        ("CFG-NMEA-FILT_QZSS", 0x10930015, "L", 1, "",
         "Disable reporting of QZSS satellites"),
        ("CFG-NMEA-FILT_GLO", 0x10930016, "L", 1, "",
         "Disable reporting of GLONASS satellites"),
        ("CFG-NMEA-FILT_BDS", 0x10930017, "L", 1, "",
         "Disable reporting of BeiDou satellites"),
        ("CFG-NMEA-OUT_INVFIX", 0x10930021, "L", 1, "",
         "Enable position output for failed or invalid fixes"),
        ("CFG-NMEA-OUT_MSKFIX", 0x10930022, "L", 1, "",
         "Enable position output for invalid fixes"),
        ("CFG-NMEA-OUT_INVTIME", 0x10930023, "L", 1, "",
         "Enable time output for invalid times"),
        ("CFG-NMEA-OUT_INVDATE", 0x10930024, "L", 1, "",
         "Enable date output for invalid dates"),
        ("CFG-NMEA-OUT_ONLYGPS", 0x10930025, "L", 1, "",
         "Restrict output to GPS satellites only"),
        ("CFG-NMEA-OUT_FROZENCOG", 0x10930026, "L", 1, "",
         "Enable course over ground output even if it is frozen"),
        ("CFG-NMEA-MAINTALKERID", 0x20930031, "E1", 1, "",
         "Main Talker ID"),
        ("CFG-NMEA-GSVTALKERID", 0x20930032, "E1", 1, "",
         "Talker ID for GSV NMEA messages"),
        ("CFG-NMEA-BDSTALKERID", 0x30930033, "U2", 1, "",
         "BeiDou Talker ID"),
        # CFG-ODO-
        ("CFG-ODO", 0x1022ffff, "", 0, "",
         "get all CFG-ODO"),
        ("CFG-ODO-USE_ODO", 0x10220001, "L", 1, "",
         "Use odometer"),
        ("CFG-ODO-USE_COG", 0x10220002, "L", 1, "",
         "Use low-speed course over ground filter"),
        ("CFG-ODO-OUTLPVEL", 0x10220003, "L", 1, "",
         "Output low-pass filtered velocity"),
        ("CFG-ODO-OUTLPCOG", 0x10220004, "L", 1, "",
         "Output low-pass filtered course over ground (heading)"),
        ("CFG-ODO-PROFILE", 0x20220005, "E1", 1, "",
         "Odometer profile configuration"),
        ("CFG-ODO-COGMAXSPEED", 0x20220021, "U1", 1, "m/s",
         "Upper speed limit for low-speed course over ground filter"),
        ("CFG-ODO-COGMAXPOSACC", 0x20220022, "U1", 1, "",
         "Maximum acceptable position accuracy for computing low-speed  "
         "filtered course over ground"),
        ("CFG-ODO-COGLPGAIN", 0x20220032, "", 1, "",
         "Course over ground low-pass filter level (at speed < 8 m/s)"),
        ("CFG-ODO-VELLPGAIN", 0x20220031, "U1", 1, "",
         "Velocity low-pass filter level"),
        # CFG-PM-
        ("CFG-PM", 0x20d0ffff, "", 0, "",
         "get all CFG-PM, reciver power management"),
        ("CFG-PM-OPERATEMODE", 0x20d00001, "L", 1, "",
         "set PSMOO or PSMCT mode"),
        ("CFG-PM-POSUPDATEPERIOD", 0x40d00002, "U4", 1, "",
         "Position update period for PSMOO."),
        ("CFG-PM-ACQPERIOD", 0x40d00003, "U4", 1, "s",
         "Acquisition period if receiver fails to achieve a position fix"),
        ("CFG-PM-GRIDOFFSET", 0x40d00004, "U4", 1, "s",
         "Position update period grid offset relative to GPS start of week."),
        ("CFG-PM-ONTIME", 0x30d00005, "U2", 1, "s",
         "Time to stay in Tracking state."),
        ("CFG-PM-MINACQTIME", 0x20d00006, "U1", 1, "s",
         "Minimum time to spend in Acquisition state"),
        ("CFG-PM-MAXACQTIME", 0x20d00007, "U1", 1, "s",
         "Maximum time to spend in Acquisition state"),
        ("CFG-PM-DONOTENTEROFF", 0x10d00008, "L", 1, "",
         "Behavior when failure to achieve a position during update period."),
        ("CFG-PM-WAITTIMEFIX", 0x10d00009, "L", 1, "",
         "wait for time fix"),
        ("CFG-PM-UPDATEEPH", 0x10d0000a, "L", 1, "",
         "Update ephemeris regularly."),
        ("CFG-PM-EXTINTSEL", 0x20d0000b, "E1", 1, "",
         "EXTINT pin select."),
        ("CFG-PM-EXTINTWAKE", 0x10d0000c, "L", 1, "",
         "EXTINT pin control (Wake)"),
        ("CFG-PM-EXTINTBACKUP", 0x10d0000d, "L", 1, "",
         "EXTINT pin control (Backup)"),
        ("CFG-PM-EXTINTINACTIVE", 0x10d0000e, "L", 1, "",
         "EXTINT pin control (Inactive)"),
        ("CFG-PM-UPDATEEPH", 0x10d0000d, "U4", 0.001, "s",
         "Inactivity time out on EXTINT pin if enabled"),
        ("CFG-PM-LIMITPEAKCURR", 0x10d00010, "L", 1, "",
         "Limit peak current"),
        # CFG-QZSS-
        ("CFG-QZSS", 0x3037ffff, "", 0, "s",
         "get all CFG-QZSS"),
        ("CFG-QZSS-USE_SLAS_DGNSS", 0x10370005, "L", 0.001, "",
         "Apply QZSS SLAS DGNSS corrections"),
        ("CFG-QZSS-USE_TESTMODE", 0x10370006, "L", 0.001, "",
         "Use QZSS SLAS data when it is in test mode"),
        ("CFG-QZSS-USE_SLAS_RAIM_UNCORR", 0x10370007, "L", 0.001, "",
         "Raim out measurements that are not corrected by QZSS SLAS"),
        # CFG-RATE-
        ("CFG-RATE", 0x3021ffff, "", 0, "s",
         "get all CFG-RATE"),
        ("CFG-RATE-MEAS", 0x30210001, "U2", 0.001, "s",
         "Nominal time between GNSS measurements"),
        ("CFG-RATE-NAV", 0x30210002, "U2", 1, "",
         "Ratio of number of measurements to number of navigation solutions"),
        ("CFG-RATE-TIMEREF", 0x20210003, "E1", 1, "",
         "Time system to which measurements are aligned"),
        # CFG-RINV-
        ("CFG-RINV", 0x10c7ffff, "", 0, "",
         "get all CFG-RINV"),
        ("CFG-RINV-DUMP", 0x10c70001, "L", 1, "",
         "Dump data at startup"),
        ("CFG-RINV-BINARY", 0x10c70002, "L", 1, "",
         "Data is binary"),
        ("CFG-RINV-DATA_SIZE", 0x20c70003, "U1", 1, "",
         "Size of data"),
        ("CFG-RINV-CHUNK0", 0x50c70004, "X8", 1, "",
         "Data bytes 1-8 (LSB)"),
        ("CFG-RINV-CHUNK1", 0x50c70005, "X8", 1, "",
         "Data bytes 9-16"),
        ("CFG-RINV-CHUNK2", 0x50c70006, "X8", 1, "",
         "Data bytes 17-24"),
        ("CFG-RINV-CHUNK3", 0x50c70007, "X8", 1, "",
         "Data bytes 25-30 (MSB)"),
        # CFG-SBAS-
        ("CFG-SBAS", 0x1036ffff, "", 0, "",
         "get all CFG-SBAS"),
        ("CFG-SBAS-USE_TESTMODE", 0x10360002, "L", 1, "",
         "Use SBAS data when it is in test mode"),
        ("CFG-SBAS-USE_RANGING", 0x10360003, "L", 1, "",
         "Use SBAS GEOs as a ranging source (for navigation)"),
        ("CFG-SBAS-USE_DIFFCORR", 0x10360004, "L", 1, "",
         "Use SBAS differential corrections"),
        ("CFG-SBAS-USE_INTEGRITY", 0x10360005, "L", 1, "",
         "Use SBAS integrity information"),
        ("CFG-SBAS-PRNSCANMASK", 0x50360006, "X8", 1, "",
         "SBAS PRN search configuration"),
        # CFG-SIGNAL-
        ("CFG-SIGNAL", 0x1031ffff, "", 0, "",
         "get all CFG-SIGNAL"),
        ("CFG-SIGNAL-GPS_ENA", 0x1031001f, "L", 1, "",
         "GPS enable"),
        ("CFG-SIGNAL-GPS_L1CA_ENA", 0x10310001, "L", 1, "",
         "GPS L1C/A"),
        ("CFG-SIGNAL-GPS_L2C_ENA", 0x10310003, "L", 1, "",
         "GPS L2C"),
        ("CFG-SIGNAL-SBAS_ENA", 0x10310020, "L", 1, "",
         "SBAS enable"),
        ("CFG-SIGNAL-SBAS_L1CA_ENA", 0x10310005, "L", 1, "",
         "SBAS L1C/A"),
        ("CFG-SIGNAL-GAL_ENA", 0x10310021, "L", 1, "",
         "Galileo enable"),
        ("CFG-SIGNAL-GAL_E1_ENA", 0x10310007, "L", 1, "",
         "Galileo E1"),
        ("CFG-SIGNAL-GAL_E5B_ENA", 0x1031000a, "L", 1, "",
         "Galileo E5b"),
        ("CFG-SIGNAL-BDS_ENA", 0x10310022, "L", 1, "",
         "BeiDou Enable"),
        ("CFG-SIGNAL-BDS_B1_ENA", 0x1031000d, "L", 1, "",
         "BeiDou B1I"),
        ("CFG-SIGNAL-BDS_B2_ENA", 0x1031000e, "L", 1, "",
         "BeiDou B2I"),
        ("CFG-SIGNAL-QZSS_ENA", 0x10310024, "L", 1, "",
         "QZSS enable"),
        ("CFG-SIGNAL-QZSS_L1CA_ENA", 0x10310012, "L", 1, "",
         "QZSS L1C/A"),
        ("CFG-SIGNAL-QZSS_L1S_ENA", 0x10310014, "L", 1, "",
         "QZSS L1S"),
        ("CFG-SIGNAL-QZSS_L2C_ENA", 0x10310015, "L", 1, "",
         "QZSS L2C"),
        ("CFG-SIGNAL-GLO_ENA", 0x10310025, "L", 1, "",
         "GLONASS enable"),
        ("CFG-SIGNAL-GLO_L1_ENA", 0x10310018, "L", 1, "",
         "GLONASS L1"),
        ("CFG-SIGNAL-GLO_L2_ENA", 0x1031001a, "L", 1, "",
         "GLONASS L2"),
        # CFG-SPI-
        ("CFG-SPI", 0x1064ffff, "", 0, "",
         "get all CFG-SPI"),
        ("CFG-SPI-MAXFF", 0x20640001, "U1", 1, "",
         "Number of bytes containing 0xFF to receive before "
         "switching off reception."),
        ("CFG-SPI-CPOLARITY", 0x10640002, "L", 1, "",
         "Clock polarity select"),
        ("CFG-SPI-CPHASE", 0x10640003, "L", 1, "",
         "Clock phase select"),
        ("CFG-SPI-EXTENDEDTIMEOUT", 0x10640005, "L", 1, "",
         "Flag to disable timeouting the interface after 1.5s"),
        ("CFG-SPI-ENABLED", 0x10640006, "L", 1, "",
         "Flag to indicate if the SPI interface should be enabled"),
        # CFG-SPIINPROT-
        ("CFG-SPIINPROT", 0x1079ffff, "", 0, "",
         "get all CFG-SPIINPROT"),
        ("CFG-SPIINPROT-UBX", 0x10790001, "L", 1, "",
         "Flag to indicate if UBX should be an input protocol on SPI"),
        ("CFG-SPIINPROT-NMEA", 0x10790002, "L", 1, "",
         "Flag to indicate if NMEA should be an input protocol on SPI"),
        ("CFG-SPIINPROT-RTCM2X", 0x10790003, "L", 1, "",
         "Flag to indicate if RTCM2X should be an input protocol on SPI"),
        ("CFG-SPIINPROT-RTCM3X", 0x10790004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an input protocol on SPI"),
        # CFG-SPIOUTPROT-
        ("CFG-SPIOUTPROT", 0x107affff, "", 0, "",
         "get all CFG-SPIOUTPROT"),
        ("CFG-SPIOUTPROT-UBX", 0x107a0001, "L", 1, "",
         "Flag to indicate if UBX should be an output protocol on SPI"),
        ("CFG-SPIOUTPROT-NMEA", 0x107a0002, "L", 1, "",
         "Flag to indicate if NMEA should be an output protocol on SPI"),
        ("CFG-SPIOUTPROT-RTCM3X", 0x107a0004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an output protocol on SPI"),
        # CFG-TMODE-
        ("CFG-TMODE", 0x2003ffff, "", 0, "",
         "get all CFG-TMODE"),
        ("CFG-TMODE-MODE", 0x20030001, "E1", 1, "",
         "Receiver mode"),
        ("CFG-TMODE-POS_TYPE", 0x20030002, "E1", 1, "",
         "Determines whether the ARP position is given in ECEF or "
         "LAT/LON/HEIGHT?"),
        ("CFG-TMODE-ECEF_X", 0x40030003, "I4", 1, "cm",
         "ECEF X coordinate of the ARP position."),
        ("CFG-TMODE-ECEF_Y", 0x40030004, "I4", 1, "cm",
         "ECEF Y coordinate of the ARP position."),
        ("CFG-TMODE-ECEF_Z", 0x40030005, "I4", 1, "cm",
         "ECEF Z coordinate of the ARP position."),
        ("CFG-TMODE-ECEF_X_HP", 0x20030006, "I1", 0.1, "mm",
         "High-precision ECEF X coordinate of the ARP position."),
        ("CFG-TMODE-ECEF_Y_HP", 0x20030007, "I1", 0.1, "mm",
         "High-precision ECEF Y coordinate of the ARP position."),
        ("CFG-TMODE-ECEF_Z_HP", 0x20030008, "I1", 0.1, "mm",
         "High-precision ECEF Z coordinate of the ARP position."),
        ("CFG-TMODE-LAT", 0x40030009, "I4", 1e-7, "deg",
         "Latitude of the ARP position."),
        ("CFG-TMODE-LON", 0x4003000a, "I4", 1e-7, "deg",
         "Longitude of the ARP position."),
        ("CFG-TMODE-HEIGHT", 0x4003000b, "I4", 1, "cm",
         "Height of the ARP position."),
        ("CFG-TMODE-LAT_HP", 0x2003000c, "I1", 1e-9, "deg",
         "High-precision latitude of the ARP position"),
        ("CFG-TMODE-LON_HP", 0x2003000d, "I1", 1e-9, "deg",
         "High-precision longitude of the ARP position."),
        ("CFG-TMODE-HEIGHT_HP", 0x2003000e, "I1", 0.1, "mm",
         "High-precision height of the ARP position."),
        ("CFG-TMODE-FIXED_POS_ACC", 0x4003000f, "U4", 0.1, "mm",
         "Fixed position 3D accuracy"),
        ("CFG-TMODE-SVIN_MIN_DUR", 0x40030010, "U4", 1, "s",
         "Survey-in minimum duration"),
        ("CFG-TMODE-SVIN_ACC_LIMIT", 0x40030011, "U4", 0.1, "mm",
         "Survey-in position accuracy limit"),
        # CFG-TP-
        ("CFG-TP", 0x3005ffff, "", 0, "",
         "get all CFG-TP"),
        ("CFG-TP-PULSE_DEF", 0x20050023, "E1", 1, "",
         "Determines whether the time pulse is interpreted as frequency "
         "or period?"),
        ("CFG-TP-PULSE_LENGTH_DEF", 0x20050030, "E1", 1, "",
         "Determines whether the time pulse length is interpreted as "
         "length[us] or pulse ratio[%]?"),
        ("CFG-TP-ANT_CABLEDELAY", 0x30050001, "I2", 0.000000001, "s",
         "Antenna cable delay"),
        ("CFG-TP-PERIOD_TP1", 0x40050002, "U4", 0.000001, "s",
         "Time pulse period (TP1)"),
        ("CFG-TP-PERIOD_LOCK_TP1", 0x40050003, "U4", 0.000001, "s",
         "Time pulse period when locked to GNSS time (TP1)"),
        ("CFG-TP-FREQ_TP1", 0x40050024, "U4", 1, "Hz",
         "Time pulse frequency (TP1)"),
        ("CFG-TP-FREQ_LOCK_TP1", 0x40050025, "U4", 1, "Hz",
         "Time pulse frequency when locked to GNSS time (TP1)"),
        ("CFG-TP-LEN_TP1", 0x40050004, "U4", 0.000001, "s",
         "Time pulse length (TP1)"),
        ("CFG-TP-LEN_LOCK_TP1", 0x40050005, "U4", 0.000001, "s",
         "Time pulse length when locked to GNSS time (TP1)"),
        ("CFG-TP-DUTY_TP1", 0x5005002a, "R8", 1, "%",
         "Time pulse duty cycle (TP1)"),
        ("CFG-TP-DUTY_LOCK_TP1", 0x5005002b, "R8", 1, "%",
         "Time pulse duty cycle when locked to GNSS time (TP1)"),
        ("CFG-TP-USER_DELAY_TP1", 0x40050006, "I4", 0.000000001, "s",
         "User configurable time pulse delay (TP1)"),
        ("CFG-TP-TP1_ENA", 0x10050007, "L", 1, "",
         "Enable the first timepulse"),
        ("CFG-TP-SYNC_GNSS_TP1", 0x10050008, "L", 1, "",
         "Sync time pulse to GNSS time or local clock (TP1)"),
        ("CFG-TP-USE_LOCKED_TP1", 0x10050009, "L", 1, "",
         "Use locked parameters when possible (TP1)"),
        ("CFG-TP-ALIGN_TO_TOW_TP1", 0x1005000a, "L", 1, "",
         "Align time pulse to top of second (TP1)"),
        ("CFG-TP-POL_TP1", 0x1005000b, "L", 1, "",
         "Set time pulse polarity (TP1)"),
        ("CFG-TP-TIMEGRID_TP1", 0x2005000c, "E1", 1, "",
         "Time grid to use (TP1)"),
        ("CFG-TP-PERIOD_TP2", 0x4005000d, "U4", 0.000001, "s",
         "Time pulse period (TP2)"),
        ("CFG-TP-PERIOD_LOCK_TP2", 0x4005000e, "U4", 0.000001, "s",
         "Time pulse period when locked to GNSS time (TP2)"),
        ("CFG-TP-FREQ_TP2", 0x40050026, "U4", 1, "Hz",
         "Time pulse frequency (TP2)"),
        ("CFG-TP-FREQ_LOCK_TP2", 0x40050027, "U4", 1, "Hz",
         "Time pulse frequency when locked to GNSS time (TP2)"),
        ("CFG-TP-LEN_TP2", 0x4005000f, "U4", 0.000001, "s",
         "Time pulse length (TP2)"),
        ("CFG-TP-LEN_LOCK_TP2", 0x40050010, "U4", 0.000001, "s",
         "Time pulse length when locked to GNSS time (TP2)"),
        ("CFG-TP-DUTY_TP2", 0x5005002c, "R8", 1, "%",
         "Time pulse duty cycle (TP2)"),
        ("CFG-TP-DUTY_LOCK_TP2", 0x5005002d, "R8", 1, "%",
         "Time pulse duty cycle when locked to GNSS time (TP2)"),
        ("CFG-TP-USER_DELAY_TP2", 0x40050011, "I4", 0.000000001, "s",
         "User configurable time pulse delay (TP2)"),
        ("CFG-TP-TP2_ENA", 0x10050012, "L", 1, "",
         "Enable the second timepulse"),
        ("CFG-TP-SYNC_GNSS_TP2", 0x10050013, "L", 1, "",
         "Sync time pulse to GNSS time or local clock (TP2)"),
        ("CFG-TP-USE_LOCKED_TP2", 0x10050014, "L", 1, "",
         "Use locked parameters when possible (TP2)"),
        ("CFG-TP-ALIGN_TO_TOW_TP2", 0x10050015, "L", 1, "",
         "Align time pulse to top of second (TP2)"),
        ("CFG-TP-POL_TP2", 0x10050016, "L", 1, "",
         "Set time pulse polarity (TP2)"),
        ("CFG-TP-TIMEGRID_TP2", 0x20050017, "E1", 1, "",
         "Time grid to use (TP2)"),
        # CFG-TXREADY-
        ("CFG-TXREADY", 0x10a2ffff, "", 0, "",
         "get all CFG-TXREADY"),
        ("CFG-TXREADY-ENABLED", 0x10a20001, "L", 1, "",
         "Flag to indicate if tx ready pin mechanism should be enabled"),
        ("CFG-TXREADY-POLARITY", 0x10a20002, "L", 1, "",
         "Polarity of the tx ready pin:false:high-active, true:low-active"),
        ("CFG-TXREADY-PIN", 0x20a20003, "U1", 1, "",
         "Pin number to use for the tx ready functionality"),
        ("CFG-TXREADY-THRESHOLD", 0x30a20004, "U2", 1, "",
         "Amount of data ready on interface before triggering tx ready pin"),
        ("CFG-TXREADY-INTERFACE", 0x20a20005, "E1", 1, "",
         "Interface where the tx ready feature should be linked to"),
        # CFG-UART1-
        ("CFG-UART1", 0x4052ffff, "", 0, "",
         "get all CFG-UART1"),
        ("CFG-UART1-BAUDRATE", 0x40520001, "U4", 1, "",
         "The baud rate that should be configured on the UART1"),
        ("CFG-UART1-STOPBITS", 0x20520002, "E1", 1, "",
         "Number of stopbits that should be used on UART1"),
        ("CFG-UART1-DATABITS", 0x20520003, "E1", 1, "",
         "Number of databits that should be used on UART1"),
        ("CFG-UART1-PARITY", 0x20520004, "E1", 1, "",
         "Parity mode that should be used on UART1"),
        ("CFG-UART1-ENABLED", 0x10520005, "L", 1, "",
         "Flag to indicate if the UART1 should be enabled"),
        # CFG-UART1INPROT
        ("CFG-UART1INPROT", 0x1073ffff, "", 0, "",
         "get all CFG-UART1INPROT"),
        ("CFG-UART1INPROT-UBX", 0x10730001, "L", 1, "",
         "Flag to indicate if UBX should be an input protocol on UART1"),
        ("CFG-UART1INPROT-NMEA", 0x10730002, "L", 1, "",
         "Flag to indicate if NMEA should be an input protocol on UART1"),
        ("CFG-UART1INPROT-RTCM2X", 0x10730003, "L", 1, "",
         "Flag to indicate if RTCM2X should be an input protocol on UART1"),
        ("CFG-UART1INPROT-RTCM3X", 0x10730004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an input protocol on UART1"),
        # CFG-UART1OUTPROT
        ("CFG-UART1OUTPROT", 0x1074ffff, "", 0, "",
         "get all CFG-UART1OUTPROT"),
        ("CFG-UART1OUTPROT-UBX", 0x10740001, "L", 1, "",
         "Flag to indicate if UBX should be an output protocol on UART1"),
        ("CFG-UART1OUTPROT-NMEA", 0x10740002, "L", 1, "",
         "Flag to indicate if NMEA should be an output protocol on UART1"),
        ("CFG-UART1OUTPROT-RTCM3X", 0x10740004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an output protocol on UART1"),
        # CFG-UART2-
        ("CFG-UART2", 0x4053FFFF, "", 0, "",
         "get all CFG-UART2"),
        ("CFG-UART2-BAUDRATE", 0x40530001, "U4", 1, "",
         "The baud rate that should be configured on the UART2"),
        ("CFG-UART2-STOPBITS", 0x20530002, "E1", 1, "",
         "Number of stopbits that should be used on UART2"),
        ("CFG-UART2-DATABITS", 0x20530003, "E1", "1", "",
         "Number of databits that should be used on UART2"),
        ("CFG-UART2-PARITY", 0x20530004, "E1", "1", "",
         "Parity mode that should be used on UART2"),
        ("CFG-UART2-ENABLED", 0x10530005, "L", "1", "",
         "Flag to indicate if the UART2 should be enabled"),
        ("CFG-UART2-REMAP", 0x10530006, "L", "1", "",
         "UART2 Remapping"),
        # CFG-UART1INPROT
        ("CFG-UART2INPROT", 0x1075ffff, "", 0, "",
         "get all CFG-UART2INPROT"),
        ("CFG-UART2INPROT-UBX", 0x10750001, "L", 1, "",
         "Flag to indicate if UBX should be an input protocol on UART2"),
        ("CFG-UART2INPROT-NMEA", 0x10750002, "L", 1, "",
         "Flag to indicate if NMEA should be an input protocol on UART2"),
        ("CFG-UART2INPROT-RTCM2X", 0x10750003, "L", 1, "",
         "Flag to indicate if RTCM2X should be an input protocol on UART2"),
        ("CFG-UART2INPROT-RTCM3X", 0x10750004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an input protocol on UART2"),
        # CFG-UART2OUTPROT
        ("CFG-UART2OUTPROT", 0x1076ffff, "", 0, "",
         "get all CFG-UART2OUTPROT"),
        ("CFG-UART2OUTPROT-UBX", 0x10760001, "L", 1, "",
         "Flag to indicate if UBX should be an output protocol on UART2"),
        ("CFG-UART2OUTPROT-NMEA", 0x10760002, "L", 1, "",
         "Flag to indicate if NMEA should be an output protocol on UART2"),
        ("CFG-UART2OUTPROT-RTCM3X", 0x10760004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an output protocol on UART2"),
        # CFG-USB-
        ("CFG-USB", 0x1065ffff, "", 0, "",
         "get all CFG-USB"),
        ("CFG-USB-ENABLED", 0x10650001, "L", 1, "",
         "Flag to indicate if the USB interface should be enabled"),
        ("CFG-USB-SELFPOW", 0x10650002, "L", 1, "",
         "Self-Powered device"),
        ("CFG-USB-VENDOR_ID", 0x3065000a, "U2", 1, "",
         "Vendor ID"),
        ("CFG-USB-PRODUCT_ID", 0x3065000b, "U2", 1, "",
         "Product ID"),
        ("CFG-USB-POWER", 0x3065000c, "U2", 1, "mA",
         "Power consumption"),
        ("CFG-USB-VENDOR_STR0", 0x5065000d, "X8", 1, "",
         "Vendor string characters 0-7"),
        ("CFG-USB-VENDOR_STR1", 0x5065000e, "X8", 1, "",
         "Vendor string characters 8-15"),
        ("CFG-USB-VENDOR_STR2", 0x5065000f, "X8", 1, "",
         "Vendor string characters 16-23"),
        ("CFG-USB-VENDOR_STR3", 0x50650010, "X8", 1, "",
         "Vendor string characters 24-31"),
        ("CFG-USB-PRODUCT_STR0", 0x50650011, "X8", 1, "",
         "Product string characters 0-7"),
        ("CFG-USB-PRODUCT_STR1", 0x50650012, "X8", 1, "",
         "Product string characters 8-15"),
        ("CFG-USB-PRODUCT_STR2", 0x50650013, "X8", 1, "",
         "Product string characters 16-23"),
        ("CFG-USB-PRODUCT_STR3", 0x50650014, "X8", 1, "",
         "Product string characters 24-31"),
        ("CFG-USB-SERIAL_NO_STR0", 0x50650015, "X8", 1, "",
         "Serial number string characters 0-7"),
        ("CFG-USB-SERIAL_NO_STR1", 0x50650016, "X8", 1, "",
         "Serial number string characters 8-15"),
        ("CFG-USB-SERIAL_NO_STR2", 0x50650017, "X8", 1, "",
         "Serial number string characters 16-23"),
        ("CFG-USB-SERIAL_NO_STR3", 0x50650018, "X8", 1, "",
         "Serial number string characters 24-31"),
        # CFG-USB-INPROT
        ("CFG-USBINPROT", 0x1077ffff, "", 0, "",
         "get all CFG-USBINPROT"),
        ("CFG-USBINPROT-UBX", 0x10770001, "L", 1, "",
         "Flag to indicate if UBX should be an input protocol on USB"),
        ("CFG-USBINPROT-NMEA", 0x10770002, "L", 1, "",
         "Flag to indicate if NMEA should be an input protocol on USB"),
        ("CFG-USBINPROT-RTCM2X", 0x10770003, "L", 1, "",
         "Flag to indicate if RTCM2X should be an input protocol on USB"),
        ("CFG-USBINPROT-RTCM3X", 0x10770004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an input protocol on USB"),
        # CFG-USB-OUTPROT
        ("CFG-USBOUTPROT", 0x1078ffff, "", 0, "",
         "get all CFG-USBOUTPROT"),
        ("CFG-USBOUTPROT-UBX", 0x10780001, "L", 1, "",
         "Flag to indicate if UBX should be an output protocol on USB"),
        ("CFG-USBOUTPROT-NMEA", 0x10780002, "L", 1, "",
         "Flag to indicate if NMEA should be an output protocol on USB"),
        ("CFG-USBOUTPROT-RTCM3X", 0x10780004, "L", 1, "",
         "Flag to indicate if RTCM3X should be an output protocol on USB"),
       )

    def item_to_type(self, item):
        """Return (size, pack format, i/i/f) for item"""

        # conversion of known types from known key
        cfg_types = {"E1": (1, "<B", "u"),
                     "E2": (2, "<H", "u"),
                     "E4": (4, "<L", "u"),
                     "I1": (1, "<b", "i"),
                     "I2": (2, "<h", "i"),
                     "I4": (4, "<l", "i"),
                     "I8": (8, "<q", "i"),
                     "L": (1, "<B", "u"),
                     "R4": (4, "<f", "f"),
                     "R8": (8, "<d", "f"),
                     "U1": (1, "<B", "u"),
                     "U2": (2, "<H", "u"),
                     "U4": (4, "<L", "u"),
                     "U8": (8, "<Q", "u"),
                     "X1": (1, "<B", "u"),
                     "X2": (2, "<H", "u"),
                     "X4": (4, "<L", "u"),
                     "X8": (8, "<Q", "u"),
                     }
        # guess of known types from unknown key
        key_map = {0: (1, "<B", "u"),       # illegal
                   1: (1, "<B", "u"),       # one bit
                   2: (1, "<B", "u"),       # one byte
                   3: (2, "<H", "u"),       # two byte
                   4: (4, "<L", "u"),       # four byte
                   5: (8, "<B", "u"),       # eight byte
                   6: (1, "<B", "u"),       # illegal
                   7: (1, "<B", "u"),       # illegal
                   }

        key = item[1]
        val_type = item[2]
        if val_type in cfg_types:
            cfg_type = cfg_types[val_type]
        else:
            # unknown? get length correct
            key_size = (key >> 28) & 0x07
            cfg_type = key_map[key_size]

        return cfg_type

    cfg_by_key_group = {0x03: "TMODE",
                        0x05: "TP",
                        0x11: "NAVSPG",
                        0x14: "NAVHPG",
                        0x21: "RATE",
                        0x22: "ODO",
                        0x23: "ANA",
                        0x24: "GEOFENCE",
                        0x25: "MOT",
                        0x26: "BATCH",
                        0x31: "SIGNAL",
                        0x37: "QZSS",
                        0x41: "ITFM",
                        0x51: "I2C",
                        0x52: "UART1",
                        0x53: "UART2",
                        0x64: "SPI",
                        0x65: "USB",
                        0x71: "I2CINPROT",
                        0x72: "I2COUTPROT",
                        0x73: "UART1INPROT",
                        0x74: "UART1OUTPROT",
                        0x75: "UART2INPROT",
                        0x76: "UART2OUTPROT",
                        0x77: "USBOUTPROT",
                        0x78: "USBOUTPROT",
                        0x79: "SPIINPROT",
                        0x7a: "SPIOUTPROT",
                        0x91: "MSGOUT",
                        0x92: "INFMSG",
                        0x93: "NMEA",
                        0xa2: "TXREADY",
                        0xa3: "HW",
                        0xc7: "RINV",
                        0xd0: "PM",
                        0xde: "LOGFILTER",
                        }

    cfg_by_key_kmap = {0: "Z0",
                       1: "L",
                       2: "U1",
                       3: "U2",
                       4: "U4",
                       5: "U8",
                       6: "Z6",
                       7: "Z7",
                       }

    def cfg_by_key(self, key):
        """Find a config item by key"""

        for item in self.cfgs:
            if item[1] == key:
                return item

        # not found, build a fake item, guess on decode
        group = (key >> 16) & 0xff
        group_name = index_s(group, self.cfg_by_key_group)
        if "Unk" == group_name:
            group_name = str(group)

        name = "CFG-%s-%u" % (group_name, key & 0xff)
        size = (key >> 28) & 0x07
        item = (name, key, self.cfg_by_key_kmap[size], 1, "Unk", "Unknown")

        return item

    def cfg_by_name(self, name):
        """Find a config item by name"""

        for item in self.cfgs:
            if item[0] == name:
                return item

        return None

    id_map = {
        0: {"name": "GPS",
            "sig": {0: "L1C/A", 3: "L2 CL", 4: "L2 CM"}},
        1: {"name": "SBAS",
            "sig": {0: "L1C/A", 3: "L2 CL", 4: "L2 CM"}},
        2: {"name": "Galileo",
            "sig": {0: "E1C", 1: "E1 B", 5: "E5 bl", 6: "E5 bQ"}},
        3: {"name": "BeiDou",
            "sig": {0: "B1I D1", 1: "B1I D2", 2: "B2I D1", 3: "B2I D2"}},
        4: {"name": "IMES",
            "sig": {0: "L1C/A", 3: "L2 CL", 4: "L2 CM"}},
        5: {"name": "QZSS",
            "sig": {0: "L1C/A", 4: "L2 CM", 5: "L2 CL"}},
        6: {"name": "GLONASS",
            "sig": {0: "L1 OF", 2: "L2 OF"}},
    }

    def gnss_s(self, gnssId, svId, sigId):
        """Verbose decode of gnssId, svId and sigId"""

        s = ''

        if gnssId in self.id_map:
            if "name" not in self.id_map[gnssId]:
                s = "%d:%d:%d" % (gnssId, svId, sigId)
            elif sigId not in self.id_map[gnssId]["sig"]:
                s = ("%s:%d:%d" %
                     (self.id_map[gnssId]["name"], svId, sigId))
            else:
                s = ("%s:%d:%s" %
                     (self.id_map[gnssId]["name"], svId,
                      self.id_map[gnssId]["sig"][sigId]))
        else:
            s = "%d:%d:%d" % (gnssId, svId, sigId)

        return s

    def ack_ack(self, buf):
        """UBX-ACK-ACK decode"""

        # NOTE: Not all messages to u-blox GPS are ACKed...

        u = struct.unpack_from('<BB', buf, 0)
        return '  ACK to %s' % self.class_id_s(u[0], u[1])

    def ack_nak(self, buf):
        """UBX-ACK-NAK decode"""

        # NOTE: Not all messages to u-blox GPS are ACKed...

        u = struct.unpack_from('<BB', buf, 0)
        return '  NAK to %s' % self.class_id_s(u[0], u[1])

    # UBX-ACK-
    ack_ids = {0: {'str': 'NAK', 'dec': ack_nak, 'minlen': 2,
                   'name': 'UBX-ACK-NAK'},
               1: {'str': 'ACK', 'dec': ack_ack, 'minlen': 2,
                   'name': 'UBX-ACK-ACK'}}

    # UBX-AID-
    def aid_alm(self, buf):
        """UBX-AID-ALM decode, GPS Aiding Almanac Data"""
        m_len = len(buf)

        if 1 == m_len:
            return "  Poll request svid %u" % buf[0]

        if 8 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<LL', buf, 0)
        s = ' svid %u week %u ' % u

        if 0 != u[1] and 8 < m_len <= 40:
            u = struct.unpack_from('<LLLLLLLL', buf, 8)
            s += ('\n dwrd %08x %08x %08x %08x'
                  '\n      %08x %08x %08x %08x' % u)

        return s

    def aid_alp(self, buf):
        """UBX-AID-ALP decode, AlmanacPlus"""

        # u-blox 6, protVer 6 to 7

        m_len = len(buf)
        if 1 == m_len(buf):
            # different meaning for in and out
            u = struct.unpack_from('<B', buf, 0)
            return '  dummy/ack  %u' % u

        if 24 == m_len(buf):
            # different meaning for in and out
            u = struct.unpack_from('LLlHHLBBH', buf, 0)
            return ('  predTow %u predDur %u age %d predWno %u almWno %u\n'
                    '  res1 %u svs %u res23 %u %u' % u)

        # else
        s = '  alpData len %u' % u

        # FIXME: partial decode

        return s

    def aid_alpsrv(self, buf):
        """UBX-AID-ALPSRV decode, AlmanacPlus"""

        # u-blox 6, protVer 6 to 7

        u = struct.unpack_from('<BBHHH', buf, 0)
        s = ' idSize %u type %u ofx %u size %u fileId %u' % u

        # FIXME: partial decode

        return s

    def aid_aop(self, buf):
        """UBX-AID-AOP decode, AssistNow Autonomous data"""
        m_len = len(buf)

        if 1 == m_len:
            return "  Poll request svid %u" % buf[0]

        # length 2 is undocumented...
        if 2 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<BB', buf, 0)
        s = ' gnssid %u svid %u' % u
        # FIXME: dump the rest...

        return s

    def aid_data(self, buf):
        """UBX-AID-DATA decode, Poll all GPS Initial Aiding Data"""

        # u-blox 6
        # If this poll is received, the messages AID-INI, AID-HUI,
        # AID-EPH and AID-ALM are sent.
        return "  Poll all GPS Initial Aiding Data"

    def aid_eph(self, buf):
        """UBX-AID-EPH decode, GPS Aiding Ephemeris Data"""
        m_len = len(buf)

        if 1 == m_len:
            return "  Poll request svid %u" % buf[0]

        if 8 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<LL', buf, 0)
        s = ' svid %u how x%x ' % u

        if 0 != u[1] and 8 < m_len <= 104:
            u = struct.unpack_from('<LLLLLLLLLLLLLLLLLLLLLLLL', buf, 8)
            s += ('\n sf1d %08x %08x %08x %08x'
                  '\n      %08x %08x %08x %08x'
                  '\n sf2d %08x %08x %08x %08x'
                  '\n      %08x %08x %08x %08x'
                  '\n sf3d %08x %08x %08x %08x'
                  '\n      %08x %08x %08x %08x' % u)

        return s

    def aid_hui(self, buf):
        """UBX-AID-HUI decode, GPS Heatlh, UTC, Ionosphere"""

        u = struct.unpack_from('<LddlhhhhhhffffffffL', buf, 0)
        s = (' health x%x utcA0 %e utcA1 %e utcTOW %d'
             '\n utcWNT %d utcLS %d utcWNF %d utcDN %d utcLSF %d utcSpare %d'
             '\n klobA0 %e klobA1 %e klobA2 %e'
             '\n klobA3 %e klobB0 %e klobB1 %e'
             '\n klobB2 %e klobB3 %e flags x%x' % u)

        return s

    def aid_ini(self, buf):
        """UBX-AID-INI decode, Aiding position, time, frequency, clock drift"""

        u = struct.unpack_from('<lllLHHLlLLlLL', buf, 0)
        s = (' ecefXOrLat %d ecefYOrLon %d ecefZOrAlt %d posAcc %u'
             '\n tmCfg x%x wnoOrDate %u towOrTime %u towNs %d'
             '\n tAccMs %u tAccNs %u clkDOrFreq %d clkDAccOrFreqAcc %u'
             '\n flags x%x' % u)

        return s

    def aid_req(self, buf):
        """UBX-AID-REQ decode, Sends a poll for all GPS Aiding Data"""

        return "  poll (AID-DATA) for all GPS Aiding Data"

    # All UBX-AID messages are deprecated; use UBX-MGA messages instead
    aid_ids = {
               # u-blox 6
               0x00: {'str': 'REQ', 'dec': aid_req, 'minlen': 0,
                      'name': 'UBX-AID-REQ'},
               0x01: {'str': 'INI', 'dec': aid_ini, 'minlen': 48,
                      'name': 'UBX-AID-INI'},
               0x02: {'str': 'HUI', 'dec': aid_hui, 'minlen': 72,
                      'name': 'UBX-AID-HUI'},
               # u-blox 6
               0x10: {'str': 'DATA', 'dec': aid_data, 'minlen': 0,
                      'name': 'UBX-AID-DATA'},
               0x30: {'str': 'ALM', 'dec': aid_alm, 'minlen': 1,
                      'name': 'UBX-AID-ALM'},
               0x31: {'str': 'EPH', 'dec': aid_eph, 'minlen': 1,
                      'name': 'UBX-AID-EPH'},
               # u-blox 6
               0x32: {'str': 'ALPSRV', 'dec': aid_alpsrv, 'minlen': 8,
                      'name': 'UBX-AID-ALPSRV'},
               0x33: {'str': 'AOP', 'dec': aid_aop, 'minlen': 1,
                      'name': 'UBX-AID-AOP'},
               0x50: {'str': 'ALP', 'dec': aid_alp, 'minlen': 1,
                      'name': 'UBX-AID-ALP'},
               }

    cfg_ant_pins = {
        1: 'svcs',
        2: 'scd',
        4: 'ocd',
        8: 'pdwnOnSCD',
        0x10: 'recovery',
        }

    def cfg_ant(self, buf):
        """UBX-CFG-ANT decode

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<HH', buf, 0)
        s = ' flags x%x pins x%x ' % u
        s += ('pinSwitch %u pinSCD %u pinOCD %u reconfig %u' %
              (u[1] & 0x1f, (u[1] >> 5) & 0x1f, (u[1] >> 10) & 0x1f,
               u[1] >> 15))
        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n      flags (%s)' % flag_s(u[0], self.cfg_ant_pins))

        return s

    cfg_batch_flags = {
        1: 'enable',
        4: 'extraPvt',
        8: 'extraOdo',
        0x20: 'pioEnable',
        0x40: 'pioActiveLow',
        }

    def cfg_batch(self, buf):
        """UBX-CFG-BATCH decode

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BBHHBB', buf, 0)
        s = ("  version %u flags x%x bufsize %u notifThrs %u\n"
             "  pioId %u reserved1 %u" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n      flags (%s)' % flag_s(u[1], self.cfg_batch_flags))

        return s

    cfg_cfg_mask = {
        0x1: 'ioPort',
        0x2: 'msgConf',
        0x4: 'infMsg',
        0x8: 'navConf',
        0x10: 'rxmConf',
        0x100: 'senConf',        # not on M8030, sfdrConf in u-blox 5
        0x200: 'rinvConf',
        0x400: 'antConf',
        0x800: 'logConf',        # not in u-blox 5
        0x1000: 'ftsConf',       # protVer 16+
        }

    cfg_cfg_dev = {
        0x1: 'devBBR',
        0x2: 'devFlash',
        0x4: 'devEEPROM',             # only protVer less then 14.00
        0x10: 'devSpiFlash',          # only protVer less than 14.00
        }

    def cfg_cfg(self, buf):
        """UBX-CFG-CFG decode

"not completely  backwards-compatible."

Deprecated in protVer 34.00
"""
        m_len = len(buf)

        if 12 == m_len:
            u = struct.unpack_from('<LLL', buf, 0)
        elif 13 == m_len:
            u = struct.unpack_from('<LLLB', buf, 0)
        else:
            return "  Bad Length %s" % m_len

        s = ('  clearMask: %#x (%s)\n' %
             (u[0], flag_s(u[0], self.cfg_cfg_mask)))
        s += ('  saveMask: %#x (%s)\n' %
              (u[1], flag_s(u[1], self.cfg_cfg_mask)))
        s += ('  loadMask: %#x (%s)\n' %
              (u[2], flag_s(u[2], self.cfg_cfg_mask)))

        if 13 <= m_len:
            s += ('  deviceMask: %#x (%s)\n' %
                  (u[3], flag_s(u[3], self.cfg_cfg_dev)))

        return s

    def cfg_dat(self, buf):
        """UBX-CFG-DAT decode, Standard Datum configuration

Deprecated in protVer 34.00
"""

        # u-blox 5 to 9, protVer 4.00 to 29
        m_len = len(buf)

        if 2 == m_len:
            # standard datum
            u = struct.unpack_from('<H', buf, 0)
            s = "  datumNum %u" % u

        elif 44 > m_len:
            s = "  Bad Length %d" % m_len

        elif 44 == m_len:
            # set user defined datum
            u = struct.unpack_from('<ddfffffff', buf, 0)
            s = ("  majA %.1f flat %.1f dX %.1f dY %.1f dZ %.1f\n"
                 "  rotX %.1f rotY %.1f rotZ %.1f scale %.1f" % u)

        elif 52 > m_len:
            s = "  Bad Length %d" % m_len

        elif 52 <= m_len:
            # get user defined datum
            u = struct.unpack_from('<HBBBBBBddfffffff', buf, 0)
            s = ("  datumNum %u datumNam %u %u %u %u %u %u\n"
                 "  majA %.1f flat %.1f dX %.1f dY %.1f dZ %.1f\n"
                 "  rotX %.1f rotY %.1f rotZ %.1f scale %.1f" % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ('\n   datumName (%s)' %
                      gps.polystr(buf[2:8]).rstrip('\0'))

        else:
            s = "I'm confused..."

        return s

    cfg_dgnss_mode = {
        2: "RTK Float",
        3: "RTK Fixed",
        }

    def cfg_dgnss(self, buf):
        """UBX-CFG-DGNSS decode, DGNSS configuration"""

        u = struct.unpack_from('<BBBB', buf, 0)
        s = (" dgnssMode %u (%s) reserved1 %u %u %u" % u
             (u[0], index_s(u[0], self.cfg_dgnss_mode), u[1], u[2], u[3]))
        return s

    def cfg_dosc(self, buf):
        """UBX-CFG-DOSC decode, Disciplined oscillator configuration"""

        u = struct.unpack_from('<BBBB', buf, 0)
        s = " version %u numOsc %u reserved1 %u" % u
        # FIXME, partial decode
        return s

    def cfg_dynseed(self, buf):
        """UBX-CFG-DYNSEED decode,
Programming the dynamic seed for host interface signature"""

        # u-blox 8 only, protVer 18 to 23
        u = struct.unpack_from('<BBHLL', buf, 0)
        s = " version %u reserved1 %u %u seedHi %u seedLo %u" % u
        return s

    # UBX-CFG-ESFALG, protVer 15.01 and up, ADR and UDR only

    # UBX-CFG-ESFA, protVer 19 and up, UDR only

    # UBX-CFG-ESFG, protVer 19 and up, UDR only

    # UBX-CFG-ESFWT, protVer 15.01 and up, ADR only

    def cfg_esrc(self, buf):
        """UBX-CFG-ESRC decode, External synchronization source
        configuration"""

        u = struct.unpack_from('<BBBB', buf, 0)
        s = "  version %u numSources %u reserved1 %u" % u
        # FIXME, partial decode
        return s

    def cfg_fixseed(self, buf):
        """UBX-CFG-FIXSEED decode,
Programming the fixed seed for host interface signature"""

        # u-blox 8 only, protVer 18 to 23
        u = struct.unpack_from('<BBHLL', buf, 0)
        s = " version %u length %u reserved1 %u seedHi %u seedLo %u" % u
        # FIXME, partial decode
        return s

    cfg_fxn_flags = {
        2: "sleep Float",
        8: "absAlign",
        0x10: "onOff",
        }

    def cfg_fxn(self, buf):
        """UBX-CFG-FXN decode, FXN FixNOW configuration"""

        # Antaris 4, u-blox 5, protVer 6.00 to 6.02
        u = struct.unpack_from('<LLLLLLLLL', buf, 0)
        s = ("  flags x%x tReacq %u tAcq %u tReacqOff %u\n"
             "  tAcqOff %u tOn %u tOff %u res %u baseTow %u\n" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    flags (%s)" %
                  (flag_s(u[0], self.cfg_fxn_flags)))
        return s

    def cfg_geofence(self, buf):
        """UBX-CFG-GEOFENCE decode, Geofencing configuration

Deprecated in protVer 34.00
"""

        # not in M10, protVer 34 and up

        u = struct.unpack_from('<BBBBBBBB', buf, 0)
        s = (" version %u numFences %u confLvl %u reserved1 %u\n"
             " pioEnabled %u pinPolarity %u pin %u reserved2 %u" % u)
        for i in range(0, u[1]):
            u = struct.unpack_from('<llL', buf, 8 + (i * 12))
            s = "\n   lat %d lon %d radius %d" % u
        return s

    # signals defined in protver 27+
    # signals used in protver 15+
    # top byte used, but not defined
    cfg_gnss_sig = {
        0: {0x010000: "L1C/A",    # GPS
            0x100000: "L2C",
            0x200000: "L5"},
        1: {0x010000: "L1C/A"},   # SBAS
        2: {0x010000: "E1",       # Galileo
            0x100000: "E5a",
            0x200000: "E5b"},
        3: {0x010000: "B1I",      # BeiDou
            0x100000: "B2I",
            0x800000: "B2A"},
        4: {0x010000: "L1"},      # IMES
        5: {0x010000: "L1C/A",    # QZSS
            0x040000: "L1S",
            0x100000: "L2C",
            0x200000: "L5"},
        6: {0x010000: "L1",       # GLONASS
            0x100000: "L2"},
        }

    def cfg_gnss(self, buf):
        """UBX-CFG-GNSS decode, GNSS system configuration

Present in protVer 15 and up
Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BBBB', buf, 0)
        s = " msgVer %u  numTrkChHw %u numTrkChUse %u numConfigBlocks %u" % u

        for i in range(0, u[3]):
            u = struct.unpack_from('<BBBBL', buf, 4 + (i * 8))
            sat = u[0]
            s += ("\n  gnssId %u TrkCh %2u maxTrCh %2u reserved %u "
                  "Flags x%08x\n" % u)

            if 7 > sat:
                s += ("   %s %s " %
                      (index_s(sat, self.gnss_id),
                       flag_s(u[4], self.cfg_gnss_sig[sat])))
            else:
                s += "Unk "

            if u[4] & 0x01:
                s += 'enabled'

        return s

    def cfg_hnr(self, buf):
        """UBX-CFG-HNR decode, High Navigation Rate Settings"""

        u = struct.unpack_from('<BBBb', buf, 0)
        s = " highNavRate %u reserved %u %u %u" % u
        return s

    cfg_inf_protid = {
        0: "UBX",
        1: "NMEA",
        # labels of following values based on u-blox document
        # no. GPS.G3-X-03002-D (Antaris protocol specification)
        2: "RTCM",      # cannot be used to output INF messages
        3: "RAW",       # used by u-center
        12: "User 0",   # used by u-center
        13: "User 1",   # used by u-center
        14: "User 2",   # used by u-center
        15: "User 3",   # used by u-center
        }

    def cfg_inf(self, buf):
        """UBX-CFG-INF decode, Poll configuration for one protocol

Deprecated in protVer 34.00
"""

        m_len = len(buf)
        if 1 == m_len:
            return ("  Poll request: %s" %
                    index_s(buf[0], self.cfg_inf_protid))

        if 8 > m_len:
            return "  Bad Length %d" % m_len

        # very old u-blox have 8 octets, e.g. Antaris 4 w/ protVer 11
        u = struct.unpack_from('<BBBBBBBB', buf, 0)
        s = (" protocolId %u reserved1 %u %u %u\n"
             " infMsgMask %u %u %u %u" % u)

        # newer u-blox have 10 octets, e.g. u-blox 6 w/ protVer 13
        if 9 < m_len:
            u = struct.unpack_from('<BB', buf[8:], 0)
            s += (" %u %u" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n   protocolId (%s)' %
                  index_s(buf[0], self.cfg_inf_protid))
        return s

    cfg_itfm_config = {
        0x80000000: "enable",
        }

    cfg_itfm_config2 = {
        0x4000: "enable2",
        }

    cfg_itfm_ant = {
        1: "passive",
        2: "active",
        }

    def cfg_itfm(self, buf):
        """UBX-CFG-ITFM decode, Jamming/Interference Monitor configuration

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<LL', buf, 0)
        s = " config x%x config2 x%x" % u
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   config (%s) bbThreshold %u cwThreshold %u "
                  "algorithmBits x%x"
                  "\n   config2 (%s) generalBits x%x antSetting (%s)" %
                  (flag_s(buf[0], self.cfg_itfm_config),
                   u[0] & 0x0f, (u[0] >> 4) & 0x1f, (u[0] >> 9) & 0x1fffff,
                   flag_s(buf[1], self.cfg_itfm_config2),
                   u[1] & 0x0fff,
                   index_s((u[1] >> 12) & 3, self.cfg_itfm_config2)))
        return s

    cfg_logfilter_flags = {
        1: "recordEnabled",
        2: "psmOncePerWakupEnabled",
        4: "applyAllFilterSettings",
        }

    def cfg_logfilter(self, buf):
        """UBX-CFG-LOGFILTER decode, Data Logger Configuration"""

        # u-blox 7+, protVer 14+
        u = struct.unpack_from('<BBHHHL', buf, 0)
        s = (" version %u flags x%x minInterval %u timeThreshold %u\n"
             " speedThreshold %u positionThreshold %u" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   flags (%s)" %
                  (flag_s(buf[1], self.cfg_logfilter_flags)))

        return s

    utc_std = {
        0: "Auto",
        1: "CRL",
        2: "NIST",
        3: "USNO",
        4: "BIPM",
        5: "EU",
        6: "SU",
        7: "NTSC",
        }

    cfg_nav5_dyn = {
        0: "Portable",
        2: "Stationary",
        3: "Pedestrian",
        4: "Automotive",
        5: "Sea",
        6: "Airborne with <1g Acceleration",
        7: "Airborne with <2g Acceleration",
        8: "Airborne with <4g Acceleration",
        }

    cfg_nav5_fix = {
        1: "2D only",
        2: "3D only",
        3: "Auto 2D/3D",
        }

    cfg_nav5_mask = {
        1: "dyn",
        2: "minEl",
        4: "posFixMode",
        8: "drLim",
        0x10: "posMask",
        0x20: "timeMask",
        0x40: "staticHoldMask",
        0x80: "dgpsMask",
        0x100: "cnoThreshold",
        0x400: "utc",
        }

    def cfg_nav5(self, buf):
        """UBX-CFG-NAV5 nav Engine Settings

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<HBBlLbBHHHHbbbbHHbBL', buf, 0)
        s = (' mask %#x dynModel %u fixmode %d fixedAlt %d FixedAltVar %u\n'
             ' minElev %d drLimit %u pDop %u tDop %u pAcc %u tAcc %u\n'
             ' staticHoldThresh %u dgpsTimeOut %u cnoThreshNumSVs %u\n'
             ' cnoThresh %u res %u staticHoldMaxDist %u utcStandard %u\n'
             ' reserved x%x %x' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   dynModel (%s) fixMode (%s) utcStandard (%s)"
                  "\n   mask (%s)" %
                  (index_s(u[1], self.cfg_nav5_dyn),
                   index_s(u[2], self.cfg_nav5_fix),
                   index_s(u[17] >> 4, self.utc_std),
                   flag_s(u[0] >> 4, self.cfg_nav5_mask)))
        return s

    cfg_navx5_mask1 = {
        4: "minMax",
        8: "minCno",
        0x40: "initial3dfix",
        0x200: "wknRoll",
        0x400: "ackAid",
        0x2000: "ppp",
        0x4000: "aop",
        }

    cfg_navx5_mask2 = {
        0x40: "adr",
        0x80: "sigAttenComp",
        }

    cfg_navx5_aop = {
        1: "useAOP",
        }

    def cfg_navx5(self, buf):
        """UBX-CFG-NAVX5 decode, Navigation Engine Expert Settings

Deprecated in protVer 34.00
"""

        # deprecated protver 23+
        # length == 20 case seems broken?
        m_len = len(buf)

        u = struct.unpack_from('<HHLHBBBBBHBH', buf, 0)
        s = (" version %u mask1 x%x mask2 x%x reserved1 %u minSVs %u "
             "maxSVs %u minCNO %u\n"
             " reserved2 %u iniFix3D %u reserved3 %u  ackAiding %u "
             "wknRollover %u" % u)

        # length == 40 in protver 27
        if 40 <= m_len:
            u1 = struct.unpack_from('<BBHHBBHHLHBB', buf, 20)
            s += ("\n sigAttenCompMode %u reserved456 %u %u %u usePPP %u "
                  "aopCfg %u reserved7 %u"
                  "\n aopOrbMaxErr %u reserved89 %u %u %u useAdr %u" % u1)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   mask1 (%s)"
                  "\n   mask2 (%s) aopCfg (%s)" %
                  (flag_s(u[1], self.cfg_navx5_mask1),
                   flag_s(u[2], self.cfg_navx5_mask2),
                   flag_s(u1[5], self.cfg_navx5_aop)))

        return s

    def cfg_msg(self, buf):
        """UBX-CFG-MSG decode

Deprecated in protVer 34.00
"""
        m_len = len(buf)
        if 2 == m_len:
            u = struct.unpack_from('<BB', buf, 0)
            return '  Rate request %s' % self.class_id_s(u[0], u[1])

        if 3 == m_len:
            u = struct.unpack_from('<BBB', buf, 0)
            return ('  Rate set %s Rate %d' %
                    (self.class_id_s(u[0], u[1]), u[2]))

        if 8 != m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<BBBBBBBB', buf, 0)
        s = (' %s Rates %u %u %u %u %u %u' %
             (self.class_id_s(u[0], u[1]), u[2], u[3], u[4], u[5], u[6], u[7]))
        return s

    cfg_nmea_filter = {
        1: "posFilt",
        2: "mskPosFilt",
        4: "timeFilt",
        8: "dateFilt",
        0x10: "gpsOnlyFilter",
        0x20: "trackFilt",
        }

    cfg_nmea_ver = {
        0x21: "2.1",
        0x23: "2.3",
        0x40: "4.0",
        0x41: "4.10",
        0x4b: "4.11",
        }

    cfg_nmea_flags = {
        1: "compat",
        2: "consider",
        4: "limit82",
        8: "highPrec",
        }

    cfg_nmea_svn = {
        0: "Strict",
        1: "Extended",
        }

    cfg_nmea_mtid = {
        0: "Default",
        1: "GP",
        2: "GL",
        3: "GN",
        4: "GA",
        5: "GB",
        6: "GQ",
        }

    cfg_nmea_gtid = {
        0: "GNSS Specific",
        1: "Main",
        }

    cfg_nmea_gnssfilt = {
        1: "gps",
        2: "sbas",
        4: "galileo",
        0x10: "qzss",
        0x20: "glonass",
        0x40: "beidou",
        }

    def cfg_nmea(self, buf):
        """UBX-CFG-NMEA decode, NMEA protocol configuration

Deprecated in protVer 34.00
"""

        # old u-blox have 4 octets, e.g. u-blox 6 w/ protVer < 14
        # less old u-blox have 12 octets, e.g. u-blox 7 w/ protVer == 14
        # more recent u-blox have 20 octets, e.g. u-blox 8 w/ protVer > 14
        # deprecated in most recent u-blox, e.g. u-blox 9 w/ protVer > 23.01

        u = struct.unpack_from('<BBBB', buf, 0)
        s = (" filter x%x nmeaVersion x%x numSv %u flags x%x " % u)

        if 11 < len(buf):
            u1 = struct.unpack_from('<LBBBB', buf[4:], 0)
            s += ("gnssToFilter x%x\n svNumbering %u"
                  " mainTalkerId %u gsvTalkerId %u version %u" % u1)
            u += u1

        if 19 < len(buf):
            u2 = struct.unpack_from('<BBBBBBBB', buf[12:], 0)
            s += ("\n bdsTalkerId %u %u reserved1 %u %u %u %u %u %u" % u2)
            u += u2

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n  filter (%s) NMEA Version (%s) numSV (%s) flags (%s)" %
                  (flag_s(u[0], self.cfg_nmea_filter),
                   index_s(u[1], self.cfg_nmea_ver),
                   u[2] if 0 != u[2] else "Unlimited",
                   flag_s(u[3], self.cfg_nmea_flags)))

            if 11 < len(buf):
                s += ("\n  gnssToFilter (%s) svNumbering (%s) "
                      "mainTalkerId (%s)"
                      "\n  gsvTalkerId (%s)" %
                      (flag_s(u[4], self.cfg_nmea_gnssfilt),
                       index_s(u[5], self.cfg_nmea_svn),
                       index_s(u[6], self.cfg_nmea_mtid),
                       index_s(u[7], self.cfg_nmea_gtid)))
        return s

    cfg_nvs_mask = {
        0x20000: 'alm',
        0x20000000: 'aop',
        }

    def cfg_nvs(self, buf):
        """UBX-CFG-NVS decode, Clear,
Save and Load non-volatile storage data"""

        # u-blox 6, protVer 7.03
        u = struct.unpack_from('<LLLB', buf, 0)
        s = ('  clearMask: %#x (%s)\n' %
             (u[0], flag_s(u[0], self.cfg_nvs_mask)))
        s += ('  saveMask: %#x (%s)\n' %
              (u[1], flag_s(u[1], self.cfg_nvs_mask)))
        s += ('  loadMask: %#x (%s)\n' %
              (u[2], flag_s(u[2], self.cfg_nvs_mask)))
        s += ('  deviceMask: %#x (%s)\n' %
              (u[3], flag_s(u[3], self.cfg_cfg_dev)))

        return s

    cfg_odo_flags = {
        1: "useODO",
        2: "useCOG",
        4: "useLPVel",
        8: "useLPCog",
        }

    cfg_odo_profile = {
        0: "Running",
        1: "Cycling",
        2: "Swimming",
        3: "Car",
        4: "Custom",
        }

    def cfg_odo(self, buf):
        """UBX-CFG-ODO decode, Odometer, Low-speed COG Engine Settings

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BBBBBBBBBBBBBBBBBBBB', buf, 0)
        s = (" version %u reserved1 %u %u %u flags x%x odoCfg x%x\n"
             " reserved2 %u %u %u %u %u %u\n"
             " cagMaxSpeed %u cogMaxPosAcc %u reserved3 %u %u\n"
             " velLpGain %u cogLpGain %u reserved4 %u %u" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   flags (%s) odoCfg (%s)" %
                  (flag_s(u[4], self.cfg_odo_flags),
                   index_s(u[5], self.cfg_odo_profile)))
        return s

    cfg_pm_flags = {
        0x20: "extintWake",
        0x40: "extintBackup",
        0x80: "extintInactive",
        0x400: "waitTimeFix",
        0x800: "updateRTC",
        0x1000: "updateEPH",
        0x10000: "doNotEnterOff",
        }

    cfg_pm_limitPeakCurr = {
        0: "disabled",
        1: "enabled",
        2: "reserved",
        3: "reserved3",
        }

    def cfg_pm(self, buf):
        """UBX-CFG-PM decode, Poswer Management Configuration"""

        # u-blox 5, protVer 6.00 to 6.02

        u = struct.unpack_from('<BBBBLLLLHH', buf, 0)
        s = (" version %u res1 %u res2 %u res3 %u flags x%x updatePeriod %u\n"
             " searchPeriod %u gridOffset %u onTime %u minAcqTime %u\n" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n  flags (%s) extintSel (EXTINT%u) '
                  'limitPeakCurr (%s)' %
                  (flag_s(u[4], self.cfg_pm_flags),
                   (u[4] >> 4) & 1,
                   index_s((u[4] >> 8) & 3, self.cfg_pm_limitPeakCurr)))
        return s

    cfg_pm2_mode = {
        0: "ON/OFF operation (PSMOO)",
        1: "Cyclic tracking operation (PSMCT)",
        2: "reserved",
        3: "reserves3",
        }

    cfg_pm2_optTarget = {
        0: "performance",
        1: "power save",
        }

    def cfg_pm2(self, buf):
        """UBX-CFG-PM2 decode, Extended Power Mode Configuration

Deprecated in protVer 34.00
"""

        # three versions, two lengths
        # "version" 1 is 44 bytes
        # "version" 2 is 48 bytes,protver <= 22
        # "version" 2 is 48 bytes,protver >= 23

        m_len = len(buf)

        # 48 bytes protver 18+

        u = struct.unpack_from('<BBBBLLLLHHLLLLL', buf, 0)
        s = (" version %u reserved1 %u maxStartupStateDur %u reserved2 %u\n"
             " flags x%x updatePeriod %u searchPeriod %u\n"
             " gridOffset %u ontime %u minAcqTime %u\n"
             " reserved3 %u %u %u %u %u" % u)
        if 48 <= m_len:
            u1 = struct.unpack_from('<L', buf, 44)
            s += "\n extintInactivityMs %u" % u1

        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n  flags (%s) extintSel (EXTINT%u)'
                  '\n  limitPeakCurr (%s)'
                  '\n  optTarget (%s) mode (%s)' %
                  (flag_s(u[4], self.cfg_pm_flags),
                   (u[4] >> 4) & 1,
                   index_s((u[4] >> 8) & 3, self.cfg_pm_limitPeakCurr),
                   index_s((u[4] >> 1) & 3, self.cfg_pm2_optTarget,
                           nf="reserved"),
                   index_s((u[4] >> 17) & 3, self.cfg_pm2_mode)))

        return s

    cfg_pms_values = {0: "Full power",
                      1: "Balanced",
                      2: "Interval",
                      3: "Aggressive with 1Hz",
                      4: "Aggressive with 2Hz",
                      5: "Aggressive with 4Hz",
                      0xff: "Invalid"
                      }

    def cfg_pms(self, buf):
        """UBX-CFG-PMS decode, Power Mode Setup

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BBHHBB', buf, 0)
        s = (' version %u powerSetupValue %u'
             ' period %u onTime %#x reserved1 %u %u' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n  powerSetupValue (%s)' %
                  index_s(u[1], self.cfg_pms_values))

        return s

    cfg_prt_flags = {
        0x2: 'extendedTxTimeout',
        }

    cfg_prt_proto = {
        0x1: 'UBX',
        0x2: 'NMEA',
        0x4: 'RTCM2',    # not in u-blox 5
        0x20: 'RTCM3',   # protVer 20+
        }

    def cfg_prt(self, buf):
        """UBX-CFG-PRT decode, Port Configuration

Deprecated in protVer 34.00
"""

        m_len = len(buf)

        portid = buf[0]
        idstr = '%u (%s)' % (portid, self.port_ids.get(portid, '?'))

        if 1 == m_len:
            return "  Poll request PortID %s" % idstr

        # Note that this message can contain multiple 20-byte submessages, but
        # only in the send direction, which we don't currently do.
        if 20 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<BBHLLHHHH', buf, 0)

        s = [' PortID %s reserved1 %u txReady %#x' % (idstr, u[1], u[2])]
        s.append({1: '  mode %#x baudRate %u',
                  2: '  mode %#x baudRate %u',
                  3: '  reserved2 [%u %u]',
                  4: '  mode %#x reserved2 %u',
                  0: '  mode %#x reserved2 %u',
                  }.get(portid, '  ???: %u,%u') % tuple(u[3:5]))
        s.append('  inProtoMask %#x outProtoMask %#x' % tuple(u[5:7]))
        s.append({1: '  flags %#x reserved2 %u',
                  2: '  flags %#x reserved2 %u',
                  3: '  reserved3 %u reserved4 %u',
                  4: '  flags %#x reserved3 %u',
                  0: '  flags %#x reserved3 %u',
                  }.get(portid, '  ??? %u,%u') % tuple(u[7:]))

        if portid == 0:
            s.append('    slaveAddr %#x' % (u[3] >> 1 & 0x7F))

        s.append('    inProtoMask (%s)\n'
                 '    outProtoMask (%s)' %
                 (flag_s(u[5], self.cfg_prt_proto),
                  flag_s(u[6], self.cfg_prt_proto)))

        if portid in set([1, 2, 4, 0]):
            s.append('    flags (%s)' % flag_s(u[7], self.cfg_prt_flags))

        return '\n'.join(s)

    cfg_pwr_state = {
        0x52554E20: "GNSS running",
        0x53544F50: "GNSS stopped",
        0x42434B50: "Software Backup",
        }

    def cfg_pwr(self, buf):
        """UBX-CFG-PWR decode, Put receiver in a defined power state

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BBBBL', buf, 0)
        s = (" version %u reserved %u %u %u state %u" %
             (u + (index_s(u[0], self.cfg_pwr_state),)))
        return s

    cfg_rate_system = {
        0: "UTC",
        1: "GPS",
        2: "GLONASS",
        3: "BeiDou",
        4: "Galileo",
        }

    def cfg_rate(self, buf):
        """UBX-CFG-RATE decode, Navigation/Measurement Rate Settings"""

        u = struct.unpack_from('<HHH', buf, 0)
        s = (" measRate %u navRate %u timeRef %u (%s)" %
             (u + (index_s(u[2], self.cfg_rate_system),)))
        return s

    cfg_rinv_flags = {
        1: "dump",
        2: "binary",
        }

    def cfg_rinv(self, buf):
        """UBX-CFG-RINV decode, Contents of Remote Inventory

Deprecated in protVer 34.00
"""

        # u-blox 5, protVer 6.00 to 6.02
        m_len = len(buf)

        u = struct.unpack_from('<B', buf, 0)
        s = (" flags x%x (%s) data:" %
             (u + (flag_s(u[0], self.cfg_rinv_flags),)))
        for i in range(0, m_len - 1):
            if 0 == (i % 8):
                s += "\n   "
            u = struct.unpack_from('<B', buf, i + 1)
            s += " %3u" % u

        return s

    cfg_rst_navBbr = {
        0: "Hot Start",
        1: "Warm Start",
        0xffff: "Cold Start",
        }

    cfg_rst_navBbr1 = {
        1: "eph",
        2: "alm",
        4: "health",
        8: "klob",
        0x10: "pos",
        0x20: "clkd",
        0x40: "osc",
        0x80: "utc",
        0x100: "rtc",
        0x8000: "aop",
        }

    cfg_rst_resetMode = {
        0: "Hardware reset",
        1: "Software reset",
        2: "Software reset (GNSS only)",
        4: "Hardware reset, after shutdown",
        8: "Controlled GNSS stop",
        9: "Controlled GNSS start",
        }

    def cfg_rst(self, buf):
        """UBX-CFG-RST decode, Reset Receiver/Clear Backup Data Structures

protVer 15 and up
"""

        u = struct.unpack_from('<HBB', buf, 0)
        s = ' navBbrmask x%x resetMode %u reserved %u' % u

        if gps.VERB_DECODE <= self.verbosity:
            # fun, two different ways to decode...
            s1 = index_s(u[0], self.cfg_rst_navBbr, nf="")
            if not s1:
                s1 = flag_s(u[0], self.cfg_rst_navBbr1)

            s += ("\n   resetMode (%s)"
                  "\n   navBbrMask (%s)" %
                  (index_s(u[1], self.cfg_rst_resetMode),
                   s1))

        return s

    cfg_rxm_lpMode = {
        0: "Continuous Mode",
        1: "Power Save Mode",
        4: "Continuous Mode",
        }

    def cfg_rxm(self, buf):
        """UBX-CFG-RXM decode, Navigation/Measurement

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BB', buf, 0)
        s = (" reserved1 %u lpMode %u (%s)" %
             (u + (index_s(u[1], self.cfg_rxm_lpMode),)))
        return s

    cfg_sbas_mode = {
        1: "enabled",
        2: "test",
        }

    cfg_sbas_usage = {
        1: "range",
        2: "diffCorr",
        3: "integrity",
        }

    cfg_sbas_scanmode1 = {
        1: "PRN120",
        2: "PRN121",
        4: "PRN122",
        8: "PRN123",
        0x10: "PRN124",
        0x20: "PRN125",
        0x40: "PRN126",
        0x80: "PRN127",
        0x100: "PRN128",
        0x200: "PRN129",
        0x400: "PRN130",
        0x800: "PRN131",
        0x1000: "PRN132",
        0x2000: "PRN133",
        0x4000: "PRN134",
        0x8000: "PRN135",
        0x10000: "PRN136",
        0x20000: "PRN137",
        0x40000: "PRN138",
        0x80000: "PRN139",
        0x100000: "PRN140",
        0x200000: "PRN141",
        0x400000: "PRN142",
        0x800000: "PRN143",
        0x1000000: "PRN144",
        0x2000000: "PRN145",
        0x4000000: "PRN146",
        0x8000000: "PRN147",
        0x10000000: "PRN148",
        0x20000000: "PRN149",
        0x40000000: "PRN150",
        0x80000000: "PRN151",
        }

    cfg_sbas_scanmode2 = {
        1: "PRN152",
        2: "PRN153",
        4: "PRN154",
        8: "PRN155",
        0x10: "PRN156",
        0x20: "PRN157",
        0x40: "PRN158",
        }

    def cfg_sbas(self, buf):
        """UBX-CFG-SBAS decode, SBAS Configuration

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<BBBBL', buf, 0)
        s = (" mode x%x usage x%x maxSBAS %u scanMode2 x%x"
             " scanMode1: x%x" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   mode (%s) usage (%s) scanmode2 (%s)"
                  "\n   scanmode1 (%s)" %
                  (flag_s(u[0], self.cfg_sbas_mode),
                   flag_s(u[1], self.cfg_sbas_usage),
                   flag_s(u[3], self.cfg_sbas_scanmode2),
                   flag_s(u[4], self.cfg_sbas_scanmode1)))

        return s

    # UBX-CFG-SENIF, protVer 19 and up, ADR and UDR only

    cfg_slas_mode = {
        1: "enabled",
        2: "test",
        4: "raim",
        }

    def cfg_slas(self, buf):
        """UBX-CFG-SLAS decode, SLAS configuration"""

        # protVer 19.2 (ADR, UDR only)

        u = struct.unpack_from('<BBH', buf, 0)
        s = " mode %u reserved1 %u %u" % u

        if gps.VERB_DECODE <= self.verbosity:
            s += "\n   mode (%s)" % (flag_s(u[0], self.cfg_slas_mode))

        return s

    cfg_smgr_messageCfg = {
        1: "measInternal",
        2: "measGNSS",
        4: "measEXTINT0",
        8: "measEXTINT1",
        }

    def cfg_smgr(self, buf):
        """UBX-CFG-SMGR decode, Synchronization manager configuration"""

        u = struct.unpack_from('<BBHHBBHHHHL', buf, 0)
        s = (" version %u minGNSSFix %u maxFreqChangeRate %u "
             "maxPhaseCorrR %u\n"
             " reserved1 %u %u freqTolerance %u timeTolerance %u "
             "messageCfg x%x\n"
             " maxSlewRate %u flags x%x" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   messageCfg (%s)" %
                  (flag_s(u[7], self.cfg_smgr_messageCfg)))

        return s

    cfg_tmode_timeMode = {
        0: "Disabled",
        1: "Survey In",
        2: "Fixed Mode",
        }

    def cfg_tmode(self, buf):
        """UBX-CFG-TMODE decode, Time Mode Settings"""

        # u-blox 5, protVer 5.00 to 6.02 (timing feature only)

        u = struct.unpack_from('<BBHlllLLL', buf, 0)
        s = ('  timeMode %u fixedPosX %d fixedPosY %d fixedPosZ %d\n'
             '  fixedPosVar %u svinMinDur %u svinAccLimit %u' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    timeMode (%s)" %
                  (index_s(u[0], self.cfg_tmode_timeMode)))

        return s

    cfg_tmode2_flags = {
        1: "lla",
        2: "altInv",
        }

    def cfg_tmode2(self, buf):
        """UBX-CFG-TMODE2 decode, Time Mode Settings 2"""

        # u-blox 6, 7 and 8 (timing only)
        # not in u-blox 9
        # protver 13+

        u = struct.unpack_from('<BBHlllLLL', buf, 0)
        s = ('  timeMode %u reserved1 %u usage %#x\n'
             '  ecefXOrLat %d ecefYOrLon %d ecefZOrAlt %d\n'
             '  fixedPosAcc %u svinMinDur %u svinAccLimit %u' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    timeMode (%s) flags (%s)" %
                  (index_s(u[0], self.cfg_tmode_timeMode),
                   flag_s(u[2], self.cfg_tmode2_flags)))

        return s

    cfg_tmode3_flags = {
        0x100: "lla",
        }

    def cfg_tmode3(self, buf):
        """UBX-CFG-TMODE3 decode, Time Mode Settings 3"""

        # in M8 HP only, protver 20 to 23
        # Not in u-blox 7-, HP only
        # undocumented, but present in ZED-F9T
        # documented in ZED-F9P, protver 27
        # deprecated in 23.01
        u = struct.unpack_from('<BBHlllbbbBLLLLL', buf, 0)
        s = ('  version %u reserved1 %u flags x%x\n'
             '  ecefXOrLat %d ecefYOrLon %d ecefZOrAlt %d\n'
             '  ecefXOrLatHP %d ecefYOrLonHP %d ecefZOrAltHP %d\n'
             '  reserved2 %u fixedPosAcc %u svinMinDur %u svinAccLimit %u\n'
             '  reserved3 %u %u' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    flags (%s %s)" %
                  (index_s(u[2], self.cfg_tmode_timeMode),
                   flag_s(u[2] & 0x100, self.cfg_tmode3_flags)))

        return s

    cfg_tp_status = {
        -1: "negative",
        0: "off",
        1: "positive",
        }

    cfg_tp_timeRef = {
        0: "UTC",
        1: "GPS",
        2: "Local",
        }

    cfg_tp_flags = {
        1: "syncMode",
        }

    def cfg_tp(self, buf):
        """UBX-CFG-TP decode, Time Pulse Settings"""

        # protVer 4.00 to 6.02

        u = struct.unpack_from('<HHbBBBhhl', buf, 0)
        s = ('  interval %u length %u status %d timeRef %u flags x%x res x%x\n'
             '  antennaCableDelay %u rfGroupDelay %d userDelay %d' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   flags (%s, %s, %s)" %
                  (index_s(u[2], self.cfg_tp_status),
                   index_s(u[3], self.cfg_tp_timeRef),
                   flag_s(u[4], self.cfg_tp_flags)))

        return s

    cfg_tp5_flags = {
        1: "Active",
        2: "lockGnssFreq",
        4: "lockedOtherSet",
        8: "isFreq",
        0x10: "isLength",
        0x20: "alignToTow",
        0x40: "RisingEdge",
        }

    cfg_tp5_grid = {
        0: 'UTC',
        1: 'GPS',
        2: 'Glonass',
        3: 'BeiDou',
        4: 'Galileo',
        }

    def cfg_tp5(self, buf):
        """UBX-CFG-TP5 decode, Time Pulse Parameters

Deprecated in protVer 34.00
"""

        m_len = len(buf)

        if 1 == m_len:
            return "  Poll request tpIdx %d" % buf[0]

        if 32 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<BBHhhLLLLlL', buf, 0)
        s = ("  tpIdx %u version %u reserved1 %u\n"
             "  antCableDelay %d rfGroupDelay %d freqPeriod %u "
             "freqPeriodLock %u\n"
             "  pulseLenRatio %u pulseLenRatioLock %u userConfigDelay %d\n"
             "  flags x%x" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    flags (%s)"
                  "\n    gridToGps (%s) syncMode %d" %
                  (flag_s(u[10] & 0x7f, self.cfg_tp5_flags),
                   index_s((u[10] >> 7) & 0x0f, self.cfg_tp5_grid),
                   (u[10] >> 11) & 0x03))

        return s

    cfg_usb_flags = {1: "reEnum "}

    cfg_usb_powerMode = {0: "self-powered",
                         2: "bus-powered",
                         }

    def cfg_usb(self, buf):
        """UBX-CFG-USB decode, USB Configuration

Only for models with built in USB.
"""

        u = struct.unpack_from('<HHHHHH', buf, 0)
        s = ('  vendorID %#x productID %#x reserved1 %u reserved2 %u\n'
             '  powerConsumption %u mA flags %#x' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    flags (%s%s)" %
                  (flag_s(u[5] & 1, self.cfg_usb_flags),
                   index_s(u[5] & 2, self.cfg_usb_powerMode)))

        s += ('\n  vendorString %s\n'
              '  productString %s\n'
              '  serialNumber %s' %
              (gps.polystr(buf[12:43]).rstrip('\0'),
               gps.polystr(buf[44:75]).rstrip('\0'),
               gps.polystr(buf[76:107]).rstrip('\0')))
        return s

    cfg_valdel_layers = {
        1: 'ram',
        2: 'bbr',
        4: 'flash',
        }

    cfg_valget_layers = {
        0: 'ram',
        1: 'bbr',
        2: 'flash',
        7: 'default',
        }

    cfg_valxxx_trans = {
        0: "Transactionless",
        1: "(Re)start Transaction",
        2: "Continue Transaction",
        3: "Apply and end Transaction",
        }

    def cfg_valdel(self, buf):
        """"UBX-CFG-VALDEL decode, Delete configuration items"""
        m_len = len(buf)

        # this is a poll options, so does not set min protver

        u = struct.unpack_from('<BBBB', buf, 0)
        s = ' version %u layer %#x transaction %#x reserved %u\n' % u
        s += ('  layers (%s) transaction (%s)' %
              (flag_s(u[1], self.cfg_valdel_layers),
               index_s(u[2], self.cfg_valxxx_trans)))

        m_len -= 4
        i = 0
        while 0 < m_len:
            u = struct.unpack_from('<L', buf, 4 + i * 4)
            item = self.cfg_by_key(u[0])
            s += ('\n    item: %s/%#x' % (item[0], u[0]))
            m_len -= 4
            i += 1
        return s

    def cfg_valget(self, buf):
        """"UBX-CFG-VALGET decode, Get configuration items"""
        m_len = len(buf)

        # version zero is a poll
        # version one is the response

        u = struct.unpack_from('<BBH', buf, 0)
        s = ' version %u layer %u position %u\n' % u
        s += '  layers (%s)' % index_s(u[1], self.cfg_valget_layers)

        m_len -= 4
        i = 0

        if 0 == u[0]:
            # this is a poll option, so does not set min protver
            while 0 < m_len:
                u = struct.unpack_from('<L', buf, 4 + i * 4)
                item = self.cfg_by_key(u[0])
                s += ('\n    item %s/%#x' % (item[0], u[0]))
                m_len -= 4
                i += 1
        else:
            # answer to poll
            # we are at least protver 27
            if 27 > self.protver:
                self.protver = 27

            # sort of duplicated in cfg_valset()
            i += 4
            while 4 < m_len:
                u = struct.unpack_from('<L', buf, i)
                m_len -= 4
                i += 4
                item = self.cfg_by_key(u[0])
                cfg_type = self.item_to_type(item)
                size = cfg_type[0]
                if size > m_len:
                    s += "\nWARNING: not enough bytes!"
                    break

                frmat = cfg_type[1]
                # flavor = cfg_type[2]  UNUSED
                v = struct.unpack_from(frmat, buf, i)
                s += ('\n    item %s/%#x val %s' % (item[0], u[0], v[0]))
                m_len -= size
                i += size

            if 0 < m_len:
                s += "\nWARNING: %d extra bytes!" % m_len

        return s

    def cfg_valset(self, buf):
        """"UBX-CFG-VALSET decode, Set configuration items"""
        m_len = len(buf)

        # this is a poll option, so does not set min protver

        u = struct.unpack_from('<BBBB', buf, 0)
        s = ' version %u layer %#x transaction %#x reserved %u\n' % u
        s += ('  layers (%s) transaction (%s)' %
              (flag_s(u[1], self.cfg_valdel_layers),
               index_s(u[2], self.cfg_valxxx_trans)))

        # sort of duplicated in cfg_valget()
        m_len -= 4
        i = 4
        while 4 < m_len:
            u = struct.unpack_from('<L', buf, i)
            m_len -= 4
            i += 4
            item = self.cfg_by_key(u[0])
            cfg_type = self.item_to_type(item)

            size = cfg_type[0]
            # FIXME!  should check for enough bytes to unpack from
            frmat = cfg_type[1]
            # flavor = cfg_type[2]  UNUSED
            v = struct.unpack_from(frmat, buf, i)
            s += ('\n    item %s/%#x val %s' % (item[0], u[0], v[0]))
            m_len -= size
            i += size

        if 0 < m_len:
            s += "\nWARNING: %d extra bytes!" % m_len

        return s

    # Broadcom calls this BRM-STP-
    cfg_ids = {
        # in u-blox 5+
        # Broadcom calls this BRM-STP-PORT
        0x00: {'str': 'PRT', 'dec': cfg_prt, 'minlen': 1,
               'name': 'UBX-CFG-PRT'},
        # in u-blox 5+
        # Broadcom calls this BRM-STP-MESSAGE
        0x01: {'str': 'MSG', 'dec': cfg_msg, 'minlen': 2,
               'name': 'UBX-CFG-MSG'},
        # in u-blox 5+
        0x02: {'str': 'INF', 'dec': cfg_inf, 'minlen': 1,
               'name': 'UBX-CFG-INF'},
        # in u-blox 5+
        # Broadcom calls this BRM-STP-RESET
        0x04: {'str': 'RST', 'dec': cfg_rst, 'minlen': 4,
               'name': 'UBX-CFG-RST'},
        # in u-blox 5 to 9
        0x06: {'str': 'DAT', 'dec': cfg_dat, 'minlen': 2,
               'name': 'UBX-CFG-DAT'},
        # u-blox 5, 6.  Not in u-blox 7+
        0x07: {'str': 'TP', 'dec': cfg_tp, 'minlen': 28,
               'name': 'UBX-CFG-TP'},
        # in u-blox 5+
        0x08: {'str': 'RATE', 'dec': cfg_rate, 'minlen': 6,
               'name': 'UBX-CFG-RATE'},
        # in u-blox 5+
        # Broadcom calls this BRM-STP-CONFIG
        0x09: {'str': 'CFG', 'dec': cfg_cfg, 'minlen': 12,
               'name': 'UBX-CFG-CFG'},
        # Antaris 4, deprecated in u-blox 5/6, gone in 7
        0x0e: {'str': 'FXM', 'dec': cfg_fxn, 'minlen': 36,
               'name': 'UBX-CFG-FXM'},
        # u-blox 5, 6, 7, 8
        0x11: {'str': 'RXM', 'dec': cfg_rxm, 'minlen': 2,
               'name': 'UBX-CFG-RXM'},
        # in u-blox 6, SFDR only.  Not in 5- or 7+
        0x12: {'str': 'EKF', 'minlen': 16, 'name': 'UBX-CFG-EKF'},
        # in u-blox 5+
        0x13: {'str': 'ANT', 'dec': cfg_ant, 'minlen': 4,
               'name': 'UBX-CFG-ANT'},
        # in u-blox 5+
        0x16: {'str': 'SBAS', 'dec': cfg_sbas, 'minlen': 8,
               'name': 'UBX-CFG-SBAS'},
        # in u-blox 5+
        # Broadcom calls this BRM-STP-NMEA
        0x17: {'str': 'NMEA', 'dec': cfg_nmea, 'minlen': 4,
               'name': 'UBX-CFG-NMEA'},
        # in u-blox 6+, Not in u-blox 5-
        0x1b: {'str': 'USB', 'dec': cfg_usb, 'minlen': 108,
               'name': 'UBX-CFG-USB'},
        # u-blox 5 and 6.  Not in u-blox 7+
        0x1d: {'str': 'TMODE', 'dec': cfg_tmode, 'minlen': 28,
               'name': 'UBX-CFG-TMODE'},
        # in u-blox 8+. Not in u-blox 7-
        0x1e: {'str': 'ODO', 'dec': cfg_odo, 'minlen': 20,
               'name': 'UBX-CFG-ODO'},
        # in u-blox 6, not in u-blox 7+
        0x22: {'str': 'NVS', 'dec': cfg_nvs, 'minlen': 13,
               'name': 'UBX-CFG-NVS'},
        # in u-blox 5+
        0x23: {'str': 'NAVX5', 'dec': cfg_navx5, 'minlen': 20,
               'name': 'UBX-CFG-NAVX5'},
        # in u-blox 6+.  Not in 5-
        # Broadcom calls this BRM-STP-CONFIG2
        0x24: {'str': 'NAV5', 'dec': cfg_nav5, 'minlen': 36,
               'name': 'UBX-CFG-NAV5'},
        # in u-blox 6. SFDR only. Not in u-blox 5- or 7+
        0x29: {'str': 'ESFGWT', 'minlen': 44, 'name': 'UBX-CFG-ESFGWT'},
        # in u-blox 6+, Not u-blox 5-
        0x31: {'str': 'TP5', 'dec': cfg_tp5, 'minlen': 1,
               'name': 'UBX-CFG-TP5'},
        # In u-blox 5, 6. Not in u-blox 7+
        0x32: {'str': 'PM', 'dec': cfg_pm, 'minlen': 24,
               'name': 'UBX-CFG-PM'},
        # in u-blox 5+
        0x34: {'str': 'RINV', 'dec': cfg_rinv, 'minlen': 1,
               'name': 'UBX-CFG-RINV'},
        # in u-blox 6+.  Not in u-blox 5-
        0x39: {'str': 'ITFM', 'dec': cfg_itfm, 'minlen': 8,
               'name': 'UBX-CFG-ITFM'},
        # in u-blox 6+.  Not in u-blox 5-
        0x3b: {'str': 'PM2', 'dec': cfg_pm2, 'minlen': 44,
               'name': 'UBX-CFG-PM2'},
        # in u-blox 6 and 7.  Not in u-blox 5- or 8+
        0x3d: {'str': 'TMODE2', 'dec': cfg_tmode2, 'minlen': 28,
               'name': 'UBX-CFG-TMODE2'},
        # in u-blox 7+  Not in u-blox 6-
        # Broadcom calls this BRM-STP-ME_SETTINGS
        0x3e: {'str': 'GNSS', 'dec': cfg_gnss, 'minlen': 4,
               'name': 'UBX-CFG-GNSS'},
        # protVer 19 and up, UDR only
        0x40: {'str': 'ESFG', 'minlen': 20, 'name': 'UBX-CFG-ESFG'},
        # in u-blox 7+  Not in u-blox 6-
        0x47: {'str': 'LOGFILTER', 'dec': cfg_logfilter, 'minlen': 12,
               'name': 'UBX-CFG-LOGFILTER'},
        # protVer 19 and up, UDR only
        0x4c: {'str': 'ESFA', 'minlen': 20, 'name': 'UBX-CFG-ESFA'},
        # Not in u-blox 7-, FTS only
        0x53: {'str': 'TXSLOT', 'minlen': 2, 'name': 'UBX-CFG-TXSLOT'},
        # protVer 15.01 and up, ADR and UDR only
        0x56: {'str': 'ESFALG', 'minlen': 12, 'name': 'UBX-CFG-ESFALG'},
        # Not in u-blox 7-
        0x57: {'str': 'PWR', 'dec': cfg_pwr, 'minlen': 8,
               'name': 'UBX-CFG-PWR'},
        # Not in u-blox 8-
        0x5c: {'str': 'HNR', 'dec': cfg_hnr, 'minlen': 4,
               'name': 'UBX-CFG-HNR'},
        # Not in u-blox 7-, protVer 16 and up,  TFS only
        0x60: {'str': 'ESRC', 'dec': cfg_esrc, 'minlen': 4,
               'name': 'UBX-CFG-ESRC'},
        # Not in u-blox 8-
        0x61: {'str': 'DOSC', 'dec': cfg_dosc, 'minlen': 4,
               'name': 'UBX-CFG-DOSC'},
        # Not in u-blox 8-
        0x62: {'str': 'SMGR', 'dec': cfg_smgr, 'minlen': 20,
               'name': 'UBX-CFG-SMGR'},
        # protVer 15.01 and up, ADR and UDR only
        0x64: {'str': 'SPT', 'minlen': 12, 'name': 'UBX-CFG-SPT'},
        # Not in u-blox 8-
        0x69: {'str': 'GEOFENCE', 'dec': cfg_geofence, 'minlen': 8,
               'name': 'UBX-CFG-GEOFENCE'},
        # Not in u-blox 8-
        0x70: {'str': 'DGNSS', 'dec': cfg_dgnss, 'minlen': 4,
               'name': 'UBX-CFG-DGNSS'},
        # Not in u-blox 7-, HP only
        # undocumented, but present in ZED-F9T
        0x71: {'str': 'TMODE3', 'dec': cfg_tmode3, 'minlen': 40,
               'name': 'UBX-CFG-TMODE3'},
        # protVer 15.01 and up, ADR only
        0x82: {'str': 'ESFWT', 'minlen': 32, 'name': 'UBX-CFG-ESFWT'},
        # Not in u-blox 7-
        0x84: {'str': 'FIXSEED', 'dec': cfg_fixseed, 'minlen': 12,
               'name': 'UBX-CFG-FIXSEED'},
        # Not in u-blox 7-
        0x85: {'str': 'DYNSEED', 'dec': cfg_dynseed, 'minlen': 12,
               'name': 'UBX-CFG-DYNSEED'},
        # Not in u-blox 8-
        # Broadcom calls this BRM-STP-PWR_MODE
        0x86: {'str': 'PMS', 'dec': cfg_pms, 'minlen': 8,
               'name': 'UBX-CFG-PMS'},
        # protVer 19 and up, ADR and UDR only
        0x88: {'str': 'SENIF', 'minlen': 6, 'name': 'UBX-CFG-SENIF'},
        # in u-blox 9
        0x8a: {'str': 'VALSET', 'dec': cfg_valset, 'minlen': 4,
               'name': 'UBX-CFG-VALSET'},
        # in u-blox 9
        0x8b: {'str': 'VALGET', 'dec': cfg_valget, 'minlen': 4,
               'name': 'UBX-CFG-VALGET'},
        # in u-blox 9
        0x8c: {'str': 'VALDEL', 'dec': cfg_valdel, 'minlen': 4,
               'name': 'UBX-CFG-VALDEL'},
        # u-blox 8
        0x8d: {'str': 'SLAS', 'dec': cfg_slas, 'minlen': 4,
               'name': 'UBX-CFG-SLAS'},
        # only in u-blox 8
        0x93: {'str': 'BATCH', 'dec': cfg_batch, 'minlen': 8,
               'name': 'UBX-CFG-BATCH'},
        # Broadcom calls this BRM-STP-L1L5bias
        # 0xb0:
        }

    # UBX-ESF-
    # only with ADR or UDR products
    esf_ids = {0x02: {'str': 'MEAS', 'minlen': 8, 'name': "UBX-ESF-MEAS"},
               0x03: {'str': 'RAW', 'minlen': 4, 'name': "UBX-ESF-RAW"},
               0x10: {'str': 'STATUS', 'minlen': 16, 'name': "UBX-ESF-STATUS"},
               0x14: {'str': 'ALG', 'minlen': 16, 'name': "UBX-ESF-ALG"},
               0x15: {'str': 'INS', 'minlen': 16, 'name': "UBX-ESF-INS"},
               }

    # UBX-HNR-
    # only with ADR or UDR products
    hnr_ids = {0x00: {'str': 'PVT', 'minlen': 72, 'name': "UBX-HNR-PVT"},
               0x01: {'str': 'ATT', 'minlen': 32, 'name': "UBX-HNR-ATT"},
               0x02: {'str': 'INS', 'minlen': 36, 'name': "UBX-HNR-INS"},
               }

    def inf_debug(self, buf):
        """UBX-INF-DEBUG decode"""
        return ' Debug: ' + gps.polystr(buf)

    def inf_error(self, buf):
        """UBX-INF-ERROR decode"""
        return ' Error: ' + gps.polystr(buf)

    def inf_notice(self, buf):
        """UBX-INF-NOTICE decode"""
        return ' Notice: ' + gps.polystr(buf)

    def inf_test(self, buf):
        """UBX-INF-TET decode"""
        return ' Test: ' + gps.polystr(buf)

    def inf_warning(self, buf):
        """UBX-INF-WARNING decode"""
        return ' Warning: ' + gps.polystr(buf)

    inf_ids = {0x0: {'str': 'ERROR', 'dec': inf_error, 'minlen': 0,
                     'name': 'UBX-INF-ERROR'},
               0x1: {'str': 'WARNING', 'dec': inf_warning, 'minlen': 0,
                     'name': 'UBX-INF-WARNING'},
               0x2: {'str': 'NOTICE', 'dec': inf_notice, 'minlen': 0,
                     'name': 'UBX-INF-NOTICE'},
               0x3: {'str': 'TEST', 'dec': inf_test, 'minlen': 0,
                     'name': 'UBX-INF-TEST'},
               0x4: {'str': 'DEBUG', 'dec': inf_debug, 'minlen': 0,
                     'name': 'UBX-INF-DEBUG'},
               }

    log_batch_contentValid = {
        1: 'extraPvt',
        2: 'extraOdo',
        }

    log_batch_valid = {
        1: 'validDate',
        2: 'validTime',
        }

    log_batch_fixType = {
        0: 'No Fix',
        2: '2D Fix',
        3: '3D Fix',
        4: 'GNSS + DR',   # only UBX-LOG-RETRIEVEPOS
        }

    log_batch_flags = {
        1: 'gnssFixOK',
        2: 'diffSoln',
        }

    log_batch_psmState = {
        0: 'Not Active',
        4: 'Enabled',
        8: 'Acquisition',
        9: 'Tracking',
        0x10: 'Power Optimized Tracking',
        0x11: 'Inactive',
        }

    def log_batch(self, buf):
        """UBX-LOG-BATCH decode
Oddly this is polled with UBX-LOG-RETRIEVEBATCH
"""

        # u-blox 8, protVer 23+
        # in NEO-M9N, protVer 32.00
        u = struct.unpack_from('<BBHLHBBBBBBLlBBBBllllLLlllllLLHHLLLL', buf, 0)
        s = ("  version %u contentValid x%x msgCnt %u iTow %u\n"
             "  year %u month %u day %u hour %u min %u sec %u valid x%x\n"
             "  tAcc %u fracSec %d fixType %u flags x%x flags2 x%x numSV %u\n"
             "  lon %d lat %d height %d hMSL %d\n"
             "  hAcc %u vAcc %u\n"
             "  vel N %u E %u D %u gSpeed %d headMot %d sAcc %u headAcc %u\n"
             "  pdep %u reserved1 x%x distance %u totalDistance %u\n"
             "  distanceStd %u reserved2 x%x" % u)
        if gps.VERB_DECODE <= self.verbosity:
            # flags2 undocumented
            s += ("\n      contentValid (%s) valid (%s)"
                  "\n      fixType (%s)"
                  "\n      flags (%s) psmState (%s)" %
                  (flag_s(u[1], self.log_batch_contentValid),
                   flag_s(u[10], self.log_batch_valid),
                   index_s(u[13], self.log_batch_fixType),
                   flag_s(u[14] & 3, self.log_batch_flags),
                   index_s(u[14] & 0x1c, self.log_batch_psmState)))

        return s

    log_create_logCfg = {
        1: 'circular',
        }

    log_create_logSize = {
        0: 'Maximum safe',
        1: 'Minimum safe',
        2: 'user defined',
        }

    def log_create(self, buf):
        """UBX-LOG-CREATE decode"""

        # u-blox 7+, protVer 14+
        u = struct.unpack_from('<BBBBL', buf, 0)
        s = ("  version %u logCfg x%x reserved1 x%x logSize %u\n"
             "  userDefinedSize %u" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n      logCfg (%s) logSize (%s)" %
                  (flag_s(u[1], self.log_create_logCfg),
                   index_s(u[3], self.log_create_logSize)))

        return s

    def log_erase(self, buf):
        """UBX-LOG-ERASE decode"""

        # u-blox 7+, protVer 14+
        return "  Erase Logged Data"

    log_findtime_type = {
        0: 'request',
        1: 'response',
        }

    def log_findtime(self, buf):
        """UBX-LOG-FINDTIME decode"""

        # u-blox 7+, protVer 14+
        m_len = len(buf)

        # length 8 (version 1, type 1) is response.
        # WTF; length 10 (version 0, type 0) is request
        # length 12 (version 0, type 0) is request
        if 8 == m_len:
            # response
            u = struct.unpack_from('<BBHL', buf, 0)
            s = "  version %u type %u reserved1 x%x entryNumber %u" % u
            if 1 != u[0] or 1 != u[1]:
                s += "\nWARNING: Unknown version, type (%u, %u)" % (u[0], u[1])
        elif 10 == m_len:
            # request
            u = struct.unpack_from('<BBHBBBBBB', buf, 0)
            s = ("  version %u type %u\n"
                 "  year %u month %u day %u hour %u min %u sec %u "
                 "reserved2 x%x" % u)
            if 0 != u[0] or 0 != u[1]:
                s += "\nWARNING: Unknown version, type (%u, %u)" % (u[0], u[1])
        elif 12 == m_len:
            # request
            u = struct.unpack_from('<BBHHBBBBBB', buf, 0)
            s = ("  version %u type %u reserved1 x%x\n"
                 "  year %u month %u day %u hour %u min %u sec %u "
                 "reserved2 x%x" % u)
            if 0 != u[0] or 0 != u[1]:
                s += "\nWARNING: Unknown version, type (%u, %u)" % (u[0], u[1])
        else:
            return "  Bad Length %s" % m_len

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n      type (%s)" %
                  (index_s(u[1], self.log_findtime_type)))

        return s

    log_info_status = {
        8: 'recording',
        0x10: 'inactive',
        0x20: 'circular',
        }

    def log_info(self, buf):
        """UBX-LOG-INFO decode"""

        # u-blox 7+, protVer 14+
        u = struct.unpack_from('<BBHLLLLLLHBBBBBBHBBBBBBBBH', buf, 0)
        s = ("  version %u reserved1 x%x x%x filestoreCapacity %u "
             "reserved2 x%x x%x\n"
             "  currentMaxLogSize %u currentLogSize %u entryCount %u\n"
             "  oldestYear %u oldestMonth %u oldestDay %u \n"
             "  oldestHour %u oldestMin %u oldestSec %u reserved3 x%x\n"
             "  newestYear %u newestMonth %u newestDay %u \n"
             "  newestHour %u newestMin %u newestSec %u reserved4 x%x\n"
             "  status x%x reserved5 x%x x%x" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n      status (%s)" %
                  (flag_s(u[23], self.log_info_status)))

        return s

    log_retrievebatch_flags = {
        1: 'sendMonFirst',
        }

    def log_retrieve(self, buf):
        """UBX-LOG-RETRIEVE decode"""

        # u-blox 7+, protVer 14+
        u = struct.unpack_from('<LLBBH', buf, 0)
        s = "  startNumber %u entryCount %u version %u reserved1 x%x %x" % u

        return s

    def log_retrievebatch(self, buf):
        """UBX-LOG-RETRIEVEBATCH decode
Oddly this is the poll for UBX-LOG-BATCH
"""

        # u-blox 8, protVer 23.01 to 23.99
        # not in u-blox 7 or 9
        u = struct.unpack_from('<BBH', buf, 0)
        s = ("  version %u flags x%x reserved1 x%x" % u)
        if gps.VERB_DECODE <= self.verbosity:
            # flags2 undocumented
            s += ("\n      flags (%s)" %
                  flag_s(u[1], self.log_retrievebatch_flags))

        return s

    def log_retrievepos(self, buf):
        """UBX-LOG-RETRIEVEPOS decode"""

        # u-blox 7+, protVer 14+
        u = struct.unpack_from('<LlllLLLBBHBBBBBBBB', buf, 0)
        s = ("  entryIndex %u lon %d lat %d hMSL %d hAcc %u\n"
             "  gSpeed %u heading %u version %u fixType %u\n"
             "  year %u month %u day %u hour %u min %u sec %u\n"
             "  reserved1 x%x numSV %u reserved2 x%x" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n      fixType (%s)" %
                  (index_s(u[8], self.log_batch_fixType)))

        return s

    def log_retrieveposextra(self, buf):
        """UBX-LOG-RETRIEVEPOSEXTRA decode"""

        # u-blox 8+, protVer 15+
        u = struct.unpack_from('<LBBHBBBBBBHLLLL', buf, 0)
        s = ("  entryIndex %u version %u reserved1 x%x\n"
             "  year %u month %u day %u hour %u minute %u seconds %u\n"
             "  reserved2 x%x %x distance %u reserved3 x%x %x %x" % u)

        return s

    def log_retrievestring(self, buf):
        """UBX-LOG-RETRIEVESTRING decode"""

        # u-blox 7+, protVer 14+
        u = struct.unpack_from('<LBBHBBBBBBH', buf, 0)
        s = ("  entryIndex %u version %u reserved2 x%x\n"
             "  year %u month %u day %u hour %u min %u sec %u\n"
             "  reserved2 x%x byteCount %u\n"
             "  bytes \"" % u)
        if 0 < u[10]:
            for c in buf[16:16 + u[10]]:
                if c < 127 and chr(c) in string.printable:
                    s += chr(c)
                else:
                    s += "\\x%02x" % c
            s += '"'

        return s

    def log_string(self, buf):
        """UBX-LOG-STRING decode"""

        # u-blox 7+, protVer 14+
        m_len = len(buf)

        if 256 < m_len:
            return "  Bad Length %s" % m_len

        s = "  bytes "
        if 0 < m_len:
            s += gps.polystr(binascii.hexlify(buf))

        return s

    # UBX-LOG-
    log_ids = {
               0x03: {'str': 'ERASE', 'dec': log_erase, 'minlen': 0,
                      'name': "UBX-LOG-ERASE"},
               0x04: {'str': 'STRING', 'dec': log_string, 'minlen': 0,
                      'name': "UBX-LOG-STRING"},
               0x07: {'str': 'CREATE', 'dec': log_create, 'minlen': 8,
                      'name': "UBX-LOG-CREATE"},
               0x08: {'str': 'INFO', 'dec': log_info, 'minlen': 48,
                      'name': "UBX-LOG-INFO"},
               0x09: {'str': 'RETRIEVE', 'dec': log_retrieve, 'minlen': 12,
                      'name': "UBX-LOG-RETRIEVE"},
               0x0b: {'str': 'RETRIEVEPOS', 'dec': log_retrievepos,
                      'minlen': 40,
                      'name': "UBX-LOG-RETRIEVEPOS"},
               0x0d: {'str': 'RETRIEVESTRING', 'dec': log_retrievestring,
                      'minlen': 16,
                      'name': "UBX-LOG-RETRIEVESTRING"},
               0x0e: {'str': 'FINDTIME', 'dec': log_findtime, 'minlen': 8,
                      'name': "UBX-LOG-FINDTIME"},
               0x0f: {'str': 'RETRIEVEPOSEXTRA', 'dec': log_retrieveposextra,
                      'minlen': 32,
                      'name': "UBX-LOG-RETRIEVEPOSEXTRA"},
               0x10: {'str': 'RETRIEVEBATCH', 'dec': log_retrievebatch,
                      'minlen': 2,
                      'name': "UBX-LOG-RETRIEVEBATCH"},
               0x11: {'str': 'BATCH', 'dec': log_batch, 'minlen': 100,
                      'name': "UBX-LOG-BATCH"},
               }

    # UBX-MGA-
    def mga_dbd(self, buf):
        """UBX-MGA-DBD- decode, Navigation Database Dump Entry"""
        # max 172

        u = struct.unpack_from('<LLL', buf, 0)
        s = ' reserved1 %u %u %u' % u
        # plus some anonymous data...

        return s

    # Braodcam calls this BRM-AST-
    mga_ids = {0x00: {'str': 'GPS', 'minlen': 16, 'name': "UBX-MGA-GPS"},
               0x02: {'str': 'GAL', 'minlen': 12, 'name': "UBX-MGA-GAL"},
               0x03: {'str': 'BDS', 'minlen': 16, 'name': "UBX-MGA-BDS"},
               0x05: {'str': 'QZSS', 'minlen': 12, 'name': "UBX-MGA-QZSS"},
               0x06: {'str': 'GLO', 'minlen': 20, 'name': "UBX-MGA-GLO"},
               # Braodcam calls this BRM-AST-LTO
               0x20: {'str': 'ANO', 'minlen': 76, 'name': "UBX-MGA-ANO"},
               0x21: {'str': 'FLASH', 'minlen': 2, 'name': "UBX-MGA-FLASH"},
               # Braodcam calls this BRM-AST-REF_LOCATION
               # Braodcam calls this BRM-AST-REF_TIME_UTC
               0x40: {'str': 'INI', 'minlen': 12, 'name': "UBX-MGA-INI"},
               # Braodcam calls this BRM-AST-ACK
               0x60: {'str': 'ACK', 'minlen': 8, 'name': "UBX-MGA-ACK"},
               # Braodcam calls this BRM-AST-NVMEM
               0x80: {'str': 'DBD', 'dec': mga_dbd, 'minlen': 12,
                      'name': "UBX-MGA-DBD"},
               }

    def mon_batch(self, buf):
        """UBX-MON-BATCH decode, Data batching buffer status"""

        # in u-blox 8 only, not in 7 or 9.
        # protVer 23.01, gone in 24
        u = struct.unpack_from('<BBBBHHHH', buf, 0)
        s = ("   version %u reserved1 %u %u %u fillLevel %u\n"
             "   dropsAll %u dropsSinceMon %u nextMsgCnt %u" % u)

        return s

    mon_comms_prot = {
        0: "UBX",
        1: "NMEA",
        2: "RTCM2",
        5: "RTCM3",
        255: "None",
        }

    def mon_comms(self, buf):
        """UBX-MON-COMMS decode, Comm port information"""

        # at least protver 27
        if 27 > self.protver:
            self.protver = 27

        u = struct.unpack_from('<BBBBBBBB', buf, 0)
        s = ('version %u nPorts %u txErrors x%x reserved1 %u\n'
             'protIds %#x/%x/%x/%x' % u)
        s += (' (%s/%s/%s/%s)\n' %
              (index_s(u[4], self.mon_comms_prot),
               index_s(u[5], self.mon_comms_prot),
               index_s(u[6], self.mon_comms_prot),
               index_s(u[7], self.mon_comms_prot)))

        if gps.VERB_DECODE <= self.verbosity:
            errors = {
               0x40: "mem",
               0x80: "alloc",
               }

            s += "     txErrors (%s)\n" % (flag_s(u[2], errors))

        for i in range(0, u[1]):
            u = struct.unpack_from('<HHLBBHLBBHHHHHLLL', buf, (8 + (i * 40)))
            name = "%#x (%s)" % (u[0], index_s(u[0], self.port_ids1))
            if 0 < i:
                s += "\n"
            s += '  Port: %s\n' % name
            s += ('   txPending %u txBytes %u txUsage %u txPeakUsage %u\n'
                  '   rxPending %u rxBytes %u rxUsage %u rxPeakUsage %u\n'
                  '   overrunErrs %u msgs %u/%u/%u/%u reserved %x %x '
                  'skipped %u'
                  % u[1:])
        return s

    mon_gnss_supported_bits = {
        1: "GPS",
        2: "Glonass",
        4: "Beidou",
        8: "Galileo",
        }

    def mon_gnss(self, buf):
        """UBX-MON-GNSS decode, Information message major GNSS selection"""
        m_len = len(buf)

        if 8 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<BBBBBBBB', buf, 0)
        s = ('   version %u supported %#x defaultGnss %#x enabled %#x\n'
             '   simultaneous %u reserved1 %u %u %u' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n     supported (%s)'
                  '\n     defaultGnss (%s)'
                  '\n     enabled (%s)' %
                  (flag_s(u[1], self.mon_gnss_supported_bits),
                   flag_s(u[2], self.mon_gnss_supported_bits),
                   flag_s(u[3], self.mon_gnss_supported_bits)))

        return s

    mon_hw_flags = {
        1: "rtcCalib",
        2: "safeBoot",
        }

    mon_hw_aPower = {
        0: "Off",
        1: "On",
        }

    jammingState = {
        0: "Unk",
        1: "OK",
        2: "Warning",
        3: "Critical",
        }

    def mon_hw(self, buf):
        """UBX-MON-HW decode, Hardware Status

extended in protVer 34

Deprecated in protVer 34.00
"""

        u = struct.unpack_from('<LLLLHHBBBBLBBBBBBBBBBBBBBBBBBBBLLL', buf, 0)
        s = ('  pinSel %#x pinBank %#x pinDir %#x pinVal %#x noisePerMS %u\n'
             '  agcCnt %u aStatus %u aPower %u flags %#x reserved1 %u\n'
             '  usedMask %#x\n'
             '  VP %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u\n'
             '  jamInd %u reserved2 %u %u pinIrq %#x pullH %#x pullL %#x' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    aStatus (%s) aPower (%s) flags (%s) "
                  "jammingState (%s)" %
                  (index_s(u[6], self.mon_rf_antstat),
                   index_s(u[7], self.mon_hw_aPower),
                   index_s(u[8], self.mon_hw_flags),
                   index_s((u[6] >> 2) & 0x03, self.jammingState)))
        return s

    mon_hw2_cfgSource = {
        102: "flash image",
        111: "OTP",
        112: "config pins",
        114: "ROM",
        }

    def mon_hw2(self, buf):
        """UBX-MON-HW2 decode, Extended Hardware Status"""

        u = struct.unpack_from('<bBbBBBBBLLLLL', buf, 0)
        s = ('   ofsI %d magI %u ofsQ %d magQ %u cfgSource %u\n'
             '   reserved0 %u %u %u lowLevCfg %d reserved1 %u %u\n'
             '   postStatus %u reserved2 %u' % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n     cfgSource (%s)' %
                  (index_s(u[4], self.mon_hw2_cfgSource)))

        return s

    mon_hw3_flags = {
        1: "rtcCalib",
        2: "safeBoot",
        4: "xtgalAbsent",
        }

    mon_hw3_pio = {
        0: "peripheral",
        1: "PIO",
        }

    mon_hw3_bank = {
        0: "A",
        1: "B",
        2: "C",
        3: "D",
        4: "E",
        5: "F",
        6: "G",
        7: "H",
        }

    mon_hw3_dir = {
        0: "In",
        1: "Out",
        }

    mon_hw3_value = {
        0: "Lo",
        1: "Hi",
        }

    mon_hw3_mask = {
        0x20: "VPM",
        0x40: "IRQ",
        0x100: "PUp",
        0x200: "PDn",
        }

    def mon_hw3(self, buf):
        """UBX-MON-HW3 decode, HW I/O pin information"""

        # at least protver 27
        if 27 > self.protver:
            self.protver = 27

        u = struct.unpack_from('<BBB', buf, 0)
        s = '   version %u nPins %u flags x%x' % u
        nPins = u[1]
        substr = buf[3:12]
        substr = substr.split(gps.polybytes('\0'))[0]
        s += ' hwVersion %s\n' % gps.polystr(substr)
        u1 = struct.unpack_from('<BBBBBBBBB', buf, 13)
        s += '   reserved1 %02x %02x %02x %02x %02x %02x %02x %02x %02x' % u1

        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n     flags (%s)' %
                  (index_s(u[2], self.mon_hw3_flags)))

        for i in range(22, 22 + (nPins * 6), 6):
            u = struct.unpack_from('<HHBB', buf, i)
            s += ('\n   pinId %4u pinMask %#5x VP %3u reserved2 %u' % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ('\n     pinMask (%s %s %s %s %s)' %
                      (index_s(u[1] & 1, self.mon_hw3_pio),
                       index_s((u[1] >> 1) & 7, self.mon_hw3_bank),
                       index_s((u[1] >> 4) & 1, self.mon_hw3_dir),
                       index_s((u[1] >> 5) & 1, self.mon_hw3_value),
                       flag_s(u[1] & 0xffc0, self.mon_hw3_mask)))

        return s

    def mon_io(self, buf):
        """UBX-MON-IO decode, I/O Subsystem Status"""
        m_len = len(buf)

        s = ''
        for i in range(0, int(m_len / 20)):
            if 0 < i:
                s += "\n"

            u = struct.unpack_from('<LLHHHHL', buf, i * 20)
            s += ('  Port: %u (%s)\n' % (i, index_s(i, self.port_ids)))
            s += ('   rxBytes %u txBytes %u parityErrs %u framingErrs %u\n'
                  '   overrunErrs %u breakCond %u reserved %u' % u)
        return s

    def mon_msgpp(self, buf):
        """UBX-MON-MSGPP decode, Message Parse and Process Status"""

        s = ''
        for i in range(1, 7):
            u = struct.unpack_from('<HHHHHHHH', buf, 0)
            s += " msg%u    %u %u %u %u %u %u %u %u\n" % ((i,) + u)

        u = struct.unpack_from('<LLLLLL', buf, 0)
        s += " skipped %u %u %u %u %u %u" % u
        return s

    mon_patch_act = {
        1: "Active"
        }
    mon_patch_loc = {
        0: "eFuse",
        2: "ROM",
        4: "BBR",
        6: "File System",
        }

    def mon_patch(self, buf):
        """UBX-MON-PATCH decode, Output information about installed patches."""

        # first seen in protver 15
        # len 0 == Poll requestm handled earlier

        u = struct.unpack_from('<HH', buf, 0)
        s = "  version %u nEntries %u" % u

        for i in range(0, u[1]):
            u = struct.unpack_from('<LLLL', buf, 4 + (i * 16))
            s += ("\n   patchInfo x%x comparatorNumber %u patchAddress %u "
                  "patchData %u" % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ('\n    patchInfo (%s, %s)' %
                      (flag_s(u[0] & 0x01, self.mon_patch_act),
                       index_s(u[0] & 0x06, self.mon_patch_loc)))

        return s

    mon_rf_antstat = {
        0: "Init",
        1: "Unk",
        2: "OK",
        3: "Short",
        4: "Open",
        }

    mon_rf_antpwr = {
        0: "Off",
        1: "On",
        2: "Unk",
        }

    def mon_rf(self, buf):
        """UBX-MON-RF decode, RF Information"""

        # first seen in protver 27
        # at least protver 27
        if 27 > self.protver:
            self.protver = 27

        u = struct.unpack_from('<BBBB', buf, 0)
        s = ' version %u nBlocks %u reserved1 %u %u' % u
        for i in range(0, u[1]):
            u = struct.unpack_from('<BBBBLBBBBHHBbBbBBBB', buf, 4 + (24 * i))
            s += ("\n   blockId %u flags x%x antStatus %u antPower %u "
                  "postStatus %u reserved2 %u %u %u %u"
                  "\n    noisePerMS %u agcCnt %u jamInd %u ofsI %d magI %u "
                  "ofsQ %d magQ %u"
                  "\n    reserved3 %u %u %u" % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ('\n     jammingState (%s) antStatus (%s) antPower (%s)' %
                      (index_s(u[1] & 0x03, self.jammingState),
                       index_s(u[2], self.mon_rf_antstat),
                       index_s(u[3], self.mon_rf_antpwr)))
        return s

    def mon_rxbuf(self, buf):
        """UBX-MON-RXBUF decode, Receiver Buffer Status"""

        rxbuf_name = {
           1: " pending   ",
           2: " usage     ",
           3: " peakUsage ",
           }

        s = ''
        u = struct.unpack_from('<HHHHHH', buf, 0)
        s += rxbuf_name[1] + "%u %u %u %u %u %u\n" % u

        for i in range(2, 4):
            u = struct.unpack_from('<BBBBBB', buf, 6 * i)
            s += rxbuf_name[i] + "%u %u %u %u %u %u\n" % u
        return s

    mon_rxr_flags = {
        1: "Awake",
        }

    def mon_rxr(self, buf):
        """UBX-MON-RXBUF decode, Receiver Status Information"""

        # No way to poll

        u = struct.unpack_from('<B', buf, 0)
        s = "  flags: x%x" % u
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n  flags (%s)" %
                  index_s(u[0], self.mon_rxr_flags))

        return s

    mon_smgr_OscState = {
        0: "autonomous operation",
        1: "calibration ongoing",
        2: "oscillator steered by host",
        3: "idle state",
        }

    mon_smgr_Osc = {
        0x10: "OscCalib",
        0x20: "OscDisc",
        }

    mon_smgr_discSrc = {
        0: "internal oscillator",
        1: "GNSS",
        2: "EXTINT0",
        3: "EXTINT1",
        4: "internal oscillator measured by host",
        5: "external oscillator measured by host",
        }

    def mon_smgr(self, buf):
        """UBX-MON-SMGR decode, Synchronization manager status"""

        u = struct.unpack_from('<BBBBLHHBBBB', buf, 0)
        s = (" version %u reserved1 %u %u %u iTOW %u intOsc x%x extOsc x%x\n"
             " discOsc %u gnss x%x extInt0 x%x extInt1 x%x" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n  intOsc (%s) intOscState (%s)"
                  "\n  extOsc(%s) extoscState (%s)"
                  "\n  flags (%s)" %
                  (flag_s(u[3], self.mon_smgr_Osc),
                   index_s(u[3] & 0x0f, self.mon_smgr_OscState),
                   flag_s(u[4], self.mon_smgr_Osc),
                   index_s(u[4] & 0x0f, self.mon_smgr_OscState),
                   index_s(u[5], self.mon_smgr_discSrc)))
        return s

    def mon_span(self, buf):
        """UBX-MON-SPAN decode, Signal characteristics

protVer 34.00 and up
"""

        u = struct.unpack_from('<BBH', buf, 0)
        s = "  version %u numRfBlocks %u reserved0 %u" % u
        for i in range(0, u[1]):
            # skip the 256 bytes of raw data for now...
            u = struct.unpack_from('<LLLBHB', buf, 260 + i * 272)
            s += "\n   span %u res %u center %u pga %u" % u

        return s

    # UBX-CFG-SPT, protVer 15.01 and up, ADR and UDR only

    def mon_txbuf(self, buf):
        """UBX-MON-TXBUF decode, Transmitter Buffer Status"""

        txbuf_name = {
           1: " pending   ",
           2: " usage     ",
           3: " peakUsage ",
           }

        errors = {
           0x40: "mem",
           0x80: "alloc",
           }

        s = ''
        u = struct.unpack_from('<HHHHHH', buf, 0)
        s += txbuf_name[1] + "%u %u %u %u %u %u\n" % u

        for i in range(2, 4):
            u = struct.unpack_from('<BBBBBB', buf, 6 * i)
            s += txbuf_name[i] + "%u %u %u %u %u %u\n" % u

        u = struct.unpack_from('<BBBB', buf, 24)
        s += " tUsage %u tPeakUsage %u errors x%x reserved1 %u" % u
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n  errors (%s) limit (%u)" %
                  (flag_s(u[2], errors), u[2] & 0x3f))

        return s

    def mon_ver(self, buf):
        """UBX-MON-VER decode, Poll Receiver/Software Version"""

        # min len = 40 in u-blox 5/6
        # min len = 70 in u-blox 9
        m_len = len(buf)

        substr = buf.split(gps.polybytes('\0'))[0]
        substr1 = buf[30:39]
        substr1 = substr1.split(gps.polybytes('\0'))[0]
        s = ("  swVersion %s\n"
             "  hwVersion %s" %
             (gps.polystr(substr), gps.polystr(substr1)))

        # extensions??
        protver = None
        num_ext = int((m_len - 40) / 30)
        for i in range(0, num_ext):
            loc = 40 + (i * 30)
            substr = buf[loc:]
            substr = substr.split(gps.polybytes('\0'))[0]
            polystr = gps.polystr(substr)
            s += '\n  extension %s' % polystr
            # is protver? delimiter may be space or equal
            if "PROTVER" == polystr[:7]:
                protver = "%.2f" % float(polystr[8:])

        opts_protver = "%.2f" % self.protver
        if protver and protver != opts_protver:
            s += ('\nWARNING:  protVer is %s, should be %s.'
                  '  Hint: use option "-P %s"' %
                  (opts_protver, protver, protver))
            # prolly too late to fix, try anyway.
            self.protver = float(protver)

        return s

    mon_ids = {0x02: {'str': 'IO', 'dec': mon_io, 'minlen': 20,
                      'name': 'UBX-MON-IO'},
               0x04: {'str': 'VER', 'dec': mon_ver, 'minlen': 40,
                      'name': 'UBX-MON-VER'},
               0x06: {'str': 'MSGPP', 'dec': mon_msgpp, 'minlen': 120,
                      'name': 'UBX-MON-MSGPP'},
               0x07: {'str': 'RXBUF', 'dec': mon_rxbuf, 'minlen': 24,
                      'name': 'UBX-MON-RXBUF'},
               0x08: {'str': 'TXBUF', 'dec': mon_txbuf, 'minlen': 28,
                      'name': 'UBX-MON-TXBUF'},
               0x09: {'str': 'HW', 'dec': mon_hw, 'minlen': 60,
                      'name': 'UBX-MON-HW'},
               0x0b: {'str': 'HW2', 'dec': mon_hw2, 'minlen': 28,
                      'name': 'UBX-MON-HW2'},
               0x21: {'str': 'RXR', 'dec': mon_rxr, 'minlen': 1,
                      'name': 'UBX-MON-RXR'},
               0x27: {'str': 'PATCH', 'dec': mon_patch, 'minlen': 4,
                      'name': 'UBX-MON-PATCH'},
               0x28: {'str': 'GNSS', 'dec': mon_gnss, 'minlen': 8,
                      'name': 'UBX-MON-GNSS'},
               0x2e: {'str': 'SMGR', 'dec': mon_smgr, 'minlen': 16,
                      'name': 'UBX-MON-SMGR'},
               # protVer 19 and up, ADR and UDR only
               0x2f: {'str': 'SPT', 'minlen': 4, 'name': 'UBX-MON-SPT'},
               0x31: {'str': 'SPAN', 'dec': mon_span, 'minlen': 4,
                      'name': 'UBX-MON-SPAN'},
               0x32: {'str': 'BATCH', 'dec': mon_batch, 'minlen': 12,
                      'name': 'UBX-MON-BATCH'},
               0x36: {'str': 'COMMS', 'dec': mon_comms, 'minlen': 8,
                      'name': 'UBX-MON-COMMS'},
               0x37: {'str': 'HW3', 'dec': mon_hw3, 'minlen': 22,
                      'name': 'UBX-MON-HW3'},
               0x38: {'str': 'RF', 'dec': mon_rf, 'minlen': 4,
                      'name': 'UBX-MON-RF'},
               }

    def nav_aopstatus(self, buf):
        """UBX-NAV-AOPSTATUS decode, AssistNow Autonomous Status"""

        u = struct.unpack_from('<LBBLLH', buf, 0)
        s = '  iTOW %u aopCfg %u status %u reserved1 %u %u %u' % u
        if gps.VERB_DECODE <= self.verbosity:
            aopCfg = {1: "useAOP"}
            s += "\n   aopCfg (%s)" % flag_s(u[1], aopCfg)

        return s

    def nav_att(self, buf):
        """UBX-NAV-ATT decode, Attitude Solution"""

        u = struct.unpack_from('<LBHBlllLLL', buf, 0)
        s = ("  iTOW %u version %u reserved1 %u %u\n"
             "  roll %d pitch %d heading %d\n"
             "  accRoll %d accPitch %d accHeading %d" % u)

        return s

    def nav_clock(self, buf):
        """UBX-NAV-CLOCK decode, Clock Solution"""

        u = struct.unpack_from('<LllLL', buf, 0)
        return '  iTOW %u clkB %d clkD %d tAcc %u fAcc %u' % u

    nav_dgps_status = {
        0: "None",
        1: "PR+PRR correction",
        }

    def nav_cov(self, buf):
        """UBX-NAV-COV decode, Covariance matrices

protVer 34 and up
"""

        u = struct.unpack_from('<LBBBLLBffffffffffff', buf, 0)
        return('  iTOW %u version %u posCovValid %u velCovValid %u '
               'reserved0 %u %u %u\n'
               ' posCovNN %f posCovNE  %f posCovND %f\n'
               ' posCovEE %f posCovED  %f posCovDD %f\n'
               ' velCovNN %f velCovNE  %f velCovND %f\n'
               ' velCovEE %f velCovED  %f velCovDD %f\n' % u)

    def nav_dgps(self, buf):
        """UBX-NAV-DGPS decode, DGPS Data used for NAV"""

        # not present in protver 27+
        u = struct.unpack_from('<LlhhBBH', buf, 0)
        s = (' iTOW %u age %d baseID %d basehealth %d numCh %u\n'
             ' status x%x reserved1 %u' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n  status (%s)" %
                  index_s(u[5], self.nav_dgps_status))

        for i in range(0, u[4]):
            u = struct.unpack_from('<BbHff', buf, 16 + i * 12)
            s += ('\n  svid %3u flags x%2x ageC %u prc %f prcc %f' % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ("\n   channel %u dgps %u" %
                      (u[1] & 0x0f, (u[1] >> 4) & 1))

        return s

    def nav_dop(self, buf):
        """UBX-NAV-DOP decode, Dilution of Precision"""

        u = struct.unpack_from('<Lhhhhhhh', buf, 0)
        s = ('  iTOW %u gDOP %u pDOP %u tDOP %u vDOP %u\n'
             '  hDOP %u nDOP %u eDOP %u' % u)
        return s

    # UBX-NAV-EELL, protVer 19.1 and up, ADR only

    def nav_eoe(self, buf):
        """UBX-NAV-EOE decode, End Of Epoch"""

        u = struct.unpack_from('<L', buf, 0)
        return ' iTOW %u' % u

    nav_geofence_state = {
        1: "Inside",
        2: "Outside",
        }

    nav_geofence_status = {
        0: "n/a",
        1: "Active",
        }

    def nav_geofence(self, buf):
        """UBX-NAV-GEOFENCE decode, Geofencing status"""

        u = struct.unpack_from('<LBBBB', buf, 0)
        s = '  iTOW:%u version %u status %u numFences %u combState %u' % u
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    status (%s) combState (%s)" %
                  (index_s(u[2], self.nav_geofence_status),
                   index_s(u[4], self.nav_geofence_state)))

        for i in range(0, u[3]):
            u = struct.unpack_from('<BB', buf, 8 + (i * 2))
            s += '\n  state %u reserved1 %u' % u
            if gps.VERB_DECODE <= self.verbosity:
                s += ("\n    state (%s)" %
                      (index_s(u[0], self.nav_geofence_state)))

        return s

    def nav_hpposecef(self, buf):
        """UBX-NAV-POSECEF decode, High Precision Position Solution in ECEF"""

        u = struct.unpack_from('<BBBBLlllbbbbL', buf, 0)
        return ('  version %u reserved1 %u %u %u iTOW %u\n'
                '  ecef: X %d Y %d Z %d\n'
                '  ecefHP: X %d Y %d Z %d\n'
                '  reserved2 %u pAcc %u' % u)

    def nav_hpposllh(self, buf):
        """UBX-NAV-HPPOSLLH decode, HP Geodetic Position Solution"""

        u = struct.unpack_from('<BBBBLllllbbbbLL', buf, 0)
        return ('  version %u reserved1 %u %u %u iTOW %u\n'
                '  lon %d lat %d height %d hMSL %d\n'
                '  lonHp %d latHp %d heightHp %d hMSLHp %d\n'
                '  hAcc %u vAcc %u' % u)

    def nav_odo(self, buf):
        """UBX-NAV-ODO decode, Odometer Solution"""

        u = struct.unpack_from('<BBBBLLLL', buf, 0)
        return ("  version %u reserved1 %u %u %u iTOW %u\n"
                "  distance %u totalDistance %u distanceStd %u" % u)

    nav_orb_almUsability = {
            0: "Unusable",
            30: "> 30 days",
            31: "Unknown",
        }

    nav_orb_ephUsability = {
            0: "Unusable",
            30: "> 450 mins",
            31: "Unknown",
        }

    nav_orb_ephSource = {
            0: "not available",
            1: "GNSS transmission",
            2: "external aiding",
        }

    nav_orb_type = {
            0: "not available",
            1: "Assist now offline data",
            2: "Assist now autonomous data",
        }

    def nav_orb(self, buf):
        """UBX-NAV-ORB decode, GNSS Orbit Database Info"""

        u = struct.unpack_from('<LBBH', buf, 0)
        s = "  iTOW %u version %u numSv %u reserved1 %u" % u

        for i in range(0, u[2]):
            u = struct.unpack_from('<BBBBBB', buf, 8 + (i * 6))
            s += ("\n   gnssId %u svId %3u svFlag x%02x eph x%02x alm x%02x "
                  "otherOrb x%x" % u)
            if gps.VERB_DECODE <= self.verbosity:
                eph = int(u[3] & 0x1f)
                s1 = index_s(eph, self.nav_orb_ephUsability, nf="")
                if not s1:
                    s1 = "%d to %d mins" % ((eph - 1) * 15, eph * 15)

                alm = int(u[4] & 0x1f)
                s2 = index_s(alm, self.nav_orb_almUsability, nf="")
                if not s2:
                    s2 = "%d to %d days" % (alm - 1, alm)

                other = int(u[5] & 0x1f)
                s3 = index_s(other, self.nav_orb_almUsability, nf="")
                if not s3:
                    s3 = "%d to %d days" % (other - 1, other)

                s += ("\n    (%s:%u) health (%s) visibility (%s)"
                      "\n     ephUsability (%s) ephSource (%s)"
                      "\n     almUsability (%s) almSource (%s)"
                      "\n     anoAopUsability (%s) type (%s)" %
                      (index_s(u[0], self.gnss_id), u[1],
                       index_s(u[2] & 3, self.health),
                       index_s((u[2] >> 2) & 3, self.visibility),
                       s1,
                       index_s(u[3] >> 5, self.nav_orb_ephSource, nf="other"),
                       s2,
                       index_s(u[4] >> 5, self.nav_orb_ephSource, nf="other"),
                       s3,
                       index_s(u[5] >> 5, self.nav_orb_type, nf="other")))

        return s

    def nav_posecef(self, buf):
        """UBX-NAV-POSECEF decode, Position Solution in ECEF"""

        # protVer 4+
        u = struct.unpack_from('<LlllL', buf, 0)
        return '  iTOW %u ecefX %d Y %d Z %d pAcc %u' % u

    def nav_posllh(self, buf):
        """UBX-NAV-POSLLH decode, Geodetic Position Solution"""

        u = struct.unpack_from('<LllllLL', buf, 0)
        return ('  iTOW %u lon %d lat %d height %d\n'
                '  hMSL %d hAcc %u vAcc %u' % u)

    nav_pvt_valid = {
        1: "validDate",
        2: "ValidTime",
        4: "fullyResolved",
        8: "validMag",      # protver 27
        }

    # u-blox TIME ONLY is same as Surveyed
    nav_pvt_fixType = {
        0: 'None',
        1: 'Dead Reckoning',
        2: '2D',
        3: '3D',
        4: 'GPS+DR',
        5: 'Surveyed',
        }

    nav_pvt_flags = {
        1: "gnssFixOK",
        2: "diffSoln",
        0x20: "headVehValid",
        }

    nav_pvt_flags2 = {
        0x20: "confirmedAvai",
        0x40: "confirmedDate",
        0x80: "confirmedTime",
        }

    nav_pvt_psm = {
        0: "Not Active",
        1: "Enabled",
        2: "Acquisition",
        3: "Tracking",
        4: "Power Optimized Tracking",
        5: "Inactive",
        }

    # in UBX-NAV-STATUS since Antaris 4
    carrSoln = {
        0: "None",
        1: "Floating",
        2: "Fixed",
        }

    def nav_pvt(self, buf):
        """UBX-NAV-PVT decode, Navigation Position Velocity Time Solution"""
        m_len = len(buf)

        # 84 bytes long in protver 14.
        # 92 bytes long in protver 15.

        # flags2 is protver 27
        u = struct.unpack_from('<LHBBBBBBLlBBBBllllLLlllllLLHHHH', buf, 0)
        s = ('  iTOW %u time %u/%u/%u %02u:%02u:%02u valid x%x\n'
             '  tAcc %u nano %d fixType %u flags x%x flags2 x%x\n'
             '  numSV %u lon %d lat %d height %d\n'
             '  hMSL %d hAcc %u vAcc %u\n'
             '  velN %d velE %d velD %d gSpeed %d headMot %d\n'
             '  sAcc %u headAcc %u pDOP %u reserved1 %u %u %u' % u)

        if 92 <= m_len:
            # version 15
            u1 = struct.unpack_from('<lhH', buf, 81)
            s += ('\n  headVeh %d magDec %d magAcc %u' % u1)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    valid (%s)"
                  "\n    fixType (%s)"
                  "\n    flags (%s)"
                  "\n    flags2 (%s)"
                  "\n    psmState (%s)"
                  "\n    carrSoln (%s)" %
                  (flag_s(u[7], self.nav_pvt_valid),
                   index_s(u[10], self.nav_pvt_fixType),
                   flag_s(u[11], self.nav_pvt_flags),
                   flag_s(u[12], self.nav_pvt_flags2),
                   index_s((u[11] >> 2) & 0x0f, self.nav_pvt_psm),
                   index_s((u[11] >> 6) & 0x03, self.carrSoln)))
        return s

    nav_relposned_flags = {
        1: "gnssFixOK",
        2: "diffSoln",
        4: "relPosValid",
        0x20: "isMoving",             # protVer 20.3+
        0x40: "refPosMiss",           # protVer 20.3+
        0x80: "refObsMiss",           # protVer 20.3+
        0x100: "relPosHeadingValid",  # protVer 27.11+
        0x200: "relPosNormalized",    # protVer 27.11+
        }

    def nav_relposned(self, buf):
        """UBX-NAV-RELPOSNED decode
Relative Positioning Information in NED frame.
protVer 20+ is 40 bytes
protVer 27.11+ is 64 bytes, and things reordered, so not upward compatible
High Precision GNSS products only."""

        m_len = len(buf)

        # common part
        u = struct.unpack_from('<BBHLlll', buf, 0)
        s = ('  version %u reserved1 %u refStationId %u iTOW %u\n'
             '  relPosN %d relPosE %d relPosD %d\n' % u)

        if (1 == u[0] and 64 <= m_len):
            # valid version 1 packet, newer u-blox 9
            u1 = struct.unpack_from('<llLbbbbLLLLLLL', buf, 20)
            s += ('  relLength %d relHeading %d reserved2 %u\n'
                  '  relPosHPN %d relPosHPE %d relPosHPD %d '
                  'relPosHPLength %d\n'
                  '  accN %u accE %u accD %u accLength %u accHeading %u\n'
                  '  reserved3 %u flags x%x' % u1)
            flags = u1[13]
        elif (0 == u[0] and 40 <= m_len):
            # valid version 0 packet, u-blox 8, and some u-blox 9
            u1 = struct.unpack_from('<bbbbLLLLLLL', buf, 20)
            s += ('  relPosHPN %d relPosHPE %d relPosHPD %d reserved2 %u\n'
                  '  accN %u accE %u accD %u flags x%x' % u1)
            flags = u1[7]
        else:
            # WTF?
            return "  Bad Length %d version %u combination" % (m_len, u[0])

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    flags (%s)\n"
                  "    carrSoln (%s)" %
                  (flag_s(flags, self.nav_relposned_flags),
                   index_s((flags >> 3) & 0x03, self.carrSoln)))
        return s

    def nav_resetodo(self, buf):
        """UBX-NAV-RESETODO decode, reset odometer"""

        m_len = len(buf)
        if 0 == m_len:
            s = " reset request"
        else:
            s = " unexpected data"
        return s

    qualityInd = {
        0: "None",
        1: "Searching",
        2: "Acquired",
        3: "Detected",
        4: "Code and time locked",
        5: "Code, carrier and time locked",
        6: "Code, carrier and time locked",
        7: "Code, carrier and time locked",
        }

    health = {
        0: "Unknown",
        1: "Healthy",
        2: "Unhealthy",
        }

    visibility = {
        1: "below horizon",
        2: "above horizon",
        3: "above elevation mask",
        }

    nav_sat_orbit = {
        0: "None",
        1: "Ephemeris",
        2: "Almanac",
        3: "AssistNow Offline",
        4: "AssistNow Autonomous",
        5: "Other",
        6: "Other",
        7: "Other",
        }

    nav_sat_flags = {
        8: "svUsed",
        0x40: "diffCorr",
        0x80: "smoothed",
        0x800: "ephAvail",
        0x1000: "almAvail",
        0x2000: "anoAvail",
        0x4000: "aopAvail",
        0x10000: "sbasCorrUsed",
        0x20000: "rtcmCorrUsed",
        0x40000: "slasCorrUsed",
        0x100000: "prCorrUsed",
        0x200000: "crCorrUsed",
        0x400000: "doCorrUsed",
        }

    def nav_sat(self, buf):
        """UBX-NAV-SAT decode"""

        u = struct.unpack_from('<LBBBB', buf, 0)
        s = '  iTOW %u version %u numSvs %u reserved1 %u %u' % u

        for i in range(0, u[2]):
            u = struct.unpack_from('<BBBbhhL', buf, 8 + (i * 12))
            s += ('\n   gnssId %u svid %3u cno %2u elev %3d azim %3d prRes %6d'
                  ' flags x%x' % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ("\n     flags (%s)"
                      "\n     qualityInd x%x (%s) health (%s)"
                      "\n     orbitSource (%s)" %
                      (flag_s(u[6], self.nav_sat_flags),
                       u[6] & 7, index_s(u[6] & 7, self.qualityInd),
                       index_s((u[6] >> 4) & 3, self.health),
                       index_s((u[6] >> 8) & 7, self.nav_sat_orbit)))

        return s

    nav_sbas_mode = {
        0: "Disabled",
        1: "Enabled Integrity",
        2: "Enabled Testmode",
        }

    # sometimes U1 or I1, 255 or -1 == Unknown
    nav_sbas_sys = {
        0: "WAAS",
        1: "EGNOS",
        2: "MSAS",
        3: "GAGAN",
        4: "SDCM",      # per ICAO Annex 10, v1, Table B-27
        16: "GPS",
        }

    nav_sbas_service = {
        1: "Ranging",
        2: "Corrections",
        4: "Integrity",
        8: "Testmode",
        }

    def nav_sbas(self, buf):
        """UBX-NAV-SBAS decode, SBAS Status Data"""

        # present in protver 10+ (Antaris4 to ZOE-M8B
        # undocumented, but present in protver 27+
        # undocumented, but present in protver 32, NEO-M9N

        u = struct.unpack_from('<LBBbBBBBB', buf, 0)
        s = (" iTOW %d geo %u mode x%x sys %d service x%x cnt %u "
             "reserved0 %u %u %u" % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n    mode (%s) sys (%s)"
                  "\n    service (%s)" %
                  (index_s(u[2], self.nav_sbas_mode),
                   index_s(u[3], self.nav_sbas_sys),
                   flag_s(u[4], self.nav_sbas_service)))

        for i in range(0, u[5]):
            u = struct.unpack_from('<BBBBBBhHh', buf, 12 + (i * 12))
            s += ("\n  svid %3d flags x%04x udre x%02x svSys %3d svService %2d"
                  " reserved2 %u"
                  "\n   prc %3d reserved3 %u ic %3d" % u)
            if gps.VERB_DECODE <= self.verbosity:
                # where are flags and udre defined??
                s += ("\n   svSys (%s) svService (%s)" %
                      (index_s(u[3], self.nav_sbas_sys),
                       flag_s(u[4], self.nav_sbas_service)))

        return s

    nav_sig_corrSource = {
        0: "None",
        1: "SBAS",
        2: "BeiDou",
        3: "RTCM2",
        4: "RTCM3 OSR",
        5: "RTCM3 SSR",
        6: "QZSS SLAS",
        }

    nav_sig_ionoModel = {
        0: "None",
        1: "Klobuchar over GPS",
        2: "SBAS",
        3: "Klobuchar over BeiDou",
        8: "Dual Frequency obs",
        }

    nav_sig_sigFlags = {
        4: "prSmoothed",
        8: "prUsed",
        0x10: "crUsed",
        0x20: "doUsed",
        0x40: "prCorrUsed",
        0x80: "crCorrUsed",
        0x100: "doCorrUsed",
        }

    def nav_sig(self, buf):
        """UBX-NAV-SIG decode, Signal Information"""

        u = struct.unpack_from('<LBBH', buf, 0)
        s = '  iTOW %u version %u numSigs %u reserved1 %u' % u

        for i in range(0, u[2]):
            u = struct.unpack_from('<BBBBhBBBBHL', buf, 8 + (i * 16))
            s += ('\n   gnssId %u svId %u sigId %u freqId %u prRes %d cno %u '
                  'qualityInd %u\n'
                  '    corrSource %u ionoModel %u sigFlags %#x reserved2 %u' %
                  u)

            if gps.VERB_DECODE <= self.verbosity:
                s += ("\n      (%s) corrSource (%s)"
                      "\n      qualityInd (%s)"
                      "\n      ionoModel (%s) health (%s)"
                      "\n      sigFlags (%s)" %
                      (self.gnss_s(u[0], u[1], u[2]),
                       index_s(u[7], self.nav_sig_corrSource),
                       index_s(u[6], self.qualityInd),
                       index_s(u[8], self.nav_sig_ionoModel),
                       index_s(u[9] & 3, self.health),
                       flag_s(u[9], self.nav_sig_sigFlags)))
        return s

    nav_slas_flags = {
        1: "gmsAvailable",
        2: "qzssSvAvailable",
        4: "testMode",
        }

    def nav_slas(self, buf):
        """UBX-NAV-SLAS decode, QZSS L1S SLAS Status Data"""

        u = struct.unpack_from('<LBBBBllBBBB', buf, 0)
        s = ('  iTOW %u version %u reserved1 %u %u %u'
             '  gmsLon %d gmsLon %d gmsCode %u qzssSvId %u'
             '  serviceFlags x%x cnt %d' % u)

        for i in range(0, u[8]):
            u = struct.unpack_from('<BBLh', buf, 20 + (i * 8))
            s += '\n   gnssId %u svId %u reserved23 %u prc %d ' % u

            if gps.VERB_DECODE <= self.verbosity:
                s += ("\n     flags (%s)" %
                      (flag_s(u[3], self.nav_slas_flags)))
        return s

    nav_sol_flags = {
        1: "GPSfixOK",
        2: "DiffSoln",
        4: "WKNSET",
        8: "TOWSET",
        }

    def nav_sol(self, buf):
        """UBX-NAV-SOL decode, Navigation Solution Information"""

        # removed from protVer 34 and up
        # deprecated by u-blox

        u = struct.unpack_from('<LlhBBlllLlllLHBBL', buf, 0)
        s = ('  iTOW %u fTOW %d week %d gpsFix %u flags x%x\n'
             '  ECEF X %d Y %d Z %d pAcc %u\n'
             '  VECEF X %d Y %d Z %d sAcc %u\n'
             '  pDOP %u reserved1 %u numSV %u reserved2 %u' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   gpsfix (%s)"
                  "\n   flags (%s)" %
                  (index_s(u[3], self.nav_pvt_fixType),
                   flag_s(u[4], self.nav_sol_flags)))

        return s

    nav_status_fixStat = {
        1: "diffCorr",
        2: "carrSolnValid",
        }

    nav_status_mapMatching = {
        0: "None",
        0x40: "Too old",
        0x80: "Valid10",
        0xC0: "Valid11",
        }

    nav_status_psmState = {
        0: "Acquisition",
        1: "Tracking",
        2: "Power Optimized Tracking",
        3: "Inactive",
        }

    nav_status_spoofDetState = {
        0: "Deactivated",
        1: "None indicated",
        2: "Indicated",
        3: "Multiple Indicated",
        }

    def nav_status(self, buf):
        """UBX-NAV-STATUS decode"""

        u = struct.unpack_from('<LBBBBLL', buf, 0)
        s = ('  iTOW %d gpsFix %d flags %#x fixStat %#x flags2 %#x\n'
             '  ttff %d, msss %d' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   gpsfix (%s)"
                  "\n   flags (%s)"
                  "\n   fixStat (%s) mapMatching (%s)"
                  "\n   flags2 (psmState %s spoofDetState %s carrSoln %s)" %
                  (index_s(u[1], self.nav_pvt_fixType),
                   flag_s(u[2], self.nav_sol_flags),
                   flag_s(0x3f & u[3], self.nav_status_fixStat),
                   index_s(0xc0 & u[3], self.nav_status_mapMatching),
                   index_s(3 & u[4], self.nav_status_psmState),
                   index_s(3 & (u[4] >> 3), self.nav_status_spoofDetState),
                   index_s(3 & (u[4] >> 6), self.carrSoln)))
        return s

    def nav_svin(self, buf):
        """UBX-NAV-SVIN decode, Survey-in data"""

        # in M8 HPG only
        u = struct.unpack_from('<BBBBLLlllbbbBLLBB', buf, 0)
        return ('  version %u reserved1[%u %u %u] iTOW %u dur %u\n'
                '  meanX %d meanY %d meanZ %d\n'
                '  meanXHP %d meanYHP %d meanZHP %d reserved2 %u meanAcc %u\n'
                '  obs %u valid %u active %u' % u)

    nav_svinfo_gflags = {
        0: 'Antaris, Antaris 4',
        1: 'u-blox 5',
        2: 'u-blox 6',
        3: 'u-blox 7',
        4: 'u-blox 8/M8',
        }

    nav_svinfo_flags = {
        1: 'svUsed',
        2: 'diffCorr',
        4: 'orbitAvail',
        8: 'orbitEph',
        0x10: 'unhealthy',
        0x20: 'orbitAlm',
        0x40: 'orbitAop',
        0x80: 'smoothed',
        }

    nav_svinfo_quality = {
        0: 'no signal',
        1: 'searching signal',
        2: 'signal acquired',
        3: 'signal detected but unusable',
        4: 'code locked, time synced',
        5: 'code and carrier locked, time synced',
        6: 'code and carrier locked, time synced',
        7: 'code and carrier locked, time synced',
        }

    def nav_svinfo(self, buf):
        """UBX-NAV-SVINFO decode"""

        # removed from protVer 34 and up
        # in M8 Timing and FTS only
        m_len = len(buf)

        u = struct.unpack_from('<LbbH', buf, 0)
        s = ' iTOW:%d numCh %d globalFlags %d reserved1 x%x' % u
        if gps.VERB_DECODE <= self.verbosity:
            s += '\n  globalFlags (%s)' % index_s(u[2], self.nav_svinfo_gflags)

        m_len -= 8
        i = 0
        while 0 < m_len:
            u = struct.unpack_from('<BBBBBbhl', buf, 8 + i * 12)
            s += ('\n  chn %3d svid %3d flags %#0.2x quality %u cno %2d'
                  ' elev %3d azim %3d prRes %6d' % u)
            if gps.VERB_DECODE <= self.verbosity:
                s += ('\n   flags (%s)'
                      '\n   quality (%s)' %
                      (flag_s(u[2], self.nav_svinfo_flags),
                       index_s(u[3], self.nav_svinfo_quality)))
            m_len -= 12
            i += 1

        return s

    nav_time_valid = {
        1: "towValid",
        2: "weekValid",
        4: "leapValid",
        }

    def nav_timebds(self, buf):
        """UBX-NAV-TIMEBDS decode"""

        u = struct.unpack_from('<LLlhbBL', buf, 0)
        s = ("  iTOW %d SOW %d fSOW %d week %d leapS %d\n"
             "  Valid %#x tAcc %d" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   valid (%s)" %
                  (flag_s(u[5], self.nav_time_valid)))
        return s

    def nav_timegal(self, buf):
        """UBX-NAV-TIMEGAL decode"""

        u = struct.unpack_from('<LLlhbBL', buf, 0)
        s = ("  iTOW %d galTOW %d fGalTow %d galWno %d leapS %d\n"
             "  Valid x%x, tAcc %d" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   valid (%s)" %
                  (flag_s(u[5], self.nav_time_valid)))
        return s

    def nav_timeglo(self, buf):
        """UBX-NAV-TIMEGLO decode"""

        u = struct.unpack_from('<LLlhbBL', buf, 0)
        s = ("  iTOW %d TOD %d fTOD %d Nt %d  N4 %d\n"
             "  Valid x%x tAcc %d" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   valid (%s)" %
                  (flag_s(u[5], self.nav_time_valid)))
        return s

    def nav_timegps(self, buf):
        """UBX-NAV-TIMEGPS decode"""

        u = struct.unpack_from('<LlhbBL', buf, 0)
        s = "  iTOW %u fTOW %u week %d leapS %d valid x%x tAcc %d" % u

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   valid (%s)" %
                  (flag_s(u[4], self.nav_time_valid)))
        return s

    nav_timels_src = {
        0: "Default",
        1: "GPS/GLONASS derived",
        2: "GPS",
        3: "SBAS",
        4: "BeiDou",
        5: "Galileo",
        6: "Aided data",
        7: "Configured",
        }

    nav_timels_src1 = {
        0: "None",
        2: "GPS",
        3: "SBAS",
        4: "BeiDou",
        5: "Galileo",
        6: "GLONASS",
        }

    nav_timels_valid = {
        1: "validCurrLs",
        2: "validTimeToLsEvent",
        }

    def nav_timels(self, buf):
        """UBX-NAV-TIMELS decode, Leap second event information"""

        u = struct.unpack_from('<LBBBBBbBblHHBBBB', buf, 0)
        s = ('  iTOW %u version %u reserved2 %u %u %u srcOfCurrLs %u\n'
             '  currLs %d srcOfLsChange %u lsChange %d timeToLsEvent %d\n'
             '  dateOfLsGpsWn %u dateOfLsGpsDn %u reserved2 %u %u %u\n'
             '  valid x%x' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   srcOfCurrLs (%s) srcOfLsChange (%s)"
                  "\n   valid (%s)" %
                  (index_s(u[5], self.nav_timels_src),
                   index_s(u[7], self.nav_timels_src1),
                   flag_s(u[15], self.nav_timels_valid)))
        return s

    nav_timeqzss_valid = {
        1: "qzssTowValid",
        2: "qzssWnoValid",
        4: "leapSValid",
        }

    def nav_timeqzss(self, buf):
        """UBX-NAV-TIMEQZSS decode, QZSS time solution

protVer 34 and up
"""

        u = struct.unpack_from('<LLlhbBL', buf, 0)
        s = ("  iTOW %u qzssTow %u fQzssTow %d qzssWno %d leapS %d\n"
             "  valid x%x tAcc %d" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   valid (%s)" %
                  (flag_s(u[5], self.nav_timeqzss_valid)))
        return s

    nav_timeutc_valid = {
        1: "validTOW",
        2: "validWKN",
        4: "validUTC",
        }

    def nav_timeutc(self, buf):
        """UBX-NAV-TIMEUTC decode"""

        u = struct.unpack_from('<LLlHbbbbbB', buf, 0)
        s = ("  iTOW %u tAcc %u nano %d Time  %4u/%02u/%02u %02u:%02u:%02u\n"
             "  valid x%x" % u)

        if gps.VERB_DECODE <= self.verbosity:
            s += ("\n   valid (%s) utcStandard (%s)" %
                  (flag_s(u[9], self.nav_timeutc_valid),
                   index_s(u[9] >> 4, self.utc_std)))
        return s

    def nav_velecef(self, buf):
        """UBX-NAV-VELECEF decode"""

        # protVer 4+
        u = struct.unpack_from('<LlllL', buf, 0)
        return '  iTOW %d ecef: VX %d VY %d VZ %d vAcc:%u' % u

    def nav_velned(self, buf):
        """UBX-NAV-VELNED decode."""

        # protVer 15+
        u = struct.unpack_from('<LlllLLlLL', buf, 0)
        return ('  iTOW %u vel: N %d E %d D %d speed %u\n'
                '  gspeed %u heading %d sAcc %u cAcc %u' % u)

    # Broadcom calls this BRM-PVT-
    nav_ids = {0x01: {'str': 'POSECEF', 'dec': nav_posecef, 'minlen': 20,
                      'name': 'UBX-NAV-POSECEF'},
               0x02: {'str': 'POSLLH', 'dec': nav_posllh, 'minlen': 20,
                      'name': 'UBX-NAV-POSLLH'},
               0x03: {'str': 'STATUS', 'dec': nav_status, 'minlen': 16,
                      'name': 'UBX-NAV-STATUS'},
               # Broadcom calls this BRM-PVT-DOP
               0x04: {'str': 'DOP', 'dec': nav_dop, 'minlen': 18,
                      'name': 'UBX-NAV-DOP'},
               0x05: {'str': 'ATT', 'dec': nav_att, 'minlen': 32,
                      'name': 'UBX-NAV-ATT'},
               0x06: {'str': 'SOL', 'dec': nav_sol, 'minlen': 52,
                      'name': 'UBX-NAV-SOL'},
               # Broadcom calls this BRM-PVT-PVT
               0x07: {'str': 'PVT', 'dec': nav_pvt, 'minlen': 84,
                      'name': 'UBX-NAV-PVT'},
               # Broadcom calls this BRM-PVT-ACC_DIST
               0x09: {'str': 'ODO', 'dec': nav_odo, 'minlen': 20,
                      'name': 'UBX-NAV-ODO'},
               # Broadcom calls this BRM-PVT-RESET_ACC_DIST
               0x10: {'str': 'RESETODO', 'dec': nav_resetodo, 'minlen': 0,
                      'name': 'UBX-NAV-RESETODO'},
               0x11: {'str': 'VELECEF', 'dec': nav_velecef, 'minlen': 20,
                      'name': 'UBX-NAV-VELECEF'},
               0x12: {'str': 'VELNED', 'dec': nav_velned, 'minlen': 36,
                      'name': 'UBX-NAV-VELNED'},
               0x13: {'str': 'HPPOSECEF', 'dec': nav_hpposecef, 'minlen': 28,
                      'name': 'UBX-NAV-HPPOSECEF'},
               0x14: {'str': 'HPPOSLLH', 'dec': nav_hpposllh, 'minlen': 36,
                      'name': 'UBX-NAV-HPPOSLLH'},
               0x20: {'str': 'TIMEGPS', 'dec': nav_timegps, 'minlen': 16,
                      'name': 'UBX-NAV-TIMEGPS'},
               0x21: {'str': 'TIMEUTC', 'dec': nav_timeutc, 'minlen': 20,
                      'name': 'UBX-NAV-TIMEUTC'},
               0x22: {'str': 'CLOCK', 'dec': nav_clock, 'minlen': 20,
                      'name': 'UBX-NAV-CLOCK'},
               0x23: {'str': 'TIMEGLO', 'dec': nav_timeglo, 'minlen': 20,
                      'name': 'UBX-NAV-TIMEGLO'},
               0x24: {'str': 'TIMEBDS', 'dec': nav_timebds, 'minlen': 20,
                      'name': 'UBX-NAV-TIMEBDS'},
               0x25: {'str': 'TIMEGAL', 'dec': nav_timegal, 'minlen': 20,
                      'name': 'UBX-NAV-TIMEGAL'},
               0x26: {'str': 'TIMELS', 'dec': nav_timels, 'minlen': 24,
                      'name': 'UBX-NAV-TIMELS'},
               0x27: {'str': 'TIMEQZSS', 'dec': nav_timeqzss, 'minlen': 20,
                      'name': 'UBX-NAV-QZSS'},
               0x30: {'str': 'SVINFO', 'dec': nav_svinfo, 'minlen': 8,
                      'name': 'UBX-NAV-SVINFO'},
               0x31: {'str': 'DGPS', 'dec': nav_dgps, 'minlen': 16,
                      'name': 'UBX-NAV-DGPS'},
               0x32: {'str': 'SBAS', 'dec': nav_sbas, 'minlen': 12,
                      'name': 'UBX-NAV-SBAS'},
               0x34: {'str': 'ORB', 'dec': nav_orb, 'minlen': 8,
                      'name': 'UBX-NAV-ORB'},
               # Broadcom calls this BRM-PVT-SAT
               0x35: {'str': 'SAT', 'dec': nav_sat, 'minlen': 8,
                      'name': 'UBX-NAV-SAT'},
               0x36: {'str': 'COV', 'dec': nav_cov, 'minlen': 64,
                      'name': 'UBX-NAV-COV'},
               0x39: {'str': 'GEOFENCE', 'dec': nav_geofence, 'minlen': 8,
                      'name': 'UBX-NAV-GEOFENCE'},
               0x3B: {'str': 'SVIN', 'dec': nav_svin, 'minlen': 40,
                      'name': 'UBX-NAV-SVIN'},
               # M8P length = 40, M9P length = 64
               0x3C: {'str': 'RELPOSNED', 'dec': nav_relposned, 'minlen': 40,
                      'name': 'UBX-NAV-RELPOSNED'},
               # protVer 19.1 and up, ADR only
               0x3d: {'str': 'EELL', 'minlen': 16, 'name': 'UBX-NAV-EELL'},
               # deprecated in u-blox 6, SFDR only
               0x40: {'str': 'EKFSTATUS', 'minlen': 36,
                      'name': 'UBX-NAV-EKFSTATUS'},
               0x42: {'str': 'SLAS', 'dec': nav_slas, 'minlen': 20,
                      'name': 'UBX-NAV-SLAS'},
               0x43: {'str': 'SIG', 'dec': nav_sig, 'minlen': 8,
                      'name': 'UBX-NAV-SIG'},
               0x60: {'str': 'AOPSTATUS', 'dec': nav_aopstatus, 'minlen': 16,
                      'name': 'UBX-NAV-AOPSTATUS'},
               # Broadcom calls this BRM-PVT-EOE
               0x61: {'str': 'EOE', 'dec': nav_eoe, 'minlen': 4,
                      'name': 'UBX-NAV-EOE'},
               }

    # used for RTCM3 rate config
    rtcm_ids = {5: {'str': '1005'},
                0x4a: {'str': '1074'},
                0x4d: {'str': '1077'},
                0x54: {'str': '1084'},
                0x57: {'str': '1087'},
                0x61: {'str': '1097'},
                0x7c: {'str': '1124'},
                0x7f: {'str': '1127'},
                0xe6: {'str': '1230'},
                0xfd: {'str': '4072-1'},
                0xfe: {'str': '4072-0'},
                }

    # used for NMEA rate config
    nmea_ids = {0: {'str': 'GGA'},
                1: {'str': 'GLL'},
                2: {'str': 'GSA'},
                3: {'str': 'GSV'},
                4: {'str': 'RMC'},
                5: {'str': 'VTG'},
                6: {'str': 'GRS'},
                7: {'str': 'GST'},
                8: {'str': 'ZDA'},
                9: {'str': 'GBS'},
                0x0a: {'str': 'DTM'},
                0x0d: {'str': 'GNS'},
                0x0f: {'str': 'VLW'},
                0x40: {'str': 'GPQ'},
                0x41: {'str': 'TXT'},
                0x42: {'str': 'GNQ'},
                0x43: {'str': 'GLQ'},
                0x44: {'str': 'GBQ'},
                0x45: {'str': 'GAQ'},
                }

    def rxm_imes(self, buf):
        """UBX-RXM-IMES decode, Indoor Messaging System Information"""

        # not supported in M1
        u = struct.unpack_from('<BBH', buf, 0)
        s = ' numTx %u version %u reserved1 %u' % u

        for i in range(0, u[0]):
            u = struct.unpack_from('<BBHBBHlLLLllLLL', buf, 4 + (i * 44))
            s += ('\n  reserved %u txId %u reserved3 %u %u cno %u reserved4 %u'
                  '\n doppler %d position1_1 x%x position1_2 x%x'
                  '\n position2_1 x%x lat %d lon %d shortIdFrame x%x'
                  '\n mediumIdLSB %u mediumId_2 x%x' % u)

        return s

    def rxm_measx(self, buf):
        """UBX-RXM-RAW decode"""
        m_len = len(buf)

        u = struct.unpack_from('<BBBBLLLLLHHHHHBBLL', buf, 0)
        s = (' version %u reserved1 %u %u %u gpsTOW %u gloTOW %u\n'
             ' bdsTOW %u reserved2 %u qzssTOW %u gpsTOWacc %u\n'
             ' gloTOWacc %u bdsTOWacc %u reserved3 %u qzssTOWacc %u\n'
             ' numSV %u flags %#x reserved4 %u %u' % u)

        m_len -= 44
        i = 0
        while 0 < m_len:
            u = struct.unpack_from('<BBBBllHHLBBH', buf, 44 + i * 24)
            s += ('\n  gnssId %u svId %u cNo %u mpathIndic %u DopplerMS %d\n'
                  '    dopplerHz %d wholeChips %u fracChips %u codephase %u\n'
                  '    intCodePhase %u pseudoRangeRMSErr %u reserved5 %u' % u)
            m_len -= 24
            i += 1

        return s

    rxm_pmreq_flags = {
        1: "backup",
        2: "force",
        }

    rxm_pmreq_wakeup = {
        4: "uartrx",
        0x10: "extint0",
        0x20: "extint1",
        0x40: "spics",
        }

    def rxm_pmreq(self, buf):
        """UBX-RXM-PMREQ decode Power management request

protVer 34 and up
"""

        m_len = len(buf)
        if 4 == m_len:
            # short poll
            u = struct.unpack_from('<Ll', buf, 0)
            s = ' duration %u flags %u' % u
            if gps.VERB_DECODE < self.verbosity:
                s += '\n flags (%s)' % flag_s(u[1], self.rxm_pmreq_flags)
        elif 16 == m_len:
            # long  poll
            u = struct.unpack_from('<BBHLLL', buf, 0)
            s = (' version %u reserved %u %u duration %u flags x%x\n'
                 ' wakeupSources x%x' % u)
            if gps.VERB_DECODE < self.verbosity:
                s += ('\n flags (%s) wakeupSources (s)' %
                      (flag_s(u[4], self.rxm_pmreq_flags),
                       flag_s(u[5], self.rxm_pmreq_wakeup)))
        else:
            s = "  Bad Length %s" % m_len
        return s

    def rxm_raw(self, buf):
        """UBX-RXM-RAW decode"""
        m_len = len(buf)

        u = struct.unpack_from('<lhBB', buf, 0)
        s = ' iTOW %d weeks %d numSV %u res1 %u' % u

        m_len -= 8
        i = 0
        while 0 < m_len:
            u = struct.unpack_from('<ddfBbbB', buf, 8 + i * 24)
            s += ('\n  cpMes %f prMes %f doMes %f sv %d mesQI %d\n'
                  '     eno %d lli %d' % u)
            m_len -= 24
            i += 1

        return s

    rxm_rawx_recs = {
        1: "leapSec",
        2: "clkReset",
        }

    def rxm_rawx(self, buf):
        """UBX-RXM-RAWX decode"""
        m_len = len(buf)

        # version not here before protver 18, I hope it is zero.
        u = struct.unpack_from('<dHbBBBBB', buf, 0)
        s = (' rcvTow %.3f week %u leapS %d numMeas %u recStat %#x'
             ' version %u\n'
             ' reserved1[2] %#x %#x\n  recStat (' % u)
        s += flag_s(u[4], self.rxm_rawx_recs) + ')'

        m_len -= 16
        i = 0
        while 0 < m_len:
            u = struct.unpack_from('<ddfBBBBHBBBBB', buf, 16 + i * 32)
            s += ('\n  prmes %.3f cpMes %.3f doMes %f\n'
                  '   gnssId %u svId %u sigId %u freqId %u locktime %u '
                  'cno %u\n'
                  '   prStdev %u cpStdev %u doStdev %u trkStat %u' % u)

            if gps.VERB_DECODE < self.verbosity:
                s += '\n      (%s)' % self.gnss_s(u[3], u[4], u[5])

            m_len -= 32
            i += 1
        return s

    def rxm_rlm(self, buf):
        """UBX-RXM-RLM decode, Galileo SAR RLM report"""
        m_len = len(buf)

        # common to Short-RLM and Long-RLM report
        u = struct.unpack_from('<BBBBLLB', buf, 0)
        s = ("  version %u type %u svId %u reserved1 %u beacon x%x %x "
             " message %u" % u)
        if 16 == m_len:
            # Short-RLM report
            u = struct.unpack_from('<BBB', buf, 13)
            s += "\n  params %u %u reserved2 %u" % u
        elif 28 == m_len:
            # Long-RLM report
            u = struct.unpack_from('<BBBBBBBBBBBBBBB', buf, 13)
            s += ("\n  params %u %u %u %u %u %u %u %u %u %u %u %u"
                  "\n  reserved2 %u %u %u" % u)

        return s

    rxm_rtcm_flags = {
        1: "crcFailed",
        }

    def rxm_rtcm(self, buf):
        """UBX-RXM-RTCM decode, RTCM Input Status"""

        # present in some u-blox 8 and 9, protVer 20+
        # undocumented, but in NEO-M9N, protVer 32
        u = struct.unpack_from('<BBHHH', buf, 0)
        s = "  version %u flags x%x subtype %u refstation %u msgtype %u" % u
        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n    flags (%s)' % flag_s(u[1], self.rxm_rtcm_flags))
        return s

    def rxm_sfrb(self, buf):
        """UBX-RXM-SFRB decode, Subframe Buffer"""

        u = struct.unpack_from('<BBLLLLLLLLLL', buf, 0)
        s = ('  chn %d s svid %3d\n'
             '  dwrd %08x %08x %08x %08x %08x\n'
             '       %08x %08x %08x %08x %08x' % u)

        return s

    # decode GPS subframe 5, pages 1 to 24,
    # and subframe 4, pages 2 to 5, and 7 to 10
    def almanac(self, words):
        """Decode GPS Almanac"""

        # [1] Section 20.3.3.5, Figure 20-1 Sheet 4, and Table 20-VI.
        # Current almanac: https://www.navcen.uscg.gov/?pageName=gpsAlmanacs

        # e = Eccentricity
        # toa = Almanac reference time
        # deltai =
        # Omegadot = Rate of Right Ascension
        # SVH = SV Health
        # sqrtA = Square Root of the Semi-Major Axis
        # Omega0 = Longitude of Ascending Node of Orbit Plane at Weekly Epoch
        # omega = Argument of Perigee
        # M0 = Mean Anomaly at Reference Time
        # af0 = SV Clock Bias Correction Coefficient
        # af1 = SV Clock Drift Correction Coefficient
        s = "    Almanac"
        s += ("\n    e %e toa %u deltai %e Omegadot %e"
              "\n    SVH x%x sqrtA %.6f Omega0 %e omega %e"
              "\n    M0 %e af0 %e af1 %e" %
              (unpack_u16(words[2], 6) * (2 ** -21),
               unpack_u8(words[3], 22) * (2 ** 12),
               unpack_s16(words[3], 6) * (2 ** -19),
               unpack_s16(words[4], 14) * (2 ** -38),
               unpack_u8(words[4], 6),
               unpack_u24(words[5], 6) * (2 ** -11),     # sqrtA
               unpack_s24(words[6], 6) * (2 ** -23),
               unpack_s24(words[7], 6) * (2 ** -23),
               unpack_s24(words[8], 6) * (2 ** -23),     # M0
               unpack_s11s(words[9]) * (2 ** -20),
               unpack_s11(words[9], 11) * (2 ** -38)))
        return s

    def _decode_sfrbx_bds(self, words):
        """Decode UBX-RXM-SFRBX BeiDou frames"""
        # See u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf
        # Section 10.4 BeiDou
        # gotta decode the u-blox munging and the BeiDou packing...
        # http://en.beidou.gov.cn/SYSTEMS/ICD/
        # BeiDou Interface Control Document v1.0
        Rev = (words[0] >> 15) & 0x0f
        FraID = (words[0] >> 12) & 7

        # unmung u-blox 30 bit words in 32 bits
        page = 0
        for i in range(0, 10):
            page <<= 30
            page |= words[i] & 0x03fffffff

        # sanity check
        if (FraID != ((page >> 282) & 7)):
            s = ("\n    BDS: Math Error! %u != %u"
                 "\n      page %u" %
                 (FraID, (page >> 282) & 7, page))
            return s

        # common to all pages
        SOW = ((page >> 274) & 0x0f) << 12
        SOW |= (page >> 258) & 0x0fff
        s = ("\n    BDS: Rev %u FraID %i SOW %u" %
             (Rev, FraID, SOW))
        if 1 == FraID:
            SatH1 = (page >> 257) & 1
            AODC = (page >> 252) & 0x01f
            URAI = (page >> 248) & 0x0f
            WN = (page >> 227) & 0x01fff
            t0c = ((page >> 218) & 0x01ff) << 8
            t0c |= (page >> 202) & 0x0ff
            TGD1 = (page >> 192) & 0x3ff
            TGD2 = ((page >> 188) & 0x0f) << 6
            TGD2 |= (page >> 174) & 0x03f
            alpha0 = (page >> 166) & 0x0ff
            alpha1 = (page >> 158) & 0x0ff
            alpha2 = (page >> 142) & 0x0ff
            alpha3 = (page >> 134) & 0x0ff
            beta0 = ((page >> 128) & 0x03f) << 2
            beta0 |= (page >> 118) & 3
            beta1 = (page >> 110) & 0x0ff
            beta2 = (page >> 102) & 0x0ff
            beta3 = ((page >> 98) & 0x0f) << 4
            beta3 |= (page >> 86) & 0x0f
            a2 = (page >> 75) & 0x07ff
            a0 = ((page >> 68) & 0x07f) << 17
            a0 |= (page >> 43) & 0x01ffff
            a1 = ((page >> 38) & 0x01f) << 17
            a1 |= (page >> 13) & 0x01ffff
            AODE = (page >> 8) & 0x01f
            s += ("\n    SatH1 %u AODC %u URAI %u WN %u t0c %u TGD1 %u "
                  "TGD2 %u"
                  "\n      alpha0 %u alpha1 %u alpha2 %u alpha3 %u"
                  "\n      beta0 %u beta1 %u beta2 %u beta3 %u"
                  "\n      a2 %u a0 %u a1 %u AODE %u" %
                  (SatH1, AODC, URAI, WN, t0c, TGD1, TGD2, alpha0, alpha1,
                   alpha2, alpha3, beta0, beta1, beta2, beta3,
                   a2, a0, a1, AODE))
        elif 2 == FraID:
            deltan = ((page >> 248) & 0x03ff) << 6
            deltan |= (page >> 234) & 0x03f
            Cuc = ((page >> 218) & 0x0ffff) << 2
            Cuc |= (page >> 210) & 3
            M0 = ((page >> 188) & 0x0fffff) << 12
            M0 |= (page >> 168) & 0x0fff
            e = ((page >> 158) & 0x03ff) << 22
            e |= (page >> 128) & 0x03fffff
            Cus = (page >> 102) & 0x03ffff
            Crc = ((page >> 98) & 0x0f) << 14
            Crc |= (page >> 76) & 0x03fff
            Crs = ((page >> 68) & 0x0f) << 10
            Crs |= (page >> 50) & 0x03ff
            sqrtA = ((page >> 38) & 0x0fff) << 20
            sqrtA |= (page >> 10) & 0x0fffff
            toeMSB = (page >> 8) & 3
            s += ("\n    deltan %u Cuc %u M0 %u e %u Cus %u Crc %u"
                  "\n    Crs %u sqrtA %u toeMSB %u" %
                  (deltan, Cuc, M0, e, Cus, Crc, Crs, sqrtA, toeMSB))
        elif 3 == FraID:
            toeLSB = ((page >> 248) & 0x03ff) << 5
            toeLSB |= (page >> 235) & 0x01f
            i0 = ((page >> 218) & 0x01ffff) << 15
            i0 |= (page >> 195) & 0x07fff
            Cic = ((page >> 188) & 0x07f) << 11
            Cic |= (page >> 137) & 0x07fff
            Omegadot = ((page >> 158) & 0x07ff) << 13
            Omegadot |= (page >> 137) & 0x01fff
            Cis = ((page >> 128) & 0x01ff) << 9
            Cis |= (page >> 111) & 0x01ff
            IDOT = ((page >> 98) & 0x01fff) << 1
            IDOT |= (page >> 49) & 1
            Omega0 = ((page >> 68) & 0x01fffff) << 11
            Omega0 |= (page >> 49) & 0x07ff
            omega = ((page >> 38) & 0x07ff) << 21
            omega |= (page >> 9) & 0x01fffff
            Rev = (page >> 8) & 1
            s += ("\n    toeLSB %u i0 %u Cic %u Omegadot %u Cis %u"
                  "\n    IDOT %u Omega0 %u omega %u Rev %u" %
                  (toeLSB, i0, Cic, Omegadot, Cis, IDOT, Omega0, omega, Rev))
        elif FraID in [4, 5]:
            Pnum = (page >> 250) & 0x07f
            s += "\n    Pnum %u: " % Pnum
            if (((4 == FraID and (1 <= Pnum <= 24)) or
                 (1 <= Pnum <= 6) or
                 (11 <= Pnum <= 23))):
                # Subfram 4, page 1 to 24: Almanac
                # Subfram 5, page 1 to 6: Almanac
                # Subfram 5, page 11 to 23: maybe Almanac
                AmEpID = (page >> 8) & 3
                if 3 != AmEpID:
                    # not Almanac
                    s += "Reserved AmEpID %u" % AmEpID
                else:
                    sqrtA = ((page >> 248) & 3) << 22
                    sqrtA |= (page >> 218) & 0x03fffff
                    a1 = (page >> 199) & 0x07ff
                    a0 = (page >> 188) & 0x07ff
                    Omega0 = ((page >> 158) & 0x3fffff) << 2
                    Omega0 |= (page >> 148) & 3
                    e = (page >> 131) & 0x01ffff
                    deltai = ((page >> 128) & 3) << 13
                    deltai |= (page >> 107) & 0x01ffff
                    t0a = (page >> 99) & 0x0ff
                    Omegadot = ((page >> 98) & 1) << 16
                    Omegadot |= (page >> 74) & 0x0ffff
                    omega = ((page >> 68) & 0x03f) << 18
                    omega |= (page >> 42) & 0x03ffff
                    M0 = ((page >> 38) & 0x0f) << 20
                    M0 |= (page >> 10) & 0x0fffff
                    s += ("Almanac; sqrtA %u a1 %u a0 %u Omega0 %u"
                          "\n         e %u deltai %u t0a %u Omegadot %u"
                          "\n         omega %u M0 %u AmEpID %u" %
                          (sqrtA, a1, a0, Omega0, e, deltai, t0a, Omegadot,
                           omega, M0, AmEpID))
            elif 5 == FraID:
                if Pnum in [7, 8, 24]:
                    # make a packed integer
                    hlth = 0
                    for i in range(0, 10):
                        hlth <<= 22
                        # remove top two random bits and last 8 bits parity
                        hlth |= (words[i] & 0x3fffffff) >> 8

                if 7 == Pnum:
                    s += "Health 1 to 19:\n   "
                    # remove 7 reserved bits from last word
                    hlth >>= 7
                    for i in range(1, 20):
                        # take 9 bits at a time from the top
                        h = (hlth >> ((19 - i) * 9)) & 0x1ff
                        s += " %3x" % h
                elif 8 == Pnum:
                    # remove 63 reserved bits from LSBs
                    hlth >>= 63
                    WNa = (hlth >> 8) & 0x0ff
                    t0a = hlth & 0x0ff
                    # Hea20 to Hea30 now in the LSB
                    hlth >>= 16
                    s += "Health 20 to 30 WNa %u t0a %u\n       " % (WNa, t0a)
                    for i in range(20, 31):
                        # take 9 bits at a time from the top
                        h = (hlth >> ((30 - i) * 9)) & 0x1ff
                        s += " %3x" % h
                elif 9 == Pnum:
                    A0GPS = (page >> 106) & 0x03fff
                    A1GPS = ((page >> 188) & 0x03) << 14
                    A1GPS |= (page >> 166) & 0x03fff
                    A0GAL = ((page >> 158) & 0x0ff) << 6
                    A0GAL |= (page >> 144) & 0x03f
                    A1GAL = (page >> 128) & 0x0ffff
                    A0GLO = (page >> 106) & 0x03fff
                    A1GLO = ((page >> 98) & 0x0f) << 8
                    A1GLO |= (page >> 82) & 0x0f
                    s += ("Timing A0GPS %u A1GPS %u A0GAL %u A1GAL %u"
                          "\n       A0GLO %u A1GLO %u" %
                          (A0GPS, A1GPS, A0GAL, A1GAL, A0GLO, A1GLO))
                elif 10 == Pnum:
                    deltatLS = ((page >> 248) & 0x03) << 6
                    deltatLS |= (page >> 234) & 0x03f
                    deltatLSF = (page >> 226) & 0x0ff
                    WNLSF = (page >> 218) & 0x0ff
                    A0UTC = ((page >> 188) & 0x03fffff) << 10
                    A0UTC |= (page >> 170) & 0x03ff
                    A1UTC = ((page >> 158) & 0x0fff) << 12
                    A1UTC |= (page >> 138) & 0x0fff
                    DN = (page >> 130) & 0x0ff
                    s += ("Timing: deltatLS %u deltatLSF %u WNLSF %u A0UTC %u"
                          " A1UTC %u" % 
                          (deltatLS, deltatLSF, WNLSF, A0UTC, A1UTC))
                elif 24 == Pnum:
                    # ICD calls this AmID and AmEpID
                    AmEpID = (page >> 83) & 3
                    if 3 != AmEpID:
                        # not Almanac
                        s += "Reserved AmEpID %u" % AmEpID
                    else:
                        s += "Health 31 to 43: AmEpID %u" % AmEpID
                        # Hea31 to Hea43 now in the LSB
                        hlth >>= 85
                        s += "Health 31 to 43 t0a %u\n       " % SOW
                        for i in range(31, 44):
                            # take 9 bits at a time from the top
                            h = (hlth >> ((43 - i) * 9)) & 0x1ff
                            s += " %3x" % h
                else:
                    s += "Unknown page number"
            else:
                s += "Unknown page number"

        return s

    def _decode_sfrbx_gal(self, words):
        """Decode UBX-RXM-SFRBX Galileo I/NAV frames"""
        # Galileo_OS_SIS_ICD_v2.0.pdf
        # See u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf
        # Section 10.5 Galileo
        # gotta decode the u-blox munging and the Galileo packing...

        if 8 > len(words):
            return "\n    GAL: runt message, len %u" % len(words)

        s = ""
        if 8 != len(words):
            s = "\n    GAL: long message? len %u" % len(words)

        # always zero on E5b-I, always 1 on E1-B
        even = words[0] >> 31
        # zero for nominal page, one for alert page
        page_type = (words[0] >> 30) & 1
        word_type = (words[0] >> 24) & 0x03f
        s += ("\n    GAL: even %u page_type %u word_type %u" %
              (even, page_type, word_type))

        if (1 == page_type):
            # Alerts pages are all "Reserved"
            s += "\n    Alert page"
            return s

        if (1 == even):
            # page flipped!?
            s += "\n    page flipped!?"
            return s

        # untangle u-blox words into a Galileo 128 bit page
        # except we get 130 bits...
        # even (1), page (1), 128 data bits
        page = words[0] << 32
        page |= words[1]
        page <<= 32
        page |= words[2]
        page <<= 18
        page |= (words[3] >> 14) & 0x03ffff
        page <<= 16
        page |= (words[4] >> 14) & 0x0ffff

        # sanity check
        if (word_type != ((page >> 122) & 0x3f)):
            s += "\n    Math Error!"
            return s

        # all unscaled
        if (0 == word_type):
            s += "\n    Spare Word"
            time = (page >> 120) & 3;
            if 2 == time:
                # valid time
                WN = (page >> 20) & 0x0fff
                TOW =  page & 0x0fffff
                s += " WN %u TOW %u" % (WN, TOW)

        elif (1 == word_type):
            IODnav = (page >> 112) & 0x03ff
            toe = (page >> 98) & 0x03fff
            M0 = (page >> 66) & 0x0ffffffff
            e = (page >> 34) & 0x0ffffffff
            sqrt_A = (page >> 2) & 0x0ffffffff
            s += ("\n    Ephemeris 1: IODnav %u toe %u M0 %u e %u  sqrt_A %u" %
                  (IODnav, toe, M0, e, sqrt_A))
        elif (2 == word_type):
            IODnav = (page >> 112) & 0x03ff
            Omega0 = (page >> 80) & 0x0ffffffff
            i0 = (page >> 48) & 0x0ffffffff
            omega = (page >> 16) & 0x0ffffffff
            i_dot = (page >> 2) & 0x03fff
            s += ("\n    Ephemeris 2: IODnav %u Omega0 %u i0 %u"
                  "\n       omega %u i_dot %u" %
                  (IODnav, Omega0, i0, omega, i_dot))
        elif (3 == word_type):
            IODnav = (page >> 112) & 0x03ff
            Omega_dot = (page >> 88) & 0x0ffffff
            delta_n = (page >> 72) & 0x0ffff
            Cuc = (page >> 56) & 0x0ffff
            Cus = (page >> 40) & 0x0ffff
            Crc = (page >> 24) & 0x0ffff
            Crs = (page >> 8) & 0x0ffff
            SISA = page & 0x0ff
            s += ("\n    Ephemeris 3: IODnav %u Omega_dot %u delta_n %u"
                  "\n       Cuc %u Cus %u Crs %u Crs %u SISA %u" %
                  (IODnav, Omega_dot, delta_n, Cuc, Cus, Crc, Crc, SISA))
        elif (4 == word_type):
            IODnav = (page >> 112) & 0x03ff
            SVID = (page >> 106) & 0x03f
            Cic = (page >> 90) & 0x0ffff
            Cis = (page >> 74) & 0x0ffff
            t0c = (page >> 60) & 0x03fff
            af0 = (page >> 29) & 0x07fffffff
            af1 = (page >> 8) & 0x01fffff
            af2 = (page >> 2) & 0x03f
            s += ("\n    Ephemeris 4: IODnav %u SVID %u Cic %u Cis %u"
                  "\n       t0c %u af0 %u af1 %u af2 %u" %
                  (IODnav, SVID, Cic, Cis, t0c, af0, af1, af2))
        elif (5 == word_type):
            Ax_af0 = (page >> 111) & 0x7ff
            Ax_af1 = (page >> 100) & 0x7ff
            Ax_af2 = (page >> 86) & 0x3fff
            Iono1 = (page >> 85) & 1
            Iono2 = (page >> 84) & 1
            Iono3 = (page >> 83) & 1
            Iono4 = (page >> 82) & 1
            Iono5 = (page >> 81) & 1
            BGD_E1E5a = (page >> 71) & 0x3ff
            BGD_E1E5b = (page >> 61) & 0x3ff
            E5BHS = (page >> 59) & 3
            E1BHS = (page >> 57) & 3
            E5BDVS = (page >> 56) & 1
            E1BDVS = (page >> 55) & 1
            WN = (page >> 43) & 0x0fff
            TOW = (page >> 23) & 0x0fffff
            s += ("\n    Ionosphere: Ax_af0 %u Ax_af1 %u Ax_af2 %u"
                  "\n       Iono1 %u Iono2 %u Iono3 %u Iono4 %u Iono5 %u"
                  "\n       BGD_E1E5a %u BGD_E1E5b %u E5BHS %u E1BHS %u"
                  "\n       E5BDVS %u E1BDVS %u WN %u TOW %u" %
                  (Ax_af0, Ax_af1, Ax_af2, Iono1, Iono2, Iono3, Iono4, Iono5,
                   BGD_E1E5a, BGD_E1E5b, E5BHS, E1BHS, E5BDVS, E1BDVS,
                   WN, TOW))
        elif (6 == word_type):
            A0 = (page >> 90) & 0x0ffffffff
            A1 = (page >> 66) & 0x0ffffff
            delta_tLS = (page >> 58) & 0x0ff
            t0t = (page >> 50) & 0x0ff
            WN0t = (page >> 42) & 0x0ff
            WNLSF = (page >> 34) & 0x0ff
            DN = (page >> 31) & 7
            delta_tLSF = (page >> 23) & 0x0ff
            TOW = (page >> 3) & 0x0fffff
            s += ("\n    GST-UTC: A0 %u A1 %u delta_tLS %u t0t %u WN0t %u"
                  "\n       WNLSF %u DN %u delta_tLSF %u TOW %u" %
                  (A0, A1, delta_tLS, t0t, WN0t, WNLSF, DN, delta_tLSF, TOW))
        elif (7 == word_type):
            IODa = (page >> 118) & 0x0f
            WNa = (page >> 116) & 0x03
            t0a = (page >> 106) & 0x03ff
            SVID1 = (page >> 100) & 0x03f
            delta_sqrtA = (page >> 87) & 0x01fff
            e = (page >> 76) & 0x07ff
            omega = (page >> 60) & 0x0ffff
            delta_i = (page >> 49) & 0x07ff
            Omage0 = (page >> 33) & 0x0ffff
            Omage_dot = (page >> 22) & 0x07ff
            M0 = (page >> 6) & 0x0ffff
            s += ("\n    Almanac SVID1 (1/2): IODa %u WNa %u t0a %u SVID1 %u"
                  "\n       delta_sqrtA %u e %u omega %u delta_i %u Omage0 %u"
                  "\n       Omage_dot %u M0 %u" %
                  (IODa, WNa, t0a, SVID1, delta_sqrtA, e, omega, delta_i,
                   Omage0, Omage_dot, M0))
        elif (8 == word_type):
            IODa = (page >> 118) & 0x0f
            af0 = (page >> 102) & 0x0ffff
            af1 = (page >> 89) & 0x01fff
            E5BHS = (page >> 87) & 3
            E1BHS = (page >> 85) & 3
            SVID2 = (page >> 79) & 0x03f
            delta_sqrtA = (page >> 66) & 0x01fff
            e = (page >> 55) & 0x07ff
            omega = (page >> 39) & 0x0ffff
            delta_i = (page >> 28) & 0x07ff
            Omage0 = (page >> 12) & 0x0ffff
            Omage_dot = (page >> 1) & 0x07ff
            s += ("\n    Almanac SVID1 (2/2): IODa %u af0 %u af1 %u E5BHS %u "
                  "E1BHS %u"
                  "\n       SVID2 %u delta_sqrtA %u e %u omega %u delta_i %u"
                  "\n       Omage0 %u Omage_dot %u" %
                  (IODa, af0, af1, E5BHS, E1BHS, SVID2, delta_sqrtA, e, omega,
                   delta_i, Omage0, Omage_dot))
        elif (9 == word_type):
            IODa = (page >> 118) & 0x0f
            WNa = (page >> 116) & 3
            t0a = (page >> 106) & 0x03ff
            M0 = (page >> 90) & 0x0ffff
            af0 = (page >> 74) & 0x0ffff
            af1 = (page >> 61) & 0x01fff
            E5BHS = (page >> 59) & 3
            E1BHS = (page >> 57) & 3
            SVID3 = (page >> 51) & 0x03f
            delta_sqrtA = (page >> 38) & 0x01fff
            e = (page >> 27) & 0x07ff
            omega = (page >> 11) & 0x0ffff
            delta_i = page & 0x07ff
            s += ("\n    Almanac SVID2 (2/2): IODa %u WNa %u t0a %u M0 %u"
                  "\n       af0 %u af1 %u E5BHS %u E1BHS %u"
                  "\n       SVID3 %u delta_sqrtA %u e %u omega %u delta_i %u" %
                  (IODa, WNa, t0a, M0, af0, af1, E5BHS, E1BHS, SVID3,
                   delta_sqrtA, e, omega, delta_i))
        elif (10 == word_type):
            IODa = (page >> 118) & 0x0f
            Omage0 = (page >> 102) & 0x0ffff
            Omage_dot = (page >> 91) & 0x07ff
            M0 = (page >> 75) & 0x0ffff
            af0 = (page >> 59) & 0x0ffff
            af1 = (page >> 46) & 0x01fff
            E5BHS = (page >> 44) & 3
            E1BHS = (page >> 42) & 3
            A0G = (page >> 26) & 0x0ffff
            A1G = (page >> 14) & 0x0fff
            t0G = (page >> 6) & 0x0ff
            WN0G = page & 0x3f
            s += ("\n    Almanac SVID3 (2/2): IODa %u Omage0 %u Omage_dot %u"
                  "\n       M0 %u af0 %u af1 %u E5BHS %u E1BHS %u"
                  "\n       A0G %u A1G %u t0G %u WN0G %u" %
                  (IODa, Omage0, Omage_dot, M0, af0, af1, E5BHS, E1BHS,
                   A0G, A1G, t0G, WN0G))
        elif (16 == word_type):
            deltaAred = (page >> 117) & 0x01f
            exred = (page >> 104) & 0x01fff
            eyred = (page >> 91) & 0x01fff
            deltai0red = (page >> 74) & 0x01ffff
            Omega0red = (page >> 51) & 0x07fffff
            lambda0red = (page >> 28) & 0x07fffff
            af0red = (page >> 6) & 0x03fffff
            af1red = page & 0x03f
            s += ("\n    Reduced Clock and Ephemeris Data: deltaAred %u"
                  "\n       exred %u eyred %u deltai0red %u Omega0red %u"
                  "\n       lambda0red %u af0red %u af1red %u" %
                  (deltaAred, exred, eyred, deltai0red, Omega0red,
                   lambda0red, af0red, af1red))
        elif (17 <= word_type and 20 >= word_type):
            s += "\n    FEC2 Reed-Solomon for Clock and Ephemeris Data"
        elif (63 == word_type):
            s += "\n    Dummy Page"

        return s

    def _decode_sfrbx_glo(self, words):
        """Decode UBX-RXM-SFRBX GLONASS frames"""
        # See u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf
        # Section 10.3 GLONASS
        # L10F and L20F only
        # ICD_GLONASS_5.1_(2008)_en.pdf "ICD L1, L2 GLONASS"
        # gotta decode the u-blox munging and the GLONASS packing...
        # u-blox stripts preamble
        stringnum = (words[0] >> 27) & 0x0f

        page = 0
        for i in range(0, 4):
            page <<= 32
            page |= words[i] & 0x0ffffffff

        # sanity check
        if (stringnum != ((page >> 123) & 0x0f)):
            s = ("\n    GLO: Math Error! %u != %u"
                 "\n      page %u" %
                 (stringnum, (page >> 123) & 0xf, page))
            return s

        frame = page & 0x0ff
        superframe = (page >> 16) & 0x0ffff

        s = ("\n    GLO: superframe %u frame %u stringnum %u" %
             (superframe, frame, stringnum))
        if 1 == stringnum:
            P1 = (page >> 119) & 3
            tk = (page >> 107) & 0x0fff
            xnp = (page >> 83) & 0x0ffffffff
            xnpp = (page >> 78) & 0x01f
            xn = (page >> 51) & 0xa30ffffffff
            s += ("\n        Ephemeris 1: P1 %u tk %u xnp %u xnpp %u xn %u" %
                  (P1, tk, xnp, xnpp, xn))
        if 2 == stringnum:
            Bn = (page >> 120) & 7
            P2 = (page >> 119) & 1
            tb = (page >> 112) & 0x07f
            ynp = (page >> 83) & 0x0ffffffff
            ynpp = (page >> 78) & 0x01f
            yn = (page >> 51) & 0xa30ffffffff
            s += ("\n        Ephemeris 2: Bn %u P2 %u tb %u ynp %u ynpp %u "
                  "yn %u" %
                  (Bn, P2, tb, ynp, ynpp, yn))
        if 3 == stringnum:
            P3 = (page >> 122) & 1
            lambdan = (page >> 111) & 0x07fff
            p = (page >> 108) & 3
            ln = (page >> 107) & 1
            znp = (page >> 83) & 0x0ffffffff
            znpp = (page >> 78) & 0x01f
            zn = (page >> 51) & 0xa30ffffffff
            s += ("\n        Ephemeris 3: P3 %u znp %u znpp %u zn %u" %
                  (P3, znp, znpp, zn))
        if 4 == stringnum:
            # n is SVID
            taun = (page >> 101) & 0x03ffffff
            deltataun = (page >> 96) & 0x01f
            En = (page >> 91) & 0x01f
            P4 = (page >> 76) & 1
            FT = (page >> 72) & 0x0f
            NT = (page >> 58) & 0x03fff
            n = (page >> 53) & 0x1f
            M = (page >> 51) & 3
            s += ("\n        Ephemeris 4: taun %u deltataun %u En %u P4 %u"
                  "\n           FT %u NT %u n %u M %u" %
                  (taun, deltataun, En, P4, FT, NT, n, M))
        if 5 == stringnum:
            NA = (page >> 112) & 0x07ff
            tauc = (page >> 80) & 0x0ffffffff
            N4 = (page >> 74) & 0x01f
            tauGPS = (page >> 52) & 0x03fffff
            ln = (page >> 51) & 1
            s += ("\n        Time: NA %u tauc %u N4 %u tauGPS %u ln %u" %
                  (NA, tauc, N4, tauGPS, ln))
        if stringnum in [6, 8, 10, 12, 14]:
            if 5 == frame:
                B1 = (page >> 112) & 0x07ff
                B2 = (page >> 102) & 0x03ff
                KP = (page >> 100) & 3
                s += "\n        Extra 1: B1 %u B2 %u KP %u" % (B1, B2, KP)
            else:
                Cn = (page >> 122) & 1
                m = (page >> 120) & 3
                nA = (page >> 115) & 0x1f
                tauA = (page >> 105) & 0x03ff
                lambdaA = (page >> 84) & 0x01ffffff
                deltaiA = (page >> 66) & 0x03ffff
                epsilonA = (page >> 51) & 0x07fff
                s += ("\n        Almanac: Cn %u m %u nA %u tauA %u "
                      "lambdaA %u deltaiA %u"
                      "\n          epsilonA %u" %
                      (Cn, m, nA, tauA, lambdaA, deltaiA, epsilonA))
        if stringnum in [7, 9, 11, 13, 15]:
            if 5 == frame:
                ln = (page >> 51) & 1
                s += "\n        Extra 2: ln %u" % ln
            else:
                omegaA = (page >> 107) & 0x0ffff
                tA = (page >> 86) & 0x01fffff
                deltaTA = (page >> 64) & 0x03ffffff
                deltaTpA = (page >> 57) & 0x07f
                HA = (page >> 52) & 0x01f
                ln = (page >> 51) & 1
                s += ("\n        Almanac: omegaA %u tA %u deltaTA %u "
                      "deltaTpA %u HA %u ln %u" %
                      (omegaA, tA, deltaTA, deltaTpA, HA, ln))

        return s

    def _decode_sfrbx_sbas(self, words):
        """Decode UBX-RXM-SFRBX SBAS subframes"""
        # See u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf
        # Section 10.6 SBAS
        # The WAAS Spec is RTCA DO-229, and is not cheap!
        # the function coded w/o access to that document.
        # WAAS message described here:
        # https://gssc.esa.int/navipedia/index.php/The_EGNOS_SBAS_Message_Format_Explained

        # preamble is 83, then 154, the 198, then repeats.
        preamble = (words[0] >> 24) & 0x0ff
        msg_type = (words[0] >> 18) & 0x03f
        # untangle u-blox words into just message type and data
        # 213 bits

        page = 0
        for i in range(0, 8):
            page |= words[i] & 0x0ffffffff
            page <<= 32
        # trim parity and pad
        page >>= 30

        s = "\n   SBAS: preamble %u type %u" % (preamble, msg_type)
        # sanity check
        if (msg_type != ((page >> 244) & 0x03f)):
            s += ("\n    Math Error! %u != %u"
                  "\n    x%x" %
                  (msg_type, (page >> 212) & 0x3f, page))
            return s

        if 0 == msg_type:
            s += "\n       Don't use"
        elif 1 == msg_type:
            s += "\n       PRN mask assignments"
        elif 2 == msg_type:
            s += "\n       Fast Corrections 2"
        elif 3 == msg_type:
            s += "\n       Fast Corrections 3"
        elif 4 == msg_type:
            s += "\n       Fast Corrections 4"
        elif 5 == msg_type:
            s += "\n       Fast Corrections 5"
        elif 6 == msg_type:
            s += "\n       Integity information"
        elif 7 == msg_type:
            s += "\n       Degradation Parameters"
        elif 9 == msg_type:
            s += "\n       Geo Navigation message (X,Y,Z, time, etc.)"
        elif 10 == msg_type:
            s += "\n       Degradation parameters"
        elif 12 == msg_type:
            s += "\n       SBAS Network time/UTC offset parameters"
        elif 17 == msg_type:
            s += "\n       Geo satellite almanacs"
        elif 18 == msg_type:
            s += "\n       Ionospheric grid points masks"
        elif 24 == msg_type:
            s += "\n       Mixed fast/long term satellite error corrections"
        elif 25 == msg_type:
            s += "\n       Long term satellite error corrections"
        elif 26 == msg_type:
            s += "\n       Ionospheric delay corrections"
        elif 27 == msg_type:
            s += "\n       SBAS Service message"
        elif 28 == msg_type:
            s += "\n       Clock Ephemeris Covariance Matrix message"
        elif 31 == msg_type:
            s += "\n       L5 Satellite Mask"
        elif 32 == msg_type:
            s += "\n       L5 Clock-Ephemeris Corrections/Covariance Matrix "
        elif 34 == msg_type:
            s += "\n       L5 Integrity message"
        elif 35 == msg_type:
            s += "\n       L5 Integrity message"
        elif 36 == msg_type:
            s += "\n       L5 Integrity message"
        elif 37 == msg_type:
            s += "\n       L5 Degradation Parameters and DREI Scale Table"
        elif 39 == msg_type:
            s += "\n       L5 SBAS Sats Ephemeris and Covariance Matrix"
        elif 40 == msg_type:
            s += "\n       L5 SBAS Sats Ephemeris and Covariance Matrix"
        elif 47 == msg_type:
            s += "\n       L5 SBAS broadcasting Satellite Almanac"
        elif 62 == msg_type:
            s += "\n       Instant Test Message"
        elif 63 == msg_type:
            s += "\n       Null Message"

        return s

    cnav_msgids = {
        10: "Ephemeris 1",
        11: "Ephemeris 2",
        12: "Reduced Almanac",
        13: "Clock Differential Correction",
        14: "Ephemeris Differential Correction",
        15: "Text",
        30: "Clock, IONO & Group Delay",
        31: "Clock & Reduced Almanac",
        32: "Clock & EOP",
        33: "Clock & UTC",
        34: "Clock & Differential Correction",
        35: "Clock & GGTO",
        36: "Clock & Text",
        37: "Clock & Midi Almanac",
        }

    # map subframe 4 SV ID to Page number
    # IS-GPS-200K Table 20-V
    sbfr4_svid_page = {
        0: 0,   # dummy/self
        57: 1,   # Reserved (Dupe, also 6, 11, 16 21)
        25: 2,
        26: 3,
        27: 4,
        28: 5,
        # 57: 6,   # Reserved (Dupe)
        29: 7,
        30: 8,
        31: 9,
        32: 10,
        # 57: 11,  # Reserved (Dupe)
        62: 12,  # reserved (Dupe 12 and 24)
        52: 13,  # navigation message correction table (NMCT)
        53: 14,  # reserved
        54: 15,  # reserved
        # 57: 16,  # Reserved (Dupe)
        55: 17,  # Special messages
        56: 18,  # Ionospheric and UTC data
        58: 19,  # reserved
        59: 20,  # reserved
        # 57: 21,  # Reserved (Dupe)
        60: 22,  # reserved
        61: 23,  # reserved
        # 62: 24,  # reserved (Dupe 12 and 24)
        63: 25,  # A-S Flags/ SV health
        }

    # map subframe 5 SV ID to Page number
    # IS-GPS-200K Table 20-V
    sbfr5_svid_page = {
        0: 0,   # dummy/self
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 11,
        12: 12,
        13: 13,
        14: 14,
        15: 15,
        16: 16,
        17: 17,
        18: 18,
        19: 19,
        20: 20,
        21: 21,
        22: 22,
        23: 23,
        24: 24,
        51: 25,  # SV Health, SC 1 to 24
        }

    # URA Index to URA meters
    ura_meters = {
        0: "2.40 m",
        1: "3.40 m",
        2: "4.85 m",
        3: "6.85 m",
        4: "9.65 m",
        5: "13.65 m",
        6: "24.00 m",
        7: "48.00 m",
        8: "96.00 m",
        9: "192.00 m",
        10: "384.00 m",
        11: "768.00 m",
        12: "1536.00 m",
        13: "3072.00 m",
        14: "6144.00 m",
        15: "Unk",
        }

    codes_on_l2 = {
        0: "Invalid",
        1: "P-code ON",
        2: "C/A-code ON",
        3: "Invalid",
        }

    nmct_ai = {
        0: "OK",
        1: "Encrypted",
        2: "Unavailable",
        3: "Reserved",
        }

    sv_conf = {
        0: "Reserved",
        1: "Block II/Block IIA/IIR SV",
        2: "M-code, L2C, Block IIR-M SV",
        3: "M-code, L2C, L5, Block IIF SV",
        4: "M-code, L2C, L5, No SA, Block III SV",
        5: "Reserved",
        6: "Reserved",
        7: "Reserved",
        }

    def rxm_sfrbx(self, buf):
        """UBX-RXM-SFRBX decode, Broadcast Navigation Data Subframe"""

        # The way u-blox packs the subfram data is perverse, and
        # barely undocumnted.  Even more perverse than native subframes.

        u = struct.unpack_from('<BBBBBBBB', buf, 0)
        s = (' gnssId %u svId %3u reserved1 %u freqId %u numWords %u\n'
             '  chn %u version %u reserved2 %u' % u)
        words = ()
        for i in range(0, u[4]):
            u1 = struct.unpack_from('<L', buf, 8 + (i * 4))
            words += (u1[0],)

        if gps.VERB_DECODE <= self.verbosity:
            s += '\n    dwrd'
            i = 0
            for word in words:
                s += " %08x" % word
                if 6 == (i % 7):
                    s += "\n        "
                i += 1

        if ((0 == u[0] or
             5 == u[0])):
            # GPS and QZSS
            preamble = words[0] >> 24
            if 0x8b == preamble:
                # CNAV
                msgid = (words[0] >> 12) & 0x3f
                s += ("\n  CNAV: preamble %#x PRN %u msgid %d (%s)\n" %
                      (preamble, (words[0] >> 18) & 0x3f,
                       msgid, index_s(msgid, self.cnav_msgids)))

            else:
                # IS-GPS-200, Figure 20-2
                # LNAV-L, from sat is 10 words of 30 bits
                # from u-blox each of 10 words right aligned into 32 bits
                #             plus something in top 2 bits?
                preamble = words[0] >> 22
                subframe = (words[1] >> 8) & 0x07
                s += ("\n  LNAV-L: preamble %#x TLM %#x ISF %u" %
                      (preamble, (words[0] >> 8) & 0xffff,
                       1 if (words[0] & 0x40) else 0))

                s += ("\n  TOW17 %u Alert %u A-S %u Subframe %u" %
                      (unpack_u17(words[1], 13) * 6,
                       1 if (words[0] & 0x1000) else 0,
                       1 if (words[0] & 0x800) else 0,
                       subframe))

                if 1 == subframe:
                    # not well validated decode, possibly wrong...
                    # [1] Figure 20-1 Sheet 1, Table 20-I
                    # WN = GPS week number
                    # TGD = Group Delay Differential
                    # tOC = Time of Clock
                    # af0 = SV Clock Bias Correction Coefficient
                    # af1 = SV Clock Drift Correction Coefficient
                    # af2 = Drift Rate Correction Coefficient
                    ura = (words[2] >> 14) & 0x0f
                    c_on_l2 = (words[2] >> 18) & 0x03
                    iodc = ((((words[2] >> 6) & 0x03) << 8) |
                            (words[7] >> 24) & 0xff)
                    s += ("\n   WN %u Codes on L2 %u (%s) URA %u (%s) "
                          "SVH %#04x IODC %u" %
                          (words[2] >> 20,
                           c_on_l2, index_s(c_on_l2, self.codes_on_l2),
                           ura, index_s(ura, self.ura_meters),
                           (words[2] >> 8) & 0x3f, iodc))
                    # tOC = Clock Data Reference Time of Week
                    s += ("\n   L2 P DF %u TGD %e tOC %u\n"
                          "   af2 %e af1 %e af0 %e" %
                          ((words[2] >> 29) & 0x03,
                           unpack_s8(words[6], 6) * (2 ** -31),
                           unpack_u16(words[7], 6) * 16,
                           unpack_s8(words[8], 22) * (2 ** -55),
                           unpack_s16(words[8], 6) * (2 ** -43),
                           unpack_s22(words[9], 8) * (2 ** -31)))

                elif 2 == subframe:
                    # not well validated decode, possibly wrong...
                    # [1] Figure 20-1 Sheet 1, Tables 20-II and 20-III
                    # IODE = Issue of Data (Ephemeris)
                    # Crs = Amplitude of the Sine Harmonic Correction
                    #       Term to the Orbit Radius
                    # Deltan = Mean Motion Difference From Computed Value
                    # M0 = Mean Anomaly at Reference Time
                    # Cuc = Amplitude of the Cosine Harmonic Correction
                    #       Term to the Argument of Latitude
                    # e = Eccentricity
                    # Cus = Amplitude of the Sine Harmonic Correction Term
                    #       to the Argument of Latitude
                    # sqrtA = Square Root of the Semi-Major Axis
                    # tOE = Reference Time Ephemeris
                    s += ("\n   IODE %u Crs %e Deltan %e M0 %e"
                          "\n   Cuc %e e %e Cus %e sqrtA %f"
                          "\n   tOE %u" %
                          (unpack_u8(words[2], 22),
                           unpack_s16(words[2], 6) * (2 ** -5),
                           unpack_s16(words[3], 14) * (2 ** -43),
                           # M0
                           unpack_s32s(words[4], words[3]) * (2 ** -31),
                           unpack_s16(words[5], 14) * (2 ** -29),
                           unpack_u32s(words[6], words[5]) * (2 ** -33),
                           unpack_s16(words[7], 14) * (2 ** -29),
                           unpack_u32s(words[8], words[7]) * (2 ** -19),
                           unpack_u16(words[9], 14) * 16))

                elif 3 == subframe:
                    # not well validated decode, possibly wrong...
                    # [1] Figure 20-1 Sheet 3, Table 20-II, Table 20-III
                    # Cic = Amplitude of the Cosine Harmonic Correction
                    #       Term to the Angle of Inclination
                    # Omega0 = Longitude of Ascending Node of Orbit
                    #          Plane at Weekly Epoch
                    # Cis = Amplitude of the Sine Harmonic Correction
                    #       Term to the Orbit Radius
                    # i0 = Inclination Angle at Reference Time
                    # Crc = Amplitude of the Cosine Harmonic Correction
                    #       Term to the Orbit Radius
                    # omega = Argument of Perigee
                    # Omegadot = Rate of Right Ascension
                    # IODE = Issue of Data (Ephemeris)
                    # IODT = Rate of Inclination Angle
                    s += ("\n   Cic %e Omega0 %e Cis %e i0 %e"
                          "\n   Crc %e omega %e Omegadot %e"
                          "\n   IDOE %u IDOT %e" %
                          (unpack_s16(words[2], 14) * (2 ** -29),
                           unpack_s32s(words[3], words[2]) * (2 ** -31),
                           unpack_s16(words[4], 14) * (2 ** -29),
                           unpack_s32s(words[5], words[4]) * (2 ** -31),
                           # Crc
                           unpack_s16(words[6], 14) * (2 ** -5),
                           unpack_s32s(words[7], words[6]) * (2 ** -31),
                           # Omegadot
                           unpack_s24(words[8], 6) * (2 ** -43),
                           unpack_u8(words[9], 22),
                           unpack_s14(words[9], 8) * (2 ** -43)))

                elif 4 == subframe:
                    # pages:
                    #  2 to 5, 7 to 10 almanac data for SV 25 through 32
                    #  13 navigation message correction table (NMCT_
                    #  17 Special Messages
                    #  18 Ionospheric and UTC data
                    #  25 A-S flags/ SV health
                    #  1, 6, 11, 16 and 21 reserved
                    #  12, 19, 20, 22, 23 and 24 reserved
                    #  14 and 15 reserved
                    # as of 2018, data ID is always 1.
                    svid = (words[2] >> 22) & 0x3f
                    # 0 === svid is dummy SV
                    # almanac for dummy sat 0, same as transmitting sat
                    # Sec 3.2.1: "Users shall only use non-dummy satellites"
                    page = index_s(svid, self.sbfr4_svid_page)

                    s += ("\n   dataid %u svid %u (page %s)\n" %
                          (words[2] >> 28, svid, page))
                    if 'Unk' == page:
                        s += "\n   Unknown page ????"
                        return s

                    if 6 == page:
                        s += "    reserved"
                    elif 2 <= page <= 10:
                        s += self.almanac(words)
                    elif 13 == page:
                        # 20.3.3.5.1.9 NMCT.
                        # 30 ERDs, but more sats. A sat skips own ERD.
                        # no ERD for sat 32
                        # erds are signed! 0x20 == NA
                        s += ("    NMCT AI %u(%s)"
                              "\n      ERD1:  %s %s %s %s %s %s %s %s"
                              "\n      ERD9:  %s %s %s %s %s %s %s %s"
                              "\n      ERD17: %s %s %s %s %s %s %s %s"
                              "\n      ERD25: %s %s %s %s %s %s" %
                              ((words[2] >> 22) & 0x3,    # AI
                               index_s((words[2] >> 22) & 0x3, self.nmct_ai),
                               erd_s((words[2] >> 16) & 0x3f),   # erd1
                               erd_s((words[2] >> 8) & 0x3f),
                               erd_s((((words[2] >> 2) & 0x30) |
                                      (words[3] >> 26) & 0x0f)),
                               erd_s((words[3] >> 20) & 0x3f),
                               erd_s((words[3] >> 14) & 0x3f),   # erd5
                               erd_s((words[3] >> 8) & 0x3f),
                               erd_s((((words[3] >> 2) & 0x30) |
                                      (words[4] >> 26) & 0x0f)),
                               erd_s((words[4] >> 20) & 0x3f),
                               erd_s((words[4] >> 14) & 0x3f),   # erd9
                               erd_s((words[4] >> 8) & 0x3f),
                               erd_s((((words[4] >> 2) & 0x30) |
                                      (words[5] >> 26) & 0x0f)),
                               erd_s((words[5] >> 20) & 0x3f),
                               erd_s((words[5] >> 14) & 0x3f),   # erd 13
                               erd_s((words[5] >> 8) & 0x3f),
                               erd_s((((words[5] >> 2) & 0x30) |
                                      (words[6] >> 26) & 0x0f)),
                               erd_s((words[6] >> 20) & 0x3f),
                               erd_s((words[6] >> 14) & 0x3f),   # erd17
                               erd_s((words[6] >> 8) & 0x3f),
                               erd_s((((words[6] >> 2) & 0x30) |
                                      (words[7] >> 26) & 0x0f)),
                               erd_s((words[7] >> 20) & 0x3f),
                               erd_s((words[7] >> 14) & 0x3f),   # erd21
                               erd_s((words[7] >> 8) & 0x3f),
                               erd_s((((words[7] >> 2) & 0x30) |
                                      (words[8] >> 26) & 0x0f)),
                               erd_s((words[8] >> 20) & 0x3f),
                               erd_s((words[8] >> 14) & 0x3f),   # erd25
                               erd_s((words[8] >> 8) & 0x3f),
                               erd_s((((words[8] >> 2) & 0x30) |
                                      (words[9] >> 26) & 0x0f)),
                               erd_s((words[9] >> 20) & 0x3f),
                               erd_s((words[9] >> 14) & 0x3f),   # erd29
                               erd_s((words[9] >> 8) & 0x3f),    # erd30
                               ))
                    elif 17 == page:
                        s += ("    Special messages: " +
                              chr((words[2] >> 14) & 0xff) +
                              chr((words[2] >> 6) & 0xff) +
                              chr((words[3] >> 22) & 0xff) +
                              chr((words[3] >> 14) & 0xff) +
                              chr((words[3] >> 6) & 0xff) +
                              chr((words[4] >> 22) & 0xff) +
                              chr((words[4] >> 14) & 0xff) +
                              chr((words[4] >> 6) & 0xff) +
                              chr((words[5] >> 22) & 0xff) +
                              chr((words[5] >> 14) & 0xff) +
                              chr((words[5] >> 6) & 0xff) +
                              chr((words[6] >> 22) & 0xff) +
                              chr((words[6] >> 14) & 0xff) +
                              chr((words[6] >> 6) & 0xff) +
                              chr((words[7] >> 22) & 0xff) +
                              chr((words[7] >> 14) & 0xff) +
                              chr((words[7] >> 6) & 0xff) +
                              chr((words[8] >> 22) & 0xff) +
                              chr((words[8] >> 14) & 0xff) +
                              chr((words[8] >> 6) & 0xff) +
                              chr((words[9] >> 22) & 0xff) +
                              chr((words[9] >> 14) & 0xff))

                    elif 18 == page:
                        alpha1 = (words[2] >> 14) & 0xff
                        alpha0 = (words[2] >> 6) & 0xff
                        alpha2 = (words[3] >> 22) & 0xff
                        alpha3 = (words[3] >> 14) & 0xff
                        beta0 = (words[3] >> 6) & 0xff
                        beta1 = (words[4] >> 6) & 0xff
                        beta2 = (words[4] >> 22) & 0xff
                        beta3 = (words[4] >> 14) & 0xff
                        A1 = (words[5] >> 6) & 0xffffff
                        A0 = (((words[6] << 2) & 0xffffff00) |
                              ((words[7] >> 22) & 0xff))
                        tot = (words[7] >> 14) & 0xff
                        WNt = (words[7] >> 6) & 0xff
                        deltatls = (words[8] >> 22) & 0xff
                        WNlsf = (words[8] >> 14) & 0xff
                        DN = (words[8] >> 6) & 0xff
                        deltatlsf = (words[9] >> 22) & 0xff
                        s += ("    Ionospheric and UTC data\n"
                              "     alpah0 x%02x alpah1 x%02x "
                              "alpah2 x%02x alpah3 x%02x\n"
                              "     beta0  x%02x beta1  x%02x "
                              "beta2  x%02x beta3  x%02x\n"
                              "     A0  x%08x A1  x%06x tot x%02x WNt x%02x\n"
                              "     deltatls x%02x WNlsf x%02x DN x%02x "
                              "deltatlsf x%02x" %
                              (alpha0, alpha1, alpha2, alpha3,
                               beta0, beta1, beta2, beta3,
                               A0, A1, tot, WNt,
                               deltatls, WNlsf, DN, deltatlsf))
                    elif 25 == page:
                        aspoof = []
                        aspoof.append((words[2] >> 18) & 0x0f)
                        aspoof.append((words[2] >> 14) & 0x0f)
                        aspoof.append((words[2] >> 10) & 0x0f)
                        aspoof.append((words[2] >> 6) & 0x0f)
                        for i in range(3, 7):
                            aspoof.append((words[i] >> 26) & 0x0f)
                            aspoof.append((words[i] >> 22) & 0x0f)
                            aspoof.append((words[i] >> 18) & 0x0f)
                            aspoof.append((words[i] >> 14) & 0x0f)
                            aspoof.append((words[i] >> 10) & 0x0f)
                            aspoof.append((words[i] >> 6) & 0x0f)
                        aspoof.append((words[7] >> 26) & 0x0f)
                        aspoof.append((words[7] >> 22) & 0x0f)
                        aspoof.append((words[7] >> 18) & 0x0f)
                        aspoof.append((words[7] >> 14) & 0x0f)

                        sv = []
                        sv.append((words[7] >> 6) & 0x3f)
                        sv.append((words[8] >> 24) & 0x3f)
                        sv.append((words[8] >> 18) & 0x3f)
                        sv.append((words[8] >> 12) & 0x3f)
                        sv.append((words[8] >> 6) & 0x3f)
                        sv.append((words[9] >> 24) & 0x3f)
                        sv.append((words[9] >> 18) & 0x3f)
                        sv.append((words[9] >> 12) & 0x3f)
                        s += ("    A/S flags:\n"
                              "     as01 x%x as02 x%x as03 x%x as04 x%x "
                              "as05 x%x as06 x%x as07 x%x as08 x%x\n"
                              "     as09 x%x as10 x%x as11 x%x as12 x%x "
                              "as13 x%x as14 x%x as15 x%x as16 x%x\n"
                              "     as17 x%x as18 x%x as19 x%x as20 x%x "
                              "as21 x%x as22 x%x as23 x%x as24 x%x\n"
                              "     as25 x%x as26 x%x as27 x%x as28 x%x "
                              "as29 x%x as30 x%x as31 x%x as32 x%x\n" %
                              tuple(aspoof))
                        if gps.VERB_DECODE <= self.verbosity:
                            for i in range(1, 33):
                                f = aspoof[i - 1]
                                s += ("      as%02d x%x (A-S %s, Conf %s)\n" %
                                      (i, f,
                                       'On' if (f & 8) else 'Off',
                                       index_s(f & 7, self.sv_conf)))

                        s += ("    SV HEALTH:\n"
                              "      sv25 x%2x sv26 x%2x sv27 x%2x sv28 x%2x "
                              "sv29 x%2x sv30 x%2x sv31 x%2x sv32 x%2x" %
                              tuple(sv))
                    else:
                        s += "    Reserved"

                elif 5 == subframe:
                    svid = (words[2] >> 22) & 0x3f
                    # 0 === svid is dummy SV
                    # almanac for dummy sat 0, same as transmitting sat
                    # Sec 3.2.1: "Users shall only use non-dummy satellites"
                    page = index_s(svid, self.sbfr5_svid_page)

                    s += ("\n   dataid %u svid %u (page %s)\n" %
                          (words[2] >> 28, svid, page))
                    if 'Unk' == page:
                        s += "\n   Unknown page ????"
                        return s

                    if 1 <= page <= 24:
                        s += self.almanac(words)
                    elif 25 == page:
                        toa = (words[2] >> 14) & 0xff
                        WNa = (words[2] >> 6) & 0xff
                        sv = []
                        for i in range(3, 9):
                            sv.append((words[i] >> 24) & 0x3f)
                            sv.append((words[i] >> 18) & 0x3f)
                            sv.append((words[i] >> 12) & 0x3f)
                            sv.append((words[i] >> 6) & 0x3f)
                        s += "    SV HEALTH toa %u WNa %u\n" % (toa, WNa)
                        s += ("     sv01 x%2x sv02 x%2x sv03 x%2x sv04 x%2x "
                              "sv05 x%2x sv06 x%2x sv07 x%2x sv08 x%2x\n"
                              "     sv09 x%2x sv10 x%2x sv11 x%2x sv12 x%2x "
                              "sv13 x%2x sv14 x%2x sv15 x%2x sv16 x%2x\n"
                              "     sv17 x%2x sv18 x%2x sv19 x%2x sv20 x%2x "
                              "sv21 x%2x sv22 x%2x sv23 x%2x sv24 x%2x" %
                              tuple(sv))
                    else:
                        s += "    Reserved"

        elif 1 == u[0]:
            # SBAS
            s += self._decode_sfrbx_sbas(words)

        elif 2 == u[0]:
            # Galileo
            s += self._decode_sfrbx_gal(words)

        elif 3 == u[0]:
            # BeiDou
            s += self._decode_sfrbx_bds(words)

        elif 6 == u[0]:
            # GLONASS
            s += self._decode_sfrbx_glo(words)

        return s

    def rxm_svsi(self, buf):
        """UBX-RXM-SVSI decode, SV Status Info"""

        # not in M10, protVer 34 and up
        # Use UBX-NAV-ORB instead
        m_len = len(buf)

        u = struct.unpack_from('<LhBB', buf, 0)
        s = ' iTOW %d week %d numVis %d numSV %d' % u

        m_len -= 8
        i = 0
        while 0 < m_len:
            u = struct.unpack_from('<BBhbB', buf, 8 + i * 6)
            s += '\n  svid %3d svFlag %#x azim %3d elev % 3d age %3d' % u
            m_len -= 6
            i += 1

        return s

    # Broadcom calls this BRM-ASC-
    rxm_ids = {0x10: {'str': 'RAW', 'dec': rxm_raw, 'minlen': 8,
                      'name': 'UBX-RXM-RAW'},      # obsolete
               0x11: {'str': 'SFRB', 'dec': rxm_sfrb, 'minlen': 42,
                      'name': 'UBX-RXM-SFRB'},
               0x13: {'str': 'SFRBX', 'dec': rxm_sfrbx, 'minlen': 8,
                      'name': 'UBX-RXM-SFRBX'},
               0x14: {'str': 'MEASX', 'dec': rxm_measx, 'minlen': 44,
                      'name': 'UBX-RXM-MEASX'},
               0x15: {'str': 'RAWX', 'dec': rxm_rawx, 'minlen': 16,
                      'name': 'UBX-RXM-RAWX'},
               0x20: {'str': 'SVSI', 'dec': rxm_svsi, 'minlen': 8,
                      'name': 'UBX-RXM-SVSI'},
               # deprecated in u-blox 6, 7, raw option only
               0x30: {'str': 'ALM', 'minlen': 1, 'name': 'UBX-RXM-ALM'},
               # deprecated in u-blox 6, 7, raw option only
               0x31: {'str': 'EPH', 'minlen': 1, 'name': 'UBX-RXM-EPH'},
               0x32: {'str': 'RTCM', 'dec': rxm_rtcm, 'minlen': 8,
                      'name': 'UBX-RXM-RTCM'},
               # Broadcom calls this BRM-ASC-SCLEEP
               0x41: {'str': 'PMREQ', 'dec': rxm_pmreq, 'minlen': 4,
                      'name': 'UBX-RXM-PMREQ'},
               0x59: {'str': 'RLM', 'dec': rxm_rlm, 'minlen': 16,
                      'name': 'UBX-RXM-RLM'},
               0x61: {'str': 'IMES', 'dec': rxm_imes, 'minlen': 4,
                      'name': 'UBX-RXM-IMES'},
               # NEO-D9S, 24 to 528 bytes
               0x72: {'str': 'PMP', 'minlen': 24, 'name': 'UBX-RXM-PMP'},
               }

    # UBX-SEC-

    # UBX-SEC-SESSID in protVer 34 and up

    def sec_sign(self, buf):
        """UBX-SEC_SIGN decode, Signature of a previous message"""

        # protVer 18 to 23
        u = struct.unpack_from('<BBHBBH', buf, 0)
        s = (" version %u reserved %u %u classId x%x messageID x%x "
             " checksum %u\n  hash " % u)
        s += gps.polystr(binascii.hexlify(buf[8:39]))
        return s

    def sec_uniqid(self, buf):
        """UBX-SEC_UNIQID decode Unique chip ID

changed in protVer 34
"""

        # protVer 18 is 9 bytes
        # 10 bytes in protVer 34 and up
        m_len = len(buf)
        u = struct.unpack_from('<BBHBBBBB', buf, 0)
        s = ("  version %u reserved %u %u uniqueId %#02x%02x%02x%02x%02x"
             % u)
        if (9 < m_len):
            # version 2
            u = struct.unpack_from('<B', buf, 9)
            s += "%02x" % u

        return s

    sec_ids = {0x01: {'str': 'SIGN', 'minlen': 40, 'dec': sec_sign,
                      'name': 'UBX-SEC-SIGN'},
               0x03: {'str': 'UNIQID', 'minlen': 9, 'dec': sec_uniqid,
                      'name': 'UBX-SEC-UNIQID'},
               }

    # UBX-TIM-
    def tim_svin(self, buf):
        """UBX-TIM-SVIN decode, Survey-in data"""

        u = struct.unpack_from('<LlllLLBB', buf, 0)
        s = ('  dur %u meanX %d meanY %d meanZ %d meanV %u\n'
             '  obs %u valid %u active %u' % u)
        return s

    def tim_tm2(self, buf):
        """UBX-TIM-TM2 decode, Time mark data"""

        u = struct.unpack_from('<BBHHHLLLLL', buf, 0)
        s = ('  ch %u flags %#x count %u wnR %u wnF %u\n'
             '  towMsR %u towSubMsR %u towMsF %u towSubMsF %u accEst %u\n' % u)
        return s

    def tim_tp(self, buf):
        """UBX-TIM-TP decode, Time Pulse Timedata

qErrInvalid add in protVer 34 and up
"""

        u = struct.unpack_from('<LLlHbb', buf, 0)
        s = ('  towMS %u towSubMS %u qErr %d week %d\n'
             '  flags %#x refInfo %#x\n   flags  ' % u)

        if 0x01 & u[4]:
            s += "timeBase is UTC, "
        else:
            s += "timeBase is GNSS, "
        if 0x02 & u[4]:
            s += "UTC available, "
        else:
            s += "UTC not available, "

        raim = (u[4] >> 2) & 0x03
        if 0 == raim:
            s += "RAIM not available"
        elif 1 == raim:
            s += "RAIM not active"
        elif 2 == raim:
            s += "RAIM active"
        else:
            s += "RAIM ??"
        return s

    tim_vrfy_flags = {
        0: "no time aiding done",
        2: "source was RTC",
        3: "source was AID-IN",
        }

    def tim_vrfy(self, buf):
        """UBX-TIM-VRFY decode, Sourced Time Verification"""

        u = struct.unpack_from('<llllHBB', buf, 0)
        s = ('  itow %d frac %d deltaMs %d deltaMs %d\n'
             '  wno %u flags x%x reserved1 %u' % u)
        if gps.VERB_DECODE <= self.verbosity:
            s += ('\n   flags (%s)' %
                  index_s(u[5] & 3, self.tim_vrfy_flags))
        return s

    tim_ids = {0x01: {'str': 'TP', 'dec': tim_tp, 'minlen': 16,
                      'name': 'UBX-TIM-TP'},
               0x03: {'str': 'TM2', 'dec': tim_tm2, 'minlen': 28,
                      'name': 'UBX-TIM-TM2'},
               0x04: {'str': 'SVIN', 'dec': tim_svin, 'minlen': 28,
                      'name': 'UBX-TIM-SVIN'},
               0x06: {'str': 'VRFY', 'dec': tim_vrfy, 'minlen': 20,
                      'name': 'UBX-TIM-VRFY'},
               # u-blox 8, FTS only
               0x11: {'str': 'DOSC', 'minlen': 8, 'name': 'UBX-TIM-DOSC'},
               # u-blox 8, FTS only
               0x12: {'str': 'TOS', 'minlen': 56, 'name': 'UBX-TIM-TOS'},
               # u-blox 8, FTS only
               0x13: {'str': 'SMEAS', 'minlen': 12, 'name': 'UBX-TIM-SMEAS'},
               # u-blox 8, FTS only
               0x15: {'str': 'VCOCAL', 'minlen': 1, 'name': 'UBX-TIM-VCOCAL'},
               # u-blox 8, FTS only
               0x16: {'str': 'FCHG', 'minlen': 32, 'name': 'UBX-TIM-FCHG'},
               # u-blox 8, FTS only
               0x17: {'str': 'HOC', 'minlen': 8, 'name': 'UBX-TIM-HOC'},
               }

    # UBX-UPD-
    upd_sos_cmd = {
        0: "Create Backup File in Flash",
        1: "Clear Backup in Flash",
        2: "Backup File Creation Acknowledge",
        3: "System Restored from Backup",
        }

    upd_sos_response2 = {
        0: "Not Acknowledged",
        1: "Acknowledged",
        }

    upd_sos_response3 = {
        0: "Unknown",
        1: "Failed restoring from backup file",
        2: "Restored from backup file",
        3: "Not restored (no backup)",
        }

    def upd_sos(self, buf):
        """UBX-UPD-SOS decode, Backup File stuff"""
        m_len = len(buf)

        if 0 == m_len:
            return "  Poll Backup File Restore Status"

        if 4 > m_len:
            return "  Bad Length %s" % m_len

        u = struct.unpack_from('<BBH', buf, 0)
        s = '  command %u reserved1 x%x %x' % u

        s1 = ""
        if 0 == u[0]:
            # Create Backup in Flash
            pass
        elif 1 == u[0]:
            # Clear Backup in Flash
            pass
        elif 8 > m_len:
            s += "  Bad Length %s" % m_len
        elif 2 == u[0]:
            # Backup File Creation Acknowledge
            u1 = struct.unpack_from('<BBH', buf, 4)
            s += '\n  response %u reserved2 x%x %x' % u1
            s1 = ' response (%s)' % index_s(u1[0], self.upd_sos_response2)
        elif 3 == u[0]:
            # System Restored from Backup
            u1 = struct.unpack_from('<BBH', buf, 4)
            s += '\n  response %u reserved2 x%x %x' % u1
            s1 = ' response (%s)' % index_s(u1[0], self.upd_sos_response3)

        if gps.VERB_DECODE <= self.verbosity:
            s += '\n    cmd (%s)%s' % (index_s(u[0], self.upd_sos_cmd), s1)
        return s

    upd_ids = {
               # undocumented firmware update message
               0x0c: {'str': 'undoc1', 'minlen': 13, 'name': "UBX-UPD-undoc1"},
               0x14: {'str': 'SOS', 'dec': upd_sos, 'name': "UBX-UPD-SOS"},
               # undocumented firmware update message
               0x25: {'str': 'undoc2', 'minlen': 20, 'name': "UBX-UPD-undoc2"},
               }

    classes = {
        0x01: {'str': 'NAV', 'ids': nav_ids},
        0x02: {'str': 'RXM', 'ids': rxm_ids},
        0x04: {'str': 'INF', 'ids': inf_ids},
        0x05: {'str': 'ACK', 'ids': ack_ids},
        0x06: {'str': 'CFG', 'ids': cfg_ids},
        0x09: {'str': 'UPD', 'ids': upd_ids},
        0x0A: {'str': 'MON', 'ids': mon_ids},
        0x0B: {'str': 'AID', 'ids': aid_ids},
        0x0D: {'str': 'TIM', 'ids': tim_ids},
        0x10: {'str': 'ESF', 'ids': esf_ids},
        0x13: {'str': 'MGA', 'ids': mga_ids},
        0x21: {'str': 'LOG', 'ids': log_ids},
        0x27: {'str': 'SEC', 'ids': sec_ids},
        0x28: {'str': 'HNR', 'ids': hnr_ids},
        # Antaris 4
        # 0x4x USR, SCK Customer Messages
        0xf0: {'str': 'NMEA', 'ids': nmea_ids},
        0xf5: {'str': 'RTCM', 'ids': rtcm_ids},
    }

    def class_id_s(self, m_class, m_id):
        """Return class and ID numbers as a string."""

        s = 'Class x%02x' % (m_class)
        if (((m_class in self.classes and
              'str' in self.classes[m_class]))):
            s += ' (%s)' % (self.classes[m_class]['str'])

        s += ' ID x%02x' % (m_id)
        if (((m_class in self.classes and
              'ids' in self.classes[m_class] and
              m_id in self.classes[m_class]['ids'] and
              'str' in self.classes[m_class]['ids'][m_id]))):
            s += ' (%s)' % (self.classes[m_class]['ids'][m_id]['str'])

        return s

    def decode_msg(self, out):
        """Decode one message and then return number of chars consumed"""

        state = 'BASE'
        consumed = 0

        # decode state machine
        for this_byte in out:
            consumed += 1
            if isinstance(this_byte, str):
                # a character, probably read from a file
                c = ord(this_byte)
            else:
                # a byte, probably read from a serial port
                c = int(this_byte)

            if gps.VERB_RAW <= self.verbosity:
                if ord(' ') <= c <= ord('~'):
                    # c is printable
                    print("state: %s char %c (%#x)" % (state, chr(c), c))
                else:
                    # c is not printable
                    print("state: %s char %#x" % (state, c))

            if 'BASE' == state:
                # start fresh
                # place to store 'comments'
                comment = ''
                m_class = 0
                m_id = 0
                m_len = 0
                m_raw = bytearray(0)        # class, id, len, payload
                m_payload = bytearray(0)    # just the payload
                m_ck_a = 0
                m_ck_b = 0

                if 0xb5 == c:
                    # got header 1, mu
                    state = 'HEADER1'

                if ord('$') == c:
                    # got $, so NMEA?
                    state = 'NMEA'
                    comment = '$'

                if ord("{") == c:
                    # JSON, treat as comment line
                    state = 'JSON'

                    # start fresh
                    comment = "{"
                    continue

                if ord("#") == c:
                    # comment line
                    state = 'COMMENT'

                    # start fresh
                    comment = "#"
                    continue

                if 0xd3 == c:
                    # RTCM3 Leader 1
                    state = 'RTCM3_1'

                    # start fresh
                    comment = "#"
                    continue

                if (ord('\n') == c) or (ord('\r') == c):
                    # CR or LF, leftovers
                    return 1
                continue

            if state in ('COMMENT', 'JSON'):
                # inside comment
                if ord('\n') == c or ord('\r') == c:
                    # Got newline or linefeed
                    # terminate messages on <CR> or <LF>
                    # Done, got a full message
                    if gps.polystr('{"class":"ERROR"') in comment:
                        # always print gpsd errors
                        if 0 < self.timestamp:
                            timestamp(self.timestamp)
                        print(comment)
                    elif gps.VERB_DECODE <= self.verbosity:
                        if 0 < self.timestamp:
                            timestamp(self.timestamp)
                        print(comment)
                    return consumed

                # else:
                comment += chr(c)
                continue

            if 'NMEA' == state:
                # getting NMEA payload
                if (ord('\n') == c) or (ord('\r') == c):
                    # CR or LF, done, got a full message
                    # terminates messages on <CR> or <LF>
                    if gps.VERB_DECODE <= self.verbosity:
                        if 0 < self.timestamp:
                            timestamp(self.timestamp)
                        print(comment)
                    return consumed

                # else:
                comment += chr(c)
                continue

            if 'RTCM3_1' == state:
                # high 6 bits must be zero,
                if 0 != (c & 0xfc):
                    state = 'BASE'
                else:
                    # low 2 bits are MSB of a 10-bit length
                    m_len = c << 8
                    state = 'RTCM3_2'
                    m_raw.extend([c])
                continue

            if 'RTCM3_2' == state:
                # 8 bits are LSB of a 10-bit length
                m_len |= 0xff & c
                # add 3 for checksum
                m_len += 3
                state = 'RTCM3_PAYLOAD'
                m_raw.extend([c])
                continue

            if 'RTCM3_PAYLOAD' == state:
                m_len -= 1
                m_raw.extend([c])
                m_payload.extend([c])
                if 0 == m_len:
                    state = 'BASE'
                    ptype = m_payload[0] << 4
                    ptype |= 0x0f & (m_payload[1] >> 4)
                    if gps.VERB_DECODE <= self.verbosity:
                        print("RTCM3 packet: type %d\n" % ptype)
                continue

            if ord('b') == c and 'HEADER1' == state:
                # got header 2
                state = 'HEADER2'
                continue

            if 'HEADER2' == state:
                # got class
                state = 'CLASS'
                m_class = c
                m_raw.extend([c])
                continue

            if 'CLASS' == state:
                # got ID
                state = 'ID'
                m_id = c
                m_raw.extend([c])
                continue

            if 'ID' == state:
                # got first length
                state = 'LEN1'
                m_len = c
                m_raw.extend([c])
                continue

            if 'LEN1' == state:
                # got second length
                m_raw.extend([c])
                m_len += 256 * c
                if 0 == m_len:
                    # no payload
                    state = 'CSUM1'
                else:
                    state = 'PAYLOAD'
                continue

            if 'PAYLOAD' == state:
                # getting payload
                m_raw.extend([c])
                m_payload.extend([c])
                if len(m_payload) == m_len:
                    state = 'CSUM1'
                continue

            if 'CSUM1' == state:
                # got ck_a
                state = 'CSUM2'
                m_ck_a = c
                continue

            if 'CSUM2' == state:
                # got a complete, maybe valid, message
                if 0 < self.timestamp:
                    timestamp(self.timestamp)

                # ck_b
                state = 'BASE'
                m_ck_b = c
                # check checksum
                chk = self.checksum(m_raw, len(m_raw))
                if (chk[0] != m_ck_a) or (chk[1] != m_ck_b):
                    print("gps/ubx: ERROR checksum failed, "
                          "was (%02x,%02x) s/b (%02x, %02x)\n" %
                          (m_ck_a, m_ck_b, chk[0], chk[1]))

                s_payload = ''.join('{:02x} '.format(x) for x in m_payload)
                x_payload = ','.join(['%02x' % x for x in m_payload])

                if m_class in self.classes:
                    this_class = self.classes[m_class]
                    if 'ids' in this_class:
                        if m_id in this_class['ids']:
                            # got an entry for this message
                            # name is mandatory
                            s_payload = this_class['ids'][m_id]['name']
                            s_payload += ':\n'

                            if ((('minlen' in this_class['ids'][m_id]) and
                                 (0 == m_len) and
                                 (0 != this_class['ids'][m_id]['minlen']))):
                                s_payload += "  Poll request"
                            elif (('minlen' in this_class['ids'][m_id]) and
                                  (this_class['ids'][m_id]['minlen'] >
                                   m_len)):
                                # failed minimum length for this message
                                s_payload += "  Bad Length %s" % m_len
                            elif 'dec' in this_class['ids'][m_id]:
                                # got a decoder for this message
                                dec = this_class['ids'][m_id]['dec']
                                s_payload += dec(self, m_payload)
                            else:
                                s_payload += ("  len %#x, raw %s" %
                                              (m_len, x_payload))

                if not s_payload:
                    # huh?
                    s_payload = ("%s, len %#x, raw %s" %
                                 (self.class_id_s(m_class, m_id),
                                  m_len, x_payload))

                if gps.VERB_INFO <= self.verbosity:
                    print("%s, len: %#x" %
                          (self.class_id_s(m_class, m_id), m_len))
                    x_raw = ','.join(['%02x' % x for x in m_raw[0:4]])
                    print("header: b5,62,%s" % x_raw)
                    print("payload: %s" % x_payload)
                    print("chksum: %02x,%02x" % (m_ck_a, m_ck_b))
                print("%s\n" % s_payload)
                return consumed

            # give up
            state = 'BASE'

        # fell out of loop, no more chars to look at
        return 0

    def checksum(self, msg, m_len):
        """Calculate u-blox message checksum"""
        # the checksum is calculated over the Message, starting and including
        # the CLASS field, up until, but excluding, the Checksum Field:

        ck_a = 0
        ck_b = 0
        for c in msg[0:m_len]:
            ck_a += c
            ck_b += ck_a

        return [ck_a & 0xff, ck_b & 0xff]

    def make_pkt(self, m_class, m_id, m_data):
        """Make a message packet"""
        # always little endian, leader, class, id, length
        m_len = len(m_data)

        # build core message
        msg = bytearray(m_len + 6)
        struct.pack_into('<BBH', msg, 0, m_class, m_id, m_len)

        # copy payload into message buffer
        i = 0
        while i < m_len:
            msg[i + 4] = m_data[i]
            i += 1

        # add checksum
        chk = self.checksum(msg, m_len + 4)
        m_chk = bytearray(2)
        struct.pack_into('<BB', m_chk, 0, chk[0], chk[1])

        header = b"\xb5\x62"
        return header + msg[:m_len + 4] + m_chk

    def gps_send(self, m_class, m_id, m_data):
        """Build, and send, a message to GPS"""
        m_all = self.make_pkt(m_class, m_id, m_data)
        self.gps_send_raw(m_all)

    def gps_send_raw(self, m_all):
        """Send a raw message to GPS"""
        if not self.read_only:
            self.io_handle.ser.write(m_all)
            if gps.VERB_QUIET < self.verbosity:
                sys.stdout.write("sent:\n")
                if gps.VERB_INFO < self.verbosity:
                    sys.stdout.write(gps.polystr(binascii.hexlify(m_all)))
                    sys.stdout.write("\n")
                self.decode_msg(m_all)
                sys.stdout.flush()

    def send_able_cfg_batch(self, able, args):
        """dis/enable batching, UBX-CFG-BATCH"""

        flags = 0x0d if able else 0x0c
        m_data = []
        struct.pack_into('<BBHHBB', m_data, 0, 0, flags, 128, 0, 0, 0)
        self.gps_send(6, 0x93, m_data)

    def send_able_beidou(self, able, args):
        """dis/enable BeiDou"""
        # Two frequency GNSS receivers use BeiDou or GLONASS
        # disable, then enable
        self.send_cfg_gnss1(3, able, args)

    def send_able_binary(self, able, args):
        """dis/enable basic binary messages. -e/-d BINARY"""

        # FIXME: does not change UBX-CFG-PRT outProtoMask for current port.
        # FIXME: in u-blox 9, use VAL-SET to ensure NMEA mask on.
        # Workarouund: gpsctl -b
        # try to keep in sync with driver_ubx.c, ubx_cfg_prt()

        # UBX-NAV we always toggle
        # we assume no oddball UBX to toggle
        ubx_nav_toggle = (
            0x04,          # msg id = UBX-NAV-DOP

            # UBX-NAV-TIMEGPS
            # Note: UTC may, or may not be UBX-NAV-TIMEGPS.
            #       depending on UBX-CFG-NAV5 utcStandard
            # Note: We use TIMEGPS to get the leapS
            # UBX-NAV-TIMEGPS is a great cycle ender, NAV-EOE better
            0x20,          # msg id = UBX-NAV-TIMEGPS
            )

        # UBX for protver < 15
        ubx_14_nav_on = (
            # UBX-NAV-SOL is ECEF. deprecated in protver 14, gone in protver 27
            0x06,              # msg id = NAV-SOL
            0x30,              # msg id = NAV-SVINFO
        )

        # UBX for protver >= 15
        ubx_15_nav_on = (
            # Need NAV-POSECEF, NAV-VELECEF and NAV-PVT to replace NAV-SOL
            0x01,              # msg id = NAV-POSECEF
            0x07,              # msg id = NAV-PVT
            0x11,              # msg id = NAV-VELECEF
            0x35,              # msg id = NAV-SAT
            0x61,              # msg id = NAV-EOE, first in protver 18
        )

        # some we always turn off, user can enable later
        ubx_nav_off = (
            0x12,              # msg id = NAV-VELNED
            # turn off NAV-SBAS as the gpsd decode does not go to JSON,
            # so the data is wasted. */
            0x32,              # msg id = NAV-SBAS, in u-blox 4 to 8, not 9
            )

        rate = 1 if able else 0

        # msgClass (UBX-NAV), msgID, rate
        m_data = bytearray([0x01, 0x09, rate])
        for mid in ubx_nav_toggle:
            m_data[1] = mid
            # UBX-CFG-MSG
            self.gps_send(6, 1, m_data)

        if 15 > self.protver:
            for mid in ubx_14_nav_on:
                m_data[1] = mid
                # UBX-CFG-MSG
                self.gps_send(6, 1, m_data)

            # turn off >= 15 messages.  Yes this makes NAKs.
            m_data[2] = 0       # rate off
            for idx in ubx_15_nav_on:
                m_data[1] = idx
                # UBX-CFG-MSG
                self.gps_send(6, 1, m_data)

        else:
            for id in ubx_15_nav_on:
                m_data[1] = id
                # UBX-CFG-MSG
                self.gps_send(6, 1, m_data)

            # turn off < 15 messages.  Yes this may make NAKs.
            m_data[2] = 0       # rate off
            for id in ubx_14_nav_on:
                m_data[1] = id
                # UBX-CFG-MSG
                self.gps_send(6, 1, m_data)

        # msgClass (UBX-NAV), msgID (TIMELS), rate (0xff)
        # 0xff is about every 4 minutes if nav rate is 1Hz
        m_data = bytearray([0x01, 0x26, 0xff])
        # UBX-CFG-MSG
        self.gps_send(6, 1, m_data)

        # always off NAV messages
        m_data[2] = 0       # rate off
        for id in ubx_nav_off:
            m_data[1] = id
            # UBX-CFG-MSG
            self.gps_send(6, 1, m_data)

    def send_able_ecef(self, able, args):
        """Enable ECEF messages"""
        # set NAV-POSECEF rate
        self.send_cfg_msg(1, 1, able)
        # set NAV-VELECEF rate
        self.send_cfg_msg(1, 0x11, able)

    def send_able_gps(self, able, args):
        """dis/enable GPS/QZSS"""
        # GPS and QZSS both on, or both off, together
        # GPS
        self.send_cfg_gnss1(0, able, args)
        # QZSS
        self.send_cfg_gnss1(5, able, args)

    def send_able_galileo(self, able, args):
        """dis/enable GALILEO

"If Galileo is enabled, UBX-CFG-GNSS must be followed by UBX-CFG-RST
with resetMode set to Hardware reset."
"""
        self.send_cfg_gnss1(2, able, args)

    def send_able_glonass(self, able, args):
        """dis/enable GLONASS"""
        # Two frequency GPS use BeiDou or GLONASS
        # disable, then enable
        self.send_cfg_gnss1(6, able, args)

    def send_able_logfilter(self, able, args):
        """Enable logging"""

        if able:
            m_data = bytearray([1,            # version
                                5,            # flags
                                # All zeros below == log all
                                0, 0,         # minInterval
                                0, 0,         # timeThreshold
                                0, 0,         # speedThreshold
                                0, 0, 0, 0    # positionThreshold
                                ])
        else:
            m_data = bytearray([1,      # version
                                0,      # flags
                                0, 0,   # minInterval
                                0, 0,   # timeThreshold
                                0, 0,   # speedThreshold
                                0, 0, 0, 0    # positionThreshold
                                ])

        # set UBX-CFG-LOGFILTER
        self.gps_send(6, 0x47, m_data)

    def send_able_nav_sig(self, able, args):
        """dis/enable UBX-NAV-SIG Time Pulse"""
        rate = 1 if able else 0
        m_data = bytearray([0x1, 0x43, rate])
        self.gps_send(6, 1, m_data)

    def send_able_ned(self, able, args):
        """Enable NAV-RELPOSNED and VELNED messages.
protver 15+ required for VELNED
protver 20+, and HP GNSS, required for RELPOSNED"""
        if 15 > self.protver:
            sys.stderr.write('gps/ubx: WARNING: protver %d too low for NED\n' %
                             (self.protver))
            return

        # set NAV-VELNED rate
        self.send_cfg_msg(1, 0x12, able)

        if 20 > self.protver:
            sys.stderr.write('gps/ubx: WARNING: protver %d too low for '
                             'RELPOSNED\n' %
                             (self.protver))
            return

        # set NAV-RELPOSNED rate
        self.send_cfg_msg(1, 0x3C, able)

    def send_able_nmea(self, able, args):
        """dis/enable basic NMEA messages"""

        # try to keep in sync with driver_ubx.c, ubx_cfg_prt()
        # FIXME: does not change UBX-CFG-PRT outProtoMask for current port.
        # FIXME: in u-blox 9, use VAL-SET to ensure NMEA mask on.
        # Workarouund: gpsctl -n

        # we assume no oddball NMEA to toggle
        nmea_toggle = (
            0x00,          # msg id  = GGA
            # 0x01,        # msg id  = GLL, only need RMC */
            0x02,          # msg id  = GSA
            0x03,          # msg id  = GSV
            0x04,          # msg id  = RMC
            0x05,          # msg id  = VTG
            0x07,          # msg id  = GST, GNSS pseudorange error statistics
            0x08,          # msg id  = ZDA, for UTC year
            0x09,          # msg id  = GBS, for RAIM errors
            )

        rate = 1 if able else 0

        # msgClass (UBX-NMEA), msgID, rate
        m_data = bytearray([0xf0, 0x09, rate])
        for mid in nmea_toggle:
            m_data[1] = mid
            # UBX-CFG-MSG
            self.gps_send(6, 1, m_data)

        # xxGLL, never need it
        m_data = bytearray([0xf0, 0x01, 0])
        self.gps_send(6, 1, m_data)

    def send_able_rtcm3(self, able, args):
        """dis/enable RTCM3 1005, 1077, 1087, 1230 messages"""

        # protVer 20+, High Precision only
        # No u-blox outputs RTCM2
        # USB ONLY!

        if able:
            rate = 1
            # UBX-CFG-PRT, USB
            # can't really do other portIDs as the messages are different
            # and need data we do not have.
            # does not seem to hurt to enable all in and out, even unsupported
            m_data = bytearray(20)
            m_data[0] = 0x03         # default to USB port
            m_data[12] = 0x27        # in: RTCM3, RTCM2, NMEA and UBX
            # Ensures RTCM3 output (all) are set (outProtoMask)
            # no u-blox has RTCM2 out
            m_data[14] = 0x23        # out:  RTCM3, NMEA and UBX
            self.gps_send(0x06, 0x00, m_data)
        else:
            # leave  UBX-CFG-PRT alone
            rate = 0

        # 1005, Stationary RTK reference station ARP
        m_data = bytearray([0xf5, 0x05, rate])
        self.gps_send(6, 1, m_data)
        # 1077, GPS MSM7
        m_data = bytearray([0xf5, 0x4d, rate])
        self.gps_send(6, 1, m_data)
        # 1087, GLONASS MSM7
        m_data = bytearray([0xf5, 0x57, rate])
        self.gps_send(6, 1, m_data)
        # 1230, GLONASS code-phase biases
        m_data = bytearray([0xf5, 0xe6, rate])
        self.gps_send(6, 1, m_data)
        # we skip Galileo or BeiDou for now, unsupported by u-blox rover

        # ZED-F9P rover requires MSM7 and 4072,0 or 4072,1
        # 4072,0
        m_data = bytearray([0xf5, 0xfe, rate])
        # 4072,1
        m_data = bytearray([0xf5, 0xfd, rate])
        self.gps_send(6, 1, m_data)

    def send_able_rawx(self, able, args):
        """dis/enable UBX-RXM-RAW/RAWXX"""

        rate = 1 if able else 0
        if 15 > self.protver:
            # u-blox 7 or earlier, use RAW
            sid = 0x10
        else:
            # u-blox 8 or later, use RAWX
            sid = 0x15
        m_data = bytearray([0x2, sid, rate])
        self.gps_send(6, 1, m_data)

    def send_able_pps(self, able, args):
        """dis/enable PPS, using UBX-CFG-TP5"""

        m_data = bytearray(32)
        m_data[0] = 0         # tpIdx
        m_data[1] = 1         # version
        m_data[2] = 0         # reserved
        m_data[3] = 0         # reserved
        m_data[4] = 2         # antCableDelay
        m_data[5] = 0         # antCableDelay
        m_data[6] = 0         # rfGroupDelay
        m_data[7] = 0         # rfGroupDelay
        m_data[8] = 0x40      # freqPeriod
        m_data[9] = 0x42      # freqPeriod
        m_data[10] = 0x0f     # freqPeriod
        m_data[11] = 0        # freqPeriod
        m_data[12] = 0x40     # freqPeriodLock
        m_data[13] = 0x42     # freqPeriodLock
        m_data[14] = 0x0f     # freqPeriodLock
        m_data[15] = 0        # freqPeriodLock
        m_data[16] = 0        # pulseLenRatio
        m_data[17] = 0        # pulseLenRatio
        m_data[18] = 0        # pulseLenRatio
        m_data[19] = 0        # pulseLenRatio
        m_data[20] = 0xa0     # pulseLenRatioLock
        m_data[21] = 0x86     # pulseLenRatioLock
        m_data[22] = 0x1      # pulseLenRatioLock
        m_data[23] = 0        # pulseLenRatioLock
        m_data[24] = 0        # userConfigDelay
        m_data[25] = 0        # userConfigDelay
        m_data[26] = 0        # userConfigDelay
        m_data[27] = 0        # userConfigDelay
        m_data[28] = 0x77     # flags
        m_data[29] = 0        # flags
        m_data[30] = 0        # flags
        m_data[31] = 0        # flags
        if not able:
            m_data[28] &= ~1  # bit 0 is active

        self.gps_send(6, 0x31, m_data)

    def send_able_sbas(self, able, args):
        """dis/enable SBAS"""
        self.send_cfg_gnss1(1, able, args)

    def send_able_sfrbx(self, able, args):
        """dis/enable UBX-RXM-SFRB/SFRBX"""

        rate = 1 if able else 0
        if 15 > self.protver:
            # u-blox 7 or earlier, use SFRB
            sid = 0x11
        else:
            # u-blox 8 or later, use SFRBX
            sid = 0x13
        m_data = bytearray([0x2, sid, rate])
        self.gps_send(6, 1, m_data)

    def send_able_tmode2(self, able, args):
        """SURVEYIN, UBX-CFG-TMODE2, set time mode 2 config"""

        m_data = bytearray(28)

        # on a NEO-M8T, with good antenna
        # five minutes, gets about 1 m
        # ten minutes, gets about 0.9 m
        # twenty minutes, gets about 0.7 m
        # one hour, gets about 0.5 m
        # twelve hours, gets about 0.14 m

        # Survey-in minimum duration seconds
        seconds = 300

        # Survey-in position accuracy limit in mm
        # make it big, so the duration decides when to end survey
        mmeters = 50000          # default 50 meters

        if able:
            # enable survey-in
            m_data[0] = 1
            if args and args[0]:
                seconds = int(args[0])
            if 1 < len(args) and args[1]:
                mmeters = int(args[1])

        struct.pack_into('<LL', m_data, 20, seconds, mmeters)
        self.gps_send(6, 0x3d, m_data)

    def send_able_tmode3(self, able, args):
        """SURVEYIN3, UBX-CFG-TMODE3, set time mode 3 config"""

        m_data = bytearray(40)

        # Survey-in minimum duration seconds
        seconds = 300

        # Survey-in position accuracy limit in 0.1mm
        # make it big, so the duration decides when to end survey
        # mmeters is 5m!
        mmeters = 500000         # default 50 meters

        if able:
            # enable survey-in
            m_data[2] = 1
            if args and args[0]:
                seconds = int(args[0])
            if 1 < len(args) and args[1]:
                mmeters = int(args[1])

        struct.pack_into('<LL', m_data, 24, seconds, mmeters)
        self.gps_send(6, 0x71, m_data)

    def send_able_tp(self, able, args):
        """dis/enable UBX-TIM-TP Time Pulse"""
        rate = 1 if able else 0
        m_data = bytearray([0xd, 0x1, rate])
        self.gps_send(6, 1, m_data)

    def send_cfg_cfg(self, save_clear, args=[]):
        """UBX-CFG-CFG, save config"""

        # Save: save_clear = 0
        # Clear: save_clear = 1

        # basic configs always available to change:
        # ioPort = 1, msgConf = 2, infMsg = 4, navConf = 8, rxmConf =0x10
        cfg1 = 0x1f
        # senConf = 1, rinvConf = 2, antConf = 4, logConf = 8, ftsConf = 0x10
        cfg2 = 0x0f

        m_data = bytearray(13)

        # clear mask
        # as of protver 27, any bit in clearMask clears all
        if 0 == save_clear:
            # saving, so do not clear
            m_data[0] = 0
            m_data[1] = 0
        else:
            # clearing
            m_data[0] = cfg1
            m_data[1] = cfg2
        m_data[2] = 0       #
        m_data[3] = 0       #

        # save mask
        # as of protver 27, any bit in saveMask saves all
        if 0 == save_clear:
            # saving
            m_data[4] = cfg1
            m_data[5] = cfg2
        else:
            # clearing, so do not save
            m_data[4] = 0
            m_data[5] = 0
        m_data[6] = 0       #
        m_data[7] = 0       #

        # load mask
        # as of protver 27, any bit in loadMask loads all
        if False and 0 == save_clear:
            # saving
            m_data[8] = 0
            m_data[9] = 0
        else:
            # clearing, load it to save a reboot
            m_data[8] = cfg1
            m_data[9] = cfg2
        m_data[10] = 0      #
        m_data[11] = 0      #

        # deviceMask, where to save it, try all options
        # devBBR = 1, devFLASH = 2, devEEPROM = 4, devSpiFlash = 0x10
        m_data[12] = 0x17

        self.gps_send(6, 0x9, m_data)

    def send_cfg_gnss1(self, gnssId, enable, args):
        """UBX-CFG-GNSS, set GNSS config

WARNING: the receiver will  ACK, then ignore, many seemingly valid settings.
Always double check with "-p CFG-GNSS".
"""

        # FIXME!  Add warning if ,2 is requested on single frequency devices
        # Only u-blox 9 supports L2, except for M9N does not.

        m_data = bytearray(12)
        m_data[0] = 0       # version 0, msgVer
        m_data[1] = 0       # read only protVer 23+, numTrkChHw
        m_data[2] = 0xFF    # read only protVer 23+, numTrkChUse
        m_data[3] = 1       # 1 block follows
        # block 1
        m_data[4] = gnssId  # gnssId

        # m_data[5], resTrkCh, read only protVer 23+
        # m_data[6], maxTrkCh, read only protVer 23+
        m_data[7] = 0       # reserved1
        m_data[8] = enable  # flags
        m_data[9] = 0       # flags, unused

        # m_data[10], sigCfgMask, enable all signals
        if args:
            parm1 = args[0]
        else:
            parm1 = ''

        if 0 == gnssId:
            # GPS.  disable does not seem to work on NEO-M9N?
            m_data[5] = 8   # resTrkCh
            m_data[6] = 16  # maxTrkCh
            if '2' == parm1 and enable:
                # The NEO-M9N ACKS, then ignores if 0x11 is sent
                m_data[10] = 0x11   # flags L1C/A, L2C
            else:
                m_data[10] = 0x01   # flags L1C/A
        elif 1 == gnssId:
            # SBAS
            m_data[5] = 1   # resTrkCh
            m_data[6] = 3   # maxTrkCh
            m_data[10] = 1      # flags L1C/A
        elif 2 == gnssId:
            # Galileo
            m_data[5] = 4   # resTrkCh
            m_data[6] = 8   # maxTrkCh
            if '2' == parm1 and enable:
                # The NEO-M9N ACKS, then ignores if 0x11 is sent
                m_data[10] = 0x21   # flags E1, E5b
            else:
                m_data[10] = 0x01   # flags E1
        elif 3 == gnssId:
            # BeiDou
            m_data[5] = 2   # resTrkCh
            m_data[6] = 16  # maxTrkCh
            if '2' == parm1 and enable:
                # The NEO-M9N ACKS, then ignores if 0x11 is sent
                m_data[10] = 0x11   # flags B1I, B2I
            else:
                m_data[10] = 0x01   # flags B1I
        elif 4 == gnssId:
            # IMES
            m_data[5] = 0   # resTrkCh
            m_data[6] = 8   # maxTrkCh
            m_data[10] = 1      # flags L1
        elif 5 == gnssId:
            # QZSS
            m_data[5] = 0   # resTrkCh
            m_data[6] = 3   # maxTrkCh
            if '2' == parm1 and enable:
                # The NEO-M9N ACKS, then ignores if 0x11 is sent
                m_data[10] = 0x15   # flags L1C/A, L1S, L2C
            else:
                m_data[10] = 0x05   # flags L1C/A, L1S
        elif 6 == gnssId:
            # GLONASS
            m_data[5] = 8   # resTrkCh
            m_data[6] = 14  # maxTrkCh
            if '2' == parm1 and enable:
                # The NEO-M9N ACKS, then ignores if 0x11 is sent
                m_data[10] = 0x11   # flags L1, L2
            else:
                m_data[10] = 0x01   # flags L1
        else:
            # what else?
            m_data[10] = 1      # flags L1

        m_data[11] = 0          # flags, bits 24:31, unused
        self.gps_send(6, 0x3e, m_data)

    def poll_cfg_inf(self):
        """UBX-CFG-INF, poll"""

        m_data = bytearray(1)
        m_data[0] = 0        # UBX
        self.gps_send(6, 0x02, m_data)

        m_data[0] = 1        # NMEA
        self.gps_send(6, 0x02, m_data)

    def send_poll_cfg_msg(self, args):
        """UBX-CFG-MSG, mandatory args: class, ID, optional rate"""

        if 0 == len(args):
            sys.stderr.write('gps/ubx: ERROR: CFG-MSG missing class\n')
            sys.exit(1)
        if 1 == len(args):
            sys.stderr.write('gps/ubx: ERROR: CFG-MSG,x%x missing ID\n' %
                             (args[0]))
            sys.exit(1)

        if 2 < len(args):
            # optional set rate
            m_data = bytearray(3)
            m_data[2] = int(args[2])
        else:
            m_data = bytearray(2)
        m_data[0] = int(args[0])
        m_data[1] = int(args[1])

        self.gps_send(6, 1, m_data)

    def send_cfg_nav5_model(self, args):
        """MODEL, UBX-CFG-NAV5, set dynamic platform model"""

        m_data = bytearray(36)
        if 0 < len(args):
            m_data[0] = 1        # just setting dynamic model
            m_data[1] = 0        # just setting dynamic model
            m_data[2] = int(args[0])
        # else:
        # Just polling deprecated

        self.gps_send(6, 0x24, m_data)

    def send_cfg_msg(self, m_class, m_id, rate=None):
        """UBX-CFG-MSG, poll, or set, message rates decode"""
        m_data = bytearray(2)
        m_data[0] = m_class
        m_data[1] = m_id
        if rate is not None:
            m_data.extend([rate])
        self.gps_send(6, 1, m_data)

    def send_cfg_pms(self, args):
        """UBX-CFG-PMS, poll/set Power Management Settings"""

        if 0 < len(args):
            m_data = bytearray(8)
            # set powerSetupValue to mode
            m_data[1] = int(args[0])
            # leave period and onTime zero, which breaks powerSetupValue = 3
        else:
            # just poll, DEPRECATED
            m_data = []

        self.gps_send(6, 0x86, m_data)

    def send_cfg_prt(self, args=None):
        """UBX-CFG-PRT, get I/O Port settings"""

        if 0 == len(args):
            # get current port
            m_data = []
        else:
            # get specified port
            # seems broken on ZED-F9P
            m_data = bytearray([int(args[0])])
        self.gps_send(6, 0x0, m_data)

    def send_cfg_rate(self, args):
        """UBX-CFG-RATE, poll/set rate settings"""

        if 0 == len(args):
            # poll
            self.gps_send(6, 0x08, [])
            return

        m_data = bytearray(6)
        measRate = int(args[0])
        navRate = 1
        timeRef = 1
        if 1 < len(args):
            navRate = int(args[1])
            if 2 < len(args):
                timeRef = int(args[2])

        struct.pack_into('<HHH', m_data, 0, measRate, navRate, timeRef)
        self.gps_send(6, 0x08, m_data)

    def send_cfg_rst(self, reset_type):
        """UBX-CFG-RST, reset"""
        # Always do a hardware reset
        # If on native USB: both Hardware reset (0) and Software reset (1)
        # will disconnect and reconnect, giving you a new /dev/tty.
        m_data = bytearray(4)
        m_data[0] = reset_type & 0xff
        m_data[1] = (reset_type >> 8) & 0xff
        self.gps_send(6, 0x4, m_data)

    def send_cfg_rxm(self, args):
        """UBX-CFG-RXM, poll/set low power mode"""

        if 0 == len(args):
            # poll
            m_data = []
        else:
            # lpMode
            m_data = bytearray([0, int(args[0])])

        self.gps_send(6, 0x11, m_data)

    def send_cfg_slas(self, args):
        """UBX-CFG-SLAS, poll/set SLAS mode"""

        if 0 == len(args):
            # poll
            m_data = []
        else:
            # mode
            m_data = bytearray(4)
            m_data[0] = int(args[0])

        self.gps_send(6, 0x8d, m_data)

    def send_cfg_tp5(self, args):
        """UBX-CFG-TP5, get time0 decodes"""

        if 0 == len(args):
            # poll default tpIdx 0
            m_data = []
        else:
            # tpIdx
            m_data = bytearray([int(args[0])])

        self.gps_send(6, 0x31, m_data)

    def send_set_speed(self, speed):
        """"UBX-CFG-PRT, set port"""
        port = self.port
        # FIXME!  Determine and use current port as default
        if port is None:
            port = 1  # Default to port 1 (UART/UART_1)

        if port not in set([1, 2]):
            sys.stderr.write('gps/ubx: Invalid UART port - %d\n' %
                             (port))
            sys.exit(2)

        # FIXME!  Poll current masks, then adjust speed
        m_data = bytearray(20)
        m_data[0] = port
        m_data[4] = 0xc0          # 8N1
        m_data[5] = 0x8           # 8N1

        m_data[8] = speed & 0xff
        m_data[9] = (speed >> 8) & 0xff
        m_data[10] = (speed >> 16) & 0xff
        m_data[11] = (speed >> 24) & 0xff

        m_data[12] = 3             # in, ubx and nmea
        m_data[14] = 3             # out, ubx and nmea
        self.gps_send(6, 0, m_data)

    def send_cfg_valdel(self, keys):
        """UBX-CFG-VALDEL, delete config items by key"""
        # present in u-blox NEO-D9S+, protver 24
        # present in 9-series and higher

        m_data = bytearray(4)
        m_data[0] = 0       # version, 0 = transactionless, 1 = transaction
        m_data[1] = 6       # 2 = BBR, 4 = flash
        # can not delete RAM layer!
        # so options stay set until reset!

        for key in keys:
            k_data = bytearray(4)
            k_data[0] = (key) & 0xff
            k_data[1] = (key >> 8) & 0xff
            k_data[2] = (key >> 16) & 0xff
            k_data[3] = (key >> 24) & 0xff
            m_data.extend(k_data)
        self.gps_send(0x06, 0x8c, m_data)

    def send_cfg_valget(self, keys, layer, position):
        """UBX-CFG-VALGET, get config items by key"""

        # present in u-blox NEO-D9S+, protver 24
        # present in 9-series and higher

        m_data = bytearray(4)
        # version, 0 = request, 1 = answer
        # RAM layer
        # position
        struct.pack_into('<BBH', m_data, 0, 0, 0, position)

        k_data = bytearray(4)
        for key in keys:
            struct.pack_into('<L', k_data, 0, key)
            m_data.extend(k_data)

        if layer is None:
            # blast them for now, should do one at a time...
            for lyr in set([0, 1, 2, 7]):
                m_data[1] = lyr
                self.gps_send(0x06, 0x8b, m_data)
        else:
            m_data[1] = layer
            self.gps_send(0x06, 0x8b, m_data)

    def send_cfg_valset(self, nvs):
        """UBX-CFG-VALSET, set config items by key/val pairs"""

        # present in u-blox NEO-D9S+, protver 24
        # present in 9-series and higher

        m_data = bytearray(4)
        m_data[0] = 0      # version, 0 = request, 1 = transaction
        m_data[1] = 0x7    # RAM layer, 1=RAM, 2=BBR, 4=Flash

        for nv in nvs:
            size = 4
            nv_split = nv.split(',')
            name = nv_split[0]
            val = nv_split[1]
            if 3 <= len(nv_split):
                m_data[1] = int(nv_split[2])

            item = self.cfg_by_name(name)
            key = item[1]
            # val_type = item[2]  # unused

            cfg_type = self.item_to_type(item)

            size = 4 + cfg_type[0]
            frmat = cfg_type[1]
            flavor = cfg_type[2]
            if 'u' == flavor:
                val1 = int(val)
            elif 'i' == flavor:
                val1 = int(val)
            elif 'f' == flavor:
                val1 = float(val)

            kv_data = bytearray(size)
            kv_data[0] = (key) & 0xff
            kv_data[1] = (key >> 8) & 0xff
            kv_data[2] = (key >> 16) & 0xff
            kv_data[3] = (key >> 24) & 0xff

            struct.pack_into(frmat, kv_data, 4, val1)
            m_data.extend(kv_data)
        self.gps_send(0x06, 0x8a, m_data)

    def send_log_findtime(self, args):
        """UBX-LOG-FINDTIME, search log for y,m,d,h,m,s"""
        m_data = bytearray(10)
        m_data[0] = 0      # version, 0 = request
        m_data[1] = 0      # type, 0 = request
        # the doc says two reserved bytes here, the doc is wrong
        # searches for before 1 Jan 2004 always fail
        year = 2004
        month = 1
        day = 1
        hour = 0
        minute = 0
        second = 0

        if 0 < len(args):
            year = int(args[0])
            if 1 < len(args):
                month = int(args[1])
                if 2 < len(args):
                    day = int(args[2])
                    if 3 < len(args):
                        hour = int(args[3])
                        if 4 < len(args):
                            minute = int(args[4])
                            if 5 < len(args):
                                second = int(args[5])

        m_data[2] = year % 256                # year 1-65635
        m_data[3] = int(year / 256) & 0xff    # year
        m_data[4] = month                     # month 1-12
        m_data[5] = day                       # day 1-31
        m_data[6] = hour                      # hour 0-23
        m_data[7] = minute                    # minute 0-59
        m_data[8] = second                    # second 0-60
        m_data[9] = 0      # reserved
        self.gps_send(0x21, 0x0e, m_data)

    def send_log_retrieve(self, args):
        """UBX-LOG-RETRIEVE, gets logs from start,count"""
        m_data = bytearray(12)

        # defaults
        startNumber = 0
        entryCount = 256      # max 256

        if 0 < len(args):
            startNumber = int(args[0])
            if 1 < len(args):
                entryCount = int(args[1])

        struct.pack_into('<LLB', m_data, 0, startNumber, entryCount, 0)
        self.gps_send(0x21, 0x09, m_data)

    def send_log_string(self, args):
        """UBX-LOG-STRING, send string to log"""

        if 0 < len(args):
            s = args[0:256]
        else:
            s = "Hi"

        m_data = gps.polybytes(s)
        self.gps_send(0x21, 0x04, m_data)

    def send_poll(self, m_data):
        """generic send poll request"""
        self.gps_send(m_data[0], m_data[1], m_data[2:])

    CFG_ANT = [0x06, 0x13]
    CFG_BATCH = [0x06, 0x93]
    CFG_DAT = [0x06, 0x06]
    CFG_GNSS = [0x06, 0x3e]
    CFG_GEOFENCE = [0x06, 0x69]
    CFG_INF_0 = [0x06, 0x02, 0]
    CFG_INF_1 = [0x06, 0x02, 1]
    CFG_LOGFILTER = [0x06, 0x47]
    CFG_ODO = [0x06, 0x1e]
    CFG_PRT = [0x06, 0x00]     # current port only
    CFG_NAV5 = [0x06, 0x24]
    CFG_NAVX5 = [0x06, 0x23]
    CFG_NMEA = [0x06, 0x17]
    CFG_PM2 = [0x06, 0x3b]
    CFG_PMS = [0x06, 0x86]
    CFG_RATE = [0x06, 0x08]
    CFG_RXM = [0x06, 0x11]
    CFG_TMODE3 = [0x06, 0x71]
    CFG_TP5 = [0x06, 0x31]
    CFG_USB = [0x06, 0x1b]
    LOG_INFO = [0x21, 0x08]
    MON_COMMS = [0x0a, 0x36]
    MON_GNSS = [0x0a, 0x28]
    MON_HW = [0x0a, 0x09]
    MON_HW2 = [0x0a, 0x0b]
    MON_HW3 = [0x0a, 0x37]
    MON_IO = [0x0a, 0x02]
    MON_MSGPP = [0x0a, 0x06]
    MON_RF = [0x0a, 0x38]
    MON_RXBUF = [0x0a, 0x0a]
    MON_TXBUF = [0x0a, 0x08]
    MON_VER = [0x0a, 0x04]
    NAV_SVIN = [0x01, 0x3b]
    TIM_SVIN = [0x0d, 0x04]

    def get_config(self):
        """CONFIG.  Get a bunch of config messages"""

        cmds = [ubx.MON_VER,          # UBX-MON-VER
                ubx.CFG_ANT,          # UBX-CFG-ANT
                ubx.CFG_DAT,          # UBX-CFG-DAT
                # skip UBX-CFG-DGNSS, HP only
                # skip UBX-CFG-DOSC, FTS only
                # skip UBX-CFG-ESRC, FTS only
                ubx.CFG_GEOFENCE,     # UBX-CFG-GEOFENCE
                ubx.CFG_GNSS,         # UBX-CFG-GNSS
                # skip UBX-CFG-HNR, ADR, UDR, only
                ubx.CFG_INF_0,        # UBX-CFG-INF
                ubx.CFG_INF_1,
                # skip UBX-CFG-ITFM
                ubx.CFG_LOGFILTER,    # UBX-CFG-LOGFILTER
                ubx.CFG_NAV5,         # UBX-CFG-NAV5
                ubx.CFG_NAVX5,        # UBX-CFG-NAVX5
                ubx.CFG_NMEA,         # UBX-CFG-NMEA
                ubx.CFG_ODO,          # UBX-CFG-ODO
                ubx.CFG_PRT,          # UBX-CFG-PRT
                ubx.CFG_PM2,          # UBX-CFG-PM2
                ubx.CFG_PMS,          # UBX-CFG-PMS
                ubx.CFG_RATE,         # UBX-CFG-RATE
                ubx.CFG_RXM,          # UBX-CFG-RXM
                ubx.CFG_TP5,          # UBX-CFG-TP5
                ubx.CFG_USB,          # UBX-CFG-USB
                ]

        if 20 < self.protver:
            cmds.append(ubx.CFG_TMODE3)  # UBX-CFG-TMODE3, protVer 20+
        if 22 < self.protver:
            cmds.append(ubx.CFG_BATCH)   # UBX-CFG-BATCH, protVer 23.01+

        # blast them for now, should do one at a time...
        for cmd in cmds:
            self.send_poll(cmd)

    def get_status(self):
        """STATUS.  Get a bunch of status messages"""

        cmds = [ubx.MON_VER,          # UBX-MON-VER
                ubx.LOG_INFO,         # UBX-LOG-INFO
                ubx.MON_GNSS,         # UBX-MON-GNSS
                # UBX-MON-PATH, skipping
                ]

        if 27 <= self.protver:
            cmds.extend([ubx.MON_COMMS,        # UBX-MON-COMMS
                         ubx.MON_HW3,          # UBX-MON-HW3
                         ])
        else:
            # deprecated in 27+
            cmds.extend([ubx.MON_HW,           # UBX-MON-HW
                         ubx.MON_HW2,          # UBX-MON-HW2
                         ubx.MON_IO,           # UBX-MON-IO
                         ubx.MON_MSGPP,        # UBX-MON-MSGPP
                         ubx.MON_RF,           # UBX-MON-RF
                         ubx.MON_RXBUF,        # UBX-MON-RXBUF
                         ubx.MON_TXBUF,        # UBX-MON-TXBUF
                         ])

        # should only send these for Time or HP products
        cmds.extend([ubx.NAV_SVIN,        # UBX-NAV-SVIN
                     ubx.TIM_SVIN,        # UBX-TIM-SVIN
                     ])

        # blast them for now, should do one at a time...
        for cmd in cmds:
            self.send_poll(cmd)

    able_commands = {
        # en/dis able BATCH
        "BATCH": {"command": send_able_cfg_batch,
                  "help": "batching, using CFG-BATCH"},
        # en/dis able BeiDou
        "BEIDOU": {"command": send_able_beidou,
                   "help": "BeiDou B1. BEIDOU,5 for B1 and B2"},
        # en/dis able basic binary messages
        "BINARY": {"command": send_able_binary,
                   "help": "basic binary messages"},
        # en/dis able ECEF
        "ECEF": {"command": send_able_ecef,
                 "help": "ECEF"},
        # en/dis able GPS
        "GPS": {"command": send_able_gps,
                "help": "GPS and QZSS L1C/A. GPS,2 for L1C/A and L2C"},
        # en/dis able GALILEO
        "GALILEO": {"command": send_able_galileo,
                    "help": "GALILEO E1. GALILEO,2 for E1 and E5b"},
        # en/dis able GLONASS
        "GLONASS": {"command": send_able_glonass,
                    "help": "GLONASS L1. GLONASS,2 for L1 and L2"},
        # en/dis able LOG
        "LOG": {"command": send_able_logfilter,
                "help": "Data Logger"},
        # en/dis able NAV-SIG Cmessage
        "NAV-SIG": {"command": send_able_nav_sig,
                    "help": "NAV-SIG Signal Information message"},
        # en/dis able NED
        "NED": {"command": send_able_ned,
                "help": "NAV-VELNED and NAV-RELPOSNED"},
        # en/dis able basic NMEA messages
        "NMEA": {"command": send_able_nmea,
                 "help": "basic NMEA messages"},
        # en/dis able RAW/RAWX
        "RAWX": {"command": send_able_rawx,
                 "help": "RAW/RAWX measurements"},
        # en/dis able PPS
        "PPS": {"command": send_able_pps,
                "help": "PPS on TIMPULSE"},
        # en/dis able SBAS
        "SBAS": {"command": send_able_sbas,
                 "help": "SBAS L1C"},
        # en/dis able SFRB/SFRBX
        "SFRBX": {"command": send_able_sfrbx,
                  "help": "SFRB/SFRBX subframes"},
        # en/dis able TP time pulse message (deprecated)
        "TIM-TP": {"command": send_able_tp,
                   "help": "TIM-TP Time Pulse message"},
        # en/dis able TP time pulse message
        "TP": {"command": send_able_tp,
               "help": "TP Time Pulse message (Deprecated, use TIM-TP)"},
        # en/dis able TMODE2 Survey-in
        "SURVEYIN": {"command": send_able_tmode2,
                     "help": "Survey-in mode with TMODE2.\n"
                             "                    "
                             " SURVEYIN2[,svinMinDur[,svinAccLimit]]\n"
                             "                    "
                             "Default svinMinDur 300 seconds\n"
                             "                    "
                             "Default svinAccLimit 50000",
                     "args": 1},
        # en/dis able TMODE3 Survey-in
        "SURVEYIN3": {"command": send_able_tmode3,
                      "help": "Survey-in mode with TMODE3.\n"
                              "                    "
                              " SURVEYIN3[,svinMinDur[,svinAccLimit]]\n"
                              "                    "
                              "Default svinMinDur 300 seconds\n"
                              "                    "
                              "Default svinAccLimit 500000",
                      "args": 1},
        # en/dis able RTCM3 messages 1005, 1077, 1087, 1230
        "RTCM3": {"command": send_able_rtcm3,
                  "help": "required RTCM3 messages. USB port only"},
    }
    commands = {
        # UBX-CFG-RST
        "COLDBOOT": {"command": send_cfg_rst,
                     "help": "UBS-CFG-RST coldboot the GPS",
                     "opt": 0xffff},
        # CONFIG
        "CONFIG": {"command": get_config,
                   "help": "Get a lot of receiver config"},
        # UBX-CFG-RST
        "HOTBOOT": {"command": send_cfg_rst,
                    "help": "UBX-CFG-RST hotboot the GPS",
                    "opt": 0},
        # UBX-CFG-NAV5
        "MODEL": {"command": send_cfg_nav5_model,
                  "help": "set UBX-CFG-NAV5 Dynamic Platform Model. "
                          "MODEL,model",
                  "args": 1},
        # UBX-CFG-CFG
        "RESET": {"command": send_cfg_cfg,
                  "help": "UBX-CFG-CFG reset config to defaults",
                  "opt": 1},
        # UBX-CFG-CFG
        "SAVE": {"command": send_cfg_cfg,
                 "help": "UBX-CFG-CFG save current config",
                 "opt": 0},
        # STATUS
        "STATUS": {"command": get_status,
                   "help": "Get a lot of receiver status"},
        # UBX-CFG-RST
        "WARMBOOT": {"command": send_cfg_rst,
                     "help": "UBX-CFG-RST warmboot the GPS",
                     "opt": 1},
        # UBX-AID-* removed from ProtVer 34 and up.
        # UBX-AID-ALM
        "AID-ALM": {"command": send_poll, "opt": [0x0b, 0x30],
                    "help": "poll UBX-AID-ALM Poll GPS Aiding Almanac Data"},
        # UBX-AID-AOP
        "AID-AOP": {"command": send_poll, "opt": [0x0b, 0x33],
                    "help": "poll UBX-AID-AOP Poll Poll AssistNow "
                    "Autonomous data"},
        # UBX-AID-DATA
        "AID-DATA": {"command": send_poll, "opt": [0x0b, 0x10],
                     "help": "Poll all GPS Initial Aiding Data"},
        # UBX-AID-EPH
        "AID-EPH": {"command": send_poll, "opt": [0x0b, 0x31],
                    "help": "poll UBX-AID-EPH Poll GPS Aiding Ephemeris Data"},
        # UBX-AID-HUI
        "AID-HUI": {"command": send_poll, "opt": [0x0b, 0x02],
                    "help": "poll UBX-AID-HUI Poll GPS Health, UTC, Iono"},
        # UBX-AID-INI
        "AID-INI": {"command": send_poll, "opt": [0x0b, 0x01],
                    "help": "poll UBX-AID-INI Poll Aiding position, time,\n"
                    "                    "
                    "frequency, clock drift"},
        # UBX-CFG-ANT
        "CFG-ANT": {"command": send_poll, "opt": [0x06, 0x13],
                    "help": "poll UBX-CFG-ANT antenna config"},
        # UBX-CFG-BATCH
        # Assume 23 is close enough to the proper 23.01
        "CFG-BATCH": {"command": send_poll, "opt": [0x06, 0x93],
                      "help": "poll UBX-CFG-BATCH data batching config",
                      "minVer": 23},
        # UBX-CFG-DAT
        "CFG-DAT": {"command": send_poll, "opt": [0x06, 0x06],
                    "help": "poll UBX-CFG-DAT Datum Setting"},
        # UBX-CFG-DGNSS
        "CFG-DGNSS": {"command": send_poll, "opt": [0x06, 0x70],
                      "help": "poll UBX-CFG-DGNSS DGNSS configuration"},
        # UBX-CFG-DOSC
        "CFG-DOSC": {"command": send_poll, "opt": [0x06, 0x61],
                     "help": "poll UBX-CFG-DOSC Disciplined oscillator "
                     "configuration"},
        # UBX-CFG-ESRC
        "CFG-ESRC": {"command": send_poll, "opt": [0x06, 0x60],
                     "help": "poll UBX-CFG-ESRC External synchronization "
                     "source config"},
        # UBX-CFG-FXN
        "CFG-FXN": {"command": send_poll, "opt": [0x06, 0x0e],
                    "help": "poll UBX-CFG-FXN FXN Configuration"},
        # UBX-CFG-GEOFENCE
        "CFG-GEOFENCE": {"command": send_poll, "opt": [0x06, 0x69],
                         "help": "poll UBX-CFG-GEOFENCE Geofencing "
                         "configuration"},
        # UBX-CFG-GNSS
        "CFG-GNSS": {"command": send_poll, "opt": [0x06, 0x3e],
                     "help": "poll UBX-CFG-GNSS GNSS config"},
        # UBX-CFG-HNR
        "CFG-HNR": {"command": send_poll, "opt": [0x06, 0x5c],
                    "help": "poll UBX-CFG-HNR High Navigation Rate Settings"},
        # UBX-CFG-INF
        "CFG-INF": {"command": poll_cfg_inf,
                    "help": "poll UBX-CFG-INF Information Message "
                            "Configuration"},
        # UBX-CFG-ITFM
        "CFG-ITFM": {"command": send_poll, "opt": [0x06, 0x39],
                     "help": "poll UBX-CFG-ITFM Jamming/Interference "
                     "Monitor configuration"},
        # UBX-CFG-LOGFILTER
        "CFG-LOGFILTER": {"command": send_poll, "opt": [0x06, 0x47],
                          "help": "poll UBX-CFG-LOGFILTER "
                          " Data Logger Configuration",
                          "minVer": 14},
        # UBX-CFG-MSG
        "CFG-MSG": {"command": send_poll_cfg_msg,
                    "help": "poll/set UBX-CFG-MSG,class,ID[,rate]\n"
                            "                    "
                            "rate is optional and sets rate.",
                    "args": 2},
        # UBX-CFG-NAV5
        "CFG-NAV5": {"command": send_poll, "opt": [0x06, 0x24],
                     "help": "poll UBX-CFG-NAV5 Nav Engines settings"},
        # UBX-CFG-NAVX5
        "CFG-NAVX5": {"command": send_poll, "opt": [0x06, 0x23],
                      "help": "poll UBX-CFG-NAVX5 Nav Expert Settings"},
        # UBX-CFG-NMEA
        "CFG-NMEA": {"command": send_poll, "opt": [0x06, 0x17],
                     "help": "poll UBX-CFG-NMEA Extended NMEA protocol "
                             "configuration V1"},
        # UBX-CFG-ODO
        "CFG-ODO": {"command": send_poll, "opt": [0x06, 0x1e],
                    "help": "poll UBX-CFG-ODO Odometer, Low-speed COG "
                            "Engine Settings"},
        # UBX-CFG-PM
        "CFG-PM": {"command": send_poll, "opt": [0x06, 0x32],
                   "help": "poll UBX-CFG-PM Power management settings"},
        # UBX-CFG-PM2
        "CFG-PM2": {"command": send_poll, "opt": [0x06, 0x3b],
                    "help": "poll UBX-CFG-PM2 Extended power management "
                    "settings"},
        # UBX-CFG-PMS
        "CFG-PMS": {"command": send_cfg_pms,
                    "help": "poll/set UBX-CFG-PMS power management settings\n"
                            "                    "
                            "CFG-PMS[,powerSetupValue]",
                    "args": 1},
        # UBX-CFG-PRT
        "CFG-PRT": {"command": send_cfg_prt,
                    "help": "poll UBX-CFG-PRT I/O port settings.\n"
                            "                    "
                            "CFG-PRT[,portID] defaults to current port",
                    "args": 1},
        # TODO: UBX-CFG-PWR
        # UBX-CFG-RATE
        "CFG-RATE": {"command": send_cfg_rate,
                     "help": "poll/set UBX-CFG-RATE measure/nav settings.\n"
                             "                    "
                             "CFG-RATE[,measRate,[navRate]]",
                     "args": 2},
        # UBX-CFG-RINV
        "CFG-RINV": {"command": send_poll, "opt": [0x06, 0x34],
                     "help": "poll UBX-CFG-RINV Contents of Remote Inventory"},
        # UBX-CFG-RST, see COLDBOOT, WARMBOOT, HOTBOOT
        # UBX-CFG-RXM
        "CFG-RXM": {"command": send_cfg_rxm,
                    "help": "poll/set UBX-CFG-RXM RXM configuration.\n"
                            "                    "
                            "CFG-RXM[,lpMode]",
                    "args": 1},
        # UBX-CFG-SBAS
        "CFG-SBAS": {"command": send_poll, "opt": [0x06, 0x16],
                     "help": "poll UBX-CFG-SBAS SBAS settings"},
        # UBX-CFG-SLAS
        "CFG-SLAS": {"command": send_cfg_slas,
                     "help": "poll/set UBX-CFG-SLAS SLAS configuration.\n"
                             "                    "
                             "CFG-SLAS[,mode]",
                     "args": 1},
        # UBX-CFG-SMGR
        "CFG-SMGR": {"command": send_poll, "opt": [0x06, 0x62],
                     "help": "poll UBX-CFG-SMGR Synchronization manager "
                     "configuration"},
        # UBX-CFG-TMODE
        "CFG-TMODE": {"command": send_poll, "opt": [0x06, 0x1d],
                      "help": "poll UBX-CFG-TMODE time mode settings",
                      "maxVer": 6},
        # UBX-CFG-TMODE2
        "CFG-TMODE2": {"command": send_poll, "opt": [0x06, 0x3d],
                       "help": "poll UBX-CFG-TMODE2 time mode 2 config",
                       "minVer": 14},
        # UBX-CFG-TMODE3
        "CFG-TMODE3": {"command": send_poll, "opt": [0x06, 0x71],
                       "help": "poll UBX-CFG-TMODE3 time mode 3 config",
                       "minVer": 20},
        # UBX-CFG-TP
        "CFG-TP": {"command": send_poll, "opt": [0x06, 0x07],
                   "help": "poll UBX-CFG-TP TimePulse Parameters."},
        # UBX-CFG-TP5
        "CFG-TP5": {"command": send_cfg_tp5,
                    "help": "poll UBX-TIM-TP5 time pulse decodes.\n"
                            "                    "
                            "CFG-TP5[,tpIdx]  Default tpIdx is 0",
                    "args": 1},
        # UBX-CFG-USB
        "CFG-USB": {"command": send_poll, "opt": [0x06, 0x1b],
                    "help": "poll UBX-CFG-USB USB config"},
        # UBX-ESF-INS
        "ESF-INS": {"command": send_poll, "opt": [0x10, 0x15],
                    "help": "poll UBX-ESF-INS Vehicle dynamics info"},
        # UBX-ESF-MEAS
        "ESF-MEAS": {"command": send_poll, "opt": [0x10, 0x02],
                     "help": "poll UBX-ESF-MEAS External sensor fusion "
                             "measurements"},
        # UBX-ESF-STATUS
        "ESF-STATUS": {"command": send_poll, "opt": [0x10, 0x10],
                       "help": "poll UBX-ESF-STATUS External sensor fusion "
                               "status"},
        # UBX-LOG-CREATE
        "LOG-CREATE": {"command": send_poll,
                       "opt": [0x21, 0x07, 0, 1, 0, 0, 0, 0, 0, 0],
                       "help": "send UBX-LOG-CREATE",
                       "minVer": 14},
        # UBX-LOG-ERASE
        "LOG-ERASE": {"command": send_poll, "opt": [0x21, 0x03],
                      "help": "send UBX-LOG-ERASE",
                      "minVer": 14},
        # UBX-LOG-FINDTIME
        "LOG-FINDTIME": {"command": send_log_findtime,
                         "help": "search logs by time. "
                                 "LOG-FINDTIME,y,m,d,h,m,s\n"
                                 "                    "
                                 "all parameters optional",
                         "args": 6},
        # UBX-LOG-INFO
        "LOG-INFO": {"command": send_poll, "opt": [0x21, 0x08],
                     "help": "poll UBX-LOG-INFO",
                     "minVer": 14},
        # UBX-LOG-RETRIEVE
        "LOG-RETRIEVE": {"command": send_log_retrieve,
                         "help": "send UBX-LOG-RETRIEVE. "
                                 "LOG-RETRIEVE[,start,[count]]",
                         "minVer": 14,
                         "args": 2},
        # UBX-LOG-RETRIEVEBATCH
        # Assume 23 is close enough to the proper 23.01
        "LOG-RETRIEVEBATCH": {"command": send_poll,
                              "opt": [0x21, 0x10, 0, 1, 0, 0],
                              "help": "send UBX-LOG-RETRIEVEBATCH",
                              "minVer": 23},
        # UBX-LOG-STRING
        "LOG-STRING": {"command": send_log_string,
                       "help": "send UBX-LOG-STRING. LOG-STRING[,string]",
                       "minVer": 14,
                       "args": 1},
        # UBX-MGA-DBD
        "MGA-DBD": {"command": send_poll, "opt": [0x13, 0x80],
                    "help": "poll UBX-MGA-DBD Poll the Navigation Database"},
        # UBX-MON-BATCH
        # Assume 23 is close enough to the proper 23.01
        "MON-BATCH": {"command": send_poll, "opt": [0x0a, 0x32],
                      "help": "poll UBX-MON-BATCH Data batching "
                      "buffer status",
                      "maxVer": 23.99,
                      "minVer": 23},
        # UBX-MON-COMMS
        "MON-COMMS": {"command": send_poll, "opt": [0x0a, 0x36],
                      "help": "poll UBX-MON-COMMS Comm port information"},
        # UBX-MON-GNSS
        "MON-GNSS": {"command": send_poll, "opt": [0x0a, 0x28],
                     "help": "poll UBX-MON-GNSS major GNSS selection"},
        # UBX-MON-HW
        "MON-HW": {"command": send_poll, "opt": [0x0a, 0x09],
                   "help": "poll UBX-MON-HW Hardware Status"},
        # UBX-MON-HW2
        "MON-HW2": {"command": send_poll, "opt": [0x0a, 0x0b],
                    "help": "poll UBX-MON-HW2 Extended Hardware Status"},
        # UBX-MON-HW3
        "MON-HW3": {"command": send_poll, "opt": [0x0a, 0x37],
                    "help": "poll UBX-MON-HW3 HW I/O pin information"},
        # UBX-MON-IO
        "MON-IO": {"command": send_poll, "opt": [0x0a, 0x02],
                   "help": "poll UBX-MON-IO I/O Subsystem Status"},
        # UBX-MON-MSGPP
        "MON-MSGPP": {"command": send_poll, "opt": [0x0a, 0x06],
                      "help": "poll UBX-MON-MSGPP Message Parese and "
                              "Process Status"},
        # UBX-MON-PATCH
        "MON-PATCH": {"command": send_poll, "opt": [0x0a, 0x27],
                      "help": "poll UBX-MON-PATCH Info on Installed Patches"},
        # UBX-MON-RF
        "MON-RF": {"command": send_poll, "opt": [0x0a, 0x38],
                   "help": "poll UBX-MON-RF RF Information"},
        # UBX-MON-RXBUF
        "MON-RXBUF": {"command": send_poll, "opt": [0x0a, 0x07],
                      "help": "poll UBX-MON-RXBUF Receiver Buffer Status"},
        # UBX-MON-SMGR
        "MON-SMGR": {"command": send_poll, "opt": [0x0a, 0x2e],
                     "help": "poll UBX-MON-SMGR Synchronization manager "
                     "configuration"},
        # UBX-MON-TXBUF
        "MON-TXBUF": {"command": send_poll, "opt": [0x0a, 0x08],
                      "help": "poll UBX-MON-TXBUF Transmitter Buffer Status"},
        # UBX-MON-VER
        "MON-VER": {"command": send_poll, "opt": [0x0a, 0x04],
                    "help": "poll UBX-MON-VER GPS version"},
        # UBX-NAV-AOPSTATUS
        "NAV-AOPSTATUS": {"command": send_poll, "opt": [0x01, 0x60],
                          "help": "poll UBX-NAV-AOPSTATUS AssistNow "
                          "Autonomous Status"},
        # UBX-NAV-ATT
        "NAV-ATT": {"command": send_poll, "opt": [0x1, 0x5],
                    "help": "poll UBX-NAV-ATT Attitude Solution"},
        # UBX-NAV-CLOCK
        "NAV-CLOCK": {"command": send_poll, "opt": [0x01, 0x22],
                      "help": "poll UBX-NAV-CLOCK Clock Solution"},
        # UBX-NAV-DGPS
        "NAV-DGPS": {"command": send_poll, "opt": [0x01, 0x31],
                     "help": "poll UBX-NAV-DGPS DGPS Data Used for NAV"},
        # UBX-NAV-DOP
        "NAV-DOP": {"command": send_poll, "opt": [0x01, 0x04],
                    "help": "poll UBX-NAV-DOP Dilution of Precision"},
        # UBX-NAV-GEOFENCE
        "NAV-GEOFENCE": {"command": send_poll, "opt": [0x01, 0x39],
                         "help": "poll UBX-NAV-GEOFENCE Geofence status"},
        # UBX-NAV-HPPOSECEF
        "NAV-HPPOSECEF": {"command": send_poll, "opt": [0x01, 0x13],
                          "help": "poll UBX-NAV-HPPOSECEF ECEF position"},
        # UBX-NAV-HPPOSLLH
        "NAV-HPPOSLLH": {"command": send_poll, "opt": [0x01, 0x14],
                         "help": "poll UBX-NAV-HPPOSECEF LLH position"},
        # UBX-NAV-ODO
        "NAV-ODO": {"command": send_poll, "opt": [0x01, 0x09],
                    "help": "poll UBX-NAV-ODO Odometer Solution"},
        # UBX-NAV-ORB
        "NAV-ORB": {"command": send_poll, "opt": [0x01, 0x34],
                    "help": "poll UBX-NAV-ORB GNSS Orbit Database Info"},
        # UBX-NAV-POSECEF
        "NAV-POSECEF": {"command": send_poll, "opt": [0x01, 0x01],
                        "help": "poll UBX-NAV-POSECEF ECEF position"},
        # UBX-NAV-POSLLH
        "NAV-POSLLH": {"command": send_poll, "opt": [0x01, 0x02],
                       "help": "poll UBX-NAV-POSLLH LLH position"},
        # UBX-NAV-PVT
        "NAV-PVT": {"command": send_poll, "opt": [0x01, 0x07],
                    "help": "poll UBX-NAV-PVT Navigation Position Velocity "
                            "Time Solution"},
        # UBX-NAV-RELPOSNED
        # HP only, 20+, otherwise not ACKed or NACKed
        "NAV-RELPOSNED": {"command": send_poll, "opt": [0x01, 0x3c],
                          "help": "poll UBX-NAV-RELPOSNED Relative "
                                  "Positioning Info in NED frame"},
        # UBX-NAV-RESETODO
        "NAV-RESETODO": {"command": send_poll, "opt": [0x01, 0x10],
                         "help": "UBX-NAV-RESETODO Reset odometer"},
        # UBX-NAV-SAT
        "NAV-SAT": {"command": send_poll, "opt": [0x01, 0x35],
                    "help": "poll UBX-NAV-SAT Satellite Information"},
        # UBX-NAV-SBAS
        "NAV-SBAS": {"command": send_poll, "opt": [0x01, 0x32],
                     "help": "poll UBX-NAV-SBAS SBAS Status Data"},
        # UBX-NAV-SIG
        "NAV-SIG": {"command": send_poll, "opt": [0x01, 0x43],
                    "help": "poll UBX-NAV-SIG Signal Information"},
        # UBX-NAV-SLAS
        "NAV-SLAS": {"command": send_poll, "opt": [0x01, 0x42],
                     "help": "poll UBX-NAV-SLAS QZSS L1S SLAS Status Data"},
        # UBX-NAV-SOL
        "NAV-SOL": {"command": send_poll, "opt": [0x01, 0x06],
                    "help": "poll UBX-NAV-SOL Navigation Solution "
                    "Information"},
        # UBX-NAV-STATUS
        "NAV-STATUS": {"command": send_poll, "opt": [0x01, 0x03],
                       "help": "poll UBX-NAV-STATUS Receiver Nav Status"},
        # UBX-NAV-SVIN
        "NAV-SVIN": {"command": send_poll, "opt": [0x01, 0x3b],
                     "help": "poll UBX-NAV-SVIN Survey-in data",
                     "minver": 20},
        # UBX-NAV-SVINFO
        "NAV-SVINFO": {"command": send_poll, "opt": [0x01, 0x30],
                       "help": "poll UBX-NAV-SVINFO Satellite Information"},
        # UBX-NAV-TIMEBDS
        "NAV-TIMEBDS": {"command": send_poll, "opt": [0x01, 0x24],
                        "help": "poll UBX-NAV-TIMEBDS BDS Time Solution"},
        # UBX-NAV-TIMEGAL
        "NAV-TIMEGAL": {"command": send_poll, "opt": [0x01, 0x25],
                        "help": "poll UBX-NAV-TIMEGAL Galileo Time Solution"},
        # UBX-NAV-TIMEGLO
        "NAV-TIMEGLO": {"command": send_poll, "opt": [0x01, 0x23],
                        "help": "poll UBX-NAV-TIMEGLO GLO Time Solution"},
        # UBX-NAV-TIMEGPS
        "NAV-TIMEGPS": {"command": send_poll, "opt": [0x01, 0x20],
                        "help": "poll UBX-NAV-TIMEGPS GPS Time Solution"},
        # UBX-NAV-TIMELS
        "NAV-TIMELS": {"command": send_poll, "opt": [0x01, 0x26],
                       "help": "poll UBX-NAV-TIMELS Leap Second Info"},
        # UBX-NAV-TIMEUTC
        "NAV-TIMEUTC": {"command": send_poll, "opt": [0x01, 0x21],
                        "help": "poll UBX-NAV-TIMEUTC UTC Time Solution"},
        # UBX-NAV-VELECEF
        "NAV-VELECEF": {"command": send_poll, "opt": [0x01, 0x11],
                        "help": "poll UBX-NAV-VELECEF ECEF velocity"},
        # UBX-NAV-VELNED
        "NAV-VELNED": {"command": send_poll, "opt": [0x01, 0x12],
                       "help": "poll UBX-NAV-VELNED NED velocity"},
        # UBX-RXM-IMES
        "RXM-IMES": {"command": send_poll, "opt": [0x02, 0x61],
                     "help": "poll UBX-RXM-IMES Indoor Messaging System "
                     "Information"},
        # UBX-RXM-MEASX
        "RXM-MEASX": {"command": send_poll, "opt": [0x02, 0x14],
                      "help": "poll UBX-RXM-MEASX Satellite Measurements "
                      " for RRLP"},
        # UBX-RXM-RAWX
        "RXM-RAWX": {"command": send_poll, "opt": [0x02, 0x15],
                     "help": "poll UBX-RXM-RAWX raw measurement data"},
        # UBX-CFG-SBAS
        "SEC-UNIQID": {"command": send_poll, "opt": [0x27, 0x03],
                       "help": "poll UBX-SEC-UNIQID Unique chip ID"},
        # UBX-TIM-SVIN
        "TIM-SVIN": {"command": send_poll, "opt": [0x0d, 0x04],
                     "help": "poll UBX-TIM-SVIN survey in data"},
        # UBX-TIM-TM2
        "TIM-TM2": {"command": send_poll, "opt": [0x0d, 0x03],
                    "help": "poll UBX-TIM-TM2 time mark data"},
        # UBX-TIM-TP
        "TIM-TP": {"command": send_poll, "opt": [0x0d, 0x01],
                   "help": "poll UBX-TIM-TP time pulse timedata"},
        # UBX-TIM-VRFY
        "TIM-VRFY": {"command": send_poll, "opt": [0x0d, 0x06],
                     "help": "poll UBX-TIM-VRFY Sourced Time Verification"},
        # UBX-UPD-SOS
        "UPD-SOS": {"command": send_poll, "opt": [0x09, 0x14],
                    "help": "poll UBX-UPD-SOS Backup File restore Status"},
        # UBX-UPD-SOS
        "UPD-SOS0": {"command": send_poll, "opt": [0x09, 0x14, 0, 0, 0, 0],
                     "help": "UBX-UPD-SOS Create Backup File in Flash"},
        # UBX-UPD-SOS
        "UPD-SOS1": {"command": send_poll, "opt": [0x09, 0x14, 1, 0, 0, 0],
                     "help": "UBX-UPD-SOS Create Clear File in Flash"},
    }
    # end class ubx
