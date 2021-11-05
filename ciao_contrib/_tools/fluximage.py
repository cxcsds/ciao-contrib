#
# Copyright (C) 2010-2012, 2013, 2014, 2015, 2016, 2018, 2019, 2021
# Smithsonian Astrophysical Observatory
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.
#

"""
Routines to support the fluximage tool.

We now display the "starting ..." message for each task when
evaluating the first chip/band/image/... rather than the previous
behaviour of using a barrier to write the message and then have the
actual tasks depend on the barrier. This is to avoid the case of
having all the "starting" messages be displayed (i.e. for all the
obsids) before the actual processing starts.

The new approach means that the user gets a better idea of when the
various tasks are being run, but it's not technically correct since
there's no guarantee that the "first" task we create for a particular
section is going to get run first. For now I think it is worth it.
"""

# TODO:
#
#   Should the tmpdir arguments default to None rather than /tmp?  in
#   general they are being passed to routines that (for now at least,
#   Aug 2014) are being converted to using ASCDS_WORK_PATH environment
#   variable if tmpdir is None. So, leaving them here to default to
#   /tmp runs the risk of overriding this choice, for those codes that
#   have not sent in the actual tmpdir argument (which we assume that
#   we have also set the ASCDS_WORK_PATH environment to).
#

import os
import tempfile
import shutil
import subprocess as sbp

import numpy as np

import paramio
import pycrates as pcr

import ciao_contrib.logger_wrapper as lw

from ciao_contrib.runtool import new_pfiles_environment
from ciao_contrib.runtool import add_tool_history

import ciao_contrib._tools.fileio as fileio
from ciao_contrib._tools.obsinfo import ObsInfo
import ciao_contrib._tools.utils as utils

import ciao_contrib._tools.run as run
from ciao_contrib._tools.run import \
    punlearn, dmcopy, dmimgcalc, dmimgcalc2, dmimgcalc_add, \
    dmhedit_key, dmhedit_file

# for now, export nothing
__all__ = ()

# Name of the background events file for HRC-I data.
# TODO: this should be changed; eg include ObsId?
HRCI_BG_EVTS = "HRC-I_bkg.fits"

lgr = lw.initialize_module_logger('_tools.fluximage')
v1 = lgr.verbose1
v2 = lgr.verbose2
v3 = lgr.verbose3
v4 = lgr.verbose4


def add_defargs(args, clobber, verbose):
    "Add clobber/verbse arguments to args list (modified *in place*)."

    if clobber:
        clstr = "yes"
    else:
        clstr = "no"

    args.append(f"clobber={clstr}")
    args.append(f"verbose={verbose}")


def add_band_keywords(infile, enband, tmpdir="/tmp"):
    """For ACIS data, add the ENERGYLO/ENERGHI keywords to infile.
    For HRC data, adds PILO/PIHI if either are set.
    """

    if enband.loval is None and enband.hival is None:
        return

    tfile = tempfile.NamedTemporaryFile(dir=tmpdir, mode='w+',
                                        suffix=".band.keys")
    try:
        tfile.write("#add\n")
        tfile.write(f"COMMENT =Adding keywords for band={enband.bandlabel}\n")
        if enband.colname == "energy":
            # For ACIS data we require that both loval and hival are included
            tfile.write(f"ENERGYLO = {enband.loval} / [keV] Min photon energy in the image\n")
            tfile.write(f"ENERGYHI = {enband.hival} / [keV] Max photon energy in the image\n")

        else:
            colname = enband.colname.upper()
            if enband.loval is not None:
                tfile.write(f"{colname}LO = {enband.loval} / [{enband.units}] Min value in the image\n")
            if enband.hival is not None:
                tfile.write(f"{colname}HI = {enband.hival} / [{enband.units}] Max value in the image\n")

        tfile.flush()

        dmhedit_file(infile, tfile.name, verbose=0)
    finally:
        tfile.close()


def add_dmh_keyword(fh, keyval):
    """Add a line to the file handle fh - assumed to be the
    input to dmhedit - to add the give keyword, where
    keyval = (name, value, unit, desc) where unit and desc
    are ignored if set to ''.

    This attempts to handle different datatypes for value.
    """

    (name, value, unit, desc) = keyval

    # need to be careful with string values
    fh.write(f"{name} = ")
    if isinstance(value, str):
        if "/" in value:
            fh.write(f"'{value}'")
        else:
            fh.write(f"\"'{value}'\"")
    else:
        fh.write(f"{value}")

    if unit != "" or desc != "":
        fh.write(" /")
        if unit != "":
            fh.write(f" [{unit}]")

        if desc != "":
            fh.write(" " + desc)

    fh.write("\n")


def copy_keywords(infile, outfile, keynames, tmpdir="/tmp"):
    """Copy the values of keynames from infile to outfile.

    If the keyword does not exist it is skipped.
    """

    if keynames == []:
        return

    vals = []
    cr = pcr.read_file(infile)
    for keyname in keynames:
        key = cr.get_key(keyname)
        if key is None:
            continue

        vals.append((keyname, key.value, key.unit, key.desc))

    cr = None

    if vals == []:
        return

    tfile = tempfile.NamedTemporaryFile(dir=tmpdir, mode='w+',
                                        suffix=".copy.keys")
    try:
        tfile.write("#add\n")
        tfile.write("COMMENT = Copying over keywords from " + infile)
        tfile.write("\n")

        for val in vals:
            add_dmh_keyword(tfile, val)

        tfile.flush()
        dmhedit_file(outfile, tfile.name, verbose=0)
    finally:
        tfile.close()


def cleanup_files_task(filenames, msg=None):
    """Delete the files in the filenames array
    and, if msg is not None, display the message
    at verbose=2 level (after pre-pending the text
    'Cleaning up ')."""

    if msg is not None:
        v2(f"Cleaning up {msg}")

    v3(f"Deleting files: {filenames}")
    for filename in filenames:
        os.unlink(filename)


def get_unique_vals(infile, colname, xrange=None, yrange=None):
    """Returns an array of the unique values for a column
    in the input file. An error is thrown if the column
    does not exist. If the column is empty then None is returned.

    If xrange is given then it is used as a filter on the
    x values in the file; [x={}:{}] is added to infile
    where xrange is assumed to be a pair of values.

    Similar for yrange, with the y column.

    """

    fname = infile
    if xrange is not None:
        fname += "[x={}:{}]".format(*xrange)
    if yrange is not None:
        fname += "[y={}:{}]".format(*yrange)

    return fileio.get_column_unique(fname, colname)


# Perhaps this should be included in the final output text
# rather than during processing?
#
def warn_unfilled_pixels(xr, yr, nr, binsize):
    """Warn if the grid size leads to 'partially-filled' last bin.

    Displays a warning message at verbose=1 if either (or both) axes
    result in a partially-filled bin.

    Parameters
    ----------
    xr : float, float
        Pair of numbers defining the low and high values of the X axis
    yr : float, float
        Pair of numbers defining the low and high values of the Y axis
    nr : int, int
        Pair of numbers defining the number of bins for the X and Y axes.
    binsize : float
        The bin size

    """

    xlo, xhi = xr
    ylo, yhi = yr
    nx, ny = nr

    axes = 0
    if (xhi - xlo) % binsize != 0:
        axes |= 1
    if (yhi - ylo) % binsize != 0:
        axes |= 2

    if axes == 0:
        return

    if axes == 3:
        wstr = "row and column"
    elif axes == 2:
        wstr = "row"
    else:
        wstr = "column"

    v1(f"Fluxed image will underestimate the last {wstr} since the exposure")
    v1("map is overestimated there. This is because the requested width and height")
    v1("is not a whole number of pixels.")


#################################################################
#
# File names
#
#################################################################

# In all these the head argument represents
# the location of the file (can be a directory or
# directory + string); it is expected to tbe outpath
# variable in the params dictionary.
#
def name_asphist(head, num, blockname=False):
    """The name of the aspect histogram for chip/ccdid num.

    If blockname is True then [asphist] is appended.
    """

    o = f"{head}{num}.asphist"
    if blockname:
        o += "[asphist]"

    return o


def name_fov(head, obs):
    """The name of the FOV file.

    Unlike the other obsids we use the obsid label. This is okay for
    fluximage but becomes problematic for merge_obs, when the head
    label already includes the obsid label. For now we hack around
    this, but this needs to be re-worked.

    """

    if not isinstance(obs, ObsInfo):
        raise ValueError(f'Internal error: sending {type(obs)} and not an ObsInfo!')

    v4(f"name_fov: head={head} obs.obsid={obs.obsid}")

    # Remember, obs.obsid includes any OBI number if needed.
    #
    label = str(obs.obsid)
    if head.endswith(f'{label}_'):
        v3(f"WARNING: name_fov sent head={head} - need to fix")
        return head[:-1] + '.fov'

    return f"{head}{label}.fov"


def base_name(head, enband, num=None):
    """The base of most of the names."""

    if enband is None:
        raise ValueError("Internal error - base_name called with enband=None")

    out = f"{head}"
    if num is not None:
        out += f"{num}_"

    out += f"{enband.bandlabel}"
    return out


def name_instmap(head, num, enband):
    """The name of the instrument map for chip/ccdid num
    when evaluated with the given energy band.
    """

    return f"{base_name(head, enband, num=num)}.instmap"


def name_expmap(head, enband, num=None):
    """The name of the exposure map when evaluated for the
    given energy band.

    If num is not None then this is the chip/ccd number, otherwise
    the exposure map is for all chips/ccds.
    """

    return f"{base_name(head, enband, num=num)}.expmap"


def name_expmap_thresh(head, enband):
    """The thresholded exposure map. Unlike name_expmap this is
    only for the per-observation exposure map (ie no support for the
    num argument).
    """

    return f"{base_name(head, enband)}_thresh.expmap"


def name_psfmap(head, enband, thresh=False):
    """The name of the PSF map when evaluated for the
    given energy band.
    """

    mid = "_thresh" if thresh else ""
    return f"{base_name(head, enband)}{mid}.psfmap"


def name_image(head, enband):
    """The binned image for the given energy band.

    See also name_image_thresh() and name_fluxed().
    """

    return f"{base_name(head, enband)}.img"


def name_image_thresh(head, enband):
    """The thresholded image for the given energy band.
    """

    return f"{base_name(head, enband)}_thresh.img"


