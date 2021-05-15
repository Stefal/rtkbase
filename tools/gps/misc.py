# misc.py - miscellaneous geodesy and time functions
# -*- coding: utf-8 -*-
"""miscellaneous geodesy and time functions"""
#
# This file is Copyright 2010 by the GPSD project
# SPDX-License-Identifier: BSD-2-Clause

# This code runs compatibly under Python 2 and 3.x for x >= 2.
# Preserve this property!

# A good more complete 3d math implementation:
# https://github.com/geospace-code/pymap3d/
#
from __future__ import absolute_import, print_function, division

import calendar
import io
import math
import time


def monotonic():
    """return monotonic seconds, of unknown epoch.
    Python 2 to 3.7 has time.clock(), deprecates in 3.3+, removed in 3.8
    Python 3.5+ has time.monotonic()
    This always works
    """

    if hasattr(time, 'monotonic'):
        return time.monotonic()
    # else
    return time.clock()


# Determine a single class for testing "stringness"
try:
    STR_CLASS = basestring  # Base class for 'str' and 'unicode' in Python 2
except NameError:
    STR_CLASS = str         # In Python 3, 'str' is the base class

# We need to be able to handle data which may be a mixture of text and binary
# data.  The text in this context is known to be limited to US-ASCII, so
# there aren't any issues regarding character sets, but we need to ensure
# that binary data is preserved.  In Python 2, this happens naturally with
# "strings" and the 'str' and 'bytes' types are synonyms.  But in Python 3,
# these are distinct types (with 'str' being based on Unicode), and conversions
# are encoding-sensitive.  The most straightforward encoding to use in this
# context is 'latin-1' (a.k.a.'iso-8859-1'), which directly maps all 256
# 8-bit character values to Unicode page 0.  Thus, if we can enforce the use
# of 'latin-1' encoding, we can preserve arbitrary binary data while correctly
# mapping any actual text to the proper characters.

BINARY_ENCODING = 'latin-1'

if bytes is str:  # In Python 2 these functions can be null transformations

    polystr = str
    polybytes = bytes

    def make_std_wrapper(stream):
        """Dummy stdio wrapper function."""
        return stream

    def get_bytes_stream(stream):
        """Dummy stdio bytes buffer function."""
        return stream

else:  # Otherwise we do something real

    def polystr(o):
        """Convert bytes or str to str with proper encoding."""

        if isinstance(o, str):
            return o
        if isinstance(o, (bytes, bytearray)):
            return str(o, encoding=BINARY_ENCODING)
        if isinstance(o, int):
            return str(o)
        raise ValueError

    def polybytes(o):
        """Convert bytes or str to bytes with proper encoding."""
        if isinstance(o, bytes):
            return o
        if isinstance(o, str):
            return bytes(o, encoding=BINARY_ENCODING)
        raise ValueError

    def make_std_wrapper(stream):
        """Standard input/output wrapper factory function"""
        # This ensures that the encoding of standard output and standard
        # error on Python 3 matches the binary encoding we use to turn
        # bytes to Unicode in polystr above.
        #
        # newline="\n" ensures that Python 3 won't mangle line breaks
        # line_buffering=True ensures that interactive command sessions
        # work as expected
        return io.TextIOWrapper(stream.buffer, encoding=BINARY_ENCODING,
                                newline="\n", line_buffering=True)

    def get_bytes_stream(stream):
        """Standard input/output bytes buffer function"""
        return stream.buffer

# WGS84(G1674) defining parameters
# https://en.wikipedia.org/wiki/Geodetic_datum
# Section #World_Geodetic_System_1984_(WGS_84)
#
# http://www.unoosa.org/pdf/icg/2012/template/WGS_84.pdf
# 8-Jul-2014:
# ftp://ftp.nga.mil/pub2/gandg/website/wgs84/NGA.STND.0036_1.0.0_WGS84.pdf
WGS84A = 6378137.0                # equatorial radius (semi-major axis), meters
WGS84F = 298.257223563            # flattening
WGS84B = 6356752.314245           # polar radius (semi-minor axis)
# 1st eccentricity squared = (WGS84A ** 2 + WGS84B **^ 2) / (WGS84A **^ 2)
# valid 8-Jul-2014:
WGS84E = 6.694379990141e-3        # 1st eccentricity squared
# 2nd  eccentricity squared = ((WGS84A **^ 2 - WGS84B **^ 2) / (WGS84B **^ 2)
# valid 8-Jul-2014:
WGS84E2 = 6.739496742276e-3       # 2nd eccentricy squared
# WGS 84 value of the earth's gravitational constant for GPS user
# GMgpsnav, valid 8-JUl-2014
# Galileo uses μ = 3.986004418 × 1014 m3/s2
# GLONASS uses 3.986004418e14 м3/s2
WGS84GM = 3.9860050e14            # m^3/second^2
# Earth's Angular Velocity, Omega dot e
# valid 8-Jul-2014:
# also Galileo
# GLONASS uses 7.292115x10-5
WGS84AV = 7.2921151467e-5         # rad/sec

