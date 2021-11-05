#
#  Copyright (C) 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2021
#            Smithsonian Astrophysical Observatory
#
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
Utility routines used by fluximage/merge_obs/...
"""

import os
import functools
import subprocess as sbp

import paramio
import stk

import ciao_contrib.logger_wrapper as lw

import ciao_contrib.runtool as rt
import coords.format

__all__ = (
    "ObsId",
    "make_obsid_from_headers",

    "print_version",
    "split_outroot",
    "to_number",
    "equal_elements",
    "getUniqueSynset",
    "thresh_is_set",

    "parse_range",
    "parse_xygrid",
    "parse_refpos",
    "sky_to_arcsec",

    "process_tmpdir"
    )

lgr = lw.initialize_module_logger('_tools.utils')
v1 = lgr.verbose1
v3 = lgr.verbose3
v4 = lgr.verbose4

# This is a manually-curated list. It is (as of 2015) not expected
# to grow.
#
_multi_obi_obsids = [
    82, 108, 279, 380, 400, 433, 800, 861, 897, 906, 943, 1411, 1431,
    1456, 1561, 1578, 2010, 2042, 2077, 2365, 2783, 3057, 3182, 3764,
    4175, 60879, 60880, 62249, 62264, 62796
    ]


def list_multi_obi_obsids():
    """Returns the list of Chandra multi-OBI ObsIds.

    Returns
    -------
    obsids : array of int
        An array of the Chandra ObsIds which have multiple OBIs.

    """
    return _multi_obi_obsids[:]


def is_multi_obi_obsid(obsid):
    """Returns True if obsid is a multi-obi ObsId.

    Parameters
    ----------
    obsid
        The ObsId to check. Will be converted to an integer.

    Returns
    -------
    flag : Bool

    """

    try:
        return int(obsid) in _multi_obi_obsids
    except ValueError:
        raise ValueError(f"obsid argument does not appear to be an integer: {obsid}")


# TODO: should the file name be provided to ObsId so that error
#       messages can be more illuminating?
#

@functools.total_ordering
class ObsId:
    """Represents an observation, as specified by
    an OBS_ID value and, optionally:

      "e1" or "e2"
        if an interleaved ACIS observation (corresponding
        to CYCLE=P/S)

      obi_num
        for multi-obi datasets.

    Unlike the header of the ACIS file, the cycle attribute will only
    be present if this file appears to be part of an interleaved-mode
    observation (either CYCLE=S or TIMEDELB!=0).

    The presence of the OBI_NUM keyword in a file depends on how it
    was processed (if an archive evt2 file then it may not have the
    keyword [*], but if processed via chandra_repro then it should
    have it).

    [*] multi-obi datasets will not have it because they are formed by
    merging together the different OBIs which results in the keyword
    being removed.

    Converting to a string uses the observation id followed by "e1" if
    a primary observation or "e2" if a secondary observation. The
    decision to append "_{:03d}.format(obi)" to this string is
    controlled by the is_multi_obi attribute. I am not 100% happy with
    this interface - hard to reason about - but it makes some things
    easier.

    Objects are judged to be equal based on

      1) ObsId (lower values come first)
      2) cycle (primary before secondary)
      3) OBI_NUM (lower values first; None/undefined is "first")

    So the ordering is nothing to do with time (even though for many
    cases it will end up so, it is not guaranteed). Also, as the
    values are strings, the comparison is done using string rather
    than numeric rules (apart from OBI_NUM).

    If an ObsId is marked as being multi-obi, then it is checked to
    make sure we recognize it (as there's a small set of such
    observations, and it is not expected to increase, this is a
    feasible check). This behavior may change, as more experience is
    gained with the multi-OBI case.

    Use the make_obsid_from_headers() routine if you have a dictionary
    of headers.

    Experimental change: for multi-obi observations we error out if
    obi is not set.

    """

    def __init__(self, obsid, cycle=None, obi=None):
        """Represent an ObsId:

          obsid is the OBS_ID keyword
          cycle        CYCLE
          obi          OBI_NUM

        The inputs are expected to be string value (when not None).

        Fails if obsid is 'merged' (case insensitive). Invalid CYCLE
        values (not 'P' or 'S') or OBI_NUM values (integer >= 0) are
        ignored; in this case a warning is displayed at the verbose=1
        level.

        The is_multi_obi attribute should be set after calling this
        object when the OBI value is important (i.e. if only using a
        single OBI of a multi-OBI dataset, it may not be important).
        """

        v3(f"ObsId sent obsid={obsid} cycle={cycle} obi={obi}")
        if obsid.lower() == "merged":
            raise ValueError(f"The OBS_ID value is '{obsid}'")

        if cycle not in [None, 'P', 'S']:
            v1(f"WARNING: ObsId {obsid} has unrecognized CYCLE={cycle}, assuming not interleaved.")
            cycle = None

        obival = None
        if obi is not None:
            try:
                obival = int(obi)
                if obival < 0:
                    v1(f"WARNING: ObsId {obsid} has obi={obi} which is < 0; ignoring.")
                    obival = None

            except ValueError:
                v1(f"WARNING: ObsId {obsid} has invalid obi={obi} (expected integer); ignoring.")

        # Note: store obi as an integer value; it's an integer in
        # the header, so retain that here. The choice to display as
        # a three-digit, zero-prefixed, integer is made at display
        # time, not here.
        #
        self._obsid = obsid
        self._cycle = cycle
        self._obi   = obival

        self._is_multi_obi = False

        # experimental support for multi-obi cases
        #
        if is_multi_obi_obsid(obsid):
            if obival is None:
                raise ValueError(f"For multi-OBI datasets like {obsid} the obi argument must be set")

            self._is_multi_obi = True

    @property
    def obsid(self):
        "The ObsId value."
        return self._obsid

    @property
    def cycle(self):
        "The Cycle value (None, 'S', or 'P')."
        return self._cycle

    @property
    def obi(self):
        "The OBI value (None, or an integer >= 0)."
        return self._obi

    @property
    def is_multi_obi(self):
        """Is this marked as a multi-OBI observation (so that the OBI value is
        included in the string representation of the ObsId)? This can
        only be set if the OBI value is not None, and if the ObsId is
        recognized as a multi-OBI dataset (it errors out, as a safety
        precaution; this might be relaxed).

        """
        return self._is_multi_obi

    # TODO: take this away????
    @is_multi_obi.setter
    def is_multi_obi(self, flag):
        if flag and self.obi is None:
            raise ValueError(f"Unable to set multi-obi flag for ObsId {self.obsid} as no OBI value.")

        v3(f"Checking if ObsId {self.obsid} (with OBI={self.obi}) is a multi-OBI dataset")
        v4(f"ObsId {self.obsid} has type {type(self.obsid)}")
        if flag and not is_multi_obi_obsid(self.obsid):
            raise ValueError(f"ObsId {self.obsid} is not recognized as a multi-OBI dataset.")

        self._is_multi_obi = flag

    # The reason for ignoring OBI is that in most cases we do not want to use
    # it (since it's not needed in the vast-majority of ObsIds). To support
    # multi-OBI datasets, the is_multi_obi flag can be changed by the caller
    # (since it's not obvious we can tell from an ObsId/OBI value whether
    # it's a multi-obi dataset). Technically we now can, but this comment
    # is from an earlier version of the code.
    #
    def __str__(self):
        """The OBI is included if is_multi_obi is set on the object
        (and there is an OBI value to include)."""
        out = f"{self.obsid}"
        if self.cycle == 'P':
            out += 'e1'
        elif self.cycle == 'S':
            out += 'e2'
        if self.is_multi_obi and self.obi is not None:
            out += f"_{self.obi:03d}"
        return out

    def __repr__(self):
        "This is only for debugging rather than being valid Python"
        return f"ObsId({self.obsid},cycle={self.cycle},obi={self.obi})"

    # no checks to avoid attribute errors if used with an invalid rhs
    def __eq__(self, rhs):
        return (self.obsid, self.cycle, self.obi) == \
            (rhs.obsid, rhs.cycle, rhs.obi)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    # Fortunately 'P' and 'S' have the ordering we want and we assume that
    # we do not end up comparing the same interleaved-mode ObsId where
    # one of them does not have information on its cycle.
    #
    # None also appears to compare < other values - e.g. None < 0 == True
    # which is what we defined the ordering to be.
    #
    def __lt__(self, rhs):
        return (self.obsid, self.cycle, self.obi) < \
            (rhs.obsid, rhs.cycle, rhs.obi)

    # So we can use this as a key in a dictionary
    def __hash__(self):
        return hash((self.obsid, self.cycle, self.obi))


def make_obsid_from_headers(headers, infile=None):
    """Create an ObsId object from the headers, which should
    accept dictionary-like access for the OBS_ID, OBI_NUM, CYCLE, and
    TIMEDELB keywords. The TIMEDELB keyword is used to determine
    whether this is an interleaved mode observatioin, when > 0,
    or not. The only required keyword is OBS_ID.

    This routine errors with a ValueError if OBS_ID indicates
    a merged observation.

    The infile argument is only used in error messages.
    """

    if infile is not None:
        v3(f"Looking for ObsId from headers of {infile}.")
    else:
        v3("Looking for ObsId from headers.")

    try:
        obsid = headers['OBS_ID']
    except KeyError:
        emsg = "The OBS_ID value is missing"
        if infile is None:
            emsg += "."
        else:
            emsg += f" in {infile}."
        raise KeyError(emsg)
    except TypeError:
        raise TypeError("The input must accept string indexing.")

    if obsid.lower() == "merged":
        emsg = f"The OBS_ID value is '{obsid}'"
        if infile is None:
            emsg += "."
        else:
            emsg += f" in {infile}."
        raise ValueError(emsg)

    try:
        cycle = headers['CYCLE']
        timedelb = headers['TIMEDELB']
        try:
            timedelb = float(timedelb)
        except ValueError:
            v3(f"ObsId: obsid={obsid} cycle={cycle} unable to convert timedelb={timedelb}")
            cycle = None

        if timedelb > 0:
            v3(f"TIMEDEL={timedelb} is > 0 so assuming interleaved.")
        else:
            v3(f"TIMEDEL={timedelb} is <= 0 so assuming non-interleaved.")
            cycle = None

    except KeyError:
        v3(f"ObsId: obsid={obsid}; does not contain CYCLE or TIMEDELB.")
        cycle = None

    if cycle not in [None, 'P', 'S']:
        v1(f"WARNING: ObsId {obsid} has unrecognized CYCLE={cycle}, assuming not interleaved.")
        cycle = None

    try:
        obi = headers['OBI_NUM']
    except KeyError:
        v3(f"ObsId: obsid={obsid}; does not contain OBI_NUM")
        obi = None

    v3(f"ObsId: obsid={obsid} cycle={cycle} obi={obi}")
    return ObsId(obsid, cycle=cycle, obi=obi)


def print_version(toolname, version):
    """Print the name and version of the script"""

    v1(f"Running {toolname}")
    v1(f"Version: {version}\n")


def split_outroot(outroot):
    """Given the user's outroot, split it into
       (dirname, headname)
    where either component can be empty.

    If headname is not empty then we ensure it ends with
    '_'.
    """

    # split up the user's outroot into a directory name,
    # with the trailing /, and remaining text (which will
    # have a trailing _ added to it if one does not exist).
    #
    (dirname, head) = os.path.split(outroot)
    if dirname == "":
        outdir = ""
    else:
        outdir = dirname + "/"

    if head == '' or head.endswith('_'):
        outhead = head
    else:
        outhead = head + "_"

    v3(f"Splitting outroot parameter: {outroot} to dirname={outdir} head={outhead}")
    return (outdir, outhead)


def to_number(inval):
    """Convert a string-formatted number into an integer or float.  The input is assumed
    to have been created by paramio.pget, so is assumed to either be a valid number of INDEF.

    INDEF is converted to None, '1.0' to 1 (integer), and '1.2' to 1.2 (float).
    Any invalid input will throw a ValueError.
    """

    if inval.lower() == "indef":
        return None
    else:
        try:
            out = float(inval)
        except ValueError:
            raise ValueError(f"Unable to convert '{inval}' to a number.") from None

    # should we use out.is_integer()?
    if int(out) == out:
        return int(out)
    else:
        return out


def equal_elements(ls):
    """test to see if all elements in a list are equal"""
    if ls:
        i = iter(ls)
        try:
            element = i.__next__()
        except AttributeError:
            element = i.next()

        for value in i:
            if element != value:
                return False
    return True


def getUniqueSynset(ls):
    """get unique entries, while preserving order."""

    s = {}
    return [s.setdefault(u, u) for u in ls if u not in s]


def thresh_is_set(val):
    """Returns true if val is not one of
        None
        empty string
        none (case insensitive)
        0 or 0% or :
    """

    if val is None:
        return False

    return val.lower() not in ["", "none", "0", "0%", ":"]


def parse_range(rstr):
    """Convert a:b:#c or a:b:c into a tuple
    (lo, hi, binsize, nbins).
    """

    toks = rstr.split(":")
    if len(toks) != 3:
        raise ValueError(f"Expected a:b:c or a:b:#c, not {rstr}")

    toks = [tok.strip() for tok in toks]
    lo = to_number(toks[0])
    hi = to_number(toks[1])
    if toks[2][0] == '#':
        nbins = to_number(toks[2][1:])
        if nbins <= 0:
            raise ValueError(f"Number of bins must be > 0 in {rstr}")

        binsize = (hi - lo) * 1.0 / nbins

    else:
        binsize = to_number(toks[2])
        if binsize <= 0:
            raise ValueError(f"The binsize must be > 0 in {rstr}")

        nbins = (hi - lo) * 1.0 / binsize

    return (lo, hi, binsize, nbins)


def parse_xygrid(gstr):
    """Given the xygrid parameter value, return the
    grid specification. We first check to see if there is
    a file that matches this value, and run get-sky_limits
    on it. If this fails we return the input string.

    The return value is actually
      (grid, binval, xrng, yrng, (nx,ny))

    where we use the minimum bin size if the two axes have
    a different value. There is a validation check on the
    string value. xrng and yrng are tuples containing the lo/hi
    values for each axes, and nx/ny are the number of bins
    in the output image for each axis.
    """

    v3(f"Verifying xygrid={gstr}")

    with rt.new_pfiles_environment(ardlib=False, copyuser=False):
        devnull = open('/dev/null', 'w')
        sbp.call(["get_sky_limits", f"image={gstr}"],
                 stdout=devnull, stderr=devnull)
        devnull.close()
        xygrid = paramio.pgetstr("get_sky_limits", "xygrid")

    if xygrid == "":
        xygrid = gstr

    xystk = xygrid.split(",")
    if len(xystk) != 2:
        raise ValueError(f"xygrid should be a filename or 2 ranges separated by a comma, not '{xygrid}'!")

    # Note: lose some info if there is an error
    try:
        xrng = parse_range(xystk[0])
        yrng = parse_range(xystk[1])

    except ValueError:
        raise ValueError(f"xygrid should be a filename or xlo:xhi:#nx or dx,ylo:yhi:#ny or dy, not '{xygrid}'!") from None

    xbinsize = xrng[2]
    ybinsize = yrng[2]

    # We pick the smaller binsize (expect them to be the same)
    if xbinsize != ybinsize:
        v1(f"WARNING: X and Y axis bin sizes are different ({xbinsize} vs {ybinsize}); using the smaller.")
        binsize = min(xbinsize, ybinsize)
    else:
        binsize = xbinsize

    if int(binsize) == binsize:
        binsize = int(binsize)

    return (f"x={xystk[0]},y={xystk[1]}", binsize,
            (xrng[0], xrng[1]), (yrng[0], yrng[1]), (xrng[3], yrng[3]))


# TODO: need to deal with a file name that includes a DM filter
def parse_refpos(refpos):
    """Given a reference position from a user - a string that can be
    empty, a file name, or ra/dec values, return the tuple

      (ra, dec, filename)

    where the values are None if not relevant, otherwise are
    numbers or a string.

    If no values are given then returns None.
    """

    if refpos.strip() == "":
        return None

    elif os.path.isfile(refpos):
        v3("Reference position is a file.")
        return (None, None, refpos)

    v3(f"Extracting reference position from {refpos}")

    # Assume that no spaces are used to separate out
    # sexagesimal formats, so that we can treat the
    # argument as a stack
    #
    coord = stk.build(refpos)
    if len(coord) != 2:
        raise ValueError(f"Unable to parse {refpos} as a ra and dec value.")

    ra = coords.format.ra2deg(coord[0])
    dec = coords.format.dec2deg(coord[1])

    return (ra, dec, None)


def sky_to_arcsec(instrume, pixsize):
    """Given a distance in SKY pixels, convert to arc seconds.
    The instrume value should be ACIS or HRC.
    """

    if instrume == 'ACIS':
        return pixsize * 0.492
    elif instrume == 'HRC':
        return pixsize * 0.1318
    else:
        raise ValueError(f"Invalid instrume={instrume} argument, expected ACIS or HRC.")


def process_tmpdir(tmpdir):
    """Given a tmpdir argument we

        - converts the tmpdir to an absolute path, that is
          relative to the current working diretory
        - check that it exists (IOError if not)
        - check that it is a directory (IOError if not)
        - set os.environ["ASCDS_WORK_PATH"] to this value

    It returns the absolute path.
    """

    dname = os.path.abspath(tmpdir)
    if not os.path.exists(dname):
        raise IOError(f"The temporary directory {dname} does not exist!")

    if not os.path.isdir(dname):
        raise IOError(f"The temporary directory {dname} is not actually a directory!")

    os.environ["ASCDS_WORK_PATH"] = dname
    return dname

# End