def name_fluxed(head, enband):
    """The fluxed (normalized by exposure map) image for the given
    energy band.
    """

    return f"{base_name(head, enband)}_flux.img"


def name_hrci_particle_background(head, enband):
    """Return the name of the unscaled background image
    for the given image.
    """

    return f"{base_name(head, enband)}_particle_bgnd.img"


def name_hrci_unsubtracted_background(head, enband):
    """Return the name of the image file that contains
    the full image data - i.e. before background subtraction).
    """

    return f"{base_name(head, enband)}_unsubtracted.img"


# TODO: this is used by flux/merge_obs; should they use get_output_filenames()
#       instead (since fluximage uses that).
#
def fluximage_output(outdir, outhead, obsinfos, enbands,
                     psf=False,
                     threshold=False):
    """Return a dictionary listing all the output files that
    fluximage creates for the given inputs.

    Note that although PSF maps use the "_thresh" nomenclature,
    since they are calculated using a thresholded exposure map
    if thresholding is applied, there is no need to both
    pstmap and psfmap_thresh fields, since only one file is created.
    """

    # TODO: SHOULD THIS BE SENT IN THE CLEANUP STATUS?

    def start():
        return dict([(enband.bandlabel, []) for enband in enbands])

    # keys are energy band (as a string) and values are the list
    # of files in obsid order.
    #
    out = {
        'images': start(),
        'expmaps': start(),
        'fluxmaps': start(),
    }

    if threshold:
        out['image_thresh'] = start()
        out['expmap_thresh'] = start()

    if psf:
        out['psfmaps'] = start()

    # FOV file info:
    #   fovs lists the individual names
    #   combinedfov lists the combined name
    #
    out['fovs'] = []
    out['combinedfov'] = f"{outdir}{outhead}merged.fov"

    # Going for simple over efficient.
    for enband in enbands:
        estr = enband.bandlabel

        for obs in obsinfos:
            obsid = obs.obsid
            head = f"{outdir}{outhead}{obsid}_"

            out['images'][estr].append(name_image(head, enband))
            out['expmaps'][estr].append(name_expmap(head, enband))
            out['fluxmaps'][estr].append(name_fluxed(head, enband))

            if threshold:
                out['image_thresh'][estr].append(name_image_thresh(head, enband))
                out['expmap_thresh'][estr].append(name_expmap_thresh(head, enband))
            if psf:
                out['psfmaps'][estr].append(name_psfmap(head, enband,
                                                        thresh=threshold))

            # FOV
            out['fovs'].append(name_fov(head, obs))

    return out


##########################################################################
##########################################################################
#
# Start constructing routines to create exposure-corrected images
#
##########################################################################
##########################################################################

"""

The following was an attempt to avoid warning messages from
asphist with HRC data - e.g.

asphist (CIAO 4.4): WARNING: skipping 40 livetime correction records (from time: 61963173.370213 to time: 61963253.320216)

but it does not seem to help too much.

        efile = "{}[{}={}]".format(evtfile, filt, chip)
        timefilter = ""

        # if dtf file is not empty then add in a time filter
        # that matches the event file to avoid warning messages
        # like
        # asphist (CIAO 4.4): WARNING: skipping 40 livetime correction records (from time: 61963173.370213 to time: 61963253.320216)
        #
        # NOTE: not sure if correct/worth it
        #
        if dtffile != "":
            # note that unlike merging.reproject_events_task, we
            # use the first/last times from the event file itself
            # rather than from the aspect solutions
            # --> well, that didn't seem to fix things, so
            #
            #(t1, t2) = fileio.get_minmax_times(efile)
            #dtffile += "[time={}:{}]".format(t1, t2)

            atimes = []
            for afile in stk.build(asolobj.name):
                v3("Finding time range of aspect file: {}".format(afile))
                (t1, t2) = fileio.get_minmax_times(afile)
                atimes.append("{}:{}".format(t1, t2))
                v3(" >> {}".format(atimes[-1]))

            if len(atimes) != 0:
                timefilter = "[time={}]".format(",".join(atimes))

"""


def run_asphist(outpath, asolobj, chip, evtfile, filt, dtffile,
                nbins, res_xy,
                message=None,
                verbose=0,
                tmpdir="/tmp",
                clobber=False):
    "Run asphist."

    if message is not None:
        v1(message)

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        # punlearn("asphist")

        args = ["infile=" + asolobj.name,
                "outfile=" + name_asphist(outpath, chip),
                f"evtfile={evtfile}[{filt}={chip}]",
                "dtffile=" + dtffile,
                f"max_bin={nbins}",
                f"res_xy={res_xy}",
                "mode=h"]
        add_defargs(args, clobber, verbose)
        run.run("asphist", args)


def make_asphist(taskrunner, labelconv,
                 obs,
                 asolobj, chips, pixscale,
                 outpath,
                 parallel=True,
                 tmpdir="/tmp",
                 verbose=0,
                 clobber=False):
    """Calculate aspect histograms for the given chip(s) in this observation.
    asolobj is an AspectSolution object; pixscale is the final pixel size in
    arcsec and is used to scale the res_xy argument in asphist.
    """

    if obs.instrument == 'HRC':
        dtffile = obs.get_ancillary_('dtf')
        if dtffile == 'NONE':
            dtffile = ""
    else:
        dtffile = ""

    filt = obs.get_chipname()

    res_xy = 0.5
    if pixscale > 1.0:
        res_xy = pixscale / 2.0
    nbins = asolobj.nbins(xy=res_xy)

    tasks = []
    for chip in chips:
        task = labelconv(f"asphist-chip{chip}")
        if chip == chips[0]:
            if len(chips) == 1:
                smsg = f"Creating aspect histogram for obsid {obs.obsid}"
            else:
                smsg = f"Creating {len(chips)} aspect histograms for obsid {obs.obsid}"
        else:
            smsg = None

        taskrunner.add_task(task, [],
                            run_asphist, outpath, asolobj, chip,
                            obs.get_evtfile(),
                            filt,
                            dtffile,
                            nbins, res_xy,
                            message=smsg,
                            tmpdir=tmpdir,
                            verbose=verbose,
                            clobber=clobber)
        tasks.append(task)

    etask = labelconv("asphist-end")
    taskrunner.add_barrier(etask, tasks)

    return etask


def make_fov(taskrunner, labelconv,
             obs,
             asolobj, chips,
             outpath,
             parallel=True,
             tmpdir="/tmp",
             verbose=0,
             clobber=False):
    """Create the FOV file

    Notes
    -----
    The tmpdir, verbose, and clobber arguments are unused.

    """

    # Do I need to bother with the chip filter here or can I just
    # use obs.get_evtfile()? I'm going to be careful just in case.
    #
    chipstr = ','.join([str(c) for c in chips])
    evtfile = f"{obs.get_evtfile()}[{obs.get_chipname()}={chipstr}]"

    task = labelconv("fov")
    taskrunner.add_task(task, [],
                        run.make_fov,
                        evtfile,
                        asolobj.name,
                        obs.get_ancillary('mask'),
                        name_fov(outpath, obs),
                        # tmpdir=tmpdir,
                        # verbose=verbose,
                        # clobber=clobber
                        )

    return task


def reproject_bgnd(blanksky_map, outfile, asolfile, matchfile,
                   random=0,
                   verbose="0",
                   clobber=False):
    """Reproject the background (blank-sky or particle background)
    events file.
    """

    punlearn("reproject_events")
    args = ["infile=" + blanksky_map,
            "outfile=" + outfile,
            "aspect=" + asolfile,
            "match=" + matchfile,
            f"random={random}"]
    add_defargs(args, clobber, verbose)
    run.run("reproject_events", args)


# Does this not exist somewhere already?
def _get_keywords(filename, keywords):
    """Return the value of each keyword in keywords
    (converted to the
    correct Python datatype), or raise an IOError if
    not found.

    Actually, returns (name, value, unit, description)
    with unit/description set to '' if not defined.

    Note that strings are returned as np.string_
    """

    cr = pcr.read_file(filename)
    out = []
    for keyword in keywords:
        rval = cr.get_key(keyword)
        if rval is None:
            raise IOError(f"Unable to find keyword {keyword} in {filename}")

        # do not return the CrateKey object so that we give a chance
        # for the Crate to be freed, in case the Key somehow retains
        # a reference to the parent crate.
        #
        out.append((rval.name, rval.value, rval.unit, rval.desc))

    return out


def _get_keyword(filename, keyword):
    """Return the value of keyword
    (converted to the correct Python datatype), or raise an IOError if
    not found.

    Note that strings are returned as np.string_

    Use _get_keywords for multiple keywords, which also
    returns (name, value, units, comments) instead of
    just the value.
    """

    return _get_keywords(filename, [keyword])[0][1]


# Does this not exist somewhere already?
def _get_nrows(filename):
    "Return the number of rows in filename."
    try:
        cr = pcr.read_file(filename)
    except IOError as ie:
        # In CIAO 4.6 the error messages from read_file may not
        # include the filename. This may have been fixed by CIAO 4.8
        # but leaving in for now
        raise IOError(f"Unable to open '{filename}'\n{ie}") from None

    try:
        return cr.get_nrows()
    except AttributeError:
        raise IOError(f"Unable to find the number of rows in {filename}; is it an image?") from None


def calc_exposure_ratio(file1, file2):
    """Return exposure (file1) / exposure (file2),
    using the header keywords, or errors out if
    either is missing the kewyord.
    """

    # The explicit coercion into a floating-point number
    # is unlikely to be needed here, but just in case
    e1 = _get_keyword(file1, 'EXPOSURE')
    e2 = _get_keyword(file2, 'EXPOSURE')
    v2(f"Exposure scaling: {file1}={e1} {file2}={e2}")

    return (e1, e2)


def calc_count_ratio(file1, file2, filterstr):
    """Return the nrows(file1 + filterstr) / nrows(file2 + filterstr)
    ie after applying the specified filter.
    """

    nr1 = _get_nrows(file1 + filterstr)
    nr2 = _get_nrows(file2 + filterstr)
    v2(f"Count scaling {filterstr}: {file1}={nr1} {file2}={nr2}")

    return (nr1, nr2)


