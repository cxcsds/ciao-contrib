#
# Copyright (C) 2013, 2014, 2015, 2016, 2019
#           Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""

Summary
-------

This module allows basic access to the CIAO proposal tools from
Python. At present there is support for colden, precess, and dates,
and not all the functionality of the command-line or web versions are
supported.

There is no interface to PIMMS; for this it is suggested that the
modelflux command-line tool is used, or the ciao_contrib.runtool
Python wrapper for it - for more details see

  https://cxc.harvard.edu/ciao/ahelp/modelflux.html
  https://cxc.harvard.edu/ciao/ahelp/ciao_runtool.html

This is an *experimental* interface and may change in the future.

>>> import ciao_contrib.proptools as proptools
>>> proptools.colden(23, 40)
6.56
>>> proptools.colden(23, 40, dataset='bell')
6.66
>>> proptools.colden([2.1, 15.8, 356.2, 178.9], [43.5, -0.1, 83.4, -76], dataset='bell')
[7.34, 3.35, 10.61, None]

Note that the return value from colden has units of 10^20 cm^-2.

>>> proptools.precess(12.138, -0.001)
(12.778809, 0.270858)
>>> proptools.precess([12.138, 341.2342], [-0.001, 87.342], fromsys="J", tofmt="HMS")
(['00 48 33.12', '22 44 56.21'], ['-00 00 03.60', '+87 20 31.20'])

>>> proptools.dates(268499019.5)
datetime.datetime(2006, 7, 5, 15, 3, 37, 500000)
>>> proptools.dates('2006-07-05T15:03:37.5', fromcal="GREG", tocal="CHANDRA")
268499019.5

Debugging
=========

This module uses the ciao_contrib.logger_wrapper module for logging,
if available, with the module name 'proptools'. If the module is not
available then the logging is turned off.

An example of turning on the logging is shown below (the screen output
and verbosity level used for them is not guaranteed to remain stable):

>>> import ciao_contrib.logger_wrapper as lw
>>> lw.initialize_logger("test", verbose=2)
>>> ans = proptools.colden(23, 40)
Running colden for 1 position (using NRAO data set)
Running colden with ra=23 dec=40 for dataset NRAO

>>> lw.set_module_verbosity(4)
>>> ans = proptools.precess(23.2, -0.012)
Running precess for 1 position (from B1950/DEG to J2000/DEG)
Running precess for x=23.2 y=-0.012 B1950/DEG to J2000/DEG
Converting position '23.2  -0.012'
* precess args: ['prop_precess', 'f', 'B1950/DEG', 't', 'J2000/DEG', 'p0', 'eval', '23.2  -0.012']
* precess output: returncode=0
* precess output: stdout= 23.840873     0.243283

* precess output: stderr=
>>>

