#
#  Copyright (C) 2010, 2011, 2012, 2014, 2015, 2018, 2019
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

import os
import subprocess as sbp
import tempfile

import numpy as np

import paramio

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
    "fix_bunit"
    # TODO: skyfov
    )

lgr = lw.initialize_module_logger('_tools.run')
v2 = lgr.verbose2
v3 = lgr.verbose3


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

    args.append("clobber={}".format(clstr))
    args.append("verbose={}".format(verbose))


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
        print("*** Internal warning: dmcopy clobber={}".format(clobber))
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
        ["infile=" + infile,
         "columns=sky",
         "round=yes",
         "verbose={}".format(verbose),
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
    if lookupTab is not None:
        args.append("lookupTab=" + lookupTab)

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
            "weight={}".format(weight1),
            "weight2={}".format(weight2),
            "mode=h"]
    if lookupTab is not None:
        args.append("lookupTab=" + lookupTab)

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
    """

    instk = make_stackfile(infiles, dir=tmpdir, suffix=".dmimgcalc")
    try:
        args = ["infile=@" + instk.name,
                "infile2=",
                "outfile=" + outfile,
                "op=imgout=" + op,
                "mode=h"]
        if lookupTab is not None:
            args.append("lookupTab=" + lookupTab)

        add_defargs(args, clobber, verbose)
        punlearn("dmimgcalc")
        run("dmimgcalc", args)
    finally:
        instk.close()


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
    hopefully-safe chunk size. There is however a limit: 100**2,
    just because I can't be bothered with recursion here. If we
    are trying to add this many files we are probably going to
    have problems anyway!

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


# End
