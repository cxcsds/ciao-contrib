
# Python35Support

#
#  Copyright (C) 2011, 2012, 2015, 2016
#            Smithsonian Astrophysical Observatory
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Utility routines for handling coordinates. At present only one routine
is exported.

The interface is liable to change.
"""

import numpy as np

__all__ = ("point_separation",)


def spherical_to_cartesian(longitude, latitude):
    """Converts longitue, latitude (in radians) into
    a vector (cartesian coordinate system).

    Based on the SLALIB routine SLA_DCS2C

    https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dcs2c.f

    long/lat can also be RA/Dec. The longitude coordinate has
    positive anti-clockwise (or counter-clockwise) looking from
    the positive latitude pole.

    The output vector is right handed, with the X axis at zero
    longiture and latitude, and the Z axis at the positive latitude
    pole. It is a unit vector.
    """

    clat = np.cos(latitude)
    return np.asarray([np.cos(longitude) * clat,
                       np.sin(longitude) * clat,
                       np.sin(latitude)])


def cartesian_to_spherical(x, y, z):
    """Converts the cartesian coordinate system
    into a spherical one (longitude, with +ve being anti-clockwise
    looking from the positive latitude pole, and latitude).

    Based on the SLALIB routine SLA_DCC2S

    https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dcc2s.f

    The output is in radians.

    """

    r = np.sqrt(x * x + y * y)
    if r == 0.0:
        a = 0.0
    else:
        a = np.arctan2(y, x)

    if z == 0.0:
        b = 0.0
    else:
        b = np.arctan2(z, r)

    # Normalization is not in the FORTRAN version
    if a < 0:
        return (a + 2 * np.pi, b)
    elif a >= 2 * np.pi:
        return (a - 2 * np.pi, b)
    else:
        return (a, b)


def normalize_v3(x, y, z):
    """Return ((xn, yn, zn), m) where xn,yn,zn are
    the unit vector in the direction of (x,y,z) and m is the
    length of (x,y,z).

        Based on the SLALIB routine SLA_DVN

    https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dvn.f
    """

    v = np.asarray([x, y, z]) * 1.0  # ensure not integers
    m = np.sqrt(np.sum(v * v))

    if m <= 0.0:
        return ((0, 0, 0), m)
    else:
        v /= m
        return ((v[0], v[1], v[2]), m)


def calculate_nominal_position(ras, decs, tinyval=1.0e-6):
    """Given arrays of ra and dec positions (both in decimal
    degrees), calculate the 'mean' value of these values
    and return as (ra, dec), also in decimal degrees.

    A ValueError is returned if there is no valid
    location (absolute value of all coordinate elements
    when in cartesian coordinates are less than tinyval).

    The use of the word 'nominal' in the function name indicates
    it is developed for use with the RA_NOM/DEC_NOM values of
    Chandra pointings but it can be used with other data.
    """

    rarads = degtorad(np.asarray(ras))
    decrads = degtorad(np.asarray(decs))

    xyz = spherical_to_cartesian(rarads, decrads)

    # Use the mean value for each coordinate; for the moment
    # not worth trying anything fancier
    #
    xyz = xyz.mean(axis=1)
    if np.all(np.abs(xyz) < tinyval):
        raise ValueError("The nominal position is not defined.")

    ((xn, yn, zn), b) = normalize_v3(xyz[0], xyz[1], xyz[2])
    (ranom, decnom) = cartesian_to_spherical(xn, yn, zn)

    return (radtodeg(ranom), radtodeg(decnom))


def angular_separation(vv1, vv2):
    """Return the angular separation of the two vectors
    vv1 and vv2 (output of spherical_to_cartesian)

    The result is in radians and should always be >= 0.

    Based on the SLALIB routines SLA_DSEP and SLA_DSEPV

    https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dsep.f
    https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dsepv.f

    """

    cp = np.cross(vv1, vv2)
    s = np.sqrt(np.sum(cp * cp))
    c = np.sum(vv1 * vv2)
    return np.arctan2(s, c)


# TODO:
#   https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dpav.f
# for the version using direction cosines.
#
def bearing(long1, lat1, long2, lat2):
    """Return the bearing (position angle) of
    (long2,lat2) from (long1,lat1).

    The result is in radians and is in the range +/- pi. 0 is
    returned if the two points are coincident.

    Based on the SLALIB routine SLA_DBEAR

    https://github.com/scottransom/pyslalib/blob/c6178c2a9a1d6fadaa2e7dc50ada7bebb5e633a7/dbear.f

    """

    dlong = long2 - long1
    y = np.sin(dlong) * np.cos(lat2)
    x = np.sin(lat2) * np.cos(lat1) - \
        np.cos(lat2) * np.sin(lat1) * np.cos(dlong)
    if (x == 0.0) and (y == 0.0):
        return 0.0
    else:
        return np.arctan2(y, x)


def degtorad(x):
    "Convert decimal degrees into radians"
    return x * np.pi / 180.0


def radtodeg(x):
    "Convert radians into decimal degrees"
    return x * 180.0 / np.pi


def point_separation(long1, lat1, long2, lat2):
    """Return the separation between the points. The input
    coordinates and return values are in degrees."""

    args = [degtorad(x) for x in [long1, lat1, long2, lat2]]
    a = spherical_to_cartesian(args[0], args[1])
    b = spherical_to_cartesian(args[2], args[3])
    return radtodeg(angular_separation(a, b))