"""

import subprocess as sbp
import numpy as np

import datetime

__all__ = ("colden", "precess", "dates")

# Allow use in a system without the logging code, as it is not
# essential functionality.
#
try:
    from ciao_contrib.logger_wrapper import initialize_module_logger

    logger = initialize_module_logger("proptools")
    v2 = logger.verbose2
    v3 = logger.verbose3
    v4 = logger.verbose4

except ImportError:

    def _vdummy(msg):
        pass

    v2 = _vdummy
    v3 = _vdummy
    v4 = _vdummy


def _run_proc(label, args):
    """Run the process, provide debugging output, return output.

    Parameters
    ----------
    label : str
        The label to add to debug messages
    args : sequence
        The arguments to send to subprocess.Popen.

    Returns
    -------
    returncode, stdout : int, str
        The return code and STDOUT.
    """

    v4("* {} args: {}".format(label, args))

    proc = sbp.Popen(args, stdout=sbp.PIPE, stderr=sbp.PIPE)
    (sout, serr) = proc.communicate()
    rval = proc.returncode

    # display output without any conversion
    v4("* {} output: returncode={}".format(label, rval))
    v4("* {} output: stdout={}".format(label, sout))
    v4("* {} output: stderr={}".format(label, serr))

    return rval, sout.decode()


def _colden(ra, dec, dataset):
    """Returns the column density, in units of 10^20 cm^-2,
    for the given location and dataset. ra and dec are
    scalars, and are decimal degrees (J2000). dataset should
    be NRAO or Bell.

    None is returned if the value can not be computed. This
    includes invalid inputs or there is a problem parsing the
    output.
    """

    v2("Running colden with ra={} dec={} for dataset {}".format(ra,
                                                                dec,
                                                                dataset))
    args = ["prop_colden", "f", "j/deg", "data",
            dataset, "eval", str(ra), str(dec)]

    rval, sout = _run_proc('colden', args)
    if rval != 0:
        v2("Colden failed to run successfully")
        return None

    lines = sout.splitlines()
    try:
        oline = lines[-2]
    except IndexError:
        v2("Unexpected colden output: not enough lines")
        return None

    toks = oline.split()
    out = None
    try:
        if toks[0] == 'Hydrogen' and toks[1] == 'density':
            out = float(toks[4])
        else:
            v2("Unexpected colden output; line should start 'Hydrogen density', not '{} {}'".format(toks[0], toks[1]))

    except IndexError:
        v2("Unexpected colden output: line should start 'Hydrogen density', not '{}'".format(oline))

    except ValueError:
        v2("Unexpected colden output: unable to convert '{}' to a number".format(toks[4]))

    return out


# Note that this is inefficient when sent in multiple values, since the
# tool is run once per coordinate, rather than taking advantage of the
# 'batch' mode of colden.
#
def colden(ra, dec, dataset='NRAO'):
    """Return the column density, in units of 10^20 cm^2,
    for the given location(s).

    ra and dec are in decimal degrees, J2000. The dataset argument
    should be 'NRAO' or 'Bell' (case insensitive).

    If ra and dec are scalar, then a scalar value is returned.
    If they are arrays of the same length, then an array is returned
    (if either ra or dec is a numpy array then the return will be a
    numpy array - which may have a surprising data type if
    any values are missing - otherwise it is a Python list).

    A value of None is returned for any position for which a value can
    not be computed.

    There is no support for changing the velocity limits for the
    Stark et al data (dataset='Bell') or for indicating whether
    the result is interpolated or not.

    See https://cxc.harvard.edu/ciao/ahelp/colden.html for more information
    on the colden proposal tool.

    The precess routine and the coords.format module can be used for converting
    coordinates into the format needed by this routine.

    Examples
    ========

    >>> proptools.colden(23, 40)
    6.56
    >>> proptools.colden(23, 40, dataset='bell')
    6.66
    >>> proptools.colden([2.1, 15.8, 356.2, 178.9], [43.5, -0.1, 83.4, -76])
    [9.0, 3.17, 9.65, 10.04]
    >>> proptools.colden([2.1, 15.8, 356.2, 178.9], [43.5, -0.1, 83.4, -76], dataset='bell')
    [7.34, 3.35, 10.61, None]

    """

    if dataset.upper() not in ["NRAO", "BELL"]:
        raise ValueError("Invalid dataset={}; must be NRAO or Bell".format(dataset))

    try:
        args = zip(ra, dec)
        multi = True

    except TypeError:
        args = zip([ra], [dec])
        multi = False

    args = list(args)
    nargs = len(args)
    if nargs == 1:
        v2("Running colden for 1 position (using {} data set)".format(dataset))
    else:
        v2("Running colden for {} positions (using {} data set)".format(nargs, dataset))

    out = []
    for (a, b) in args:
        out.append(_colden(a, b, dataset))

    if multi:
        if isinstance(ra, np.ndarray) or isinstance(dec, np.ndarray):
            oval = np.asarray(out)
        else:
            oval = out
    else:
        oval = out[0]

    return oval


def _validate_system(csys):
    "Returns a 'normalized' coordinate system or None if invalid"

    csys = csys.upper()
    if csys == "J":
        return "J2000"
    elif csys == "B":
        return "B1950"
    elif csys in ["G", "SG"]:
        return csys
    elif csys.startswith("J") or csys.startswith("B"):
        raise NotImplementedError
    else:
        return None


def _validate_format(fmt):
    "Returns a 'normalized' format or None if invalid"

    fmt = fmt.upper()
    if fmt in ["DEG", "HMS"]:
        return fmt
    else:
        return None


# The fromfmt could be determined from the type of x/y: numeric means
# "DEG", string means "HMS", but it's easier/cleaner to be explicit here.
#
def _precess(x, y, fromfmt="HMS", fromsys="J2000", tofmt="DEG", tosys="J2000"):
    """Perform the coordinate conversion defined by the
    (fromfmt,fromsys) to (tofmt,tosys) pairs and return the
    answer.

    None is returned if the value can not be computed.
    """

    v2("Running precess for x={} y={} {}/{} to {}/{}".format(x, y, fromsys, fromfmt, tosys, tofmt))

    # Rely on Python format conversion here (could do it manually based on
    # fromfmt/tofmt)
    xval = "{}".format(x)
    yval = "{}".format(y)

    # To support 'incomplete' HMS/DMS values; e.g. 10 h and 10 23 m,
    # need to separate with a semicolon (or perhaps other terminal).
    #
    if fromfmt == "HMS":
        possep = ";"
    else:
        possep = ""

    posval = "{} {} {}".format(xval, possep, yval)
    v3("Converting position '{}'".format(posval))

    args = ["prop_precess",
            "f", "{}/{}".format(fromsys, fromfmt),
            "t", "{}/{}".format(tosys, tofmt),
            "p0", "eval", posval]
    rval, sout = _run_proc('precess', args)
    if rval != 0:
        v2("Precess failed to run successfully")
        return None

    lines = sout.splitlines()
    try:
        oline = lines[0]
    except IndexError:
        v2("Unexpected precess output: not enough lines")
        return None

    toks = oline.split()
    if tofmt == "DEG":
        try:
            xout = float(toks[0])
            yout = float(toks[1])

        except (IndexError, ValueError):
            v2("Unexpected precess output: expected two numbers, found '{}'".format(oline))
            return None

    elif tofmt == "HMS":
        try:
            xout = " ".join(toks[0:3])
            yout = " ".join(toks[3:6])

        except IndexError:
            v2("Unexpected precess output: expected 6 numbers, found '{}'".format(oline))
            return None

    else:
        raise ValueError("Invalid tofmt argument: {}".format(tofmt))

    return (xout, yout)


def precess(x, y, fromsys="B", tosys="J", fromfmt="DEG", tofmt="DEG"):
    """Convert the position (x,y), which is in degrees or sexagesimal
    format (as defined by fromfmt) and system fromsys, to the system
    and format defined by the tosys and tofmt arguments.

    The return value is (xconv, yconv) where xconv,yconv are scalars
    or arrays, depending on x, y.

    Supported systems (case insensitive):
      "J"     - Equatorial coordinates, J2000 (FK5)
      "JXXXX" - Equatorial coordinates with the given Julian epoch (FK5)
      "B"     - Equatorial coordinates, B1950 (FK4)
      "BXXXX" - Equatorial coordinates with the given Besselian epoch (FK4)
      "G"     - Galactic
      "SG"    - Supergalactic

    Supported formats (case insensitive):
      "DEG"   - decimal degrees
      "HMS"   - sexagesimal, using HH MM SS.SS DD MM SS.SS

    Decimal format values are assumed to be numbers (not strings),
    whereas sexagesimal are assumed to be strings. The return value is
    always a numpy array when there are multiple positions and tofmt='DEG'.

    See https://cxc.harvard.edu/ciao/ahelp/precess.html for more information
    on the precess proposal tool and
    https://cxc.harvard.edu/ciao/ahelp/prop-coords.html for coordinate systems.

    Unlike the command-line version, there is no support for constellations
    or the Ecliptic coordinate system (Bessalian epoch).

    The coords.format module can also be used for format conversion (it supports
    more variants of sexagesimal) but does not provide any conversion between
    systems or epochs.

    Examples
    ========

    >>> precess(12.138, -0.001, fromsys="J")
    (12.138, -0.001)
    >>> proptools.precess([12.138], [-0.001], fromsys="J")
    (array([ 12.138]), array([-0.001]))
    >>> precess(12.138, -0.001, fromsys="J", tofmt="HMS")
    ('00 48 33.12', '-00 00 03.60')
    >>> precess([12.138, 341.2342], [-0.001, 87.342], fromsys="J", tofmt="HMS")
    (['00 48 33.12', '22 44 56.21'], ['-00 00 03.60', '+87 20 31.20'])

    """

    fsys = _validate_system(fromsys)
    if fsys is None:
        raise ValueError("Invalid fromsys argument: '{}'".format(fromsys))

    tsys = _validate_system(tosys)
    if tsys is None:
        raise ValueError("Invalid tosys argument: '{}'".format(tosys))

    ffmt = _validate_format(fromfmt)
    if ffmt is None:
        raise ValueError("Invalid fromfmt argument: '{}'".format(fromfmt))

    tfmt = _validate_format(tofmt)
    if tfmt is None:
        raise ValueError("Invalid tofmt argument: '{}'".format(tofmt))

    if ffmt == "DEG":
        try:
            args = zip(x, y)
            multi = True

        except TypeError:
            args = zip([x], [y])
            multi = False

    elif ffmt == "HMS":
        try:
            # let np.asarray worry about converting "foo" into ["foo"]
            args = zip(np.asarray(x), np.asarray(y))
            multi = True
        except TypeError:
            args = zip([x], [y])
            multi = False

    else:
        raise RuntimeError("*Internal Error* fromfmt={} is unsupported.".format(ffmt))

    args = list(args)
    nargs = len(args)
    if nargs == 1:
        v2("Running precess for 1 position (from {}/{} to {}/{})".format(fsys, ffmt, tsys, tfmt))
    else:
        v2("Running precess for {} positions (using {} data set)".format(nargs, fsys, ffmt, tsys, tfmt))

    out = []
    for (a, b) in args:
        out.append(_precess(a, b, fromfmt=ffmt, tofmt=tfmt, fromsys=fsys, tosys=tsys))

    if multi:
        (xout, yout) = list(zip(*out))
        if tfmt == 'DEG':
            return (np.asarray(xout), np.asarray(yout))
        elif tfmt == 'HMS':
            xout = [xo for xo in xout]
            yout = [yo for yo in yout]
            return (xout, yout)
        else:
            raise RuntimeError("*Internal Error* tofmt={} is unsupported.".froamt(tfmt))

    else:
        return out[0]


"""
prop_dates supports the following; the dates routine only supports a small subset of this.