# GLONASS
# ICD_GLONASS_5.1_(2008)_en.pdf
# Table 3.2 Geodesic constants and parametres uniearth ellipsoid ПЗ 90.02
# Earth rotation rate 7,292115x10-5 rad/s
# Gravitational constant 398 600,4418×109 м3/s2
# Gravitational constant of atmosphere( fMa ) 0.35×109 м3/s2
# Speed of light 299 792 458 м/s
# Semi-major axis 6 378 136 м
# Flattening 1/298,257 84
# Equatorial acceleration of gravity 978 032,84 мGal
# Correction to acceleration of gravity at sea-level due to Atmosphere
# 0,87 мGal
# Second zonal harmonic of the geopotential ( J2 0 ) 1082625,75×10-9
# Fourth zonal harmonic of the geopotential ( J4 0 ) (- 2370,89×10-9)
# Sixth zonal harmonic of the geopotential( J6 0 ) 6,08×10-9
# Eighth zonal harmonic of the geopotential ( J8 0 ) 1,40×10-11
# Normal potential at surface of common terrestrial ellipsoid  (U0)
# 62 636 861,4 м2/s2

# speed of light (m/s), exact
# same as GLONASS
CLIGHT = 299792458.0
# GPS_PI.  Exact!  The GPS and Galileo say so.
GPS_PI = 3.1415926535898
# GPS F, sec/sqrt(m), == -2*sqrt(WGS*$M)/c^2
GPS_F = -4.442807633e-10

# GPS L1 Frequency Hz (1575.42 MHz)
GPS_L1_FR = 1575420000
# GPS L1 Wavelength == C / GPS_L1_FR meters
GPS_L1_WL = CLIGHT / GPS_L1_FR

# GPS L2 Frequency Hz (1227.60 MHz)
GPS_L2_FR = 1227600000
# GPS L2 Wavelength == C / GPS_L2_FR meters
GPS_L2_WL = CLIGHT / GPS_L2_FR

# GPS L3 (1381.05 MHz) and L4 (1379.9133)  unused as of 2020

# GPS L5 Frequency Hz (1176.45 MHz)
GPS_L5_FR = 1176450000
# GPS L5 Wavelength == C / GPS_L2_FR meters
GPS_L5_WL = CLIGHT / GPS_L5_FR

RAD_2_DEG = 57.2957795130823208767981548141051703
DEG_2_RAD = 0.0174532925199432957692369076848861271


# some multipliers for interpreting GPS output
# Note: A Texas Foot is ( meters * 3937/1200)
#       (Texas Natural Resources Code, Subchapter D, Sec 21.071 - 79)
#       not the same as an international fooot.
FEET_TO_METERS = 0.3048                   # U.S./British feet to meters, exact
METERS_TO_FEET = (1 / FEET_TO_METERS)     # Meters to U.S./British feet, exact
MILES_TO_METERS = 1.609344                # Miles to meters, exact
METERS_TO_MILES = (1 / MILES_TO_METERS)   # Meters to miles, exact
FATHOMS_TO_METERS = 1.8288                # Fathoms to meters, exact
METERS_TO_FATHOMS = (1 / FATHOMS_TO_METERS)  # Meters to fathoms, exact
KNOTS_TO_MPH = (1852 / 1609.344)          # Knots to miles per hour, exact
KNOTS_TO_KPH = 1.852                      # Knots to kilometers per hour, exact
MPS_TO_KPH = 3.6                        # Meters per second to klicks/hr, exact
KNOTS_TO_MPS = (KNOTS_TO_KPH / MPS_TO_KPH)  # Knots to meters per second, exact
MPS_TO_MPH = (1 / 0.44704)             # Meters/second to miles per hour, exact
MPS_TO_KNOTS = (3600.0 / 1852.0)            # Meters per second to knots, exact


def Deg2Rad(x):
    """Degrees to radians."""
    return x * (math.pi / 180)


def Rad2Deg(x):
    """Radians to degrees."""
    return x * (180 / math.pi)