def validate_bkgparams(method, params):
    """Returns the "validated" string, or raises a ValueError if params
    is not empty or surrounded by '[..]'. More validation could be
    done - e.g. by trying to parse the statement and checking it
    matches the DM spec - but this is tricky to get right, so for now
    leave as a basic check.

    This check is only performed for method=particle; other background
    methods do not use params so the value is return unchecked and
    unchanged.

    """

    v3(f"Validating bkgparams={params} for method={method}")
    if method != "particle":
        return params

    bkg = params.strip()
    if bkg == '' or (bkg.startswith('[') and bkg.endswith(']')):
        return bkg

    raise ValueError(f"Invalid bkgparams filter, expected empty string or [..] but sent {bkg}")


def scale_hrci_background(enband,
                          bkgmethod,
                          bkgparams,
                          events,
                          bkgevents,
                          bin_filter,
                          rawimg, bkgimg, img,
                          ltable,
                          bevtname="",
                          verbose="0",
                          tmpdir="/tmp"):
    """Scale and subtract off the HRC-I background
    image, bkgimg, from the original data (rawimg),
    to create img. It is expected that img already
    exists so will be clobbered.

    Keywords added to img are
       BEVTFILE  - the name of the HRC-I background file
                   (before filtering/cleanup), as given by the
                   bevtname argument
       BKGMETH   - the method name
       BKGSCALE  - the scale factor (for those methods
                   which use a scalar scaling factor)

       BKGFACT1  - the numerator in the scaling term
       BKGFACT2  - the denominator in the scaling term
       BKGPARAM  - the filter used for the particle-background scaling (if BKGMETH=particle)

    The ONTIME/LIVETIME/EXPOSURE keywords are copied
    across from rawimg to img.
    """

    # dmimgcalc can use header keywords in its expressions,
    # but allow different scaling methods here (and this lets
    # us add in the BKGSCALE keyword).
    #
    # It does mean that files may be opened multiple times to
    # access keywords/data.
    #
    if bkgmethod == "default":
        bkgmethod = "time"
        (bkgfact1, bkgfact2) = calc_exposure_ratio(events, bkgevents)
    elif bkgmethod == "time":
        (bkgfact1, bkgfact2) = calc_exposure_ratio(events, bkgevents)
    elif bkgmethod == "particle":
        (bkgfact1, bkgfact2) = calc_count_ratio(events, bkgevents, bkgparams)
    else:
        # should have been caught earlier
        raise ValueError(f"Internal error: bkgmethod={bkgmethod} is not supported by scale_hrci_background")

    bkgscale = bkgfact1 * 1.0 / bkgfact2

    v2(f"Background subtraction: method={bkgmethod} scale={bkgscale}")

    dmcopy(f"{bkgevents}[bin {bin_filter}]{enband.dmfilterstr}[opt type=i4]",
           bkgimg, clobber=True, verbose="0")

    # To avoid changing downstream code (which is expecting the file
    # img to contain background-subtracted data at the end of this
    # call), we copy the original image to a different file, so that
    # this can be retained when cleanup=False.
    #
    # option=all is not needed here since, with the conversion to an image
    # above, I have explicitly chosen not to bother with extra blocks
    # (it could be done, but for now leaving out)
    #
    dmcopy(img, rawimg, clobber=True, verbose="0")

    dmimgcalc([rawimg, bkgimg], img,
              f"img1-({bkgscale}*img2)",
              lookupTab=ltable,
              verbose=verbose, clobber=True,
              tmpdir=tmpdir)

    # Keywords to copy across to the output image
    okeys = _get_keywords(rawimg, ["ONTIME", "LIVETIME", "EXPOSURE"])

    tfile = tempfile.NamedTemporaryFile(dir=tmpdir, mode='w+',
                                        suffix=".hrci.keys")
    try:
        tfile.write("#add\n")

        for okey in okeys:
            add_dmh_keyword(tfile, okey)

        add_dmh_keyword(tfile,
                        ('BEVTFILE', bevtname, '', 'Background event file'))
        add_dmh_keyword(tfile,
                        ('BKGMETH', bkgmethod, '',
                         'Background subtraction method'))
        add_dmh_keyword(tfile,
                        ('BKGSCALE', bkgscale, '',
                         'Background scaling factor'))

        # ensure a floating-point value since large integers seem to cause
        # dmhedit to fail to write out the keyword (CIAO 4.6)
        add_dmh_keyword(tfile,
                        ('BKGFACT1', bkgfact1 * 1.0, '',
                         'Numerator of BKGSCALE'))
        add_dmh_keyword(tfile,
                        ('BKGFACT2', bkgfact2 * 1.0, '',
                         'Denominator of BKGSCALE'))

        if bkgmethod == 'particle':
            add_dmh_keyword(tfile,
                            ('BKGPARAM', bkgparams, '',
                             'Filter used for background scaling'))

        tfile.flush()
        dmhedit_file(img, tfile.name, verbose=0)

    finally:
        tfile.close()


def make_images_hrci(enbands,
                     imgs,
                     imgs_pcle,
                     imgs_unsub,
                     evtfile,
                     bkgmethod,
                     bkgparams,
                     bkgevents,
                     orig_bkgevts,
                     obsid,
                     bin_filter,
                     tmpdir,
                     ltable,
                     verbose="0"):
    """Subtract the HRC-I background (bkgevents) from the
    images (imgs array). The current support is such that
    imgs can only contain a single element, but leave in support
    for multiple files as the situation is in flux.

    orig_bkgevts is the original name of the background events
    file, so that it can be added to the image header using the
    BEVTFILE keyword.

    Temporary files created by this routine that can be cleaned up
    are:

      bkgevents
      imgs_pcle
      imgs_unsub

    """

    if len(imgs) == 1:
        lbl = ""
    else:
        lbl = "s"
    imsg = f"Subtracting HRC-I background{lbl} for obsid {obsid}"
    v1(imsg)
    v2(f"Background scaling: method={bkgmethod} params={bkgparams}")

    # The aim of the following is to improve the history - i.e. tracing what
    # happened from the dmhistory output - rather than speed/simplicity,
    # so dmcopy is used rather than a filesystem copy.
    #
    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):

        # At present the code is only called with
        # imgs being a list of length 1 so it does not matter how
        # the background file is created, but with the
        # possibility of multiple PI ranges being used this
        # could change (i.e. if the restriction on the number
        # of bands to 1 is relaxed).
        #
        for (enband, img, bkgimg, rawimg) in \
                zip(enbands, imgs, imgs_pcle, imgs_unsub):

            scale_hrci_background(enband,
                                  bkgmethod,
                                  bkgparams,
                                  evtfile,
                                  bkgevents, bin_filter,
                                  rawimg, bkgimg, img,
                                  ltable,
                                  bevtname=orig_bkgevts,
                                  verbose=verbose,
                                  tmpdir=tmpdir)


def create_event_image(infile, outfile,
                       tmpdir="/tmp",
                       verbose=0,
                       clobber=False):
    """This is basically

      dmcopy(infile, outfile)

    but it also removes the GTI block from the output file to
    (hopefully) make it easier to use the images downstream,
    in particular to get the correct EXPOSURE time in the
    exposure-corrected image.
    """

    v4(f"Binning up {infile} to {outfile}")
    tmpfile = tempfile.NamedTemporaryFile(dir=tmpdir, suffix='.img')

    # As we want to exclude the GTI blocks we do not want to
    # use option=all here (probably could still use it, but
    # have not tested it and this code works, so do not change it).
    dmcopy(infile, tmpfile.name, clobber=True, verbose=verbose)
    dmcopy(tmpfile.name + "[subspace - time]", outfile,
           clobber=clobber, verbose=verbose)


# TODO:
#   support providing a fov file to use
#
#   for HRC data, should be able to create energy-band independant
#   images (ie only one file rather than one per band).
#
def make_event_images(taskrunner, labelconv,
                      obs,
                      bkginfo,
                      asol,
                      grid,
                      enbands,
                      chips,
                      outpath,
                      lookuptab,
                      random=0,
                      tmpdir="/tmp",
                      verbose="0",
                      clobber=False,
                      cleanup=True):
    """Create the binned count images. The return value is the list
    of file names that have been created.

    evtfile should include any filters given by the user and grid
    is the sky grid to use for the images. asol is a comma-separated
    string containing the asol file names.

    enbands is the set of energy bands with unique energy ranges
    (i.e. there are no repeat a:b pairs in this list of a:b:c values).

    bkginfo is None for no background subtraction, otherwise the
    tuple (methodname, methodparams, bkgevtfile). The random
    parameter is sent to reproject_events (if needed) when
    background subtraction is used.
    """

    filename = obs.get_evtfile()
    if obs.instrument == "ACIS" and obs.grating != "NONE":
        filename += "[tg_m=0,Null]"

    out = []
    tasks = []
    for enband in enbands:
        v3(f"Creating an image with {enband.dmfilterstr}")
        ifile = f"{filename}[bin {grid}]{enband.dmfilterstr}[opt type=i4]"
        ofile = name_image(outpath, enband)

        task = labelconv(f"evtbin-{enband.bandlabel}")
        taskrunner.add_task(task, [], create_event_image, ifile, ofile,
                            tmpdir=tmpdir, clobber=clobber, verbose=verbose)
        out.append(ofile)

        etask = labelconv(ofile)
        taskrunner.add_task(etask, [task], add_band_keywords,
                            ofile, enband, tmpdir=tmpdir)
        tasks.append(etask)

    etask = labelconv("evtbin-end")
    taskrunner.add_barrier(etask, tasks)
    if bkginfo is None:
        return etask

    btask = background_subtract_hrci(taskrunner, labelconv, [etask],
                                     obs,
                                     out,
                                     bkginfo,
                                     asol,
                                     grid,
                                     outpath,
                                     enbands,
                                     lookuptab,
                                     random=random,
                                     tmpdir=tmpdir,
                                     verbose=verbose,
                                     clobber=clobber,
                                     cleanup=cleanup
                                     )

    return btask


def reproject_bgnd_hrci(bkgevts, evtfile, obsid, asol, outfile,
                        random=0,
                        tmpdir="/tmp/",
                        verbose=0,
                        clobber=False
                        ):
    """Reproject the background event file for HRC-I (bkgevts), which
    is assumed to be one of the "particle background" files from the
    CALDB, to match the observation (evtfile, obsid, asol).

    The name of the reprojected event file is outfile.
    """

    bevt = blanksky_hrci(bkgevts, evtfile,
                         tmpdir, obsid, verbose)
    reproject_bgnd(bevt.name,
                   outfile,
                   asol, evtfile,
                   random=random,
                   verbose=verbose,
                   clobber=clobber)