Dates [Setup]>: l/cal
       1 GREG        Gregorian date                   Gregorian Calendar
       2 JD          Julian Day                       Julian Day Number
       3 MJD         Modified Julian Day              Julian Day Number
       4 DAYS        Elapsed Days                     Julian Day Number
       5 DATE        Date                             Gregorian Calendar
       6 PACK        Packed date                      Gregorian Calendar
       7 DOY         Day of year                      Gregorian Calendar
       8 OS          Julian Calendar                  Julian Calendar
       9 ROMAN       Roman calendar                   Roman Calendar
      10 RF          French Rev. Calendar             French Revolutionary Calendar
      11 GSD         Greenwich Sidereal Date          Greenwich Sidereal Date
      12 GST         Sidereal Time                    Greenwich Sidereal Date
      13 TIME        Elapsed Seconds                  Elapsed Seconds
      14 JEPOCH      Julian Epoch                     Epoch
      15 BEPOCH      Besselian Epoch                  Epoch
      16 MAYA        Maya Long Count                  Maya
      17 AZTEC       Aztec calendar                   Maya

Dates [Setup]>: l/ts
TSID  Timescale   Timescale Name                   Type                    Zone Par   Zone

1      UTC         Coordinated Universal Time       Civil Time                     0 +0000
2      TT          Terrestrial Time                 Terrestrial Time               0
3      TDB         Barycentric Dynamical Time       Dynamical Time                 0
4      TAI         Coordinated Atomic Time          Atomic Time                    0
5      UT1         UT1 Universal Time               UT1 Time                       0
6      GMST        Greenwich Mean Sidereal Time     Sidereal Time                  0
7      LST         Local Sidereal Time              Local Sid. Time                0
8      Local       Zone +0000                       Civil Time                     0 +0000
9      MSV         Moscow Summer Time               Civil Time                 14400 +0400
10     DMV         Moscow Decree Time               Civil Time                 10800 +0300
11     BST         British Summer Time              Civil Time                  3600 +0100
12     GMT         Greenwich Mean Time              Civil Time                     0 +0000
13     EDT         Eastern Daylight Time            Civil Time                -14400 -0400
14     EST         Eastern Standard Time            Civil Time                -18000 -0500
15     CDT         Central Daylight Time            Civil Time                -18000 -0500
16     CST         Central Standard Time            Civil Time                -21600 -0600
17     MDT         Mountain Daylight Time           Civil Time                -21600 -0600
18     MST         Mountain Standard Time           Civil Time                -25200 -0700
19     PDT         Pacific Daylight Time            Civil Time                -25200 -0700

