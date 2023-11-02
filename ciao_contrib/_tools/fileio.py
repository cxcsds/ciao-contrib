#
#  Copyright (C) 2010-2016, 2019, 2020, 2023
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
File I/O utility routines: intended for processing FIS/data files.
"""

import glob
import os
import tempfile

import numpy as np

import cxcdm
import pycrates
import stk

import ciao_contrib.ancillaryfiles as ancillary
import ciao_contrib.cxcdm_wrapper as cw
import ciao_contrib.logger_wrapper as lw
import ciao_contrib.runtool as runtool

import ciao_contrib._tools.utils as utils

from ciao_contrib.region.fov import FOVRegion, AxisRange

__all__ = (
    "get_infile_type",
    "get_filter",
    "get_file",
    "get_file_filter",
    "get_ccds",
    "get_chips",
    "get_obsid",
    "get_image_units",
    "get_keys_from_file",
    "get_keys_cols_from_file",
    "get_column_unique",
    "outfile_clobber_checks",
    "rename_file_extension",
    "remove_path",
    "check_valid_file",
    "validate_outdir",

    "get_file_from_header",
    "get_minmax_times",

    # may want to move the following elsewhere
    "get_subspace",
    "fov_limits",
    "get_sky_range",
    "find_output_grid",
    "get_tangent_point")

lgr = lw.initialize_module_logger('_tools.fileio')
v1 = lgr.verbose1
v2 = lgr.verbose2
v3 = lgr.verbose3
v4 = lgr.verbose4


def get_infile_type(infile):
    """Returns 'Table' or 'Image' depending on what Crates thinks
    the type of infile is."""
    cr = pycrates.read_file(infile)
    return pycrates.get_crate_type(cr)


def get_filter(infile):
    """returns the DM filter used with an input file or stack"""
    if type(infile) == str:
        return infile[infile.find("["):infile.rfind("]") + 1]

    elif type(infile) == list:
        filter = [infile[k][infile[k].find("["):infile[k].rfind("]") + 1]
                  for k in range(len(infile))]
        if filter == "":
            # DJB: should this be 'return ""' ?
            pass
        else:
            return filter

    else:
        raise ValueError("*internal error* expected string or array, sent {} / {}".format(type(infile), infile))


def get_file(infile):
    """returns the input file without DM filter"""
    if type(infile) == str:
        if infile.find("[") != -1:
            infiles = infile[0:infile.find("[")]
        else:
            infiles = infile

    elif type(infile) == list:
        infiles = []
        for i in range(len(infile)):
            if infile[i].find("[") != -1:
                infiles.append(infile[i][0:infile[i].find("[")])
            else:
                infiles.append(infile[i])

    else:
        raise ValueError("*internal error* expected string or array, sent {} / {}".format(type(infile), infile))

    return infiles


def get_file_filter(infile):
    """Returns the input file without DM filter and then the DM filter.

    infile can be a string or an array.
    """

    # Not efficient but this is not a time-critical part of the code
    return (get_file(infile), get_filter(infile))


def get_ccds(infile):
    """Returns an array of the unique CCD_ID values
    in the ACIS event file. The behavior is undefined if
    the file has no CCD_ID column (at present it will
    raise an error but this may change)."""

    return get_column_unique(infile, "ccd_id")


def get_chips(infile):
    """Returns an array of the unique CCD_ID values
    in the HRC event file. The behavior is undefined if
    the file has no CCD_ID column (at present it will
    raise an error but this may change)."""

    return get_column_unique(infile, "chip_id")


def get_obsid_object(infile):
    """Return a ciao_contrib._tools.utils.ObsId object using the OBS_ID
    and (optional) CYCLE and OBI_NUM keywords in the header. Note that
    the cycle keyword will always be set even if this is not an
    interleaved observation for ACIS data.

    As of CIAO 4.7, blank CYCLE keywords, as found in aspect-solution
    files, is treated as cycle=None. Care should be used in
    using the return object in such a case (there's no indication
    of it from the return value).

    """

    cr = pycrates.read_file(infile)
    obsid = cr.get_key_value("OBS_ID")

    if obsid is None:
        raise IOError("OBS_ID keyword is missing from '{}'.".format(infile))

    # Do not need to validate the value here, but it results in a
    # better error message than if ObsId fails.
    #
    cycle = cr.get_key_value("CYCLE")
    if cycle is not None and cycle.strip() == '':
        cycle = None
        v3("Changing blank CYCLE keyword from {} to None.".format(infile))

    elif cycle not in [None, 'P', 'S']:
        raise IOError("Invalid CYCLE={} keyword in '{}'.".format(cycle, infile))

    obi = cr.get_key_value("OBI_NUM")
    return utils.ObsId(obsid, cycle=cycle, obi=obi)


def get_obsid(infile):
    """Return the value of the OBS_ID keyword in the file. An IOError
    is raised if the keyword does not exist in the file.
    """

    cr = pycrates.read_file(infile)
    val = cr.get_key_value("OBS_ID")
    if val is None:
        raise IOError("OBS_ID keyword is missing from '{}'".format(infile))

    return val


def get_image_units(fname):
    """Returns the units of the image, which can be an
    empty string. A TypeError is raised if the input is not
    an image."""

    # We do not use dmImageOpen since that will promote a
    # table to an image (if possible) and we do not want that.
    #
    bl = cxcdm.dmBlockOpen(fname)
    try:
        if cxcdm.dmBlockGetType(bl) != cxcdm.dmIMAGE:
            raise IOError("The file {} is not an image.".format(fname))

        dd = cxcdm.dmImageGetDataDescriptor(bl)
        unit = cxcdm.dmGetUnit(dd)

    finally:
        cxcdm.dmBlockClose(bl)

    return unit


def _get_key_values(blockinfo):
    """Return a dictionary of key=keyname value=keyval
    given the block info dictionary returned by
    ciao_contrib.cxcdm_wrapper.get_block_info_from_file().

    Also adds in __NCOLS/__NROWS if a table and __SHAPE
    if an image.
    """

    kdict = blockinfo['records']
    keys = dict([(k, v.value) for (k, v) in kdict.items()])
    if blockinfo['type'] in ['TABLE', 'EMPTY-TABLE']:
        keys['__NCOLS'] = len(blockinfo['columns'])
        keys['__NROWS'] = blockinfo['nrows']
    elif blockinfo['type'] == 'IMAGE':
        keys['__SHAPE'] = blockinfo['shape']
    elif blockinfo['type'] == 'PRIMARY':
        keys['__SHAPE'] = None
    else:
        raise ValueError("Internal error: unrecognized block type {}".format(blockinfo['type']))

    return keys


def get_keys_from_file(fname):
    """Return a dictionary of keyword values for the
    'most-interesting-block' of the given file.

    The number of columns and rows are returned as the
    __NCOLS and __NROWS keywords if the block is a table,
    and if it is an image the shape is returned in the
    __SHAPE keyword.
    """

    (bname, bi) = cw.get_block_info_from_file(fname)
    return _get_key_values(bi)


def get_keys_cols_from_file(fname):
    """Return a dictionary of keyword values and
    a list of column info for the
    'most-interesting-block' of the given file.

    The number of columns and rows are returned as the
    __NCOLS and __NROWS keywords if the block is a table,
    and if it is an image the shape is returned in the
    __SHAPE keyword.

    The column info is None if the input is an image,
    otherwise it is a named tuple containing fields for
    - amongst others - column name, type, and size.
    """

    (bname, bi) = cw.get_block_info_from_file(fname)
    keys = _get_key_values(bi)

    if bi['type'] in ['TABLE', 'EMPTY-TABLE']:
        # get_block_info_from_file loses the ordering
        # of the columns, so need to reconstruct it
        colinfo = [None] * keys['__NCOLS']
        try:
            for cinfo in bi['columns'].values():
                colinfo[cinfo.pos - 1] = cinfo
        except IndexError as exc:
            raise IndexError(f"check if '{fname}' has duplicate column names!") from exc

    else:
        colinfo = None

    return (keys, colinfo)


# It is likely that this routine is inefficient, since it
# will cause the same information to be read in as used in
# earlier, or later, code, but for now go with the simplicity
# of this approach.
#
def validate_asol(infile):
    """Returns if infile appears to be an aspect solution file,
    otherwise raises an IOError.

    This check is done explicitly
    to avoid returning a less-than helpful message such as

    # skyfov (CIAO 4.5): dsFINDCOLUMNERR -- ERROR: Column 'RA' was not found in file ' '.

    although the current check is not guaranteed to be complete,
    just to catch common errors (e.g. using aspect histogram).

    Added in DS10.8.3 is a change from CONTENT=ASPSOL to
    CONTENT=ASPSOLOBI, so we check we have one of these
    two here (since we'll switch on this later so may as
    well error out if it is unexpected).
    """

    # Could check things like the block type, but for
    # not just try a simplistic check.
    #
    (keys, cols) = get_keys_cols_from_file(infile)
    try:
        content = keys['CONTENT']
    except KeyError:
        raise IOError("The file {} is missing the CONTENT keyword.".format(infile))

    if content not in ['ASPSOL', 'ASPSOLOBI', 'ASPSOL3']:
        raise IOError("Aspect solutions have CONTENT=ASPSOL or ASPSOLOBI, but found {} in\n{}".format(content, infile))

    req = ['time', 'ra', 'dec', 'roll']
    for col in cols:
        cname = col.name.lower()
        if cname in req:
            req.remove(cname)
            if req == []:
                return

    missing = ", ".join(req)
    if len(req) == 1:
        emsg = "Missing aspect column {} in {}".format(missing, infile)
    else:
        emsg = "Missing aspect columns {} in {}".format(missing, infile)

    raise IOError(emsg)


def get_aimpoint(infile):
    """Return the aim-point ccd_id/chip value by
    inspecting the contents of the first table block
    that starts with the name 'GTI'.

    Raises an IOError if unable to find a block that
    starts with GTI.
    """

    v3("Looking for aimpoint CCD in {}".format(infile))
    try:
        ds = cxcdm.dmDatasetOpen(infile)

    except IOError as ioe:
        msg = str(ioe)
        if msg.startswith("dmDatasetOpen() "):
            msg = msg[16:]

        raise IOError(msg)

    try:
        nblocks = cxcdm.dmDatasetGetNoBlocks(ds)
        v4("File has {} blocks".format(nblocks))
        for blnum in range(1, nblocks + 1):
            blname = cxcdm.dmDatasetGetBlockName(ds, blnum)
            v4("Block #{} = {}".format(blnum, blname))
            if blname.startswith("GTI") and \
               cxcdm.dmDatasetGetBlockType(ds, blnum) == cxcdm.dmTABLE:
                bl = cxcdm.dmDatasetGetBlock(ds, blnum)
                try:
                    nkeys = cxcdm.dmBlockGetNoKeys(bl)
                    for keynum in range(1, nkeys + 1):
                        dd = cxcdm.dmBlockGetKey(bl, keynum)
                        # TODO: is it CHIP for HRC data? Does it matter?
                        if cxcdm.dmGetName(dd) == 'CCD_ID':
                            aimpoint = cxcdm.dmGetData(dd)
                            v4("Found aimpoint CCD = {}".format(aimpoint))
                            return aimpoint

                finally:
                    cxcdm.dmBlockClose(bl)

                raise IOError("No CCD_ID keyword found in {} block of {}".format(blname, infile))

        raise IOError("No block starting with GTI found in {}".format(infile))

    finally:
        cxcdm.dmDatasetClose(ds)


def get_column_unique(infile, colname):
    """Return a NumPy array listing the unique values
    in the given column.

    If the file is empty the routine returns None.
    """

    cr = pycrates.read_file("{}[cols {}]".format(infile, colname))
    try:
        if cr.get_nrows() == 0:
            return None

        vals = pycrates.get_colvals(cr, colname).copy()

    except AttributeError:
        raise IOError("Unable to find column {0} in {1} - is it an image?".format(colname, infile))

    return np.unique(vals)


# TODO: drop support for clobber="yes"/"no"
def outfile_clobber_checks(clobber, fname):
    """If clobber is False or "no" then errors out if fname exists,
    otherwise if it does exist then error out if the user does not
    have write permission."""

    hdr = "File " + fname
    if clobber in [False, "no"]:
        if os.path.isfile(fname):
            raise IOError(hdr + " exists and clobber=no.")
        else:
            v3(hdr + " does not exist.")
    else:
        if os.path.isfile(fname):
            if os.access(fname, os.W_OK):
                v3(hdr + " has write permission.")
            else:
                raise IOError(hdr + " does not have write permission and clobber=yes.")
        else:
            v3(hdr + " does not exist.")


def rename_file_extension(fname, extension):
    """Replace the last extension of the file name by extension.

    If fname ends with .gz then this is removed before the replacement.
    """

    if fname.endswith(".gz"):
        fname = fname[:-3]

    return os.path.splitext(fname)[0] + extension


def remove_path(fname):
    "use: 'outfile=' + remove_path(infile) "
    return os.path.split(fname)[1]


def check_valid_file(fname):
    """Returns True if the file exists (according to the CIAO
    DataModel, so can contain virtual-file syntax), otherwise False.

    This is not bullet proof and should really not be used.
    """

    try:
        ds = cxcdm.dmDatasetOpen(fname, update=False)
        cxcdm.dmDatasetClose(ds)
        return True

    except IOError:
        return False


def validate_outdir(outdir):
    """If outdir does not exist, create it, otherwise check that the user
    has write permission.
    """

    if outdir == "":
        return

    if os.path.isdir(outdir):
        if os.access(outdir, os.W_OK):
            v3(outdir + " has write permission.")
        else:
            raise IOError(outdir + " does not have write permission.")
    else:
        try:
            os.mkdir(outdir)
        except Exception:
            raise IOError("Unable to create directory {}".format(outdir))


def get_subspace(infile, binsize):
    """Obtain the sky range of a region filtered image, using the file
    subspace.

    This may also be used with unfiltered images too"""

    lo = {"x": None, "y": None}
    hi = {"x": None, "y": None}

    v4("get_subspace: infile={} binsize={}".format(infile, binsize))
    bl = cxcdm.dmBlockOpen(infile)
    try:
        num_compt = cxcdm.dmBlockGetNoSubspaceCpts(bl)
        v4("get_subspace: found {} sub-space components".format(num_compt))

        if num_compt == 0:
            v1("No subspace components found for " + infile)
        else:
            # get the union of all the sky x- and y-ranges from the subspace
            for i in range(1, num_compt + 1):
                v4("get_subspace: moving to subspace block #{}".format(i))
                cxcdm.dmBlockSetSubspaceCpt(bl, i)

                for colname in ["x", "y"]:
                    try:
                        col = cxcdm.dmSubspaceColOpen(bl, colname)
                        (subspace_lo, subspace_hi) = cxcdm.dmSubspaceColGet(col)
                        v4("get_subspace: col={} subspace lo={} hi={}".format(colname, subspace_lo, subspace_hi))
                        for (lo_sub, hi_sub) in zip(subspace_lo, subspace_hi):
                            if lo[colname] is None:
                                lo[colname] = lo_sub
                            else:
                                lo[colname] = min(lo[colname], lo_sub)

                            if hi[colname] is None:
                                hi[colname] = hi_sub
                            else:
                                hi[colname] = max(hi[colname], hi_sub)

                    except RuntimeError:
                        v4("get_subspace: skipping block as no x/y subspace columns")
                        # if zero subspace components, exit quietly, since
                        # cxcdm throws a RuntimeError
                        pass

    finally:
        cxcdm.dmBlockClose(bl)

    return (AxisRange(lo["x"], hi["x"], binsize),
            AxisRange(lo["y"], hi["y"], binsize))


def fov_limits(fov_file, binsize):
    """Obtain the sky range covered by a FOV file"""

    return FOVRegion(fov_file, pixsize=binsize).range


def get_sky_range(infile, fov_file, binsize):
    """Intersect the range of the input file and FOV.

    Returns AxisRange objects for both axes as a tuple.
    A None value is returned if there is no intersection
    for an axis (which is unexpected).
    """

    (sky_x, sky_y) = get_subspace(infile, binsize)
    (fov_x, fov_y) = fov_limits(fov_file, binsize)

    return (sky_x.intersect(fov_x),
            sky_y.intersect(fov_y))


def find_output_grid(evtfile, asolfile, maskfile,
                     binval, chips,
                     tmpdir="/tmp"):
    """Given the events file, aspect solution(s), and mask file,
    return the AxisRange objects for each axis which cover the data.

    The aspect solution files (asolfile is an array of strings) are
    filtered by the GTI of the event file.

    The binval parameter is the binning value to be used (in sky
    pixels) and chips is an array of chip values to use.

    A ValueError is raised if there is no intersection between
    the evtfile and asolfile (this should only happen if the
    evtfile has had an off-chip filter applied to it, so is
    empty).

    The skyfov method depends on the type of the aspect solution,
    as given by the CONTENT type:

        ASPSOL (pre DS 10.8.3)  - use method=minmax
        ASPSOLOBI               - use method=convexhull

    If possible, use find_output_grid2 instead (which just wraps
    up this routine in a bit-more logic).
    """

    v3("Calculating sky grid of {}".format(evtfile))

    # In CIAO 4.6 there is a problem with the data model in the case where
    # a filter has been applied to the event file and there are multiple
    # components in the filter; in this case the DM falls over when applying
    # it as a GTI filter to the aspect solution: that is
    #
    #     asol.fits[@evt.fits[ccd_id=7,energy=500:7000]]
    #
    # fails, but either of
    #
    #     asol.fits[@evt.fits[ccd_id=7]]
    #     asol.fits[@evt.fits[energy=500:7000]]
    #
    # are fine. The work around is to explicitly copy the event file
    # and use the copied version, but only when we think there are
    # multiple filters applied to it. This check is not robust, but
    # is hopefully robust enough.
    #
    # The following also fail
    #
    #    asol.fits[@evt.fits[sky=region(..)||sky=region(..)]
    #
    lpos = evtfile.find("[")
    if lpos == -1 or \
       (evtfile.find(",", lpos) == -1 and evtfile.find("||", lpos) == -1):
        gtifilter = "[@{}]".format(evtfile)

    else:
        v2("Copying event file {} before using it as a GTI filter for an aspect file".format(evtfile))
        evtcopy = tempfile.NamedTemporaryFile(dir=tmpdir,
                                              suffix='.evt')

        # Important to make a copy here since do not want option=all
        # to get set in the default dmcopy object.
        #
        dmcopy = runtool.make_tool('dmcopy')
        dmcopy.punlearn()
        dmcopy(evtfile, evtcopy.name, option="all", clobber=True)
        gtifilter = "[@{}]".format(evtcopy.name)

    # What SKYFOV method to use?
    #
    # I think with ASPSOLOBI (ie DS 10.8.3 or later) there should be only
    # one aspect-solution file here, but not going to enforce that.
    #
    def get_content(f):
        bl = cxcdm.dmBlockOpen(f, update=False)
        try:
            keys = cxcdm.dmKeyRead(bl, 'CONTENT')
            content = keys[1].decode('ascii')
            return content
        finally:
            cxcdm.dmBlockClose(bl)

    contents = set([get_content(f) for f in asolfile])
    if len(contents) != 1:
        emsg = "Multiple types of aspect solution found: " + \
               "{}\n{}".format(", ".join(contents),
                               " ".join(asolfile))
        raise IOError(emsg)

    content = contents.pop()
    if content == 'ASPSOLOBI':
        method = 'convexhull'
    elif content in ['ASPSOL', 'ASPSOL3']:
        method = 'minmax'
    else:
        raise IOError("Invalid CONTENT={} in aspect solution\n{}".format(content,
                                                                         " ".join(asolfile)))

    v3("Aspect solutions: CONTENT={}  skyfov method={}".format(content, method))

    fasol = [f + gtifilter for f in asolfile]

    skyfov = runtool.make_tool('skyfov')
    fov = tempfile.NamedTemporaryFile(dir=tmpdir, suffix=".fov")
    try:
        skyfov.punlearn()
        skyfov(infile=evtfile,
               outfile=fov.name,
               aspect=fasol,
               mskfile=maskfile,
               kernel="FITS",
               method=method,
               clobber=True)

        cstr = ",".join([str(c) for c in chips])
        fov_chip_filter = "[ccd_id={0}]".format(cstr)
        (xval, yval) = get_sky_range(evtfile,
                                     fov.name + fov_chip_filter,
                                     binval)

    finally:
        # I have seen a case where skyfov failed, but the error it would have
        # displayed is in fact lost since fov.close() raised an error because
        # the FOV file could not be deleted. It's not clear to me why this is,
        # since it seems like it should still exist, but catch this just in
        # case. It suggests I don't quite understand something fundamental
        # to the ordering of operations here.
        try:
            fov.close()
        except OSError:
            pass

    if xval is None or yval is None:
        raise ValueError("There is no spatial overlap between data ({}) and aspect solution ({}).".format(evtfile, asolfile))

    return (xval, yval)


def find_output_grid2(obsinfo, binval, chips,
                      tmpdir="/tmp"):
    """Given the observation info,
    return the AxisRange objects for each axis which cover the data.

    The binval parameter is the binning value to be used (in sky
    pixels) and chips is an array of chip values to use.

    A ValueError is raised if there is no intersection between
    the evtfile and asolfile (this should only happen if the
    evtfile has had an off-chip filter applied to it, so is
    empty).

    A warning is displayed if the MASKFILE can not be found,
    but it is not considered an error (this is a change in CIAO 4.7;
    in previous releases the code would exit with an error if no
    MASKFILE could be found).
    """

    # With the way that obsinfo code works, it is a bit awkward to find
    # out whether there's no MASKFILE keyword or just a missing file,
    # so catch the error from get_ancillary and display it as a
    # warning (this assumes that the file is missing; it is not really
    # intended for a case where there's other problems, but get_ancillary
    # shouldn't be error-ing out in those cases, since I can't think of
    # any at this time).
    #
    # Actually, after trying it, decided that the warning message wasn't
    # ideal (repeated too much), so gone for the simplified approach below.
    try:
        maskfile = obsinfo.get_ancillary('mask')
        if maskfile == 'NONE':
            maskfile = None

    except IOError:
        maskfile = None

    if maskfile is None:
        v1("WARNING: no mask file found for {}, region may be too large".format(obsinfo.get_evtfile()))

    # Note that get_asol returns a time-ordered list of file names
    return find_output_grid(obsinfo.get_evtfile(),
                            obsinfo.get_asol(),
                            maskfile,
                            binval, chips, tmpdir=tmpdir)


def get_file_from_header(dirname, hdr, keyword, label, warnlabel=None):
    """Return the full path to the file pointed to by
    keyword in hdr. label is used to indicate to the user
    what value was found.

    dirname is the base directory for the file name (if not
    absolute).

    If warnlabel is None then a missing keyword or filename is treated
    as an error (IOError is raised).

    If warnlabel is set then this is appended to boilerplate warnings
    (it can be ""), and "" is returned
    """

    try:
        fname = hdr[keyword]

    except KeyError:
        txt = "{} keyword not found in infile.".format(keyword)

        if warnlabel is not None:
            wmsg = "WARNING - " + txt
            if warnlabel != "":
                wmsg += " " + warnlabel
            v1(wmsg)
            return ""

        else:
            raise IOError(txt)

    # Treat a value of NONE as missing/not set.
    fullpaths = ancillary.find_files(fname, absolute=False, cwd=dirname,
                                     keepnone=False)
    if fullpaths is not None:
        if len(fullpaths) > 1:
            raise IOError("Found multiple files for {}: {}".format(keyword,
                                                                   fname))

        # We no longer check that the file can be read by the DataModel.
        fullpath = fullpaths[0]
        v1("{} file {} found.".format(label, fullpath))
        return fullpath

    elif warnlabel is not None:
        wmsg = "WARNING - {}={} not found".format(keyword, fname)
        if dirname != "":
            wmsg += " in " + dirname
            if not dirname.endswith('/'):
                wmsg += '/'

        if warnlabel != "":
            wmsg += ". " + warnlabel
        v1(wmsg)
        return ""

    emsg = "{}={} not found".format(keyword, fname)
    if dirname != "":
        emsg += " in " + dirname
        if not dirname.endswith('/'):
            emsg += '/'

    raise IOError(emsg)


def get_minmax_times(filename):
    "Return a tuple of min/max times from filename."

    # use cxcdm rather than crates so can access first/last rows without
    # having to load in all the data.
    bl = cxcdm.dmTableOpen(filename + "[cols time]")
    try:
        nrows = cxcdm.dmTableGetNoRows(bl)
        col = cxcdm.dmTableOpenColumn(bl, "time")
        t1 = cxcdm.dmGetData(col)
        check = cxcdm.dmTableSetRow(bl, nrows)
        if check != nrows:
            raise IOError("Unable to move to the end of the file: {}".format(filename))
        t2 = cxcdm.dmGetData(col)

    finally:
        cxcdm.dmTableClose(bl)

    return (t1, t2)


def _get_aimpoint_from_transform2d(transform):
    """Given a coordinate transform descriptor, return the
    reference position in the converted coordinate system.
    """

    transform_info = cxcdm.dmCoordGetTransform(transform)
    v3("Transform info =\n{}".format(transform_info))
    return (transform_info[1][0], transform_info[1][1])


def _get_tangent_point_image(fname, bl):
    """Return (ra,dec) in decimal degrees."""

    dd = cxcdm.dmImageGetDataDescriptor(bl)
    dims = cxcdm.dmGetArrayDimensions(dd)
    ndims = len(dims)
    if ndims != 2:
        raise IOError("Image {} is {}D; expected 2D.".format(fname, ndims))

    ngroups = cxcdm.dmArrayGetNoAxisGroups(dd)
    if ngroups == 0:
        raise IOError("No axis information found in {}".format(fname))
    elif ngroups > 1:
        raise IOError("Multiple axis groups found in {}".format(fname))

    ad = cxcdm.dmArrayGetAxisGroup(dd, 1)
    # ncoords = cxcdm.dmDescriptorGetNoCoords(ad)
    if ad == 0:
        raise IOError("No axis transform found in {}".format(fname))
    elif ad > 1:
        v1("WARNING: multiple axis transforms found in {}, using the first.".foramt(fname))

    transform = cxcdm.dmDescriptorGetCoord(ad)
    transform_type = cxcdm.dmCoordGetTransformType(transform)
    if transform_type[0] != 'TAN':
        raise IOError("At present can only handle tangent-plane projections; found {} in {}".format(transform_type[0], fname))

    return _get_aimpoint_from_transform2d(transform)


def _get_tangent_point_table(fname, bl):
    """Return (ra,dec) in decimal degrees."""

    cols = cxcdm.dmTableOpenColumnList(bl)
    wcscols = []
    for col in cols:
        v3("Looking for WCS transform in column {}".format(cxcdm.dmGetName(col)))
        try:
            transform = cxcdm.dmDescriptorGetCoord(col)
            v4(" - got transform")
            transform_type = cxcdm.dmCoordGetTransformType(transform)
            v4(" - transform type = {}".format(transform_type))
        except RuntimeError:
            continue

        if transform_type[0] == 'TAN':
            v3(" -> found one")
            wcscols.append(transform)

    nwcs = len(wcscols)
    if nwcs == 0:
        raise IOError("No WCS transform found in {}".format(fname))
    elif nwcs > 1:
        raise IOError("Multiple ({}) WCS transforms found in {}".format(nwcs, fname))

    return _get_aimpoint_from_transform2d(wcscols[0])


def get_tangent_point(filename):
    """Return the 'tangent point' for a file or raises an IOError.

    Given an image, return the ra/dec used in the WCS transform.
    For tables look for the column with a WCS transform.

    This is not a general-purpose routine, since it makes
    a number of assumptions.
    """

    bl = cxcdm.dmBlockOpen(filename)
    try:
        btype = cxcdm.dmBlockGetType(bl)
        if btype == cxcdm.dmIMAGE:
            (ra0, dec0) = _get_tangent_point_image(filename, bl)
        elif btype == cxcdm.dmTABLE:
            (ra0, dec0) = _get_tangent_point_table(filename, bl)
        else:
            raise IOError("Unable to find tangent point for block " +
                          "{} of {}".format(cxcdm.dmBlockGetName(bl),
                                            filename))

    finally:
        cxcdm.dmBlockClose(bl)

    v3("Tangent point in {}: {} {}".format(filename, ra0, dec0))
    return (ra0, dec0)


def expand_evtfiles_stack(instack, pattern="*evt*"):
    """Expand the instack input into an array of event files.
    For each element in the stack check if it is a file or directory,
    ignoring it if it is neither.

    If it is a file we use a DataModel open to see if we can find
    the file (so that Data Model filters are checked/handled properly).

    If it is a directory then look for the first match to
        <dirname>/repro/<pattern>
        <dirname>/primary/<pattern>
        <dirname>/<pattern>

    and add them (can have multiple matches). If the directory
    contains no matches then ignore it.

    Returns an array of file names, which can be empty.

    Note that the routine does not check that each file is an event
    file, it just checks that it is a file.
    """

    v3("Expanding out the event file stack: {}".format(instack))
    out = []
    for elem in stk.build(instack):
        v3("  - verifying element {}".format(elem))

        if os.path.isdir(elem):
            v3("    a directory")
            match = []
            for dname in ["repro", "primary", ""]:
                dpath = os.path.join(elem, dname, pattern)
                match = glob.glob(dpath)
                if match != []:
                    break

            if match != []:
                v3("    -> {}".format(match))
                for mname in match:
                    v1("Found {}".format(mname))

                out.extend(match)
            else:
                v1("Skipping directory {} as no event files found in it.".format(elem))

        else:
            # Try and cover common error cases - such as input is an
            # image instead of a table - but it's hard to tell between
            # a missing file or an incorrect DM filter without parsing
            # the error messages from the DataModel, which is fragile.
            #
            try:
                bl = cxcdm.dmTableOpen(elem)
                v3("    a table")
                cxcdm.dmTableClose(bl)
                out.append(elem)

            except IOError as ie:
                v3("Error message from table open: {}".format(ie))

                try:
                    bl = cxcdm.dmImageOpen(elem)
                    cxcdm.dmImageClose(bl)
                    v3("Oops, {} is an image".format(elem))
                    v1("Skipping {} as it is an image.".format(elem))

                except IOError:
                    # The input file might not exist, but it also
                    # could be an invalid virtual-file expression,
                    # such as
                    #      "evt2.fits[bob=10:20]"
                    #      "evt2.fits[cols sky,bob]"
                    #  when bob does exist.
                    #
                    v1("Skipping {} as it can not be opened.".format(elem))

    v3("  -> stack={}".format(out))
    return out


# Do we need to use MJD; can we not just use TSTART?
#
def sort_mjd(filenames):
    """Return filenames, sorted by MJD_OBS or MJD-OBS, as a list

    The keyword used to be MJD_OBS but was changed to MJD-OBS
    circa CIAO 4.12.
    """

    if len(filenames) < 2:
        return list(filenames)

    vals = []

    # This used to use dmkeypar to get the keyword, but with the
    # need to support multiple keywords it was changed to
    # access the keywords directly in CIAO 4.12.
    #
    for filename in filenames:
        v3("Looking for MJD-OBS keyword in {}".format(filename))

        hdr = get_keys_from_file(filename)
        try:
            mjdobs = hdr['MJD-OBS']
        except KeyError:
            v3("Not found, looking for MJD_OBS")
            try:
                mjdobs = hdr['MJD_OBS']
            except KeyError:
                v3("Also not found, so calculating MJD_OBS value.")

                # MJD(TT) = MJDREF(TT) + ( TIMEZERO + TIME ) / 86400
                try:
                    time_obs = hdr["TSTART"]
                    mjdref = hdr["MJDREF"]
                    timezero = hdr["TIMEZERO"]
                except KeyError as ke:
                    raise IOError("Unable to find keyword " +
                                  "{} in {}".format(ke, filename))

                v4("TSTART/MJDREF/TIMEZERO = " +
                   "{} / {} / {}".format(time_obs, mjdref, timezero))

                mjdobs = mjdref + (timezero + time_obs) / 86400.0

        v3(" MJD-OBS={} ({})".format(mjdobs, type(mjdobs)))
        vals.append((mjdobs, filename))

    # sort on MJD-OBS (first term) and extract the filename (second term)
    vals.sort()
    return [v[1] for v in vals]

# End