def background_subtract_hrci(taskrunner, labelconv, preconditions,
                             obs,
                             imgs,
                             bkginfo,
                             asol,
                             grid,
                             outpath,
                             enbands,
                             lookup_table,
                             random=0,
                             tmpdir="/tmp/",
                             verbose="0",
                             clobber=False,
                             cleanup=True):
    """Background subtract the HRC-I counts data (the file names in
    the bimgs array).

    bkginfo is the triple (bkgmethod, bkgparams, bkgevts):

      bkgmethod is the method name.
      bkgevts is the path to the HRC-I background file (likely in
        the CALDB but a manual version could be used)

    evtfile should include any filters given by the user, asol is
    a string containing a comma-separated list of asol files,
    and grid is the sky grid to use for the images.
    """

    (bkgmethod, bkgparams, bkgevts) = bkginfo

    reproj = outpath + HRCI_BG_EVTS

    stask = labelconv("reproject-hrci-bgnd")
    taskrunner.add_task(stask, preconditions,
                        reproject_bgnd_hrci,
                        bkgevts,
                        obs.get_evtfile(),
                        obs.obsid, asol,
                        outfile=reproj,
                        random=random,
                        tmpdir=tmpdir,
                        verbose=verbose,
                        clobber=clobber)

    # at the moment this is only called for one file so no need to
    # make it parallel.
    imgs_pcle = [name_hrci_particle_background(outpath, b)
                 for b in enbands]
    imgs_unsub = [name_hrci_unsubtracted_background(outpath, b)
                  for b in enbands]

    etask = labelconv("subtract-hrci-bgnd")
    taskrunner.add_task(etask, [stask],
                        make_images_hrci,
                        enbands,
                        imgs,
                        imgs_pcle,
                        imgs_unsub,
                        obs.get_evtfile(),
                        bkgmethod,
                        bkgparams,
                        reproj,
                        bkgevts,
                        obs.obsid,
                        grid,
                        tmpdir,
                        lookup_table,
                        verbose=verbose)

    if cleanup:
        etask2 = labelconv("subtract-hrci-bgnd-cleanup")
        delfiles = [reproj] + imgs_pcle + imgs_unsub
        taskrunner.add_task(etask2, [etask], cleanup_files_task, delfiles,
                            "HRC-I background events file")
        return etask2

    else:
        return etask


def get_imap_nbins(maxsize, npixels):
    """Calculate the largest integer binsize that divides into npixels
    and is no larger than maxsize, and return the number of pixels
    of this length.

    If maxsize < 1, which is valid, then return npixels.
    """

    ms = np.ceil(maxsize).astype(np.int)
    xs = [i for i in range(ms, 0, -1) if npixels % i == 0]
    if xs == []:
        # We should not be able to get here and hit this situation, but
        # just in case
        raise ValueError(f"Unable to find any binsizes for npixels={npixels} and max binsize={maxsize}")

    return npixels // xs[0]


def instrument_map_hrc(obs, outpath, chips, energies, binval, units):
    """Return the arguments needed for the mkinstmap calls for HRC data.

    obs is a ciao_contrib._tools.obsinfo.ObsInfo object.
    energies is an array of energy bands; assumed to be unique.

    Return is (pixelgrid, args).
    """

    out = []
    if obs.detector == "HRC-I":
        detsubsys = "HRC-I"
        nbins = get_imap_nbins(binval, 16384)
        pixelgrid = f"1:16384:#{nbins},1:16384:#{nbins}"
        v3(f"HRC-I instrument map will be {nbins} pixels square.")

        if units == "time":
            detsubsys += ";IDEAL"

    elif obs.detector == "HRC-S":
        # We do not bin up the HRC-S instrument map because
        #   . 16456 mod 4096 is not 0
        #   . mkexpmap will create an empty output image with
        #     common binning factors on 64-bit machines
        #     TODO: is this still true in CIAO 4.6?
        #
        pixelgrid = "1:4096:#4096,1:16456:#16456"

    else:
        raise ValueError(f"Invalid DETNAM={obs.detector} for HRC ({obs.get_evtfile()})")

    badpix = obs.get_ancillary('bpix')
    if badpix == "CALDB":
        ardlib = None
    elif badpix == "NONE":
        ardlib = f"AXAF_{obs.detector}_BADPIX_FILE=NONE"
    else:
        ardlib = f"AXAF_{obs.detector}_BADPIX_FILE={badpix}[BADPIX]"

    mask = obs.get_ancillary('mask')
    for j in chips:
        if obs.detector == "HRC-S":
            detsubsys = f"HRC-S{j}"
            if units == "time":
                detsubsys += ";IDEAL"

        obsfile = obs.get_evtfile_no_dmfilter()

        if mask == "":
            maskfile = ""
        else:
            maskfile = f"{mask}[MASK{j}]"

        for energy in energies:
            # Arguments are: outfile, maskfile, obsfile, detsubsys, monoenergy, weightfile, ardlib
            (enmono, wgtfile) = energy.instmap_options
            out.append(
                (name_instmap(outpath, j, energy),
                 maskfile,
                 obsfile,
                 detsubsys,
                 enmono,
                 wgtfile,
                 ardlib))

    return (pixelgrid, out)


def instrument_map_acis(obs, outpath, chips, energies, units):
    """Return the arguments needed for the mkinstmap calls for ACIS data.

    obs is a ciao_contrib._tools.obsinfo.ObsInfo object.
    energies is an array of energy bands; assumed to be unique.

    Return is (pixelgrid, args).

    In CIAO 4.6 we no longer return the pbkfile parameter.
    This may mean that very-old datasets will cause the tool to fail.
    """

    out = []
    pixelgrid = "1:1024:#1024,1:1024:#1024"

    maskfile = obs.get_ancillary('mask')
    badpix = obs.get_ancillary('bpix')

    for j in chips:
        detsubsys = f"ACIS-{j}"
        if units == "time":
            detsubsys += ";IDEAL"

        # Add the frame-store bit (needed since, as of CIAO 4.12, it
        # isn't excluded automatically even though the data has been
        # filtered at the L2 level).
        #
        detsubsys += ";BPMASK=0x03ffff"

        obsfile = obs.get_evtfile_no_dmfilter()

        if badpix == "CALDB":
            ardlib = None
        elif badpix == "NONE":
            ardlib = f"AXAF_ACIS{j}_BADPIX_FILE=NONE"
        else:
            ardlib = f"AXAF_ACIS{j}_BADPIX_FILE={badpix}[BADPIX{j}]"

        for energy in energies:
            # Arguments are: outfile, maskfile, obsfile, detsubsys, monoenergy, weightfile, ardlib
            (enmono, wgtfile) = energy.instmap_options
            out.append(
                (name_instmap(outpath, j, energy),
                 maskfile,
                 obsfile,
                 detsubsys,
                 enmono,
                 wgtfile,
                 ardlib))

    return (pixelgrid, out)


def run_mkinstmap(outfile, mfile, obsfile, detsubsys, grating,
                  monoenergy, weightfile,
                  pixelgrid, mirror, dafile, units,
                  message=None,
                  verbose=0,
                  tmpdir="/tmp",
                  clobber=False,
                  ardlib=None):
    """Run mkinstmap in its own PFILES environment.

    In CIAO 4.5 the obsfile parameter was set to the aspect histogram
    for the chip - e.g. obsfile=xx/ciaox_0039_3.asphist[asphist] - but
    with the deprecation of the pbkfile parameter in CIAO 4.6 we
    now need to use the event file. This is not enforced by this
    routine (i.e. mkinstmap will error out if an invalid file is
    specified for obsfile).
    """

    if message is not None:
        v1(message)

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):

        # punlearn("ardlib")
        if ardlib is not None:
            run.run("pset", ["ardlib", ardlib])

        # punlearn("mkinstmap")
        args = ["pixelgrid=" + pixelgrid,
                "outfile=" + outfile,
                "maskfile=" + mfile,
                "obsfile=" + obsfile,
                "detsubsys=" + detsubsys,
                "grating=" + grating,
                f"spectrumfile={weightfile}",
                f"monoenergy={monoenergy}",
                "mirror=" + mirror,
                "dafile=" + dafile,
                "mode=h"
                ]
        add_defargs(args, clobber, verbose)
        run.run("mkinstmap", args)
        if units == "time":
            dmhedit_key(outfile, 'BUNIT', "", verbose=verbose)


def make_instrument_maps(taskrunner, labelconv, preconditions,
                         obs,
                         enbands,
                         chips,
                         units,
                         outpath,
                         binval,
                         parallel=True,
                         verbose="0",
                         tmpdir="/tmp",
                         clobber=False):
    """Create the instrument maps for the observation.

    enbands is the list of energy-band objects to process, but
    has been cleaned to ensure that they monochromatic energies
    are unique.

    units determins whether we want the default instrument
    map (count cm^2 photon^-1) - when units=default or area -
    or time (no units).

    """

    if units == "default":
        mirror = "HRMA"
        dafile = "CALDB"

    elif units == "area":
        mirror = "HRMA"
        dafile = "CALDB"

    elif units == "time":
        mirror = "HRMA;area=1"
        dafile = "NONE"

    else:
        raise ValueError("Internal error: invalid setting units=" + units)

    if obs.instrument == "HRC":
        (pixelgrid, mkinstmap_args) = \
            instrument_map_hrc(obs,
                               outpath, chips, enbands,
                               binval,
                               units)

    elif obs.instrument == "ACIS":
        (pixelgrid, mkinstmap_args) = \
            instrument_map_acis(obs, outpath, chips, enbands,
                                units)

    else:
        raise ValueError(f"Invalid INSTRUME={obs.instrument} keyword.")

    tasks = []
    for arg in mkinstmap_args:

        if arg == mkinstmap_args[0]:
            if len(mkinstmap_args) == 1:
                smsg = f"Creating instrument map for obsid {obs.obsid}"
            else:
                smsg = f"Creating {len(mkinstmap_args)} instrument maps for obsid {obs.obsid}"
        else:
            smsg = None

        (outfile, mfile, obsfile, detsubsys, monoenergy, wgtfile, ardlib) = arg

        # use the output file name as the label
        task = labelconv(f"imap-{outfile}")

        taskrunner.add_task(task, preconditions, run_mkinstmap,
                            outfile, mfile, obsfile, detsubsys, obs.grating,
                            monoenergy, wgtfile,
                            pixelgrid, mirror, dafile, units,
                            message=smsg,
                            tmpdir=tmpdir,
                            ardlib=ardlib, verbose=verbose,
                            clobber=clobber)
        tasks.append(task)

    etask = labelconv("imap-end")
    taskrunner.add_barrier(etask, tasks)
    return etask


