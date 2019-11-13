#
#  Copyright (C) 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2018
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

"""A wrapper around the cxcdm module.

The aim of this module is to work around a few corner cases in the
low-level cxcdm module (e.g. improve error messages and simplify a
few common operations).

The pycrates module should be used instead of this module whereaver
possible.

The API is not guaranteed to remain stable, so use at your own risk.
"""

import os
import sys
import time

from collections import namedtuple

import numpy as np
import cxcdm as dm

from ciao_contrib.logger_wrapper import initialize_module_logger

logger = initialize_module_logger("cxcdm_wrapper")
v1 = logger.verbose3
v3 = logger.verbose3
v5 = logger.verbose5

Record = namedtuple("Record", "name value unit comment")
Column = namedtuple("Column", "name pos type dims unit comment range")

__all__ = ["open_block_from_file", "close_block",
           "get_block_info",
           "get_block_info_from_file",
           "get_info_from_file",
           "get_keyword", "get_block_name", "convert_block_number",
           "get_obsfiles",
           "open_column",
           ]


def cleanval(val):
    """If val is "empty" then return None else val."""

    if str(val).strip() == "":
        return None
    else:
        return val


def open_block_from_file(filename):
    """Open the file, returning the block"""

    v5("Opening file {0}".format(filename))
    try:
        bl = tableOpen(filename)

    except IOError:
        v5("  -- not a table, try an image")

        try:
            bl = imageOpen(filename)

        except IOError as ie:
            v5("  -- not an image")
            raise IOError("Unable to open infile='{0}'\n  {1}".format(filename, str(ie)))

    return bl


def close_block(bl):
    """This used to work around a bug in the S-Lang module; should
    not be needed in Python but left in for old code."""

    v5("Closing block '{0}'".format(blockGetName(bl)))
    blockClose(bl)


def get_block_info(bl):
    """Returns a tuple with the block name and a dictionary containing
    information about the block.

    """

    blname = blockGetName(bl)
    bltype = blockGetType(bl)

    blinfo = {
        "name": blname,
        "number": blockGetNo(bl),
        }

    if bltype == dmIMAGE:
        di = imageGetDataDescriptor(bl)
        adims = getArrayDimensions(di)
        if adims is None:
            blinfo["type"] = "PRIMARY"

        else:
            blinfo["type"] = "IMAGE"
            blinfo["datatype"] = getDataType(di)
            blinfo["shape"] = adims

    elif bltype == dmTABLE:

        # assume a table with no columns is an attempt to read
        # an arbitrary ASCII file
        #
        nc = tableGetNoCols(bl)
        if nc == 0:
            blinfo["type"] = "EMPTY-TABLE"

        else:
            blinfo["type"] = "TABLE"
            blinfo["nrows"] = tableGetNoRows(bl)
            blinfo["columns"] = dict([(getName(c),
                                       Column(getName(c),
                                              p,
                                              getDataType(c),
                                              getArrayDimensions(c).tolist(),
                                              cleanval(getUnit(c)),
                                              cleanval(getDesc(c)),
                                              descriptorGetRange(c)
                                                       ))
                                      for (c, p) in \
                                          zip(tableOpenColumnList(bl),
                                              range(1, nc + 1))])

    else:
        blinfo["type"] = "UNKNOWN ({0})".format(bltype)

    # We convert from np.string_ to basic Python string since I have
    # seen some issues with the NumPy string type when sending empty
    # values to parallel processes using multiprocessing.
    #
    keyinfo = {"HDUNAME": Record("HDUNAME", blname, None, None)}
    for key in blockGetKeyList(bl):
        keyname = getName(key)
        keyval = getData(key)

        # keytype = getDataType(key)
        keycom = cleanval(getDesc(key))
        keyunit = cleanval(getUnit(key))
        keyinfo[keyname] = Record(keyname, keyval,
                                  comment=keycom, unit=keyunit)

    blinfo["records"] = keyinfo

    return (blname, blinfo)