def lla2ecef(lat, lon, altHAE):
    """Convert Lat, lon (in degrees) and altHAE in meters
to ECEF x, y and z in meters."""
    # convert degrees to radians
    lat *= DEG_2_RAD
    lon *= DEG_2_RAD

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    n = WGS84A / math.sqrt(1 - WGS84E * (sin_lat ** 2))
    x = (n + altHAE) * cos_lat * math.cos(lon)
    y = (n + altHAE) * cos_lat * math.sin(lon)
    z = (n * (1 - WGS84E) + altHAE) * sin_lat
    return (x, y, z)


def ecef2lla(x, y, z):
    """Convert ECEF x, y and z in meters to
Lat, lon in degrees and altHAE in meters"""

    longitude = math.atan2(y, x) * RAD_2_DEG

    p = math.sqrt((x ** 2) + (y ** 2))
    theta = math.atan2(z * WGS84A, p * WGS84B)
    # sadly Python has no sincos()
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)

    phi = math.atan2(z + WGS84E2 * WGS84B * (sin_theta ** 3),
                     p - WGS84E * WGS84A * (cos_theta ** 3))
    latitude = phi * RAD_2_DEG
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)

    n = WGS84A / math.sqrt(1.0 - WGS84E * (sin_phi ** 2))

    # altitude is WGS84
    altHAE = (p / cos_phi) - n

    return (latitude, longitude, altHAE)


# FIXME: needs tests
def ecef2enu(x, y, z, lat, lon, altHAE):
    """Calculate ENU from lat/lon/altHAE to ECEF
ECEF in meters, lat/lon in degrees, altHAE in meters.
Returns ENU in meters"""

    #  Grr, lambda is a reserved name in Python...
    lambd = lat * DEG_2_RAD
    phi = lon * DEG_2_RAD
    sin_lambd = math.sin(lambd)
    cos_lambd = math.cos(lambd)
    n = WGS84A / math.sqrt(1 - WGS84E * sin_lambd ** 2)

    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)

    # ECEF of observer
    x0 = (altHAE + n) * cos_lambd * cos_phi
    y0 = (altHAE + n) * cos_lambd * sin_phi
    z0 = (altHAE + (1 - WGS84E) * n) * sin_lambd

    xd = x - x0
    yd = y - y0
    zd = z - z0

    E = -sin_phi * xd + cos_phi * yd
    N = -cos_phi * sin_lambd * xd - sin_lambd * sin_phi * yd + cos_lambd * zd
    U = cos_phi * cos_lambd * xd + cos_lambd * sin_phi * yd + sin_lambd * zd

    return E, N, U


# FIXME:  needs tests.
def enu2aer(E, N, U):
    """Convert ENU to Azimuth, Elevation and Range.
ENU is in meters. Returns Azimuth and Elevation in degrees, range in meters"""

    enr = math.hypot(E, N)
    rng = math.hypot(enr, U)
    az = math.atan2(E, N) % (math.pi * 2) * RAD_2_DEG
    el = math.atan2(U, enr) * RAD_2_DEG

    return az, el, rng


# FIXME: needs tests
def ecef2aer(x, y, z, lat, lon, altHAE):
    """Calculate az, el and range to ECEF from lat/lon/altHAE.
ECEF in meters, lat/lon in degrees, altHAE in meters.
Returns Azimuth and Elevation in degrees, range in meters"""

    (E, N, U) = ecef2enu(x, y, z, lat, lon, altHAE)
    return enu2aer(E, N, U)


def CalcRad(lat):
    """Radius of curvature in meters at specified latitude WGS-84."""
    # the radius of curvature of an ellipsoidal Earth in the plane of a
    # meridian of latitude is given by
    #
    # R' = a * (1 - e^2) / (1 - e^2 * (sin(lat))^2)^(3/2)
    #
    # where
    #   a   is the equatorial radius (surface to center distance),
    #   b   is the polar radius (surface to center distance),
    #   e   is the first  eccentricity of the ellipsoid
    #   e2  is e^2  = (a^2 - b^2) / a^2
    #   es  is the second eccentricity of the ellipsoid (UNUSED)
    #   es2 is es^2 = (a^2 - b^2) / b^2
    #
    # for WGS-84:
    # a   = WGS84A/1000 = 6378.137 km (3963 mi)
    # b   = 6356.752314245 km (3950 mi)
    # e2  = WGS84E =  0.00669437999014132
    # es2 = 0.00673949674227643
    sc = math.sin(math.radians(lat))
    x = (WGS84A / 1000) * (1.0 - WGS84E)
    z = 1.0 - WGS84E * (sc ** 2)
    y = pow(z, 1.5)
    r = x / y

    r = r * 1000.0      # Convert to meters
    return r