def run_mkexpmap(outfile, instmap, asphist, matchfile, normalize,
                 message=None,
                 hackunits=True,
                 verbose=0,
                 tmpdir="/tmp",
                 clobber=False):
    "Create the given exposure map using a separate PFILES environment."

    if message is not None:
        v1(message)

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        # punlearn("mkexpmap")

        # It is wasteful to re-calculate the grid each time,
        # but we do this to avoid having to pass information
        # between processes when running in parallel. Ideally
        # this grid would be imposed at the time the images are
        # created, so that it can be sent to further processes.
        #

        # We assume the same limits are used whatever the energy band or chip,
        # so we only need to call get_sky_limits once.
        #
        # if the grid does not 'fully fill' the image (i.e. if the last row/column
        # is part-filled due to the binning size) then we do not want to use get_sky_limits
        # here, since it assumes all rows/columns are fully filled. However, if we
        # do use a grid that does not fill the columns then you can get warning
        # messages from mkexpmap, along the lines of
        #
        #    ****** WARNING: The range [4470:5670:32,1810:3200:32] does not correspond to a
        #       whole number of pixels.  The following range will be used instead:
        #          [4470:5686:32]
        #       In the future, you should use the [min:max:#num] syntax to avoid this
        #       ambiguity.
        #
        # so we do in fact use the get_sky_limits approach and live with the fact
        # that this will result in over-correction for the image data.
        #
        punlearn("get_sky_limits")
        run.run("get_sky_limits",
                [f"image={matchfile}",
                 "verbose=0",
                 "mode=h"]
                )
        xygrid = paramio.pgetstr("get_sky_limits", "xygrid")

        args = ["outfile=" + outfile,
                "instmapfile=" + instmap,
                "asphistfile=" + asphist,
                "xygrid=" + xygrid,
                "normalize=" + normalize,
                "useavgaspect=no",
                "mode=h"
                ]
        add_defargs(args, clobber, verbose)
        run.run("mkexpmap", args)

        # copy over a few keywords. In CIAO 4.4 mkexpmap does not copy over the
        # GRATING keyword, instead just setting it to NONE. I believe this
        # has been fixed in a later release but have not checked this.
        copy_keywords(instmap, outfile,
                      ["SPECTRUM", "WGTFILE", "ENERG_LO", "ENERG_HI",
                       "GRATING"],
                      tmpdir=tmpdir)

        if hackunits:
            dmhedit_key(outfile, 'BUNIT', 's', verbose=verbose)


def make_expmap_indiv(taskrunner, labelconv, preconditions,
                      outhead, obsid, enbands, chips, matchfile,
                      normalize="no",
                      hackunits=True,
                      parallel=True,
                      verbose="0",
                      tmpdir="/tmp",
                      clobber=False,
                      cleanup=True):
    """Create the per-chip, per obsid exposure maps.

    The energy bands are assumed to have unique monochromatic energies.

    If cleanup=True then the aspect histograms and instrument maps will be deleted
    once the exposure map has been created.
    """

    nruns = len(enbands) * len(chips)
    if nruns == 1:
        smsg = f"Creating exposure map for obsid {obsid}"
    else:
        smsg = f"Creating {nruns} exposure maps for obsid {obsid}"

    tasks = []
    for j in chips:
        asphist = name_asphist(outhead, j, blockname=True)

        atasks = []
        delfiles = []
        for enband in enbands:
            outfile = name_expmap(outhead, enband, num=j)
            instmap = name_instmap(outhead, j, enband)

            task = labelconv(f"emap-{outfile}")
            taskrunner.add_task(task, preconditions,
                                run_mkexpmap,
                                outfile, instmap, asphist, matchfile,
                                normalize,
                                tmpdir=tmpdir,
                                message=smsg,
                                hackunits=hackunits,
                                verbose=verbose,
                                clobber=clobber
                                )

            smsg = None
            atasks.append(task)
            tasks.append(task)
            delfiles.append(instmap)

        if cleanup:
            # Note: we do not make the emap-end depend on this task
            delfiles.append(name_asphist(outhead, j, blockname=False))
            task2 = labelconv(f"cleanup-asphist-instmap-{j}")
            taskrunner.add_task(task2, atasks,
                                cleanup_files_task, delfiles)

    etask = labelconv("emap-end")
    taskrunner.add_barrier(etask, tasks)
    return etask


# This originally used reproject_image with res=1 since it was
# not clear what the input grids would be. At present the images
# should be defined on exactly the same grids, so it is *just*
# an addition. So, we replace
#   reproject_iamge infile=@... matchfile=match outfile=out[EXPMAP]
#     method=average lookupTab=... resolution=1
# with
#   dmimgcalc infile=@... infile2= outfile=out[EXPMAP]
#     lookupTab=...
#
# Alternatives
#   - change resolution to 0 (significantly reducing run time)
#     in the reproject_image call
#   - use dmregrid2 instead (with either resolution=1 or 0)
#
# It looks like dmimgcalc and dmregrid2 with resolution=0 are
# similar in run times, but go with dmimgcalc for now.
#
# The code *could* check to see whether the grids agree, and
# fall back to reproject_image if they do not, but it is not
# worth it.
#
def combine_emaps(infiles, match, outfile, lookup_table, detnam,
                  message=None,
                  tmpdir="/tmp/",
                  verbose=0,
                  clobber=False):
    "Combine exposure maps, fix DETNAM and image units"

    if message is not None:
        v1(message)

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        dmimgcalc_add(infiles,
                      outfile + "[EXPMAP]",
                      lookupTab=lookup_table,
                      clobber=clobber,
                      verbose=verbose,
                      tmpdir=tmpdir)

        # We could use dmhedit's filelist argument to just call the
        # tool once, with both DETNAM and BUNIT edits, but it is
        # not a huge time sink and this way we get a cleaner
        # history record.

        # restore the original DETNAM keyword
        dmhedit_key(outfile, 'DETNAM', detnam, verbose=verbose)

        # add the lost expmap BUNIT lost during dmimgcalc
        bunit = fileio.get_image_units(infiles[0])
        tunit = fileio.get_image_units(outfile)
        if bunit != tunit:
            dmhedit_key(outfile, 'BUNIT', bunit, verbose=verbose)


def single_expmap_chips(taskrunner, labelconv, preconditions,
                        outhead,
                        enbands,
                        chip,
                        verbose=0,
                        clobber=False,
                        cleanup=True):
    """There is only a single chip in this obsid so copy over
    to the output.
    """

    tasks = []
    delfiles = []
    for enband in enbands:
        infile = name_expmap(outhead, enband, num=chip)
        outfile = name_expmap(outhead, enband)

        # image with only one interesting block, so do not need
        # option=all in the dmcopy call
        task = labelconv(f"imap-copy-{infile}")
        taskrunner.add_task(task, preconditions,
                            dmcopy, infile, outfile,
                            verbose=verbose, clobber=clobber)
        tasks.append(task)
        delfiles.append(infile)

    etask = labelconv("imap-combine-end")
    if cleanup:
        taskrunner.add_task(etask, tasks,
                            cleanup_files_task, delfiles)
    else:
        taskrunner.add_barrier(etask, tasks)

    return etask


def combine_expmap_chips(taskrunner, labelconv, preconditions,
                         outhead, enbands, obsid, chips, matchfile, detnam,
                         lookup_table, tmpdir,
                         parallel=True,
                         verbose=0,
                         clobber=False,
                         cleanup=True):
    """Combine per-chip exposure maps for each energy.

    The energy bands are assumed to have unique monochromatic energies.
    """

    # setup arguments to reproject images
    #
    fouthead = os.path.normpath(os.path.join(os.getcwd(), outhead))
    if outhead.endswith("/") and not fouthead.endswith("/"):
        # normpath removes the trailing / but we need it, so add it back in
        fouthead += "/"

    nchips = len(chips)
    nruns = len(enbands)
    if nruns == 1:
        smsg = f"Combining {nchips} exposure maps for obsid {obsid}"
    else:
        smsg = f"Combining {nchips} exposure maps for {nruns} bands (obsid {obsid})"

    tasks = []
    for enband in enbands:

        # Ensure file names include the full path so that we can place the
        # stack file in any location.
        #
        expmaps = [name_expmap(fouthead, enband, num=j) for j in chips]
        task = labelconv(f"reproj-emap-{enband.bandlabel}")
        taskrunner.add_task(task, preconditions,
                            combine_emaps,
                            expmaps, matchfile, name_expmap(outhead, enband),
                            lookup_table, detnam,
                            message=smsg,
                            verbose=verbose, clobber=clobber, tmpdir=tmpdir)

        smsg = None

        if cleanup:
            task2 = labelconv(f"reproj-emap-{enband.bandlabel}-cleanup")
            taskrunner.add_task(task2, [task],
                                cleanup_files_task, expmaps)
            tasks.append(task2)
        else:
            tasks.append(task)

    etask = labelconv("reproj-emap-end")
    taskrunner.add_barrier(etask, tasks)
    return etask


def make_exposure_maps(taskrunner, labelconv, preconditions,
                       obs,
                       enbands,
                       chips,
                       outhead,
                       lookup_table,
                       normalize="no",
                       hackunits=False,
                       tmpdir="/tmp",
                       parallel=True,
                       verbose="0",
                       clobber=False,
                       cleanup=True
                       ):
    """Create exposure maps per chip and per band, and then for
    each band create a single exposure map (a copy if only one chip
    in use, otherwise adding up the individual exposure maps).

    The energy band list should have unique monochromatic energies.

    The hackunits field is set to True when the units of the
    exposure map should be changed from "cm**2 sec" to "s";
    it is an error to set hackunits=True and normalize="yes".

    If cleanup=True then the aspect solution, instrument maps,
    and per-chip exposure maps are deleted once they are finished
    with.
    """

    if hackunits and normalize == "yes":
        raise ValueError("Internal error: normalize=yes and hackuits=True")

    matchfile = name_image(outhead, enbands[0])

    etask = make_expmap_indiv(taskrunner, labelconv, preconditions,
                              outhead,
                              obs.obsid,
                              enbands,
                              chips,
                              matchfile,
                              parallel=parallel,
                              normalize=normalize,
                              hackunits=hackunits,
                              tmpdir=tmpdir,
                              verbose=verbose,
                              clobber=clobber,
                              cleanup=cleanup)

    if len(chips) == 1:
        return single_expmap_chips(taskrunner, labelconv, [etask],
                                   outhead,
                                   enbands,
                                   chips[0],
                                   verbose=verbose,
                                   clobber=clobber,
                                   cleanup=cleanup)

    return combine_expmap_chips(taskrunner, labelconv, [etask],
                                outhead,
                                enbands,
                                obs.obsid,
                                chips,
                                matchfile,
                                obs.detector,
                                lookup_table,
                                tmpdir,
                                parallel=parallel,
                                verbose=verbose,
                                clobber=clobber,
                                cleanup=cleanup)