def get_block_info_from_file(filename):
    """Return the tuple (blockname, blockinfo) for the
    "most-interesting" block in filename (which may include a block
    specifier).

    See get_info_from_file() for access to all blocks in a file.

    blockinfo is a dictionary with the following keys:

      name     - block name
      number   - block numner (starting from 1)
      type     - block type ("IMAGE", "TABLE" or "PRIMARY")
      records  - a dictionary of the block keywords where the values
                 are Record objects; some "structural" keywords will
                 not be included in this dictionary

    If the block is a TABLE then the following keys will also be
    present:

      nrows    - the number of rows
      columns  - a dictionary of Column objects listing the table columns;
                 the key is the column name

    If the block is an IMAGE then the following keys will also be
    present:

      datatype - a numpy data type
      shape    - a numpy array giving the image dimensions

    The Record object has attributes: name, value, unit and comment.
    The Column object has attributes: name, pos, type, dims, unit, comment, and range

    Both classes are created by the collections.namedtuple routine.

    """

    v3("Reading block information from {}".format(filename))
    bl = open_block_from_file(filename)
    try:
        out = get_block_info(bl)
    finally:
        close_block(bl)

    return out


def get_info_from_file(filename):
    """Return an array of (blockname, blockinfo) tuples for all the
    blocks in the file. See the description of get_block_info_from_file
    for a description of the blockinfo value.

    """

    ds = datasetOpen(filename)
    if ds is None:
        raise IOError("Unable to open file '{0}'\n  ".format(
                filename, getErrorMessage()))

    try:
        nblocks = datasetGetNoBlocks(ds)
        v5("File {0} has {1} blocks".format(filename, nblocks))

        out = []
        for i in range(1, nblocks + 1):
            try:
                bl = datasetMoveToBlock(ds, i)

            except IOError:
                datasetClose(ds)
                raise IOError("Unable to move to block number {0} in {1}".format(
                    i, filename))

            # Should we close the block?
            out.append(get_block_info(bl))

    finally:
        datasetClose(ds)

    return out


def get_keyword(bl, keyword):
    """Returns the value of the keyword in the block.

    Parameters
    ----------
    bl : dmBlock
        The block to search.
    keyword : str
        The name of the keyword (a case insensitive search is used).

    Returns
    -------
    value
        The value of the key (string, int, or float).

    Raises
    ------
    ValueError
        If the keyword does not exist in the block.

    Notes
    -----
    String values are returned as strings (not numpy.string_ or
    numpy.bytes_); this is a breaking change in CIAO 4.9.
    """

    try:
        dd = keyOpen(bl, keyword)
    except ValueError:
        # Rewrite the error message slightly
        raise ValueError("No {} keyword found in input file.".format(keyword))

    return getData(dd)


def get_block_name(filename, blnum):
    """Return the file name including block name.

    Parameters
    ----------
    filename : str
        The name of the file. It is assumed that there is no
        CXCDM virtual-file specification, but this is not enforced.
    blnum : int
        The block number, using the CXCDM scheme, where the first
        block is numbered 1.

    Returns
    -------
    vfs : str
        The name of the block is appended to the file name, using the
        CXCDM virtual file specification - e.g. "tbl.fits[ENERGY]".

    Raises
    ------
    IOError
        If the file can not be opened, or the block does not exist.
    """

    v5("Looking for name of block {} in '{}'".format(blnum, filename))
    ds = datasetOpen(filename)

    try:
        bl = datasetMoveToBlock(ds, blnum)
    except IOError:
        datasetClose(ds)
        raise IOError("Unable to move to block number {} of '{}'".format(blnum, filename))

    try:
        name = blockGetName(bl)
    finally:
        datasetClose(ds)

    v5(" -> block name='{}'".format(name))
    return "{}[{}]".format(filename, name)


