# misc.py - miscellaneous geodesy and time functions
"miscellaneous geodesy and time functions"
#
# This file is Copyright 2010 by the GPSD project
# SPDX-License-Identifier: BSD-2-Clause

# This code runs compatibly under Python 2 and 3.x for x >= 2.
# Preserve this property!
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
        "Dummy stdio wrapper function."
        return stream

    def get_bytes_stream(stream):
        "Dummy stdio bytes buffer function."
        return stream

else:  # Otherwise we do something real

    def polystr(o):
        "Convert bytes or str to str with proper encoding."
        if isinstance(o, str):
            return o
        if isinstance(o, bytes) or isinstance(o, bytearray):
            return str(o, encoding=BINARY_ENCODING)
        if isinstance(o, int):
            return str(o)
        raise ValueError

    def polybytes(o):
        "Convert bytes or str to bytes with proper encoding."
        if isinstance(o, bytes):
            return o
        if isinstance(o, str):
            return bytes(o, encoding=BINARY_ENCODING)
        raise ValueError

    def make_std_wrapper(stream):
        "Standard input/output wrapper factory function"
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
        "Standard input/output bytes buffer function"
        return stream.buffer


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
    "Degrees to radians."
    return x * (math.pi / 180)


def Rad2Deg(x):
    "Radians to degrees."
    return x * (180 / math.pi)


def CalcRad(lat):
    "Radius of curvature in meters at specified latitude WGS-84."
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
    # a   = 6378.137 km (3963 mi)
    # b   = 6356.752314245 km (3950 mi)
    # e2  = 0.00669437999014132
    # es2 = 0.00673949674227643
    a = 6378.137
    e2 = 0.00669437999014132
    sc = math.sin(math.radians(lat))
    x = a * (1.0 - e2)
    z = 1.0 - e2 * pow(sc, 2)
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
    "Distance in meters between two close points specified in degrees."
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
    "Return offset in meters of second arg from first."
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
    "Convert timestamps in ISO8661 format to and from Unix time."
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

# End
# vim: set expandtab shiftwidth=4