def run_mkpsfmap(outfile, matchfile, energy, wgtfile, ecf,
                 maskfile=None,
                 message=None,
                 verbose=0,
                 tmpdir="/tmp",
                 clobber=False):
    """Create the given PSF map using a separate PFILES environment.

    energy is used when wgtfile == NONE, otherwise wgtfile is used.

    The maskfile is used to mask the output image (i.e. any zero-valued
    elements are masked out of the output) when not None.

    Note that the block name is forced to be PSFMAP.

    The output file has no SKY subspace (i.e. it has been removed with
    an explicit 'dmcopy in.fits[subspace -sky] out.fits' call), even
    when wgtfile is None. Note that mkpsfmap sets pixels outside the
    input subspace to NaN, so any spatial filter can be considered to
    still be encoded in the output file. The reason for removing the
    explicit subspace filter is to make it easier to combine the maps
    when merging observations.
    """

    if message is not None:
        v1(message)

    if wgtfile == 'NONE':
        enarg = energy
        sparg = ''
    else:
        enarg = 'INDEF'
        sparg = wgtfile

    if maskfile is None:
        infile = matchfile
    else:
        infile = f"{matchfile}[sky=MASK({maskfile})]"

    mapfile = tempfile.NamedTemporaryFile(dir=tmpdir, suffix='.psfmap')

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        punlearn("mkpsfmap")
        args = [f"infile={infile}",
                f"outfile={mapfile.name}[PSFMAP]",
                f"energy={enarg}",
                f"spectrum={sparg}",
                f"ecf={ecf}",
                "mode=h"
                ]

        add_defargs(args, True, verbose)

        # mkpsfmap has no verbose argument, so drop it
        args = args[:-1]

        run.run("mkpsfmap", args)

        # Remove any spatial filters
        #
        run.dmcopy(f"{mapfile.name}[subspace -sky]",
                   outfile, clobber=clobber, verbose="0")


def make_psf_maps(taskrunner, labelconv, preconditions,
                  ecf,
                  obs,
                  enbands,
                  chips,
                  outhead,
                  lookup_table,
                  threshold=False,
                  tmpdir="/tmp",
                  parallel=True,
                  verbose="0",
                  clobber=False):
    """Create per-band PSF maps, filtered by the FOV.

    """

    # Create a PSF map per band
    #
    nruns = len(enbands)
    if nruns == 1:
        smsg = f"Creating PSF map for obsid {obs.obsid}"
    else:
        smsg = f"Creating {nruns} PSF maps for obsid {obs.obsid}"

    tasks = []
    for enband in enbands:
        outfile = name_psfmap(outhead, enband, thresh=threshold)
        task = labelconv(f"psfmap-{outfile}")

        # What file do we use as the "base" for the mkpsfmap call (that is,
        # this defines the location, size, pixels for the output), and
        # what is the exposure map we use to filter this output?
        #
        # It is likely that the exposure map could be used as the matchfile,
        # but for now go with two (as it makes a bit more sense for the user).
        #
        # We could also use the same base image for all runs, but that also
        # might look odd in the history record, so make it a per-band value.
        #
        if threshold:
            matchfile = name_image_thresh(outhead, enband)
            emapfile = name_expmap_thresh(outhead, enband)
        else:
            matchfile = name_image(outhead, enband)
            emapfile = name_expmap(outhead, enband)

        enmono, wgtfile = enband.instmap_options

        taskrunner.add_task(task, preconditions,
                            run_mkpsfmap,
                            outfile, matchfile, enmono, wgtfile, ecf,
                            maskfile=emapfile,
                            tmpdir=tmpdir,
                            message=smsg,
                            verbose=verbose,
                            clobber=clobber)

        tasks.append(task)
        smsg = None

    ptask = labelconv("psfmap-end")
    taskrunner.add_barrier(ptask, tasks)
    return ptask


def run_imgthresh(infile, outfile, expmap, thresh,
                  message=None,
                  verbose=0,
                  tmpdir="/tmp",
                  clobber=False):
    "Runs dmimgthresh"

    if message is not None:
        v1(message)

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        # punlearn("dmimgthresh")
        args = ["infile=" + infile,
                "outfile=" + outfile,
                "expfile=" + expmap,
                "cut=" + thresh,
                "value=0.0",
                "mode=h"]
        add_defargs(args, clobber, verbose)
        run.run("dmimgthresh", args)


# TODO: if use dmimgcalc_op with op=imgout=img1/img2 then will have
#   NaN rather than 0 for the areas with no exposure map.
#
def run_expcorr_image(imgfile, emapfile, outfile, lookup_table,
                      message=None,
                      verbose=0,
                      tmpdir="/tmp",
                      clobber=False):
    "Create exposure-corrected image"

    if message is not None:
        v1(message)

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        v3(f"Creating fluxed image: {outfile}")
        dmimgcalc2(imgfile, emapfile, outfile + "[PFLUX_IMAGE]",
                   "div", lookupTab=lookup_table,
                   verbose=verbose, clobber=clobber)

        # Copy over keywords originally from the instrument map
        copy_keywords(emapfile, outfile,
                      ["SPECTRUM", "WGTFILE", "ENERG_LO", "ENERG_HI"],
                      tmpdir=tmpdir)

        # Fix up the BUNIT field
        img_units = fileio.get_image_units(imgfile)
        emap_units = fileio.get_image_units(emapfile)
        v3(f"BUNIT cleanup: img={img_units} emap={emap_units}")

        # Some of these checks are not really necessary but left in in case
        # some of the tools change their BUNIT handling
        #
        if img_units == emap_units:
            fmap_units = fileio.get_image_units(outfile)
            if fmap_units != emap_units:
                v3(f"Cleaning out fluxed units from {fmap_units} to ''")
                dmhedit_key(outfile, 'BUNIT', '')

        else:
            # Following http://heasarc.nasa.gov/docs/heasarc/ofwg/docs/general/ogip_93_001/ogip_93_001.html
            # but not trying to parse the existing units as too much effort
            # (although we expect to only have one of three cases so could just check)
            nkey = img_units
            if nkey != '' and emap_units != '':
                nkey += ' '

            if emap_units == 's':
                nkey += '/s'

            elif emap_units == 'cm**2':
                nkey += '/cm**2'

            elif emap_units == 'cm**2 s':
                nkey += '/cm**2 /s'

            elif emap_units == 'cm**2 sec':
                nkey += '/cm**2 /sec'

            else:
                nkey += '/(' + emap_units + ')'

            v3(f"New BUNIT={nkey}")
            dmhedit_key(outfile, 'BUNIT', nkey)


def make_fluxed_images(taskrunner, labelconv, preconditions,
                       enbands,
                       obsid,
                       outhead,
                       lookup_table,
                       thresh=None,
                       parallel=True,
                       verbose="0",
                       tmpdir="/tmp",
                       clobber=False,
                       cleanup=True
                       ):
    "Create the fluxed images"

    thresh_args = []
    imcalc_args = []
    for enband in enbands:
        imgfile = name_image(outhead, enband)
        expmap = name_expmap(outhead, enband)
        fluxmap = name_fluxed(outhead, enband)

        # thresh arguments are: imgfile, expmap, img_outfile, exp_outfile
        # imcalc arguments are: imgfile, expmap, outfile
        if utils.thresh_is_set(thresh):
            img_thrfile = name_image_thresh(outhead, enband)
            exp_thrfile = name_expmap_thresh(outhead, enband)
            thresh_args.append((imgfile, expmap, img_thrfile, exp_thrfile))
            imcalc_args.append((img_thrfile, exp_thrfile, fluxmap))
        else:
            imcalc_args.append((imgfile, expmap, fluxmap))

    nthresh = len(thresh_args)
    if nthresh > 0:
        smsg = f"Thresholding data for obsid {obsid}"

        tasks = []
        for (imgfile, expmap, img_thrfile, exp_thrfile) in thresh_args:
            itask = labelconv(img_thrfile)
            taskrunner.add_task(itask, preconditions,
                                run_imgthresh,
                                imgfile, img_thrfile, expmap, thresh,
                                message=smsg, tmpdir=tmpdir,
                                verbose=verbose, clobber=clobber)
            tasks.append(itask)
            smsg = None

            etask = labelconv(exp_thrfile)
            taskrunner.add_task(etask, preconditions,
                                run_imgthresh,
                                expmap, exp_thrfile, "", thresh,
                                message=smsg, tmpdir=tmpdir,
                                verbose=verbose, clobber=clobber)
            tasks.append(etask)

            if cleanup:
                ctask = labelconv(f"cleanup-{img_thrfile}-{exp_thrfile}")
                taskrunner.add_task(ctask, [itask, etask],
                                    cleanup_files_task,
                                    [imgfile, expmap])

        preconditions = tasks

    ncalc = len(imcalc_args)
    if ncalc == 1:
        smsg = f"Exposure-correcting image for obsid {obsid}"
    else:
        smsg = f"Exposure-correcting {ncalc} images for obsid {obsid}"

    tasks = []
    for (imgfile, expmap, fluxmap) in imcalc_args:
        task = labelconv(fluxmap)
        taskrunner.add_task(task, preconditions,
                            run_expcorr_image,
                            imgfile, expmap, fluxmap, lookup_table,
                            message=smsg,
                            tmpdir=tmpdir,
                            clobber=clobber, verbose=verbose)
        smsg = None
        tasks.append(task)

    etask = labelconv("expcorr-end")
    taskrunner.add_barrier(etask, tasks)
    return etask