def convert_block_number(filename, system="cxcdm", insystem="cxcdm"):
    """Convert a file name using block name/number syntax.

    Given a file name that may include a CXCDM or CFITSIO style
    block number (specified by the insystem parameter), convert it to
    a new system given by the system parameter.

    Parameters
    ----------
    filename : str
        The file name to process. It is assumed to end in a block
        specified using "[xxx]" format, otherwise the return value
        is set to filename. See insystem for the formats supported
        for the block specifier.
    system : {'none', 'name', 'cxcdm', 'cfitsio'}
        The block-naming system to use for the output file name.
    insystem : {'cxcdm', 'cfitsio'}
        The block-naming scheme used by filename.

    Returns
    -------
    name : str
        The file name including the block specified (unless filename
        does not end in "[xxx]" or system='none'). If insystem is
        the same as system then the input file name is returned
        with no change.

    Notes
    -----
    The block formats supported are::

    ======== =============================================
    Name     Description
    ======== =============================================
    none     Removes the block specifier
    name     Replace with the block name
    cxcdm    Use the CXCDM numbering scheme (starts at 1)
    cfitsio  Use the CFITSIO scheme (starts at 0).
    ======== =============================================

    Some conversions require opening the file and reading its
    contents.

    The conversion only looks at the specifier in the last CXCDM
    virtual-file specifier, so filename should not contain any
    other specfiers, such as filters, column restrictions, or
    image-binning parameters.
    """

    systems = ["none", "name", "cxcdm", "cfitsio"]
    insystems = systems[2:]
    if system not in systems:
        raise ValueError("Unrecognized system={0}, should be one of:\n    {1}".format(system, " ".join(systems)))

    if insystem not in insystems:
        raise ValueError("Unrecognized insystem={0}, should be one of:\n    {1}".format(insystem, " ".join(insystems)))

    if filename == "" or filename[-1] != ']' or system == insystem:
        return filename

    lval = filename.rfind("[")
    if lval == -1:
        return filename

    head = filename[:lval]
    oval = filename[lval + 1:-1]
    try:
        nval = int(oval)
    except ValueError:
        raise ValueError("Expected [<integer>] but found [{0}] in:\n{1}\n".format(oval, filename))

    # Ensure nval is in the CXCDM system.
    if insystem == "cfitsio":
        nval = nval + 1

    if system == "none":
        v5("Stripping off block number from '{0}'".format(filename))
        return head

    elif system == "cfitsio":
        v5("Converting block number to CFITSIO format in '{0}'".format(filename))
        return "{0}[{1}]".format(head, nval - 1)

    elif system == "cxcdm":
        v5("Converting block number to CXCDM format in '{0}'".format(filename))
        return "{0}[{1}]".format(head, nval)

    else:
        v5("Replacing block number by name in '{0}'".format(filename))
        return get_block_name(head, nval)


