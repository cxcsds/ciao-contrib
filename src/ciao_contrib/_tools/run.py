#
#  Copyright (C) 2010, 2011, 2012, 2014, 2015, 2018, 2019, 2021, 2022
#  Smithsonian Astrophysical Observatory
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
Run some CIAO tasks. The advantage over ciao_contrib.runtool is that
the screen output is displayed to the user whilst the tool is
running rather than being returned as a single string once the tool
has finished. The disadvantages include:

  - restricted coverage

  - lack of conversion between Python and CIAO "types"

  - no protection against multiple copies of the tool accessing
    the same parameter file and leading to conflicts

Some of the "short" tools (i.e. those that run quickly) are being
moved to using the runtool module.

"""

import functools
import os
import subprocess as sbp
import tempfile

import numpy as np

import cxcdm
import paramio
from region import CXCRegion
import stk

import ciao_contrib.logger_wrapper as lw

from ciao_contrib.stacklib import make_stackfile
import ciao_contrib.runtool as rt
import ciao_contrib._tools.fileio as fileio


__all__ = (
    "run",
    "punlearn",
    "dmcopy",
    "update_column_range",
    "dmmerge",
    "dmimgcalc2", "dmimgcalc", "dmimgcalc_add",
    "dmkeypar",
    "dmhedit_key", "dmhedit_file",
    "get_lookup_table",
    "fix_bunit",
    "make_fov",
    "combined_fovs"
    )

lgr = lw.initialize_module_logger('_tools.run')
v2 = lgr.verbose2
v3 = lgr.verbose3
v4 = lgr.verbose4


def run(tname, targs):
    """Run the tool (tname) with arguments (targs). Raises an
    IOError on failure. Logs the command and arguments at the DEBUG level.
    """

    v2(">> Running {}".format(tname))
    v2(">>   args: {}".format(targs))

    args = [tname]
    args.extend(targs)
    rval = sbp.call(args)
    if rval != 0:
        argstr = " ".join(targs)
        raise IOError("Unable to run {} with arguments: {}".format(tname, argstr))


def add_defargs(args, clobber, verbose):
    "Add clobber/verbose as arguments. args is modified *in place*."

    if clobber:
        clstr = "yes"
    else:
        clstr = "no"

    args.append(f"clobber={clstr}")
    args.append(f"verbose={verbose}")


def add_lookupTab(args, lookupTab):
    """Add lookupTab if set. args is modified *in place*."""

    if lookupTab is None:
        return

    args.append(f"lookupTab={lookupTab}")


def punlearn(tname):
    """Call punlearn on the given tool name (tname).

    This used to use the paramio command-line tool but was
    changed, Jan 2014, to use the paramio module instead.
    """

    # punlearn will create an error message of its own but create one
    # here too so that it is reported as an actual error.
    #
    # Used to use the punlearn command-line tool, but switching to the
    # paramio module to try and avoid conflicts if the FTOOLS
    # punlearn is in the path
    #
    # run("punlearn", [tname])
    paramio.punlearn(tname)


def dmcopy(infile, outfile,
           clobber=False,
           option=None,
           verbose=0):
    "Run dmcopy"

    # Note: trying to move away from passing around a string
    # instead of a boolean; can probably remove this now.
    if clobber in ["yes", "no"]:
        print(f"*** Internal warning: dmcopy clobber={clobber}")
        clobber = clobber == "yes"

    v3("Copying <{}> to <{}>".format(infile, outfile))
    punlearn("dmcopy")
    args = ["infile=" + infile,
            "outfile=" + outfile,
            "mode=h"]
    if option is not None:
        args.append("option=" + option)
    add_defargs(args, clobber, verbose)
    run("dmcopy", args)


# TODO: Is this still needed in CIAO 4.6?
def update_column_range(infile, verbose=0):
    """Runs update_column_range on the sky column of
    infile with round set to yes.
    """

    punlearn('update_column_range')
    run('update_column_range',
        [f"infile={infile}",
         "columns=sky",
         "round=yes",
         f"verbose={verbose}",
         "mode=h"])


def dmmerge(infile, outfile,
            clobber=False,
            verbose=0,
            skyupdate=False,
            lookupTab=None,
            ):
    """Run dmmerge. If skyupdate is True then also runs
    update_column_range on the sky column of outfile
    with round set to yes). If lookupTab is not None then
    use it as the lookupTab parameter value in the call.
    """

    args = ['infile=' + infile,
            'outfile=' + outfile]
    add_lookupTab(args, lookupTab)

    add_defargs(args, clobber, verbose)
    punlearn('dmmerge')
    run('dmmerge', args)

    if skyupdate:
        update_column_range(outfile)


def dmimgcalc2(infile1, infile2, outfile, op,
               verbose=0,
               clobber=False,
               lookupTab=None,
               weight1=1,
               weight2=1):
    """Run dmimgcalc with infile and infile2 parameters set, so that
    op is add/div/.... rather than imgout=...

    If lookupTab is not None it is passed to dmimgcalc.
    """

    args = ["infile=" + infile1,
            "infile2=" + infile2,
            "outfile=" + outfile,
            "operation=" + op,
            f"weight={weight1}",
            f"weight2={weight2}",
            "mode=h"]
    add_lookupTab(args, lookupTab)

    add_defargs(args, clobber, verbose)
    punlearn("dmimgcalc")
    run("dmimgcalc", args)


def dmimgcalc(infiles, outfile, op,
              verbose=0,
              clobber=False,
              lookupTab=None,
              tmpdir="/tmp/"):
    """Run dmimgcalc with infile set to infiles (input is an array)
    creating outfile. The imgout parameter is set to the op
    argument, so op should be "img1+img2" rather than "imgout=img1+img2".

    If lookupTab is not None it is passed to dmimgcalc.

    As of CIAO 4.15, we can now set the operation argument to
    dmimgcalc as a stack, which will help cases when the op string is
    >~ 1000 characters. We therefore switch to this option when op
    is "too long" (and do not do so for shorter operations to reduce
    the number of changes in existing code).

    """

    # Do we want to use a stack for operation? The belief is that we
    # want to do when len('imgout=' + op) > 1023 (or 1024) but we
    # don't know the exact length, so we just use 990  (as some
    # testing I did suggests the stack library has problems with lines
    # of 1000 characters).
    #
    if len(op) > 990:
        v3(f"run.dmimgcalc sent {len(op)} chars for op - using stack")
        opstk = tempfile.NamedTemporaryFile(mode='w+', dir=tmpdir,
                                            suffix=".op", delete=True)
        opstk.write("imgout=")
        opstk.write(op)
        opstk.flush()
        opval = f"@{opstk.name}"
    else:
        opval = f"imgout={op}"
        opstk = None

    instk = make_stackfile(infiles, dir=tmpdir, suffix=".dmimgcalc")
    try:
        args = [f"infile=@{instk.name}",
                "infile2=",
                f"outfile={outfile}",
                f"op={opval}",
                "mode=h"]
        add_lookupTab(args, lookupTab)

        add_defargs(args, clobber, verbose)
        punlearn("dmimgcalc")
        run("dmimgcalc", args)
    finally:
        instk.close()
        if opstk is not None:
            opstk.close()


def dmimgcalc_add(infiles, outfile,
                  verbose=0,
                  clobber=False,
                  lookupTab=None,
                  tmpdir="/tmp/",
                  nchunk=100):
    """Add up all the images in infiles (an array) to create outfile,
    using dmimgcalc.

    If lookupTab is not None it is passed to dmimgcalc.

    To avoid problems with the command argument getting too long we
    chunk the data up into nchunk files at a maximum, and sum up the
    individual chunks. It's not obvious when it's a problem but we
    have had crashes when ~160 files have been combined even though I
    can combine a larger number of files, which suggests that it's the
    length of the total command string - see #481. So pick a
    hopefully-safe chunk size. There is however a limit: 100**2, just
    because I can't be bothered with recursion here. If we are trying
    to add this many files we are probably going to have problems
    anyway! This can be ameliorated in CIAO 4.15 and later by taking
    advantage of the stack support for the operation parameter to
    dmimgcalc, but we do not try here as we still have this workaround
    (and we may benefit from not loading all the data in at once).

    """

    nfiles = len(infiles)
    if nfiles <= nchunk:
        v3(f"Summing up {nfiles} files: {outfile}")
        inames = [f"img{i}" for i in range(1, nfiles + 1)]
        op = "+".join(inames)

        dmimgcalc(infiles, outfile, op,
                  verbose=verbose,
                  clobber=clobber,
                  tmpdir=tmpdir,
                  lookupTab=lookupTab)
        return

    # Try to use an equal number of files per chunk
    chunking = int(np.ceil(nfiles / nchunk))

    v3(f"Summing up {nfiles} files into {chunking} chunks: {outfile}")

    # We could recurse, but let's error out if we have too-many
    # files.
    if chunking >= nchunk:
        raise ValueError(f"Sent too many images to add: {nfiles}")

    start = 0
    tmpfiles = []
    while start < nfiles:
        filelist = infiles[start:start + nchunk]
        v3(f" - summing chunk of {len(filelist)} files")

        tmpfile = tempfile.NamedTemporaryFile(dir=tmpdir, suffix='.img')
        tmpfiles.append(tmpfile)
        dmimgcalc_add(filelist, tmpfile.name,
                      verbose=verbose, clobber=True,
                      lookupTab=lookupTab, tmpdir=tmpdir,
                      nchunk=nchunk)

        start += nchunk

    # Now add up the chunks
    v3(f"-> summing up the chunks: {outfile}")
    dmimgcalc_add([t.name for t in tmpfiles], outfile,
                  verbose=verbose, clobber=clobber,
                  lookupTab=lookupTab, tmpdir=tmpdir,
                  nchunk=nchunk)


def dmkeypar(infile, key, rtype='string'):
    """Run dmkeypar and return the value; errors out on failure.

    The rtype argument determines the type of the return value
    and can be one of 'string', 'bool', 'int', and 'float'.

    Note that the bool type returns True or False, and not 1 or 0.
    """

    funcs = {
        'string': paramio.pgetstr,
        'bool':   paramio.pgetb,
        'int':    paramio.pgeti,
        'float':  paramio.pgetd,
        }

    try:
        func = funcs[rtype]
    except KeyError:
        raise ValueError("Invalid rtype argument '{}'".format(rtype))

    run('dmkeypar', ["infile=" + infile,
                     "keyword=" + key,
                     "echo=no"])

    rval = func('dmkeypar', 'value')
    if rtype == 'bool':
        return (rval == 1)
    else:
        return rval


def dmhedit_key(infile, key, value, comment=None, unit=None, verbose=0):
    """Add the key/value to the header of infile.
    If unit or comment are not None then they are also set.

    Not convinced I have the quoting rules set up if the value
    contains spaces or / characters.

    Uses the runtool module version of dmhedit.
    """

    # We still use stringify rather than the type-conversion
    # implicit in runtool since this is a specialized case.
    #
    def stringify(v):
        v = str(v)
        if v.find('/') == -1:
            return v
        else:
            return "'{}'".format(v)

    dmh = rt.make_tool("dmhedit")
    if comment is not None:
        dmh.comment = stringify(comment)
    if unit is not None:
        dmh.unit = stringify(unit)

    out = dmh(infile=infile, operation="add",
              key=key, value=stringify(value),
              verbose=verbose)
    if out is not None:
        print(out)


def dmhedit_file(infile, filelist, verbose=0):
    """Run dmhedit on infile with the file in filelist.

    Uses the runtool module version of dmhedit.
    """

    dmh = rt.make_tool("dmhedit")
    out = dmh(infile=infile,
              filelist=filelist,
              verbose=verbose)
    if out is not None:
        print(out)


def get_lookup_table(toolname, pathfrom=None):
    """Return the name of the file to use as the lookupTable parameter of
    reproject_image and dmimgcalc. We look for
       data/<toolname>_header_lookup.txt
    in:
        <dir>/../data/
        <dir>/           [for testing / conda]
        $ASCDS_CONTRIB/  [optional, non-conda build]

    otherwise we default to $ASCDS_CALIB/dmmerge_header_lookup.txt.

    If pathfrom is None then the value of <dir> is set to the
    location of this module, which is unlikely to work. It is
    strongly suggested that pathfrom is set to __file__ when
    called from the script, so that <dir> becomes the
    location of the script.

    Ideally this would use importlib.resources or importlib.metadata
    but we're not there yet.

    """

    if pathfrom is None:
        fname = __file__
    else:
        fname = pathfrom
    dirpath = os.path.dirname(os.path.realpath(fname))
    fname = f"{toolname}_header_lookup.txt"

    v3(f"Looking for the lookup table for: {toolname}")

    # The assumption is that the first of these is going to match
    # most use cases (conda and non-conda builds).
    #
    infiles = [dirpath + "/../data/" + fname,
               dirpath + "/" + fname]

    # The conda build does not have ASCDS_CONTRIB, but
    # does have ASCDS_CALIB. We do not error out on the missing
    # environment variable, but on whether we find the file or not.
    #
    try:
        infiles.append(os.getenv("ASCDS_CONTRIB") + "/data/" + fname)
    except TypeError:
        pass

    try:
        infiles.append(os.getenv("ASCDS_CALIB") + "/dmmerge_header_lookup.txt")
    except TypeError:
        pass

    for f in infiles:
        f = os.path.normpath(f)
        v3(f"Looking for: {f}")
        if os.path.exists(f):
            return f

    raise IOError("Unable to find the merging rules " +
                  f"for {toolname} in\n{infiles}")


def fix_bunit(infile, outfile, verbose=0):
    """Does the BUNIT keyword need fixing?

    Crates/DM has an issue when the BUNIT field is not copied over
    to the output. This routine checks if the BUNIT field differs
    between the two files and, if it does, copies it over to the
    output file.

    Parameters
    ----------
    infile : str
        The input file.
    outfile : str
        The output file.
    verbose : int, optional
        The verbose setting.

    Notes
    -----
    As part of the BUNIT bug, it looks like the BUNIT setting is not
    "lost" but applied to the first coordinate system of the image.
    This routine does not attempt to fix this, but probably should.
    """

    bunit = fileio.get_image_units(infile)
    tunit = fileio.get_image_units(outfile)
    if bunit != tunit:
        v3(f"BUNIT check: was {tunit} but expect {bunit} in {outfile}")
        dmhedit_key(outfile, 'BUNIT', bunit, verbose=verbose)


def get_content(infile):
    """Return the CONTENT keyword of the file.

    Parameters
    ----------
    infile : str
        The input file. It must contain a CONTENT keyword.

    """

    v4(f"Checking CONTENT keyword of {infile}")
    bl = cxcdm.dmBlockOpen(infile, update=False)
    try:
        keys = cxcdm.dmKeyRead(bl, 'CONTENT')
        content = keys[1].decode('ascii')
        return content
    finally:
        cxcdm.dmBlockClose(bl)


def make_fov(evtfile, asolfiles, msk, outfile):
    """Create the FOV file (FITS format).

    Parameters
    ----------
    evtfile : str
        The event file to use.
    asolfiles : str
        The aspect solution, or solutions. When multiple files
        separate them with a ','. The aspect solution files must
        have the same CONTENT keyword.
    msk : str
        The mask file
    outfile : str
        The output file. It will be over-written if it already
        exists.

    Notes
    -----
    The skyfov method depends on the type of the aspect solution,
    as given by the CONTENT type:

        ASPSOL (pre DS 10.8.3)  - use method=minmax
        ASPSOLOBI               - use method=convexhull

    """

    afiles = stk.build(asolfiles)
    contents = set([get_content(f) for f in afiles])
    if len(contents) != 1:
        emsg = f"Multiple types of aspect solution found: " + \
            f"{', '.join(contents)}\n  {asolfiles}"
        raise OSError(emsg)

    content = contents.pop()
    if content == 'ASPSOLOBI':
        method = 'convexhull'
    elif content in ['ASPSOL', 'ASPSOL3']:
        method = 'minmax'
    else:
        raise OSError(f"Invalid CONTENT={content} in aspect solution: {asolfiles}")

    v3(f"skyfov: CONTENT={content}  method={method} -> {outfile}")

    skyfov = rt.make_tool('skyfov')
    skyfov.punlearn()
    skyfov(infile=evtfile,
           outfile=outfile,
           aspect=asolfiles,  # assume not so long we need a stack file
           mskfile=msk,
           kernel="FITS",
           method=method,
           clobber=True)


def combined_fovs(fovs, outfile, fits=True, clobber=True):
    """Create the combined FOV.

    This loses the CCD_ID column.

    Notes
    -----
    The WCS transform is copied if it is attached to the EQPOS
    column and is the same (at least as shown by the MATRIX
    representation) in all files.

    """

    v3(f"Combining FOV files: {outfile} from {len(fovs)} FOVs")

    # Read in the files to extract the WCS mapping. This also
    # checks the files exist, and gives a nicer error than
    # CXCRegion() does if the file does not exist.
    #
    # Some of the checking is a bit OTT for FOV files, but let's
    # try to be thorough.
    #
    trans_name = None
    trans_unit = None
    trans_cpt0 = None
    trans_cpt1 = None
    trans_type = None
    trans_vals = None
    trans_pars = None
    wcs = True
    for f in fovs:
        v3(f'Checking FOV for EQPOS transform: {f}')
        try:
            bl = cxcdm.dmBlockOpen(f, update=False)
        except OSError as oe:
            raise OSError(f"Unable to find FOV file: {f}") from oe

        try:
            # Do we have a POS column?
            try:
                pos = cxcdm.dmTableOpenColumn(bl, 'POS')
            except RuntimeError:
                v3('No POS column so no WCS')
                wcs = False
                break

            # Do we have transform info? For now assume only a single
            # coordinate transform is attached to POS.
            #
            ncoord = cxcdm.dmDescriptorGetNoCoords(pos)
            v3(f'Number of coords attached to POS: {ncoord}')
            if ncoord > 1:
                v2(f'WARNING: {f} has multiple coordinates attached to POS!')

            if ncoord != 1:
                wcs = False
                break

            dd = cxcdm.dmDescriptorGetCoord(pos)
            tr_name = cxcdm.dmGetName(dd)
            tr_unit = cxcdm.dmGetUnit(dd)
            tr_type = cxcdm.dmCoordGetTransformType(dd)
            tr_vals = cxcdm.dmCoordGetTransform(dd)
            tr_pars = cxcdm.dmCoordGetParams(dd)

            # unlike the other calls this will error out if the
            # transform is not 2D, but let's live with that.
            #
            tr_cpt0 = cxcdm.dmGetCptName(dd, 1)
            tr_cpt1 = cxcdm.dmGetCptName(dd, 2)

            if trans_name is None:
                v3('First FOV file, so copying WCS data')
                trans_name = tr_name
                trans_unit = tr_unit
                trans_cpt0 = tr_cpt0
                trans_cpt1 = tr_cpt1
                trans_type = tr_type
                trans_vals = tr_vals
                trans_pars = tr_pars
                continue

            # Check for equal transorms. Technically the name does not
            # have to match.
            #
            v3('Checking wether WCS info matches')
            if (trans_name != tr_name) or \
               (trans_unit != tr_unit) or \
               (trans_type != tr_type) or \
               (trans_cpt0 != tr_cpt0) or \
               (trans_cpt1 != tr_cpt1) or \
               not np.all(trans_vals[0] == tr_vals[0]) or \
               not np.all(trans_vals[1] == tr_vals[1]) or \
               not np.all(trans_vals[2] == tr_vals[2]) or \
               not np.all(trans_pars == tr_pars):
                v3(f'Note: WCS does not match {f} compared to {fovs[0]}')
                v4(f'Name: {trans_name} {tr_name}')
                v4(f'Cpts: {trans_cpt0},{trans_cpt1} {tr_cpt0},{tr_cpt1}')
                v4(f'Unit: {trans_unit} {tr_unit}')
                v4(f'Type: {trans_type} {tr_type}')
                v4(f'Vals: {trans_vals} {tr_vals}')
                v4(f'Pars: {trans_pars} {tr_pars}')
                wcs = False

        finally:
            v3(f'Closing check of FOV: {f}')
            cxcdm.dmBlockClose(bl)

    shapes = [CXCRegion(f) for f in fovs]
    combined = functools.reduce(lambda x, y: x + y, shapes)
    combined.write(outfile, fits=fits, clobber=clobber)

    if not fits:
        return

    # For FITS files we change HDUCLAS2/CONTENT from REGION to FOV
    # (CIAO 4.14), and also add in the WCS transform if all files
    # had the same transform.
    #
    v3(f"Adjusting HDUCLAS2/CONTENT keywords and EQPOS column of {outfile}")
    bl = cxcdm.dmBlockOpen(outfile, update=True)
    try:
        v3("-> HDUCLAS2/CONTENT")
        cxcdm.dmKeyWrite(bl, 'HDUCLAS2', 'FOV')
        cxcdm.dmKeyWrite(bl, 'CONTENT', 'FOV')

        pos = None
        if wcs:
            try:
                pos = cxcdm.dmTableOpenColumn(bl, 'POS')
            except RuntimeError:
                # In CIAO 4.14 the error is just an empty RutimeError.
                # We could error out here but let's just skip the WCS
                # (which should not be possible).
                #
                v3(f"WARNING: {outfile} does not contain a POS column when it should")
                pos = None

        # Ugly code to avoid too-much nesting
        if pos is not None:
            v3("-> WCS transform")
            cxcdm.dmCoordCreate(pos, 'EQPOS', trans_unit,
                                [trans_cpt0, trans_cpt1],
                                trans_type[0], trans_vals[0], trans_vals[1],
                                trans_vals[2], trans_pars)

    finally:
        cxcdm.dmBlockClose(bl)

# End