def read_first_row(filename, colname):
    "Return the value of the first row of the given column."

    cr = pcr.read_file(filename + "[#row=1]")
    return pcr.copy_colvals(cr, colname)[0]


def find_blanksky_hrci(obsinfo, verbose=True, bgndmap=None, tmpdir=None):
    """Return the HRC-I background events file for the observation.

    The verbose flag determines whether to include informational
    messages at the verbose=1 level telling the user whether a
    background file was found or not.

    The bgndmap is intended for development/testing, and should
    contain a dictionary with keys being event file names (the same path as given
    to the script), and values being the full path to the
    HRC-I background file to use. If bgndmap is not None then it
    is used instead of the CALDB lookup; missing files are treated
    as with a missing CALDB file, None is returned.

    There are two error conditions:
       - the HRC-I background files are not installed
       - there is no matching background file for the observation

    They are both signalled by (an optional screen message at verbose=1)
    and a return value of None.
    """

    evtfile = obsinfo.get_evtfile()
    v3(f"Looking for HRC-I background file for {evtfile}")

    if bgndmap is None:
        bname = _find_blanksky_hrci_caldb(evtfile, verbose=verbose,
                                          tmpdir=tmpdir)
    else:
        bname = _find_blanksky_hrci_manual(evtfile, bgndmap, verbose=verbose)

    if verbose and (bname is not None):
        v1(f"Background file for {evtfile} found: {bname}")

    return bname


def _find_blanksky_hrci_caldb(evtfile, verbose=True, tmpdir=None):
    "Find the HRC-I background file using a CALDB query"

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        v3("Querying CALDB for HRC-I background file")

        # hrc_bkgrnd_lookup displays the file name even with verbose=0 so we
        # explicitly hide it by piping to /dev/null. We also hide stderr since it
        # is unlikely that it adds anything useful to the error message we raise
        # below.
        #
        # punlearn("hrc_bkgrnd_lookup")
        devnull = open('/dev/null', 'w')
        hbl_status = sbp.call(["hrc_bkgrnd_lookup",
                               evtfile,
                               "event"],
                              stdout=devnull, stderr=devnull)
        devnull.close()

        if hbl_status != 0:
            v3(" . hrc_bkgrnd_lookup call failed")
            if verbose:
                msg = f"No HRC-I background file for {evtfile}, so skipping background subtraction."
                v1(msg)

            return None

        hrci_bkg = paramio.pgetstr("hrc_bkgrnd_lookup", "outfile")
        v3(f" . hrc_bkgrnd_lookup found {hrci_bkg}")

        # clean up file name for user consumption
        # os.path routines might be cleaner
        caldbdir = os.getenv("CALDB")
        clen = len(caldbdir)
        if caldbdir[-1] == "/":
            if hrci_bkg.startswith(caldbdir):
                bname = "$CALDB/" + hrci_bkg[clen:]
            else:
                bname = hrci_bkg
        else:
            if hrci_bkg.startswith(caldbdir) and hrci_bkg[clen] == "/":
                bname = "$CALDB" + hrci_bkg[clen:]
            else:
                bname = hrci_bkg

        # TODO: should the following be using hrci_bkg or bname?
        #       this was found during a code cleanup in preparation for
        #       the CIAO 4.8 release; I have not changed it since it
        #       needs some thought and testing
        #
        # NOTE: bname isn't actually used anywhere

        if not os.path.exists(hrci_bkg):
            v3(" . hrc bkgrnd file not found on disk")
            if verbose:
                msg = f"The background for {evtfile} is not in the CALDB, so skipping background subtraction."
                v1(msg)

            return None

        return hrci_bkg


def _find_blanksky_hrci_manual(evtfile, bgndmap, verbose=True):
    "Find the HRC-I background file using the given dictionary"

    key = evtfile
    v3(f"CALDB override: using a background map, with key={key}")
    try:
        bname = bgndmap[key]
        v3(f" -> found {bname}")

    except KeyError:
        v3(f" -> No match for key={key} from file={evtfile} in bgndmap={bgndmap}")

        if verbose:
            msg = "WARNING: No HRC-I background file for " + \
                  f"{evtfile}, so skipping background subtraction."
            v1(msg)

        return None

    # since there may be DM filters
    try:
        pcr.read_file(bname + "[#row=1]")
        return bname

    except IOError:
        if not os.path.exists(bname):
            v3(" -> hrc bkgrnd file not found on disk!")
            if verbose:
                msg = f"WARNING: The background for {evtfile}" + \
                      " is not found, so skipping background subtraction."
                v1(msg)

            return None


def find_status_filter(infile, obsid, tmpdir="/tmp"):
    """Inspect the history records for infile and find the
    status filter used to create it. It returns the
    complete filter expression (i.e. "[status=...]"),
    or the empty string.

    It also reports to the user the filter found (or
    if one was not found).

    This is not very robust, in that it assumes that the
    first dmcopy record in the history block contains the
    status filter. If it looks like it can't find a
    status filter it returns the empty string.
    """

    status = tempfile.NamedTemporaryFile(dir=tmpdir,
                                         suffix=".status")
    args = ["infile=" + infile,
            "outfile=" + status.name,
            "tool=dmcopy",
            "action=get",
            "clobber=yes"]
    run.run("dmhistory", args)

    # Need to convert from np.string_ to Python string
    statbits = str(read_first_row(status.name, "col2"))
    status.close()
    v2(f"Finding status bit filter for ObsId {obsid} from: {statbits}")

    # I had planned to report this at verbose=2 but that is
    # *very* noisy, so adding it to the verbose=1 level,
    # since it's important to know.
    spos = statbits.find("[status=")
    if spos == -1:
        v1(f"WARNING: no STATUS filter found in {infile} so unable to filter background for obsid {obsid}!")
        return ""

    epos = statbits.find("]", spos)
    if epos == -1:
        v1(f"WARNING: illegal STATUS filter found in {infile} so unable to filter background for obsid {obsid}!")
        return ""

    statbits = statbits[spos:epos + 1]
    v1(f"Background filter (obsid {obsid}): {statbits}")
    return statbits


def blanksky_hrci(caldbfile, infile, tmpdir, obsid, verbose):
    """Tailor the HRC-I background file in the CALDB (caldbfile)
    to match the given observation. Note that reprojection is not
    done here, just status filtering and header manipulation.

    The return value is the handle to the tailored events file;
    it will delete itself when it goes out of scope or the
    user explicitly closes it.

    The term 'blanksky' in the function name is a bit of a mis-nomer,
    since the HRC-I CALDB background files are actually of the
    particle background. However, it is too big a change to make
    to correct this.
    """

    v1(f"Setting up the HRC-I background for obsid {obsid}")

    bkg_stat = tempfile.NamedTemporaryFile(dir=tmpdir,
                                           suffix='.bkgevt')
    dmfilt = fileio.get_filter(caldbfile)
    if dmfilt == "":
        v2("Background file contains no DM filter, so can copy it")
        shutil.copyfile(caldbfile, bkg_stat.name)

    else:
        v2(f"Background file contains a DM filter ({dmfilt})" +
           " so need to dmcopy it")
        # Only expect a single block in the background files, so
        # do not need to add in option="all" here
        dmcopy(caldbfile, bkg_stat.name, clobber=True, verbose="0")

    ofile = tempfile.NamedTemporaryFile(dir=tmpdir,
                                        suffix='.bkgevt')

    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):

        # Find the status filter used to create infile
        statfilter = find_status_filter(infile, obsid, tmpdir=tmpdir)

        # punlearn("dmmakepar")
        header = tempfile.NamedTemporaryFile(dir=tmpdir, suffix='.hdr')
        args = ["input=" + infile,
                "output=" + header.name,
                "verbose=0",
                "clobber=yes",
                "mode=h"]
        run.run("dmmakepar", args)

        # We want the _PNT keywords, as well as
        #   OBJECT, OBS_ID, OBSERVER, TITLE, DS_IDENT
        #
        # DS_IDENT appears to be created automatically from the OBS_ID value,
        # but copy it across anyway.
        #
        # Other keywords, included to avoid warnings from merging:
        #   ASPTYPE
        #   DATAMODE  (bgnds have NEXT_IN_LINE it appears; is this a
        #              sensible change?)
        #   FOC_LEN
        #   BTIMDRFT  \
        #   BTIMNULL  | could probably just delete from all files
        #   BTIMRATE  /
        #
        # OBI_NUM appears to depend on whether the data has been reprocessed
        # or not
        #
        # The status filter used is added as the STATFILT header keyword
        # since this information is not recorded in the data subspace of
        # the file (as it is a bit column).
        #
        ts = ["ra", "dec", "roll"]
        wanted_terms = ["object", "obs_id", "observer", "title",
                        "ds_ident", "seq_num"] \
            + [i + "_nom" for i in ts] \
            + [i + "_pnt" for i in ts] \
            + ["asptype", "datamode", "foc_len"] \
            + ["btimdrft", "btimnull", "btimrate"] \
            + ["obi_num"]

        pnt = tempfile.NamedTemporaryFile(dir=tmpdir, mode='w+',
                                          suffix='.par')
        h = open(header.name)
        p = open(pnt.name, "w")
        has_obi_num = False
        for line in h:
            term = line.split(",", 1)[0]
            if term in wanted_terms:
                p.write(line)
            if not has_obi_num and (term == "obi_num"):
                has_obi_num = True

        # add in the STATFILT keyword
        p.write(f'statfilt,s,h,"{statfilter}",,,"STATUS filter"\n')

        h.close()
        p.close()
        header.close()

        # update background header
        # punlearn("dmreadpar")
        args = ["input=" + pnt.name,
                "output=" + bkg_stat.name + "[EVENTS]",
                "verbose=0",
                "clobber=yes",
                "mode=h"]
        run.run("dmreadpar", args)

        pnt.close()

        if not has_obi_num:
            try:
                run.run("dmhedit",
                        [f"infile={bkg_stat.name}",
                         "filelist=",
                         "operation=delete",
                         "key=OBI_NUM",
                         "verbose=0",
                         "mode=h"])
            except Exception:
                pass

        # change status bits to match infile; do not add option=all
        # since we have already assumed there's only a single
        # block that we are interested in
        dmcopy(bkg_stat.name + statfilter,
               ofile.name,
               verbose=verbose, clobber=True)

    bkg_stat.close()
    return ofile


