#
# Copyright (C) 2013, 2014, 2015, 2016, 2021
#           Smithsonian Astrophysical Observatory
#
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
A representation of an observation, including event file and information
about the observation, including ancillary files.

Very much a Work-In-Progress. I am wondering about having separate
ACIS and HRC sub-classes, which would require a more factory-style
interface. Is it worth it?
"""

import os

import ciao_contrib.ancillaryfiles as ancillary
import ciao_contrib.logger_wrapper as lw

# Can not rely on too many modules in ciao_contrib._tools as do
# not want circular dependencies
import ciao_contrib._tools.fileio as fileio
import ciao_contrib._tools.utils as utils

# __all__ = ("",)

lgr = lw.initialize_module_logger('_tools.obsinfo')
v2 = lgr.verbose2
v3 = lgr.verbose3


def _remove_dmfilter(fname):
    """Return fname stripped of any DM filter,
    so '/foo/bar/baz.fits' and '/foo/bar/baz.fits[sky=region(../src.reg)]'
    both return '/foo/bar/baz.fits'.

    For now only look at DM filter syntax (so anything "[...") but
    could also look for CFITSIO syntax ("+<block num>" and "...(copy-name)"),
    but only do this if find users actually use this (as unlikely used for
    the use cases of this module, although being used more).
    """

    return fname.split("[")[0]


def normalize_path(fname, start='.'):
    """Using relpath can lead to strange looking file names, e.g. when
    the file does not exist on the same path hierarchy
    as the current directory. So really it should be relative
    if sensible, otherwise absolute.

    The start argument indicates where it should be relative to;
    the default value of '.' indicates the current working directory.

    fname must be an absolute path, otherwise a ValueError is raised
    """

    if not os.path.isabs(fname):
        raise ValueError(f"Expected an absolute path for fname={fname}")

    cpath = os.getcwd()
    if os.path.commonprefix([cpath, fname]) in ['', '/']:
        return fname
    else:
        return os.path.relpath(fname, start=start)


class ObsInfo:
    """Represent an observation in a form useful to fluximage,
    merge_obs, and related codes. It may be useful for other cases.
    """

    def __init__(self, infile):
        """Create the object from the information in infile.

        Various checks are made, including that the input is a table,
        contains appropriate keywords, and does not represent a merged
        observation.
        """

        # This is not designed to be efficient, since file(s)
        # may be opened multiple times.
        #
        (keys, cols) = fileio.get_keys_cols_from_file(infile)
        if cols is None:
            raise IOError(f"{infile} is an image, not a table!")

        try:
            self._instrument = keys['INSTRUME']
            self._detector = keys['DETNAM']
            self._grating = keys['GRATING']
            self._tstart = keys['TSTART']
            self._tstop = keys['TSTOP']
        except KeyError as ke:
            raise IOError(f"File {infile} is missing the {ke.args[0]} keyword!") from None

        if self._instrument not in ['ACIS', 'HRC']:
            raise IOError(f"Unsupported INSTRUME={self._instrument} in {infile}.")

        self._obsid = utils.make_obsid_from_headers(keys, infile=infile)

        # Note this re-opens the file, so is wasteful but we assume that since
        # the file has just been opened it is in some cache so access time
        # should not be too bad
        # (and the routine is not optimised for speed anyway).
        #
        if self._instrument == 'ACIS':
            self._aimpoint = fileio.get_aimpoint(infile)
        else:
            self._aimpoint = None

        self._tangent = fileio.get_tangent_point(infile)

        # Store the absolute path
        # NOTE: for the directory we strip out any DM filter, since
        #   it can get tripped up since
        #      os.path.dirname('/foo/bar/6437_reproj_evt.fits[sky=region(../src.sky.reg)]')
        #   == '/foo/bar/6437_reproj_evt.fits[sky=region(..'
        #
        self._evtfile = os.path.normpath(os.path.abspath(infile))
        self._evtdir = os.path.dirname(_remove_dmfilter(self._evtfile))
        self._header = keys
        self._cols = cols
        self._colnames = [col.name.upper() for col in cols]
        self._nrows = keys['__NROWS']

        # Cache queries for the ancillary files
        self._ancillary = {}

    def __str__(self):
        return f"ObsInfo: file={self.evtfile} ObsId={self.obsid}"

    @property
    def evtfile(self):
        "The event file for the observation (absolute path)"
        return self._evtfile

    def get_evtfile(self):
        """The event file, relative to the current working directory
        if it makes sense, otherwise an absolute path.
        """
        return normalize_path(self._evtfile)

    def get_evtfile_no_dmfilter(self):
        "The event file, relative to the current working directory, with no DM filter expression."
        return _remove_dmfilter(self.get_evtfile())

    def get_header(self):
        "Return a copy of the header"
        return self._header.copy()

    def get_keyword(self, key):
        """Return the value of the given keyword,
        or raises a KeyError."""
        try:
            return self._header[key]
        except KeyError:
            raise KeyError(f"The event file {self.get_evtfile()} has no {key} keyword") from None

    def has_column(self, colname):
        "Does the event file contain this column (case insensitive name)"
        return colname.upper() in self._colnames

    def get_colnames(self):
        """Return a list of the column names in the event file. It is not
        guaranteed to contain virtual columns or the 'combined' name of
        vector columns. The names are returned as all upper case.
        """
        return [cname for cname in self._colnames]

    def get_columns(self):
        """Return a list of the columns in the event file. It is not
        guaranteed to contain virtual columns or the 'combined' name of
        vector columns.
        """
        # do not bother copying the elements as they are read only
        return [colinfo for colinfo in self._cols]

    @property
    def instrument(self):
        "The value of the INSTRUME keyword"
        return self._instrument

    @property
    def detector(self):
        "The value of the DETNAM keyword"
        return self._detector

    @property
    def grating(self):
        "The value of the GRATING keyword"
        return self._grating

    @property
    def tstart(self):
        "The value of the TSTART keyword"
        return self._tstart

    @property
    def tstop(self):
        "The value of the TSTOP keyword"
        return self._tstop

    @property
    def obsid(self):
        "The ObsId of the observation (an object, not a string)"
        return self._obsid

    @property
    def aimpoint(self):
        "The CCD where the aimpoint of the observation falls (None for HRC data)"
        return self._aimpoint

    @property
    def tangentpoint(self):
        "The ra,dec of the tangent point (in degrees)"
        return self._tangent

    @property
    def nrows(self):
        "The number of rows in the event file."
        return self._nrows

    def get_chipname(self):
        "The name of the chip column (ccd_id or chip_id)"
        if self._instrument == 'ACIS':
            return "ccd_id"
        elif self._instrument == 'HRC':
            return "chip_id"
        else:
            # should not happen due to check in __init__ but leave
            # here, just in case code changes or some agent decided
            # to change the _instrument field.
            raise ValueError(f"Unsupported INSTRUME={self._instrument} in {self._evtfile}")

    def get_asol_(self, indir='.'):
        """Return the location of the asol file(s), relative to the
        indir argument (if possible), based on the ASOLFILE keyword or
        the value set by a set_asol() call.

        The return value is an array unless no file can be found
        (either because the keyword is empty, missing, or the files
        can not be found), in which case None is returned.
        """

        evtfile = self.get_evtfile()
        try:
            v3(f"Looking for asol ancillary file for {evtfile} in cache.")
            fnames = self._ancillary['asol']
            v3(f" -> {fnames} (cached)")
        except KeyError:
            v2(f"Looking for asol file(s) in header of {evtfile}")
            fnames = ancillary.find_ancillary_files_header(self._header,
                                                           ['asol'],
                                                           cwd=self._evtdir,
                                                           absolute=True,
                                                           keepnone=True
                                                           )
            v3(f"Response={fnames}")
            fnames = fnames[0]
            if fnames is not None:
                v3(f"Validating as aspsols: {fnames}")
                for fname in fnames:
                    fileio.validate_asol(fname)

                fnames = fileio.sort_mjd(fnames)
                v3(f"After time-sorting, aspsols: {fnames}")

            # Store the time-sorted list
            self._ancillary['asol'] = fnames

        if fnames is None:
            return None
        else:
            return [normalize_path(fname, start=indir) for fname in fnames]

    def get_asol(self, indir='.'):
        """Return the location of the asol file(s), relative to the
        indir argument (if possible), or raise an IOError. An array is always
        returned, even if there is only one file.

        Use get_asol_() to return None rather than to raise an error
        if there is no file.
        """

        rval = self.get_asol_(indir=indir)
        if rval is None:
            evtfile = self.get_evtfile()
            try:
                asolfile = self._header['ASOLFILE']
                raise IOError(f"ASOLFILE={asolfile} from {evtfile} not found.")
            except KeyError:
                # Could throw a KeyError but then downstream code may expect
                # the full message to be the missing key. Could throw a
                # ValueError, but leave as IOError to match the other failure.
                raise IOError(f"Event file {evtfile} has no ASOLFILE keyword.") from None

        return rval

    def _validate_ancillary_type(self, atype):
        """Check that atype is valid: 'bpix', 'mask',
        or 'dtf'/'pbk', depending on the instrument.

        PBK support is deprecated as of CIAO 4.6.
        """

        atypes = ['bpix', 'mask']
        if self._instrument == 'ACIS':
            atypes.append('pbk')
        elif self._instrument == 'HRC':
            atypes.append('dtf')
        else:
            # should not happen due to check in __init__ but leave
            # here, just in case code changes or some agent decided
            # to change the _instrument field.
            raise ValueError(f"Unsupported INSTRUME={self._instrument} in {self._evtfile}")

        if atype not in atypes:
            raise ValueError(f"Invalid ancillary type '{atype}' for {self.get_evtfile()}; must be one of {atypes}")

    def get_ancillary_(self, atype, indir='.'):
        """Return the location of the ancillary file, relative to the
        indir directory (if possible), or the string 'NONE' (or 'CALDB'
        for bpix), or None (if the file can not be found or the keyword
        does not exist).  The value from the corresponding set_ancillary()
        call is used in preference to the file header.

        atype should be one of 'bpix', 'dtf', 'mask', or 'pbk'.

        Prior to January 2014, mask/pbk/dtf=NONE returned an empty string;
        this has been changed back to returning "NONE".

        As of CIAO 4.6 the 'pbk' type should no longer be needed,
        so support will be removed at a future date.
        """

        self._validate_ancillary_type(atype)
        evtfile = self.get_evtfile()
        try:
            v3(f"Looking for {atype} ancillary file for {evtfile} in cache.")
            fname = self._ancillary[atype]
            v3(f" -> {fname} (cached)")
        except KeyError:
            v2(f"Looking for {atype} file in header of {evtfile}")
            fnames = ancillary.find_ancillary_files_header(self._header,
                                                           [atype],
                                                           cwd=self._evtdir,
                                                           absolute=True,
                                                           keepnone=True)
            v3(f"Response={fnames}")
            fname = fnames[0]
            if fname is not None:
                fname = fname[0]

                # Special case the BPIX handling because ARDLIB will not
                # search for .gz versions automatically, unlike most of
                # CIAO.
                if atype == "bpix" and fname not in ['CALDB', 'NONE']:
                    if not os.path.exists(fname):
                        fname += ".gz"
                        if not os.path.exists(fname):
                            fname = None

            self._ancillary[atype] = fname

        if fname == 'NONE' and atype in ['dtf', 'mask', 'pbk']:
            return "NONE"
        elif fname is None or fname == 'NONE' or \
                (atype == 'bpix' and fname == 'CALDB'):
            return fname
        else:
            return normalize_path(fname, start=indir)

    def get_ancillary(self, atype, indir='.'):
        """Return the location of the ancillary file, relative to the indir
        directory (if possible), or the string 'NONE' (or 'CALDB' for bpix), or
        raise an IOError if it can not be found.  The value from the
        corresponding set_ancillary() call is used in preference to
        the file header.

        atype should be one of 'bpix', 'dtf', 'mask', or 'pbk'.

        Use get_ancillary_() to return None rather than to raise an error
        if there is no file.

        As of CIAO 4.6 the 'pbk' type should no longer be needed,
        so support will be removed at a future date.
        """

        self._validate_ancillary_type(atype)
        fname = self.get_ancillary_(atype, indir=indir)
        if fname is None:
            evtfile = self.get_evtfile()
            key = f"{atype.upper()}FILE"
            try:
                keyval = self._header[key]
                raise IOError(f"{key}={keyval} from {evtfile} not found")
            except KeyError:
                # See get_asol() for choice of IOError here
                raise IOError(f"Event file {evtfile} has no {key} keyword.") from None

        return fname

    # TODO:
    #    should this verify the time range overlaps the data?
    #
    def set_asol(self, asolfiles):
        """Set the asol files to use for this observation. This
        should be an array even if only one file is given. A check
        is made that each file (or file+'.gz') exists.

        A minimal check is made that the file is an aspect
        solution (not complete but does recognize the difference
        between aspsol and asphist files). The files are
        re-ordered to be in time order (if necessary).

        This *overrides* the ASOLFILE setting.
        """

        evtfile = self.get_evtfile()
        filenames = []
        for asol in asolfiles:
            v3(f"Verifying asol file: {asol}")
            if not os.path.exists(asol):
                if os.path.exists(asol + '.gz'):
                    asol += '.gz'
                else:
                    raise IOError(f"Unable to find aspect solution file: {asol}")

            asol = os.path.normpath(os.path.abspath(asol))
            fileio.validate_asol(asol)
            filenames.append(asol)

        try:
            oldfiles = self._ancillary['asol']
            v3(f"Over-riding ASOLFILE={oldfiles} for {evtfile}")

        except KeyError:
            v3(f"Setting asol files for {evtfile}")

        self._ancillary['asol'] = fileio.sort_mjd(filenames)

    # TODO:
    #    should this verify the time range overlaps the data
    #    or that the ObsId matches or ...?
    #
    def set_ancillary(self, atype, aname):
        """Set the ancillary file for the given type (atype should be one
        of 'bpix', 'dtf', 'mask', or 'pbk'). Use set_asol() for aspect
        solutions.

        aname should be the file name, and can be a relative name
        (internally it is stored as an absolute path). A check is made
        that the file exists (including '.gz').

        This *overrides* the <atype>FILE setting in the header of the
        event file.

        The file name can be set to 'NONE' (case insensitive) to
        say "ignore this calibration file", or, for bpix, 'CALDB'
        (case insensitive) to say use the CALDB bpix file instead.

        As of CIAO 4.6 the 'pbk' type should no longer be needed,
        so support will be removed at a future date.
        """

        evtfile = self.get_evtfile()
        v3(f"[set_ancillary:obsid={self.obsid}] Verifying {atype} file: {aname}")
        skipnames = ['NONE']
        if atype == 'bpix':
            skipnames.append('CALDB')

        if aname.upper() in skipnames:
            aname = aname.upper()
        else:
            if not os.path.exists(aname):
                if os.path.exists(aname + '.gz'):
                    aname += '.gz'
                else:
                    raise IOError(f"Unable to find {atype} file: {aname}")

            aname = os.path.normpath(os.path.abspath(aname))

        try:
            oldfile = self._ancillary[atype]
            v3(f"Over-riding {atype.upper()}FILE={oldfile} for {evtfile}")

        except KeyError:
            v3(f"Setting {atype} file for {evtfile}")

        self._ancillary[atype] = aname

# End