def EarthDistance(c1, c2):
    """
    Vincenty's formula (inverse method) to calculate the distance (in
    kilometers or miles) between two points on the surface of a spheroid
    WGS 84 accurate to 1mm!
    """

    (lat1, lon1) = c1
    (lat2, lon2) = c2

    # WGS 84
    a = 6378137  # meters
    f = 1 / 298.257223563
    b = 6356752.314245  # meters; b = (1 - f)a

    # MILES_PER_KILOMETER = 1000.0 / (.3048 * 5280.0)

    MAX_ITERATIONS = 200
    CONVERGENCE_THRESHOLD = 1e-12  # .000,000,000,001

    # short-circuit coincident points
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    U1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    U2 = math.atan((1 - f) * math.tan(math.radians(lat2)))
    L = math.radians(lon1 - lon2)
    Lambda = L

    sinU1 = math.sin(U1)
    cosU1 = math.cos(U1)
    sinU2 = math.sin(U2)
    cosU2 = math.cos(U2)

    for _ in range(MAX_ITERATIONS):
        sinLambda = math.sin(Lambda)
        cosLambda = math.cos(Lambda)
        sinSigma = math.sqrt((cosU2 * sinLambda) ** 2 +
                             (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
        if sinSigma == 0:
            return 0.0  # coincident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = math.atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha ** 2
        try:
            cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        except ZeroDivisionError:
            cos2SigmaM = 0
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        LambdaPrev = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinSigma *
                                               (cos2SigmaM + C * cosSigma *
                                                (-1 + 2 * cos2SigmaM ** 2)))
        if abs(Lambda - LambdaPrev) < CONVERGENCE_THRESHOLD:
            break  # successful convergence
    else:
        # failure to converge
        # fall back top EarthDistanceSmall
        return EarthDistanceSmall(c1, c2)

    uSq = cosSqAlpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (
        cosSigma * (-1 + 2 * cos2SigmaM ** 2) - B / 6 * cos2SigmaM *
        (-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
    s = b * A * (sigma - deltaSigma)

    # return meters to 6 decimal places
    return round(s, 6)


def EarthDistanceSmall(c1, c2):
    """Distance in meters between two close points specified in degrees."""
    # This calculation is known as an Equirectangular Projection
    # fewer numeric issues for small angles that other methods
    # the main use here is for when Vincenty's fails to converge.
    (lat1, lon1) = c1
    (lat2, lon2) = c2
    avglat = (lat1 + lat2) / 2
    phi = math.radians(avglat)    # radians of avg latitude
    # meters per degree at this latitude, corrected for WGS84 ellipsoid
    # Note the wikipedia numbers are NOT ellipsoid corrected:
    # https://en.wikipedia.org/wiki/Decimal_degrees#Precision
    m_per_d = (111132.954 - 559.822 * math.cos(2 * phi) +
               1.175 * math.cos(4 * phi))
    dlat = (lat1 - lat2) * m_per_d
    dlon = (lon1 - lon2) * m_per_d * math.cos(phi)

    dist = math.sqrt(math.pow(dlat, 2) + math.pow(dlon, 2))
    return dist


def MeterOffset(c1, c2):
    """Return offset in meters of second arg from first."""
    (lat1, lon1) = c1
    (lat2, lon2) = c2
    dx = EarthDistance((lat1, lon1), (lat1, lon2))
    dy = EarthDistance((lat1, lon1), (lat2, lon1))
    if lat1 < lat2:
        dy = -dy
    if lon1 < lon2:
        dx = -dx
    return (dx, dy)


def isotime(s):
    """Convert timestamps in ISO8661 format to and from Unix time."""
    if isinstance(s, int):
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(s))

    if isinstance(s, float):
        date = int(s)
        msec = s - date
        date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(s))
        return date + "." + repr(msec)[3:]

    if isinstance(s, STR_CLASS):
        if s[-1] == "Z":
            s = s[:-1]
        if "." in s:
            (date, msec) = s.split(".")
        else:
            date = s
            msec = "0"
        # Note: no leap-second correction!
        return calendar.timegm(
            time.strptime(date, "%Y-%m-%dT%H:%M:%S")) + float("0." + msec)

    # else:
    raise TypeError

def posix2gps(posix, leapseconds):
    """Convert POSIX time in seconds,  using leapseconds, to gps time.

Return (gps_time, gps_week, gps_tow)
"""

    # GPS Epoch starts: Jan 1980 00:00:00 UTC, POSIX/Unix time: 315964800
    gps_time = posix - 315964800
    gps_time += leapseconds
    # 604,800 in a GPS week
    (gps_week, gps_tow) = divmod(gps_time, 604800)
    return (gps_time, gps_week, gps_tow)


# End
# vim: set expandtab shiftwidth=4