def get_obsfiles(filename, filetypes, exist=True):
    """Return full paths to Chandra observation files.

    Get the full paths to the Chandra-observation filetypes
    listed in filename (which is assumed to be a Chandra event
    file but need not be as all that is looked for are the *FILE
    keywords in its header).

    Parameters
    ----------
    filename : str
        The file to use (it is searched for *FILE keywords and is
        assumed to follow the Chandra/CIAO rules). Event files
        contain these keywords, but derived products, such as
        images, can also contain the necessary keywords. The location
        of this file is used to determine the location of the
        files.
    filetypes : list
        The array of file types which are to be returned. The names
        are case insensitive, and give the *FILE keywords to search
        for (that is, filetypes=['asol', 'bpix'] will cause the
        ASOLFILE and BPIXFILE keywords to be used).
    exist : bool, optional
        Should a check be made to see if the files exist (the check
        is just that the file exists, not if it can be read or has
        the correct format)?

    Returns
    -------
    filenames : dict
        The keys of the dictionary are the filetypes elements, and
        the values are arrays of file names (an array is used to
        support keywords such as ASOLFILE which can contain multiple
        files). The file names are returned with an absolute path,
        and the keys match the case given in filetypes.

    Raises
    ------
    ValueError
        If a keyword is not found in filename.
    IOError
        This is raised if exist is True and any of the files can
        not be found.

    Notes
    -----
    There is no attempt to search for the files - e.g. to look in
    ../primary or ../secondary relative to filename - if they can not
    be found in the same directory as filename.

    """

    bpath = os.path.dirname(os.path.abspath(filename))
    bl = open_block_from_file(filename)
    out = {}
    try:

        for ftype in filetypes:
            key = "{}FILE".format(ftype.upper())
            val = get_keyword(bl, key)

            # Assuming that a simple split-on-comma approach will
            # work here. An alternative would be to use stk.build.
            #
            fs = [os.path.normpath(os.path.join(bpath, v))
                  for v in val.split(",")]

            if exist:
                for f in fs:
                    if not os.path.exists(f):
                        raise IOError("Unable to find {} from {}: {}".format(key, filename, f))

            out[ftype] = fs

    finally:
        blockClose(bl)

    return out


# In CIAO 4.8 cxcdm does not raise a useful error if colname
# is invalid. Looks like this is true in 4.9 as well.
#
def open_column(bl, colname, filename=None):
    """Open the given column.

    This is only needed because it adds nicer error handling to
    tableOpenColumn. If filename is not None then it is used in
    debug/error messages.

    Parameters
    ----------
    bl
        The table block to use.
    colname : str
        The name of the column (a case insensitive match is made)
    filename : str, optional
        If given, it is used in the logging output for the module
        and in any error message. It has no influence on the value
        returned.

    Returns
    -------
    dd
        The column data descriptor.

    Raises
    ------
    IOError
        If the column does not exist in the table.

    """

    try:
        if filename is None:
            msg = "Opening column {}".format(colname)
        else:
            msg = "Opening column {} in {}".format(colname, filename)

        v3(msg)
        return tableOpenColumn(bl, colname)

    except RuntimeError:
        if filename is None:
            msg = "There is no column called {}".format(colname)
        else:
            msg = "There is no column called {} in {}".format(colname, filename)

        raise IOError(msg)


### clear_acis_status_bits: START
#
# The following routines are used by clear_acis_status_bits
# and chandra_repro. They are not exported by default.
#

# Clear bits 1-5,
#            14-16
#            17-20, 23
#
# The bits are numbered from the right, starting from 0,
# so the above is - where x means pass through -
#
#    xxxxxxxx 0xx00000 00xxxxxx xx00000x
#
# The width=32 argument on binary_repr is to ensure that there
# is no overflow on 32-bit machines.
_cbits = np.uint8([0b11111111, 0b01100000, 0b00111111, 0b11000001])
_cbits_str = np.binary_repr(_cbits[3] | _cbits[2] << 8 |
                            _cbits[1] << 16 | _cbits[0] << 24,
                            width=32)


def _clear_status_column(dd, nrows):
    """dd is a data descriptor for a 32-bit STATUS column.
    We clear the bits 1-5, 14-20, and 23 (set to 0).

    We start by doing a per-row loop to see how slow that
    runs (the idea is to avoid reading in too much of the file
    in at once, if that is possible with this interface).

    """

    # Would like to chunk up into the optimal buffer size
    # but I do not know how to get that information from
    # the cxcdm API, or whether it actually makes a difference.
    #
    # However, in CIAO 4.4 getData leaks memory per call so
    # we read in all the data at once to reduce this memory
    # loss. Not sure if this is still valid in CIAO 4.9
    #
    # rstep = 1
    rstep = nrows
    for i in range(1, nrows + 1, rstep):
        idata = getData(dd, i, rstep)
        ndata = np.bitwise_and(_cbits, idata)
        setData(dd, ndata, i)


