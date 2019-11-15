#
#  Copyright (C) 2012, 2013, 2015, 2016, 2019
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
Find ancillary files from a file header (for Chandra data).

The current list of header keyword and file types are:

  =========   ========
  Keyword     Filetype
  =========   ========
  ASOLFILE    ASOL
  BPIXFILE    BPIX
  DTFFILE     DTF
  FLTFILE     FLT
  MASKFILE    MASK
  MTLFILE     MTL
  PBKFILE     PBK
  =========   ========

The following keywords may be supported at a later date.

  =========   ========
  Keyword     Filetype
  =========   ========
  THRFILE     THRESH
  GAINFILE    GAIN
  CTIFILE     CTI
  GRD_FILE    GRADE
  AIMPFILE    AIMPOINT
  GEOMFILE    GEOM
  SKYFILE     SKY
  TDETFILE    TDET
  =========   ========

Notes
-----

As of CIAO 4.6 there should be no need for the PBK (parameter block)
file, but support has been left in.

"""

import os

import pycrates
import stk

from ciao_contrib.logger_wrapper import initialize_module_logger

__all__ = (
    'find_ancillary_files',
    'find_ancillary_files_crate',
    'find_ancillary_files_header')

lgr = initialize_module_logger('ancillaryfiles')
v1 = lgr.verbose1
v3 = lgr.verbose3
v4 = lgr.verbose4

__typemap = {
    'asol': 'ASOLFILE',
    'bpix': 'BPIXFILE',
    'dtf': 'DTFFILE',
    'flt': 'FLTFILE',
    'mask': 'MASKFILE',
    'mtl': 'MTLFILE',
    'pbk': 'PBKFILE',
    # 'thresh': 'THRFILE',
    # 'gain': 'GAINFILE',
    # 'cti': 'CTIFILE',
    # 'grade': 'GRD_FILE',
    # 'aimpoint': 'AIMPFILE',
    # 'geom': 'GEOMFILE',
    # 'sky': 'SKYFILE',
    # 'tdet': 'TDETFILE',
    }


def validate_filetype(ftype):
    """Returns the header value for the
    given file type. Raises a ValueError if ftype
    is invalid. ftype is case insensitive.
    """

    try:
        key = __typemap[ftype.lower()]

    except KeyError:
        tkeys = __typemap.keys()
        tkeys.sort()
        raise ValueError("Invalid filetype '{}', ".format(ftype) +
                         "must be one of: {}".format(" ".join(tkeys)))

    return key


def find_file(filename, absolute=True, cwd='.'):
    """Return the path to the given file or None if it can
    not be found. We assume that filename contains no DM filter (or
    if it does then it doesn't contain any / characters within the filter
    that would confuse os.path.abspath).

    See find_ancillary_files_header() for a discussion of the search
    path and description of the absolute and cwd arguments.
    """

    search_path = ['.',
                   'repro', 'primary', 'secondary',
                   '../repro', '../primary', '../secondary',
                   ]

    base = os.path.abspath(cwd)
    v4("Looking for {} with base={}".format(filename, base))
    for p in search_path:
        fullpath = os.path.normpath(os.path.join(base, p, filename))
        v4(" -> " + fullpath)
        if os.path.exists(fullpath) or os.path.exists(fullpath + '.gz'):
            v4("    found")
            if absolute:
                return fullpath
            else:
                return os.path.relpath(fullpath, start='.')

    v4("File not found.")
    return None


def find_files(fnames, absolute=True, cwd='.', keepnone=True):
    """Return an array of file names giving the absolute (absolute=True)
    or relative path to fnames, if they are all found, otherwise None is
    returned.

    fnames is a string and is treated as a stack.

    cwd gives the location of the directory to use as the base when
    calculating relative paths (so it is only used if absolute=False).

    If keepnone is True then a value of NONE is retained, otherwise
    the return value is None rather than an array. This lets you
    identify when a file value was given as NONE versus it not
    being found.
    """

    out = []
    v4("Calling find_files on " + fnames)
    for fname in stk.build(fnames):
        if fname == 'NONE':
            if keepnone:
                out.append(fname)
                continue
            else:
                return None

        path = find_file(fname, absolute=absolute, cwd=cwd)
        if path is None:
            return None

        out.append(path)

    return out


def find_ancillary_files_header(header, filetypes, cwd='.',
                                absolute=True, keepnone=True):
    """Find the ancillary files for an observation.

    Report the location of files related to the input file;
    these are Chandra-specific files such as the aspect solution
    or bad-pixel file.

    Parameters
    ----------
    header : dict
        The dictionary containing the header keywords to query
        (the keys are expected to contain the relevant *FILE keywords
        used by the Chandra Standard Data Processing pipeline).
    filetypes : sequence of str
        The file types to find. The valid elements are:
        'ASOL', 'BPIX', 'DTF', 'FLT', 'MASK', 'MTL', and
        'PBK'. Note that the case of the strings is not important,
        and that although 'PBK' is supported it is not expected
        to be used (it is not needed by CIAO tools as of release
        4.6 of CIAO).
    cwd : str
        The base directory to use when absolute is True.
    absolute : bool, optional
        Should the files contain an absolute path (the default
        value of True) or be relative to the cwd parameter (False)?
    keepnone : bool, optional
        If the header keyword is set to 'NONE' for a filetype, should
        the return value be 'NONE' (the default value of True) or
        None (when False)?

    Returns
    -------
    files : list of list of strings
        The length of files matches that of the filetypes
        argument, and each element is a list of file names (this
        is to support aspect-solution files, which can have multiple
        versions for a file). If the relevant keyword in filename
        is set but the file (or files) can not be found then None
        is returned instead of a list of file names. If the keyword
        is set to 'NONE' and keepnone is True then 'NONE' is returned,
        otherwise None is returned.

    See Also
    --------
    find_ancillary_crate, find_ancillary_files

    """

    out = []
    for ftype in filetypes:
        key = validate_filetype(ftype)

        try:
            fnames = header[key]

        except KeyError:
            out.append(None)
            continue

        except TypeError:
            raise ValueError("The header argument does not appear to be a dictionary.")

        v3("Header: {} = {}".format(ftype, fnames))

        tout = find_files(fnames, absolute=absolute, cwd=cwd,
                          keepnone=keepnone)
        out.append(tout)

    return out


def find_ancillary_files_crate(cr, filetypes, cwd='.',
                               absolute=True, keepnone=True):
    """Find the ancillary files for an observation.

    Report the location of files related to the input file;
    these are Chandra-specific files such as the aspect solution
    or bad-pixel file.

    Parameters
    ----------
    cr : pycrate Crate instance
        The file to query.
    filetypes : sequence of str
        The file types to find. The valid elements are:
        'ASOL', 'BPIX', 'DTF', 'FLT', 'MASK', 'MTL', and
        'PBK'. Note that the case of the strings is not important,
        and that although 'PBK' is supported it is not expected
        to be used (it is not needed by CIAO tools as of release
        4.6 of CIAO).
    cwd : str
        The base directory to use when absolute is True.
    absolute : bool, optional
        Should the files contain an absolute path (the default
        value of True) or be relative to the cwd parameter (False)?
    keepnone : bool, optional
        If the header keyword is set to 'NONE' for a filetype, should
        the return value be 'NONE' (the default value of True) or
        None (when False)?

    Returns
    -------
    files : list of list of strings
        The length of files matches that of the filetypes
        argument, and each element is a list of file names (this
        is to support aspect-solution files, which can have multiple
        versions for a file). If the relevant keyword in filename
        is set but the file (or files) can not be found then None
        is returned instead of a list of file names. If the keyword
        is set to 'NONE' and keepnone is True then 'NONE' is returned,
        otherwise None is returned.

    See Also
    --------
    find_ancillary_files, find_ancillary_header

    """

    header = {}

    def set_header(k):
        v = cr.get_key_value(k)
        if v is not None:
            header[k] = v

    for ftype in filetypes:
        key = validate_filetype(ftype)
        set_header(key)

    v4("find_ancillary_files_crate: header={}".format(header))
    return find_ancillary_files_header(header,
                                       filetypes,
                                       absolute=absolute,
                                       cwd=cwd,
                                       keepnone=keepnone)


def find_ancillary_files(filename, filetypes,
                         absolute=True, keepnone=True):
    """Find the ancillary files for an observation.

    Report the location of files related to the input file;
    these are Chandra-specific files such as the aspect solution
    or bad-pixel file.

    Parameters
    ----------
    filename : str
        The name of the file defining the observation; it can be
        any file with the necessary *FILE header keywords, but
        it is often the event file.
    filetypes : sequence of str
        The file types to find. The valid elements are:
        'ASOL', 'BPIX', 'DTF', 'FLT', 'MASK', 'MTL', and
        'PBK'. Note that the case of the strings is not important,
        and that although 'PBK' is supported it is not expected
        to be used (it is not needed by CIAO tools as of release
        4.6 of CIAO).
    absolute : bool, optional
        Should the files contain an absolute path (the default
        value of True) or be relative to the current working
        directory (when False)?
    keepnone : bool, optional
        If the header keyword is set to 'NONE' for a filetype, should
        the return value be 'NONE' (the default value of True) or
        None (when False)?

    Returns
    -------
    files : list of list of strings
        The length of files matches that of the filetypes
        argument, and each element is a list of file names (this
        is to support aspect-solution files, which can have multiple
        versions for a file). If the relevant keyword in filename
        is set but the file (or files) can not be found then None
        is returned instead of a list of file names. If the keyword
        is set to 'NONE' and keepnone is True then 'NONE' is returned,
        otherwise None is returned.

    See Also
    --------
    find_ancillary_crate, find_ancillary_header

    Notes
    -----
    The valid file types are:

    ========== ======================================================
    File type  Description
    ========== ======================================================
    ASOL       The aspect solution (can be multiple files).
    BPIX       The bad-pixel file.
    DTF        The dead-time factor file (HRC only).
    FLT
    MASK       The mask file.
    MTL        The mission timeline.
    PBK        The paramater block (not needed in CIAO 4.6 or later).
    ========== ======================================================

    More information can be found in the Chandra Data Products
    Guide [1]_.

    The search for each file is made in the following locations,
    relative to the location of filename:

        .
        repro/
        primary/
        secondary/
        ../repro/
        ../primary/
        ../secondary/

    The file name is returned even if it doesn't exist but there
    is a *.gz version present. This is supported by most CIAO
    tools transparently, but there are places where it may not
    work (in particular the ardlib settings should use the
    actual file name).

    References
    ----------

    .. [1] https://cxc.harvard.edu/ciao/data_products_guide/

    Examples
    --------

    >>> os.chdir('/example/path')
    >>> evtfile = '50/repro/acisf00050_repro_evt2.fits'
    >>> ftypes =  ['asol', 'mtl', 'pbk', 'mask']
    >>> find_ancillary_files(evtfile, ftypes)
    [['/example/path/50/repro/pcadf053035261N003_asol1.fits'],
     ['NONE'],
     ['/example/path/50/repro/acisf053036614N003_pbk0.fits'],
     ['/example/path/50/repro/acisf00050_000N003_msk1.fits']]
    >>> find_ancillary_files(evtfile, ftypes, absolute=False)
    [['50/repro/pcadf053035261N003_asol1.fits'],
     ['NONE'],
     ['50/repro/acisf053036614N003_pbk0.fits'],
     ['50/repro/acisf00050_000N003_msk1.fits']]

    """

    # Remove DM filter since it can mess up the os.path routines.
    # This is not robust but I am willing to live with the
    # assumption that users do not have many files with [ as a
    # valid character.
    #
    lpos = filename.find('[')
    if lpos == -1:
        fullname = os.path.normpath(os.path.abspath(filename))
    else:
        fullname = os.path.normpath(os.path.abspath(filename[:lpos]))

    basedir = os.path.dirname(fullname)
    cr = pycrates.read_file(filename)
    out = find_ancillary_files_crate(cr, filetypes,
                                     absolute=absolute,
                                     cwd=basedir,
                                     keepnone=keepnone)
    return out