def clobber_checks(files, clobber=False):
    """If clobber is False then check that no output
    files already exist. If True, check that any that do
    exist can be written to.

    files is a dictionary where the values (can be a
    file name, array, or dictionary) are the file names.
    """

    v3(f"Clobber checks with clobber={clobber}")
    fnames = []
    for (key, vals) in files.items():
        v4(f"Checking for {key} files.")
        if isinstance(vals, str):
            v4(" ... a single file")
            fnames.append(vals)

        elif isinstance(vals, dict):
            v4(" ... a dictionary")
            for val in vals.values():
                fnames.extend(val)

        else:
            v4(" ... an array")
            fnames.extend(vals)

    for fname in fnames:
        fileio.outfile_clobber_checks(clobber, fname)


def get_output_filenames(outpath, enbands, chips,
                         obs=None,
                         blanksky=False,
                         psf=False,
                         thresh=False):
    """Returns information on the files to be produced

    obs is allowed to be an optional argument but we expect it to be set.
    """

    # TODO: split up exposure maps into per-observation and per-chip
    # TODO: the logic here is spread out too much and should be consolidated
    #
    asphists = [name_asphist(outpath, j) for j in chips]

    imgfiles = []
    threshimg = []
    threshemap = []
    instmaps = []
    expmaps = []
    psfmaps = []
    fluxmaps = []

    for enband in enbands:
        instmaps.extend([name_instmap(outpath, j, enband) for j in chips])
        expmaps.extend([name_expmap(outpath, enband, num=j) for j in chips])
        expmaps.append(name_expmap(outpath, enband))

        if psf:
            psfmaps.append(name_psfmap(outpath, enband,
                                       thresh=thresh))

        imgfiles.append(name_image(outpath, enband))
        threshimg.append(name_image_thresh(outpath, enband))
        threshemap.append(name_expmap_thresh(outpath, enband))
        fluxmaps.append(name_fluxed(outpath, enband))

    # write dictionary of outputs
    outputs = {}
    outputs["images"] = utils.getUniqueSynset(imgfiles)
    outputs["asphists"] = utils.getUniqueSynset(asphists)
    outputs["instmaps"] = utils.getUniqueSynset(instmaps)
    outputs["expmaps"] = utils.getUniqueSynset(expmaps)
    outputs["fluxmaps"] = utils.getUniqueSynset(fluxmaps)

    # write dictionary of files that remain after a cleanup
    saved = {}
    saved["fluxmaps"] = outputs["fluxmaps"]

    # TODO: should the raw images not be output when threshold is on
    #       by default?
    if thresh:
        outputs["image_thresh"] = utils.getUniqueSynset(threshimg)
        outputs["expmap_thresh"] = utils.getUniqueSynset(threshemap)
        saved["image_thresh"] = outputs["image_thresh"]
        saved["expmap_thresh"] = outputs["expmap_thresh"]

    else:
        saved["images"] = outputs["images"]
        saved["expmaps"] = utils.getUniqueSynset([name_expmap(outpath, b)
                                                  for b in enbands])

    # list particle background files
    if blanksky:
        outputs["blanksky"] = [outpath + HRCI_BG_EVTS]

        pcle = []
        raw = []
        for enband in enbands:
            pcle.append(name_hrci_particle_background(outpath, enband))
            raw.append(name_hrci_unsubtracted_background(outpath, enband))

        outputs["unsubtracted_image"] = utils.getUniqueSynset(raw)
        outputs["particle_background"] = utils.getUniqueSynset(pcle)

    if psf:
        outputs["psfmaps"] = utils.getUniqueSynset(psfmaps)
        saved["psfmaps"] = outputs["psfmaps"]

    # FOV file
    #
    if obs is not None:
        outputs["fovs"] = [name_fov(outpath, obs)]
        saved["fovs"] = outputs["fovs"]

    return (outputs, saved)


def add_history(outputs, cmdline_pars, toolname, toolversion,
                cleanup=True):
    """add a history entry to the header of the output files
    """

    v3(f"Updating file headers with history record for {toolname}\n")

    # This used to select which files from outputs to add history records to.
    # It now just does everything, since it is "safer" (e.g. if a new
    # 'file type' gets added), and makes the code easier.
    #
    if cleanup:
        files = outputs[1]
    else:
        files = outputs[0]

    out = set()
    for vs in files.values():
        out |= set(vs)

    # Assume that cmdline_pars contains all the parameter
    # values, even if not given directly on the command line
    # but read in from the parameter file.
    #
    add_tool_history(out,
                     toolname,
                     cmdline_pars,
                     toolversion=toolversion)


SEPVAL = "\n     "


def clean_names(fnames):
    "Prepare array of file names for display"
    return SEPVAL + SEPVAL.join(fnames)


def add_files(label, fnames):
    "Return string identifying the file(s)."

    if len(fnames) == 1:
        x = " is"
    else:
        x = "s are"

    return f" The {label}{x}:{clean_names(fnames)}\n"


# TODO: fix to deal with clipped/thresholded exposure maps
#
def print_output(outputs, cleanup=False):
    "Display the files that were created"

    if cleanup:
        files = outputs[1]
    else:
        files = outputs[0]

    created = ["", "The following files were created:", ""]

    try:
        created.append(add_files("clipped counts image",
                                 files["image_thresh"]))
    except KeyError:
        if cleanup:
            created.append(add_files("binned counts image", files["images"]))

    if not cleanup:
        created.append(add_files("binned counts image", files["images"]))

        try:
            created.append(add_files("particle background events file",
                                     files["blanksky"]))
            created.append(add_files("unsubtracted background counts image",
                                     files["unsubtracted_image"]))
            created.append(add_files("particle background counts image",
                                     files["particle_background"]))
        except KeyError:
            pass

        created.extend([add_files("aspect histogram", files["asphists"]),
                        add_files("instrument map", files["instmaps"])])

    try:
        created.append(add_files("observation FOV",
                                 files["fovs"]))
    except KeyError:
        pass

    try:
        created.append(add_files("clipped exposure map",
                                 files["expmap_thresh"]))
    except KeyError:
        if cleanup:
            created.append(add_files("exposure map", files["expmaps"]))

    try:
        created.append(add_files("PSF map",
                                 files["psfmaps"]))
    except KeyError:
        pass

    if not cleanup:
        created.append(add_files("exposure map", files["expmaps"]))

    created.append(add_files("exposure-corrected image", files["fluxmaps"]))

    for c in created:
        v1(c)


##################################
#
# Combine the steps
#
##################################

def run_fluximage_tasks(taskrunner, labelconv,
                        obs,
                        bkginfo,
                        chips,
                        asolobj,
                        outpath,
                        grid,
                        binsize,
                        enbands,
                        units,
                        thresh,
                        ecf=None,
                        tmpdir="/tmp/",
                        verbose=0,
                        random=0,
                        clobber=False,
                        cleanup=True,
                        parallel=False,
                        pathfrom=None
                        ):
    """Run the various stages.

    The routine returns the task name that indicates that the
    fluxed images are available.

    bkginfo is None or the tuple (methodname, methodparams,
    bkgevtfile).

    The random parameter is currently only used with the
    background subtraction task.

    Parameters
    ----------
    pathfrom : str or None, optional
        The location of the script (i.e. it's __file__ value) as this
        is used to find the lookup table,

    """

    pathfrom = __file__ if pathfrom is None else pathfrom
    lookup_table = run.get_lookup_table("fluximage", pathfrom=pathfrom)

    if units == 'default':
        normflag = 'no'
    elif units == 'area':
        normflag = 'yes'
    elif units == 'time':
        normflag = 'no'
    else:
        raise ValueError("Internal error: invalid setting " +
                         f"units={units}")

    want_psf = ecf is not None

    pixscale = utils.sky_to_arcsec(obs.instrument, binsize)

    asptask = make_asphist(taskrunner, labelconv,
                           obs,
                           asolobj,
                           chips,
                           pixscale,
                           outpath,
                           parallel=parallel,
                           tmpdir=tmpdir,
                           verbose=verbose,
                           clobber=clobber
                           )

    # Note: we have already created the FOV file to calculate the
    # grid, but instead of re-using that let's just create a
    # new version. Or do we just use the existing FOV file?
    #
    fovtask = make_fov(taskrunner, labelconv,
                       obs,
                       asolobj,
                       chips,
                       outpath,
                       parallel=parallel,
                       tmpdir=tmpdir,
                       verbose=verbose,
                       clobber=clobber
                       )

    imgtask = make_event_images(taskrunner, labelconv,
                                obs,
                                bkginfo,
                                asolobj.name,
                                grid,
                                enbands,
                                chips,
                                outpath,
                                lookup_table,
                                random=random,
                                tmpdir=tmpdir,
                                verbose=verbose,
                                clobber=clobber,
                                cleanup=cleanup
                                )

    imaptask = make_instrument_maps(taskrunner, labelconv, [asptask],
                                    obs,
                                    enbands,
                                    chips,
                                    units,
                                    outpath,
                                    binsize,
                                    parallel=parallel,
                                    tmpdir=tmpdir,
                                    verbose=verbose,
                                    clobber=clobber
                                    )

    emaptask = make_exposure_maps(taskrunner, labelconv, [imgtask, imaptask],
                                  obs,
                                  enbands,
                                  chips,
                                  outpath,
                                  lookup_table,
                                  normalize=normflag,
                                  hackunits=(units == 'time'),
                                  tmpdir=tmpdir,
                                  parallel=parallel,
                                  verbose=verbose,
                                  clobber=clobber,
                                  cleanup=cleanup
                                  )

    fluxtask = make_fluxed_images(taskrunner, labelconv,
                                  [imgtask, emaptask],
                                  enbands,
                                  obs.obsid,
                                  outpath,
                                  lookup_table,
                                  thresh=thresh,
                                  parallel=parallel,
                                  tmpdir=tmpdir,
                                  verbose=verbose,
                                  clobber=clobber,
                                  cleanup=cleanup
                                  )

    if not want_psf:
        return fluxtask

    pmaptask = make_psf_maps(taskrunner, labelconv, [fluxtask],
                             ecf,
                             obs,
                             enbands,
                             chips,
                             outpath,
                             lookup_table,
                             threshold=utils.thresh_is_set(thresh),
                             tmpdir=tmpdir,
                             parallel=parallel,
                             verbose=verbose,
                             clobber=clobber)

    return pmaptask


# End
