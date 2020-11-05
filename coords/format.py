#
#  Copyright (C) 2011, 2013, 2015, 2016, 2019, 2020
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
The module converts back and forth between sexadecimal and degrees. For
converting RA and Dec to degrees, the module uses the following rules:

   <ra> := {<dra>|<hr>[<sep2><rmn>[<sep2><rsc>]]}
   <dec> := [{<"+">|<"-">}]{<ddec>|<dg>[<sep2><dmn>[<sep2><dsc>]]}
   <dra> := {<drad>|<drah>}
   <drad> := {<["0"]["0"]"0".."9">|<["0"]"10".."99">|<"100".."359">}[.[<frac>]][<ws>][{<"D">| <"d">}][<ws>]
   <drah> := {<["0"]"0".."9">|<"10".."23">}[.[<frac>]][<ws>]{<"H">|<"h">}[<ws>]
   <hr> := {<["0"]"0".."9">|<"10".."23">}[<ws>][<"H">|<"h">][<ws>]
   <rmn> := {<["0"]"0".."9">|<"10".."59">}[<ws>][<"M">|<"m">][<ws>]
   <rsc> := {<["0"]"0".."9">|<"10".."59">}[.[<frac>]][<ws>][<"S">|<"s">][<ws>]
   <ddec> := {<["0"]"0".."9">|<"10".."89">}[.[<frac>]][<ws>][<"D">|<"d">][<ws>]
   <dg> := {<["0"]"0".."9">|<"10".."89">}[<ws>][<"D">|<"d">][<ws>]
   <dmn> := {<["0"]"0".."9">|<"10".."59">}[<ws>][<"'">][<ws>]
   <dsc> := {<["0"]"0".."9">|<"10".."59">}[.[<frac>]][<ws>][<\""">][<ws>]
   <frac> := <"0".."9">[<frac>]
   <sep1> := {","[<ws>]|<ws>}
   <sep2> := {":"[<ws>]|<ws>}
   <ws> := {" "|<tab>}[<ws>]
"""

import re
import math

import unittest

# __all__ = ("Formatter", "sex2deg", "ra2deg", "dec2deg", "deg2ra", "deg2dec")
__all__ = ("sex2deg", "ra2deg", "dec2deg", "deg2ra", "deg2dec")

DEG_PER_HR = 15.0
DEG_PER_MIN = 0.25
DEG_PER_SEC = DEG_PER_MIN / 60.0
DEG_PER_AMIN = 1.0 / 60.0
DEG_PER_ASEC = 1.0 / 3600.0

# Currently unused
#
# class Formatter ():
#   def __init__ (self):
#      pass
#
#   def invert (ra=None, dec=None):
#      """
#      Convert RA/Dec strings to degree values
#      """
#      if ra is not None and dec is not None:
#         return sex2deg (ra, dec)
#      elif ra is not None:
#         return ra2deg (ra)
#      elif dec is not None:
#         return dec2deg (dec)
#
#      return None
#
#   def apply (ra=None, dec=None, format="space"):
#      """
#      Convert degree values to RA/Dec formats
#      """
#
#      if ra is not None:
#         return deg2ra (ra, format)
#      elif dec is not None:
#         return deg2dec (dec)
#      return None
#


def sex2deg(ra, dec):
    """
    Converts supported RA and Dec formats to degrees. Uses ra2deg and
    dec2deg for each conversion. See individual functions for accepted
    formats for each.
    """

    ra_d = ra2deg(ra)
    dec_d = dec2deg(dec)
    return (ra_d, dec_d)


def ra2deg(ra):
    """
    Converts RA sexidecimal format to degrees. The functions supports an
    HMS (degree, minutes, seconds) format with an optional separator of either
    a : or space between each value. Minutes and seconds are optional and
    leading zeros are supported. Alternatively degrees or fractional hours are
    also supported. Degrees accept an optional D or d and fractional hours must
    have a trailing H or h.

    Examples
       359.9999
       359.9999D
       23.9999H
       23H 59M 59.976S
       23:59:59.6
       01 1 1.0
       0 59
    """

    # verify that the ra is a string if not return the value
    if not _check_str_(ra):

        # if it's float verify that it in range
        if _check_float_(ra):
            if ra < 360 and ra >= 0:
                deg = ra
            else:
                raise ValueError('RA value, {0} is not in a valid range. The value should be greater than or equal to 0 and less than 360'.format(ra))
        else:
            raise ValueError('Expected the RA value to be a string or a float')

    else:
        # first try for degrees
        deg, retval, sep = _degree_ra_(ra)

        # if degrees fail then try for hms
        if deg is None or len(retval) != 0:
            deg, retval, sep = _hms_(ra)

        # if both degrees and hms fail then
        # there was an error
        if len(retval) != 0:
            raise ValueError('Could not parse the RA value, {0}. The following segment was not expected {1}'.format(ra, retval))

    return deg


def dec2deg(dec):
    """
    Converts DEC sexidecimal format to degrees. The functions supports a
    D'" (degree, aminutes, aseconds) with an optional separator of either
    a : or space between each value. Minutes and seconds are optional and
    leading zeros are supported. Alternatively degrees are also supported.
    Degrees accept an optional D or d.

    Examples
       +89.999
       -89.999D
       89D 59' 59.6"
       -89:59:59.6
       01 1 1.0
       0 59
    """

    # verify that the dec is a string if not return the value
    if not _check_str_(dec):

        # if it's float verify that it in range
        if _check_float_(dec):
            if dec < 90 and dec > -90:
                deg = dec
            else:
                raise ValueError('Dec value, {0} is not in a valid range. The value should be greater than -90 and less than 90'.format(dec))
        else:
            raise ValueError('Expected the Dec value to be a string or a float')

    else:
        # first try for degrees
        deg, retval, sep = _degree_dec_(dec)

        # if degrees fail then try for hms
        if deg is None or len(retval) != 0:
            deg, retval, sep = _dms_(dec)

        # if both degrees and hms fail then
        # there was an error
        if len(retval) != 0:
            raise ValueError('Could not parse the Dec value, ' +
                             '{}. The following segment'.format(dec) +
                             ' was not expected {}'.format(retval))

    return deg


def deg2ra(deg, format, ndp=None):
    """
    Converts degrees to an RA format. Optional formats include:
       space or ' ' -- 1 2 3
       colon or :   -- 1:2:3
       hms          -- 1h 2m 3s
       HMS          -- 1H 2M 3S
       hour         -- 23.5h

    If ndp is not None then it is used to limit the number of decimal
    places in the last token
    """

    # a dictionary of supported formats
    #
    if ndp is None or ndp == 0:
        lval = ""
    elif ndp > 0:
        lval = f":.{ndp}f"
    else:
        raise ValueError("ndp must be None or >= 0")

    formats = {"space": "{0} {1} {2" + lval + "}",
               " ": "{0} {1} {2" + lval + "}",
               "colon": "{0}:{1}:{2" + lval + "}",
               ":": "{0}:{1}:{2" + lval + "}",
               "hms": "{0}h {1}m {2" + lval + "}s",
               "HMS": "{0}H {1}M {2" + lval + "}S",
               "hour": "{0" + lval + "}h"}

    # verify the format is an expected format
    if format not in formats.keys():
        raise ValueError("Unknown format, '{0}'. Expected format to be one of the following: {1}".format(format, formats.keys()))

    # if it's not a float try and convert it to one
    if not _check_float_(deg):
        try:
            deg = float(deg)
        except ValueError:
            raise TypeError("The input degree must be a float or a value that can be converted to type float")

    if deg < 0:
        deg += 360
    if deg >= 360:
        deg -= 360

    # extract hours from degrees
    frac = deg / DEG_PER_HR
    frac, hours = math.modf(frac)
    hours = int(hours) % 24

    # format the degrees
    if format != "hour":
        # extract minutes and seconds from degrees
        seconds, minutes = math.modf(frac * 60.0)
        minutes = int(minutes)
        if seconds < 1e-13:
            seconds = 0
        else:
            seconds *= 60

        ra = formats[format].format(hours, minutes, seconds)
    else:
        # add the seconds and minutes back into the hours
        hours += frac
        ra = formats[format].format(hours)

    return ra


def deg2dec(deg, format, ndp=None):
    """
    Converts degrees to a Dec format. Optional formats include:
       space or ' ' -- 1 2 3
       colon or :   -- 1:2:3
       dms          -- 1d 2' 3"
       degree       -- 89.99d

    If ndp is not None then it is used to limit the number of decimal
    places in the last token
    """

    # TODO: there should be some way to force a sign character.

    # a dictionary of supported formats
    #
    if ndp is None or ndp == 0:
        lval = ""
    elif ndp > 0:
        lval = f":.{ndp}f"
    else:
        raise ValueError("ndp must be None or >= 0")

    formats = {"space": "{0} {1} {2" + lval + "}",
               " ": "{0} {1} {2" + lval + "}",
               "colon": "{0}:{1}:{2" + lval + "}",
               ":": "{0}:{1}:{2" + lval + "}",
               "dms": "{0}d {1}' {2" + lval + "}\"",
               "degree": "{0" + lval + "}d"}

    # format the hours minutes and seconds as requested
    if format not in formats.keys():
        raise ValueError("Unknown format, '{0}'. Expected format to be one of the following: {1}".format(format, formats.keys()))

    # if it's not a float try and convert it to one
    if not _check_float_(deg):
        try:
            deg = float(deg)
        except ValueError:
            raise TypeError("The input degree must be a float or a value that can be converted to type float")

    if deg > 90 or deg < -90:
        raise ValueError("The input degree, {0}, cannot be greater than 90 degrees or less than -90 degrees".format(deg))

    if format != "degree":
        # extract hours minutes and seconds from degrees
        adeg = math.fabs(deg)
        frac, degrees = math.modf(adeg)
        degrees = int(degrees)
        frac = math.fabs(frac)
        arcseconds, arcminutes = math.modf(frac * 60.0)
        arcminutes = int(arcminutes)
        if arcseconds < 1e-13:
            arcseconds = 0
        else:
            arcseconds *= 60

        # format the dec
        dec = formats[format].format(degrees, arcminutes, arcseconds)
        if deg < 0:
            dec = "-" + dec
    else:
        # format the degrees
        dec = formats[format].format(deg)

    return dec


#######################################################
# RA Lexicons
#######################################################

def _degree_ra_(val):
    """
    Use following rule to convert to ra to degrees
       <dra> := {<drad>|<drah>}[ws]
    """

    local_sep = False
    deg, retval, sep = _ra_degree_(val)

    if deg is None or len(retval) != 0:
        deg, retval, sep = _ra_degree_hour_(val)

    if deg is not None:
        ws, retval = _ws_(retval)
        local_sep = ws is not None

    return (deg, retval, local_sep)


def _hms_(val):
    """
    Use following rule to convert to hms to degrees
       <hms> := {<hr>[[sep]<rmn>[[sep]<rsc>]]}[ws]
    """

    local_sep = False

    # first find the hour
    deg, val, local_sep = _hour_(val)

    if deg is not None and len(val) != 0:

        # is this true -- why?
        #  require a seperator before looking for minutes
        #  *** note: should H/M/S be valid separators probably but this
        #  *** requires a change to the rules

        sep, val = _sep_(val)

        if sep is not None or local_sep:

            # find the minutes
            frac, val, local_sep = _ra_minutes_(val)
            if frac is not None:
                deg += frac

                # again look for a seperator
                sep, val = _sep_(val)

                if sep is not None or local_sep:

                    # finally find the seconds
                    frac, val, local_sep = _ra_seconds_(val)
                    if frac is not None:
                        deg += frac

                    ws, val = _ws_(val)
                    local_sep = ws is not None

    return (deg, val, False)


def _ra_degree_(val):
    """
    Use following rule to convert to ra degrees to degrees
       <drad> := {<["0"]["0"]"0".."9">|<["0"]"10".."99">|<"100".."359">}[[<frac>]][<ws>][{<"D">|<"d">}]
    """
    sep = False
    match = re.match(r"^((3[0-5]\d)|([0-2]?\d?\d))", val)
    if match is None:
        return (None, val, sep)

    deg = float(match.group(0))
    frac, val = _frac_(val[match.end():])
    if frac is not None:
        deg += frac
    ws, val = _ws_(val)

    match = re.match("^(D|d)", val)
    if match is not None:
        val = val[match.end():]
        sep = True

    # everything passed return the degree
    # and the value
    # and if a seperator was found
    return (deg, val, sep)


def _ra_degree_hour_(val):
    """
    Use following rule to convert to ra hours to degrees
       <drah> := {<["0"]"0".."9">|<"10".."23">}[[<frac>]][<ws>]{<"H">|<"h">}
    """
    match = re.match(r"^((2[0-3])|([0-1]?\d))", val)

    drah = (None, val, False)
    if match is None:
        return drah

    deg = float(match.group(0))
    frac, val = _frac_(val[match.end():])
    if frac is not None:
        deg += frac
    deg *= DEG_PER_HR
    ws, val = _ws_(val)

    # drah has to have an H at the end
    match = re.match("^(H|h)", val)
    if match is None:
        return drah

    val = val[match.end():]
    ws, val = _ws_(val)

    # everything passed return the degree
    # and what's left over in the val
    # and if a seperator was found (which must be there)
    return (deg, val, True)


def _hour_(val):
    """
    Use following rule to convert to hours to degrees
       <hr> := {<["0"]"0".."9">|<"10".."23">}[<ws>][<"H">|<"h">]
    """
    match = re.match(r"^(((2[0-3])|([0-1]?\d))(\s*(H|h))?)", val)
    sep = False

    hr = (None, val, sep)
    if match is not None and match.group(2) is not None:
        deg = float(match.group(2)) * DEG_PER_HR

        # see if the input ends in a local seperator
        search = re.search(r'(\s*(H|h))$', match.group(1))
        sep = search is not None

        # everything passed return the degree
        # and what's left over in the val
        # and if a seperator was found
        hr = (deg, val[match.end():], sep)

    return hr


def _ra_minutes_(val):
    """
    Use following rule to convert to minutes to degrees
       <rmn> := {<["0"]"0".."9">|<"10".."59">}[<ws>][<"M">|<"m">]
    """
    sep = False
    match = re.match(r"^(([0-5]?\d)(\s*(M|m))?)", val)
    rmn = (None, val, sep)
    if match is not None and match.group(2) is not None:
        deg = float(match.group(2)) * DEG_PER_MIN

        # see if the input ends in a local seperator
        search = re.search(r'(\s*(M|m))$', match.group(1))
        sep = search is not None

        # everything passed return the degree
        # and what's left over in the val
        # and if a seperator was found
        rmn = (deg, val[match.end():], sep)

    return rmn


def _ra_seconds_(val):
    """
    Use following rule to convert to seconds to degrees
       <rsc> := {<["0"]"0".."9">|<"10".."59">}[[<frac>]][<ws>][<"S">|<"s">]
    """
    sep = False
    match = re.match(r"^([0-5]?\d)", val)

    if match is None:
        return (None, val, False)

    deg = float(match.group(0))

    frac, val = _frac_(val[match.end():])
    if frac is not None:
        deg += frac
    deg *= DEG_PER_SEC
    ws, val = _ws_(val)

    # seconds does not have to have an S at the end
    match = re.match("^(S|s)?", val)
    if match is not None:
        val = val[match.end():]
        sep = True

    # everything passed return the degree
    # and what's left over in the val
    # and if a seperator was found
    return (deg, val, sep)


#############################################################
# Dec Lexicons
#############################################################

def _degree_dec_(val):
    """
    Use following rule to convert to dec degrees to degrees
       <ddec> := {<["0"]"0".."9">|<"10".."89">}[[<frac>]][<ws>][<"D">|<"d">][<ws>]
    """
    local_sep = False
    match = re.match(r"^((\+|-)?([0-8]?\d))", val)
    if match is None:
        return (None, val, local_sep)

    deg = float(match.group(0))
    frac, val = _frac_(val[match.end():])
    if frac is not None:
        frac = math.copysign(frac, deg)
        deg += frac
    ws, val = _ws_(val)

    match = re.match(r"^(D|d)\s*|\s+", val)
    if match is not None:
        val = val[match.end():]

    ws, val = _ws_(val)
    local_sep = ws is not None

    # everything passed return the degree
    # and the value
    return (deg, val, local_sep)


def _dms_(val):
    """
    Use following rule to convert to dms to degrees
       <dms> := {<deg>[<sep><dmn>[<sep><dsc>]]}[ws]
    """

    local_sep = False

    # first find the degree
    deg, val, local_sep = _degree_(val)

    if deg is None or len(val) == 0:
        return (deg, val, local_sep)

    sep, val = _sep_(val)
    if sep is None and not local_sep:
        return (deg, val, local_sep)

    # find the minutes
    frac, val, local_sep = _arc_minutes_(val)
    if frac is None:
        return (deg, val, local_sep)

    frac = math.copysign(frac, deg)
    deg += frac

    # again look for a seperator
    sep, val = _sep_(val)

    if sep is None and not local_sep:
        return (deg, val, local_sep)

    # finally find the seconds
    frac, val, local_sep = _arc_seconds_(val)
    if frac is not None:
        frac = math.copysign(frac, deg)
        deg += frac

    ws, val = _ws_(val)
    local_sep = ws is not None

    return (deg, val, local_sep)


def _degree_(val):
    """
    Use following rule to convert to degrees to degrees
       <dg> := {<["0"]"0".."9">|<"10".."89">}[<ws>][<"D">|<"d">]
    """

    sep = False
    match = re.match(r"^(((\+|-)?([0-8]?\d))(\s*(D|d))?)", val)
    if match is None or match.group(2) is None:
        return (None, val, sep)

    deg = float(match.group(2))

    search = re.search(r"(\s*(D|d))$", match.group(1))
    sep = search is not None

    # everything passed return the degree
    # and the value
    return (deg, val[match.end():], sep)


def _arc_minutes_(val):
    """
    Use following rule to convert to arc minutes to degrees
       <dmn> := {<["0"]"0".."9">|<"10".."59">}[<ws>][<"'">]
    """

    sep = False
    match = re.match(r"^(([0-5]?\d)(\s*('))?)", val)
    if match is None or match.group(2) is None:
        return (None, val, sep)

    deg = float(match.group(2)) * DEG_PER_AMIN

    search = re.search(r"(\s*('))$", match.group(1))
    sep = search is not None

    # everything passed return the degree
    # and what's left over in the val
    return (deg, val[match.end():], sep)


def _arc_seconds_(val):
    """
    Use following rule to convert to arc seconds to degrees
       <dsc> := {<["0"]"0".."9">|<"10".."59">}[[<frac>]][<ws>][<\""">]
    """

    sep = False
    match = re.match(r"^([0-5]?\d)", val)
    if match is None:
        return (None, val, sep)

    deg = float(match.group(0))

    frac, val = _frac_(val[match.end():])
    if frac is not None:
        deg += frac
    deg *= DEG_PER_ASEC
    ws, val = _ws_(val)

    # seconds does not have to have an M at the end
    match = re.match('^(")?', val)
    if match is not None:
        val = val[match.end():]
        sep = True

    # everything passed return the degree
    # and what's left over in the val
    return (deg, val, sep)


#############################################################
# General Lexicons
#############################################################

def _frac_(val):
    """
    Use following rule to identify fractions
       <frac> := .[<"0".."9">]*
    """
    match = re.match(r"^\.\d*", val)

    if match is not None:
        frac = (float(match.group(0)), val[match.end():])
    else:
        frac = (None, val)

    return frac


def _sep_(val):
    """
    Use following rule to identify seperator
       <sep> := {":"[<ws>]|<ws>}
    """
    match = re.match(r"^\s*:\s*|\s+", val)

    if match is not None:
        sep = (match.group(0), val[match.end():])
    else:
        sep = (None, val)

    return sep


def _ws_(val):
    """
    Use following rule to identify white space
       <ws> := {" "|<tab>}[<ws>]
    """
    match = re.match(r"^\s+", val)

    if match is not None:
        space = (match.group(0), val[match.end():])
    else:
        space = (None, val)

    return space


def _check_str_(s):
    if not isinstance(s, str):
        try:
            s += 'a'
            s.split
        except (TypeError, AttributeError):
            return False

    return True


def _check_float_(n):

    if isinstance(n, float):
        return True
    try:
        if n + 0 == float(n):
            return True
    except (TypeError, ValueError):
        pass

    return False

# some simple tests


# place all the tests in a single class
class TestModule(unittest.TestCase):

    def _test_fmtconvert(self, val, formatter, results, ndp):
        for fmt, expval in results.items():

            # Want dfferent ndp for the hour/degree case
            if fmt in ['hour', 'degree']:
                xndp = ndp + 4
            else:
                xndp = ndp

            gotval = formatter(val, fmt, ndp=xndp)
            assert gotval == expval, (gotval, expval, f'format=[{fmt}]')

    def _test_convert(self, expval, converter, results):
        for _, val in results.items():
            gotval = converter(val)
            assert gotval == pytest.approx(expval), (gotval, expval, f'val={val}')

    def _test_invalid_string(self, converter, expected, ignore):
        for fmt, val in expected.items():
            if fmt in ignore:
                continue

            with pytest.raises(ValueError):
                converter(val)

    def _test_partial(self, converter, expected):
        for strval, numval in expected.items():
            gotval = converter(strval)
            self.assertEqual(str(gotval), str(numval),
                             msg="converting '{}'".format(strval))

    _test_ra = 101.28854
    _test_expected_ra = {' ': '6 45 9.2496',
                         ':': '6:45:9.2496',
                         'hms': '6h 45m 9.2496s',
                         'HMS': '6H 45M 9.2496S',
                         'hour': '6.75256933h'}

    _test_dec = -16.71314
    _test_expected_dec = {' ': '-16 42 47.304',
                          ':': '-16:42:47.304',
                          'dms': '-16d 42\' 47.304"',
                          'degree': '-16.7131400d'}

    def test_deg2ra(self):
        self._test_fmtconvert(self._test_ra,
                              deg2ra,
                              self._test_expected_ra, ndp=4)

    def test_deg2dec(self):
        self._test_fmtconvert(self._test_dec,
                              deg2dec,
                              self._test_expected_dec, ndp=3)

    def test_ra2deg(self):
        self._test_convert(self._test_ra,
                           ra2deg,
                           self._test_expected_ra)

    def test_dec2deg(self):
        self._test_convert(self._test_dec,
                           dec2deg,
                           self._test_expected_dec)

    def test_small_neg_dec(self):
        numval = -0.00138888888889
        strval = '-0:0:5.0'

        out = deg2dec(numval, ':', ndp=1)
        assert out == strval

        out = dec2deg(strval)
        assert out == pytest.approx(numval)

    def test_ra2deg_partial(self):
        expected = {'6 45': 101.25,
                    '6:45:': 101.25,
                    '6h45m': 101.25,
                    '6H 45M': 101.25,
                    '6h': 90.0,
                    '6H': 90.0,
                    '6': 6.0}
        self._test_partial(ra2deg, expected)

    def test_dec2deg_partial(self):
        expected = {'-16 42': -16.7,
                    '-16:42:': -16.7,
                    '-16d42\'': -16.7,
                    '-16d': -16.0,
                    '-16D': -16.0,
                    '-16': -16.0}
        self._test_partial(dec2deg, expected)

    # note that these are very limited tests of invalid input
    def test_invalid_rastr(self):
        self._test_invalid_string(ra2deg,
                                  self._test_expected_dec,
                                  [' ', ':'])

    def test_invalid_decstr(self):
        self._test_invalid_string(dec2deg,
                                  self._test_expected_ra,
                                  [' ', ':'])


if __name__ == "__main__":
    import pytest
    unittest.main()

# End