Dates [Setup]>: l/tt
     1 TT       Terrestrial Time
     2 UTC      Civil Time
     3 TDB      Dynamical Time
     4 TAI      Atomic Time
     5 UT1      UT1 Time
     6 GMST     Sidereal Time
     7 LST      Local Sid. Time

Dates [Setup]>: l/ct

 No.     Calendar

     1 Gregorian Calendar
     2 Julian Day Number
     3 Julian Calendar
     4 Roman Calendar
     5 French Revolutionary Calendar
     6 Greenwich Sidereal Date
     7 Elapsed Seconds
     8 Epoch
     9 Maya


"""


def _validate_calendar(cal):
    "Returns a 'normalized' format or None if invalid"

    cal = cal.upper()
    if cal in ["GREG", "CHANDRA", "JD", "MJD"]:
        return cal
    else:
        return None


_timefmt_nosec = "%Y-%m-%dT%H:%M:%S"
_timefmt_full = _timefmt_nosec + ".%f"

_timefmt_nosec_not = _timefmt_nosec.replace("T", " ")
_timefmt_full_not = _timefmt_full.replace("T", " ")

# looks like dates always reports seconds with two decimal places
_timefmt_dates = "%Y %b %d %H:%M:%S.%f"


def _from_timestr_chandra(tstr):
    """Convert a date, of the form

        YYYY-MM-DDTHH:MM:SS[.SS]
        YYYY-MM-DD HH:MM:SS[.SS]

    into a datetime object, or None.
    """

    try:
        if tstr.find("T") == -1:
            pat1 = _timefmt_nosec_not
            pat2 = _timefmt_full_not
        else:
            pat1 = _timefmt_nosec
            pat2 = _timefmt_full

        try:
            return datetime.datetime.strptime(tstr, pat1)

        except ValueError:
            try:
                return datetime.datetime.strptime(tstr, pat2)
            except ValueError:
                return None

    except AttributeError:
        return None


def _from_timestr_dates(tstr):
    """Convert a date, of the form 'DayName AD YYYY MonthName DayNum HH:MM:SS.SS UTC (Gregorian)'
    into a datetime object, or raise a ValueError.

    Explicitly does not support all formats/systems that dates does. In particular,
    it does not support BC dates (how is that encoded in datetime objects?).

    """

    expfmt = 'DayName AD YYYY MonthName DayNum HH:MM:SS.SS UTC (Gregorian)'
    idx = tstr.find(' AD ')
    if idx == -1:
        if tstr.find(' BC ') != -1:
            raise ValueError("Unable to deal with BC dates! '{}'".format(tstr))

        elif not tstr.endswith(' UTC (Gregorian)'):
            raise ValueError("Expected '{}' but sent '{}'".format(expfmt, tstr))

    tstr = tstr[idx + 4:len(tstr) - 16]
    return datetime.datetime.strptime(tstr, _timefmt_dates)


def _to_timestr_dates(date):
    """Convert a datetime object to YYYY MM DD HH MM SS[.SS]
    format. None is returned on an error.
    """

    try:
        val = "{} {} {} {} {} ".format(date.year, date.month,
                                       date.day, date.hour, date.minute)
        if date.microsecond > 0:
            val += "{}".format(date.second + (date.microsecond / 1e6))
        else:
            val += "{}".format(date.second)

        val += " UTC"
        return val

    except AttributeError:
        return None


# The fromfmt could be determined from the type of x/y: numeric means
# "DEG", string means "HMS", but it's easier/cleaner to be explicit here.
#
def _dates(date, fromcal="CHANDRA", tocal="GREG"):
    """Perform the date conversion defined by the fromcal,tocal pair,
    returning the answer. The answer is either a floating-point

    None is returned if the value can not be computed.

    For fromcal=GREG, the date is assumed to be a string of the form
        YYYY MM DD HH MM SS[.SS]
    """

    v2("Running dates for date={} ({} to {})".format(date, fromcal, tocal))

    # convert to string
    val = "{}".format(date)

    v3("Converting date '{}'".format(val))

    args = ["prop_dates",
            "f", fromcal,
            "t", tocal,
            "p0", "eval", val]

    rval, sout = _run_proc('dates', args)
    if rval != 0:
        v2("Dates failed to run successfully")
        return None

    lines = sout.splitlines()
    try:
        oline = lines[0]
    except IndexError:
        v2("Unexpected dates output: not enough lines")
        return None

    v4("* trying to convert '{}'".format(oline))

    if tocal == "GREG":
        return _from_timestr_dates(oline)

    elif tocal in ["JD", "MJD"]:
        if not oline.startswith(tocal + " "):
            v2("Unexpected dates output: expected to start with '{} ' but found '{}'".format(tocal, oline))
            return None

        if not oline.endswith(' UTC'):
            v2("Unexpected dates output: expected to end with ' UTC' but found '{}'".format(oline))
            return None

        try:
            oval = oline.split()[1]
            try:
                return float(oval)

            except ValueError:
                v2("Unexpected dates output: expected a number, not '{}' in '{}'".format(oval, oline))
                return None

        except IndexError:
            # should not happen given previous checks
            v2("Unexpected dates output: expected three words, found '{}'".format(oline))
            return None

    else:
        try:
            return float(oline)

        except ValueError:
            v2("Unexpected dates output: expected a number, not '{}'".format(oline))
            return None


def dates(date, fromcal="CHANDRA", tocal="GREG"):
    """Convert the date, from the fromcal calendar to the
    tocal calendar.

    Unlike the precess and colden versions, this routine only
    accepts a single value. Conversion of multiple dates requires
    multiple calls to this routine.

    Supported calendars (case insensitive):
      "GREG"    - Gregorian calendar, UTC
      "CHANDRA" - Seconds since 1998 Jan 1 00:00:0.0; this is the time system used
                  in Chandra event files
      "JD"      - Julian Day
      "MJD"     - Modified Julian Day

    Gregorian dates are given as either a string, in the form
    'YYYY-MM-DDTHH:MM:SS[.SS]' or 'YYYY-MM-DD HH:MM:SS[.SS]'
    or a datetime object. These dates are assumed to be in UTC. If tocal="GREG"
    is requested then a datetime object is returned (as a "naive" object, with
    no time zone information set).

    See https://cxc.harvard.edu/ciao/ahelp/dates.html for more information
    on the dates proposal tool and
    https://cxc.harvard.edu/ciao/ahelp/prop-time.html for the calendars.

    Only a small subset of the functionality of the command-line tool is provided
    by this function.

    The astropy.Time class is not supported, but really should be!

    Examples
    ========

    >>> ans = proptools.dates(268499019.5)
    >>> ans
    datetime.datetime(2006, 7, 5, 15, 3, 37, 500000)
    >>> str(ans)
    '2006-07-05 15:03:37.500000'
    >>> proptools.dates(str(ans), fromcal="GREG", tocal="CHANDRA")
    268499019.5
    >>> proptools.dates(ans, fromcal="GREG", tocal="CHANDRA")
    268499019.5
    >>> proptools.dates('2006-07-05T15:03:37.5', fromcal="GREG", tocal="CHANDRA")
    268499019.5
    >>> proptools.dates('2006-07-05T15:03:37.5', fromcal="GREG", tocal="MJD")
    53921.6275173611

    """

    fcal = _validate_calendar(fromcal)
    if fcal is None:
        raise ValueError("Invalid fromcal argument: '{}'".format(fromcal))

    tcal = _validate_calendar(tocal)
    if tcal is None:
        raise ValueError("Invalid tocal argument: '{}'".format(tocal))

    if fcal == "GREG":
        datestr = _to_timestr_dates(date)
        if datestr is None:
            dateobj = _from_timestr_chandra(date)
            if dateobj is None:
                raise ValueError("Expected datetime object or YYYY-MM-DD[T ]HH:MM:SS[.SS] but sent '{}'".format(date))

            datestr = _to_timestr_dates(dateobj)
            if datestr is None:
                raise RuntimeError("*Internal error* unable to convert datetime object {}".format(dateobj))

        date = datestr

    return _dates(date, fromcal=fcal, tocal=tcal)

# End