def clear_acis_status_bits(fname, toolname=None):
    """Clear bits 1-5, 14-20, and 23 of the STATUS
    column of fname. The edits are made in place.

    The CLSTBITS keyword will be added/modified to indicate
    the bit-mask used.

    toolname, if not None, is the name of the tool written to the
    HISTORY header,
    """

    timeVal = time.strftime("%Y-%m-%dT%H:%M:%S")
    bl = tableOpen(fname, update=True)
    try:
        col = open_column(bl, 'STATUS', filename=fname)
    except IOError:
        tableClose(bl)
        raise

    nrows = tableGetNoRows(bl)
    _clear_status_column(col, nrows)

    # should perhaps just use str(_cbits_str)
    keyWrite(bl, "CLSTBITS", "{}".format(_cbits_str),
             desc="0 means clear STATUS bit")

    # Add a note to the history records; we do not try to replicate
    # the CXCDM history block as we have no parameter file.
    #
    # This could be updated to use the CIAO-4.11 history functionality,
    # but that is more Crates than cxcdm based.
    #
    if toolname is not None:
        blockWriteComment(bl, "HISTORY", "TOOL: {} at {}".format(toolname,
                                                                 timeVal))
        blockWriteComment(bl, "HISTORY", "  infile={}".format(fname))

    tableClose(bl)


### clear_acis_status_bits: END


# Manually wram cxcdm.dmGetData to handle string conversion logic.
#
def getData(dd, rowno=None, nrows=None):
    """Return the data for the descriptor.

    Calls the cxcdm dmGetData routine on the descriptor. String
    values are explicitly converted to a Python string, rather than
    a numpy string (or bytes) where appropriate.

    Notes
    -----
    If rowno is None then nrows is ignored.
    """

    args = [dd]
    if rowno is not None:
        args.append(rowno)
        if nrows is not None:
            args.append(nrows)

    return dm.dmGetData(*args)


funcnames = [
    # "getErrorMessage",

    "blockGetType",
    "blockGetDataset",
    "blockGetName",
    "blockGetNoSubspaceCpts",
    "blockSetSubspaceCpt",
    # "blockGetSubspace",
    "blockGetKeyList",
    "blockGetNo",
    # "blockGetNoKeys",
    # "blockMoveToKeyNo",
    # "blockAdvanceKeys",
    "blockGetKey",
    "blockMoveToKey",
    "blockClose",
    "blockWriteComment",

    "getArrayDim",
    "getArrayDimensions",
    "getArraySize",
    "getName",
    "getElementDim",
    "getCpt",
    # "getData",  have a manual wrapper for this
    "getDesc",
    "getUnit",
    "getDataType",
    # "getDataTypeName",

    "descriptorGetType",
    "descriptorGetRange",

    "arrayGetNoAxisGroups",
    "arrayGetAxisGroup",

    "keyOpen",
    "keyWrite",

    "tableOpen",
    "tableClose",
    "tableOpenColumn",
    "tableOpenColumnList",
    "tableGetNoRows",
    "tableGetNoCols",

    "imageOpen",
    "imageClose",
    "imageGetDataDescriptor",

    "datasetOpen",
    "datasetMoveToBlock",
    "datasetClose",
    "datasetGetName",
    "datasetGetNoBlocks",
    "datasetGetCurrentBlockNo",
    "datasetNextBlock",

    "setData",

    "subspaceColGet",
    ]

constants = [
    # "dmBOOL",
    # "dmDOUBLE",
    # "dmLONG",
    # "dmTEXT",

    "dmTABLE",
    "dmIMAGE",
    # "dmIMAGEDATA",
    ]

for funcname in funcnames:
    setattr(sys.modules[__name__], funcname,
            getattr(dm, "dm" + funcname[0].upper() + funcname[1:]))

for const in constants:
    setattr(sys.modules[__name__], const, getattr(dm, const))

__all__ = tuple(__all__ + funcnames + constants)
