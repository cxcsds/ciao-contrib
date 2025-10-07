#
#  Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2018, 2019
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

"""Utility routines for Crates.
"""

import os
import time
import collections

import numpy as np
import pycrates

from ciao_contrib.logger_wrapper import initialize_module_logger
from ciao_contrib import smooth as sm

__all__ = (
    "make_table_crate", "make_image_crate",
    "add_colvals",
    "write_columns", "write_arrays",
    "scale_image_crate",
    "smooth_image_crate",
    "SimpleCoordTransform",
    "read_ds9_contours",
)

logger = initialize_module_logger("crates_utils")

v3 = logger.verbose3

# time.strftime format to create FITS (like) time format
_fits_time_fmt = "%Y-%m-%dT%H:%M:%S"


def add_colvals(cr, colname, colvals, unit=None, desc=None):
    """Add a new column to the crate.

    Create a new column in the crate with the given name and data
    values. The unit and desc fields are used to set the column unit
    and description if given.

    Parameters
    ----------
    cr
        A TABLECrate.
    colname : str
        The name of the column to add. If it already exists in the
        crate then a ValueError is raised, and the check is
        case insensitive.
    colvals
        The column data to add. It can be two dimensional, in which
        case each row of the table contains an array. It is expected
        that this is a NumPy array, but any iterable can be used.
        Note that unsupported data types are only recognized when the
        file is written out, not when the data is added to the crate.
    unit : None or str, optional
        The units value for the column. There are approved formats
        for FITS files but no check is made here.  This may be
        truncated, or not written out, depending on the file format
        used.
    desc : None or str, optional
        The description for the column. This may be truncated, or
        not written out, depending on the file format used.

    See Also
    --------
    make_table_crate

    Notes
    -----
    Validation of the column values - such as supported data types
    and whether the number of rows matches the other columns - is
    done when the crate is written out.

    Example
    -------

    >>> cr = pycrates.TABLECrate()
    >>> add_colvals(cr, 'index', [1, 2, 4], desc='Index')
    >>> add_colvals(cr, 'age', x, unit='year')
    >>> add_colvals(cr, 'blen', y, unit='cm', desc='Beard Length')

    """

    # In CIAO 4.4 there is some confusion within Crates if you
    # over-write a column, so force users to be explicit here.
    # In more recent versions of CIAO the add_column call will fail
    # if the column already exists, but leave this check in.
    #
    if cr.column_exists(colname):
        raise ValueError("Column {} already exists in the table crate.".format(colname))

    cd = pycrates.CrateData()
    cd.name = colname

    cd.values = colvals
    if unit is not None:
        cd.unit = unit
    if desc is not None:
        cd.desc = desc

    cr.add_column(cd)


def _sarray_to_crate(sa, colnames=None):
    """Create a TABLECrate that contains the contents
    of the supplied structured/rec array. If colnames is
    not None then it it an array of names that determines
    the order to add the columns to the crate (and can
    be used to filter out columns in sa).

    The arrays in the structured array are explicitly
    copied into the crate to avoid some memory issues
    seen in CIAO 4.4 testing. However, this may not
    resolve all issues so it is suggested that this
    routine is not used at this time.

    Not all data types are necessarily supported.
    """

    cr = pycrates.TABLECrate()
    cr.name = "TABLE"

    if colnames is None:
        names = sa.dtype.names
    else:
        names = colnames

    for cname in names:
        # We copy the values to avoid an issue on writing out the
        # crate; not sure if this is a Crates or NumPy problem
        # and whether this has been fixed since CIAO 4.4 when it
        # was seen
        #
        add_colvals(cr, cname, sa[cname].copy())

    return cr


def _dict_to_crate(d, colnames=None):
    """Create a TABLECrate that contains the contents of the
    dictionary. If colnames is not None then it it an array of names
    that determines the order to add the columns to the crate (and can
    be used to filter out columns). Use of collections.OrderedDict
    rather than a normal dictionary can also be used to determine
    the order of the columns.

    The data arrays used in the crate are references of the
    input values (i.e. they are not copied, unlike _sarray_to_crate).

    Not all data types are necessarily supported.
    """

    cr = pycrates.TABLECrate()
    cr.name = "TABLE"

    if colnames is None:
        names = d.keys()
    else:
        names = colnames

    for cname in names:
        add_colvals(cr, cname, d[cname])

    return cr


def _arrays_to_crate(arrays, colnames=None):
    """Create a TABLECrate that contains the contents of the
    columns in arrays (each element is a column).

    If colnames is not None then they are used as the column names,
    otherwise values of col1 to colN are used.

    The data arrays used in the crate are references of the
    input values (i.e. they are not copied, unlike _sarray_to_crate).

    Not all data types are necessarily supported.
    """

    na = len(arrays)
    if colnames is None:
        colnames = ["col{}".format(i) for i in range(1, na + 1)]

    else:
        nc = len(colnames)
        if nc != na:
            raise ValueError("Number of columns ({}) and column names ({}) does not match.".format(nc, na))

    cr = pycrates.TABLECrate()
    cr.name = "TABLE"
    for (col, name) in zip(arrays, colnames):
        add_colvals(cr, name, col)

    return cr


def _add_basic_metadata(cr, creator):
    """Add CREATOR and DATE keywords to the crate.

    Parameters
    ----------
    cr : Crate
        The crate to add the keywords to.
    creator : str
        The value of the CREATOR keyword.

    Notes
    -----
    The current time is used for the DATE keyword, using
    the FITS-approved format (YYYY-MM-DDTHH:MM:SS). There is
    no attempt to convert the timezone to UTC.
    """

    key1 = pycrates.CrateKey()
    key1.name = "CREATOR"
    key1.value = creator
    key1.desc = "tool that created this output"
    cr.add_key(key1)

    key2 = pycrates.CrateKey()
    key2.name = "DATE"
    key2.value = time.strftime(_fits_time_fmt)
    key2.desc = "Date and time of file creation"
    cr.add_key(key2)



def make_table_crate(*args, **kwargs):
    """Create a table Crate from the given columns.

    Parameters
    ----------
    *args
        One or more data values. The supported variants are listed
        below in the Notes section.
    colnames : list, optional
        This argument determines the names and orders of the
        columns that are written out. Its meaning depents on the
        form of the input data, as discussed in the Notes section
        below.

    Returns
    -------
    tcrate
        A table crate which contains the column values and has
        some metadata items attached to it (CREATOR and DATE
        keywords).

    See Also
    --------
    add_colvals, make_image_crate, write_arrays, write_columns

    Notes
    -----
    If called with one argument and it acts as a dictionary then
    the keys of the value are taken to be the column names and
    the values are the columns. Use a collections.OrderedDict
    to ensure the column order, since it's taken to be the
    key order returned by the dictionary. The order can be over-ridden
    with the colnames argument (this also lets you write out only
    a subset of the keys in the dictionary).

    If a single argument is used that is a stuctured array then
    the column names, order, and data is taken from the array. As
    with dictionaries the colnames argument can be used to re-order
    or subset the data.

    The arguments are taken to be the column data to use. If they are
    not the same length then the smaller arrays will be padded with
    the null value for that column type (0 for numeric columns and
    "IND" or "" for string columns). The arrays can be Python arrays
    or numpy arrays, and include strings. Python arrays should contain
    the same data type for each element; if this does not hold then
    there is no guarantee as to the behavior of this routine.

    When a dictionary or structured array is supplied then the colnames
    argument, if set, is used to order the columns in the crate.
    Columns in the input argument but not mentioned in colnames are
    excluded.

    Otherwise, the colnames argument is used to name the columns. If
    left as None then the names "col1" to "coln" will be used (n being
    the number of columns).

    The semantics of whether the input array(s) are copied or
    just referenced in the crate are currently not specified.
    Changing the original array after the crate has been created
    *may* change the value in the Crate, but this behavior should
    not be taken advantage of.

    Examples
    --------

    >>> a = [1,2,3,4,5]
    >>> b = ["aa", "bb", "", "d d", "long string"]
    >>> c = np.arange(10).reshape((5,2))
    >>> cr1 = make_table_crate(a, b)
    >>> cr2 = make_table_crate(a, b, c, colnames=["foo","bar","bax"])

    In this case bax is a vector column

    >>> d = { "foo": [1,2,3], "bar": ["xx", "yy"],
    ...       "bax": np.arange(10).reshape((5,2)) }
    >>> cr3 = make_table_crate(d)
    >>> cr4 = make_table_crate(d, colnames=["foo", "bax"])

    >>> e = np.zeros((2,),dtype=('i4,f4,a10'))
    >>> e[:] = [(1, 2., 'Hello'), (2, 3., "World")]
    >>> cr5 = make_table_crate(e)
    >>> cr6 = make_table_crate(e, colnames=['f1', f2'])

    """

    isdict = False
    isstruct = False

    nargs = len(args)
    if nargs == 0:
        raise TypeError("make_table_crate() takes at least one argument (0 given)")
    elif nargs == 1:
        try:
            isdict = isinstance(args[0], collections.Mapping)
        except AttributeError:
            isdict = isinstance(args[0], collections.abc.Mapping)
            
        if hasattr(args[0], "dtype") and hasattr(args[0].dtype, "names"):
            isstruct = args[0].dtype.names is not None

        if isdict and isstruct:
            raise ValueError("Unexpected: argument appears to be a map and a structured/rec array!")

    try:
        colnames = kwargs.pop("colnames")
    except KeyError:
        colnames = None

    if len(kwargs) != 0:
        raise TypeError("make_table_crate() got an unexpected keyword argument '{}'".format(kwargs.keys()[0]))

    if isdict:
        cr = _dict_to_crate(args[0], colnames=colnames)

    elif isstruct:
        cr = _sarray_to_crate(args[0], colnames=colnames)

    else:
        cr = _arrays_to_crate(args, colnames=colnames)

    _add_basic_metadata(cr, 'make_table_crate')
    return cr


def make_image_crate(pixvals):
    """Create an image Crate from the given array.

    Parameters
    ----------
    pixvals
        The pixel values.

    Returns
    -------
    icrate
        An image crate which contains the pixel values and has
        some metadata items attached to it (CREATOR and DATE
        keywords).

    See Also
    --------
    make_table_crate

    Notes
    -----
    The semantics of whether the input array is copied or
    just referenced in the crate are currently not specified.
    Changing the original array after the crate has been created
    *may* change the value in the Crate, but this behavior should
    not be taken advantage of.

    Examples
    --------

    >>> a = np.arange(400 * 500).reshape(400, 500)
    >>> cr = make_image_crate(a)

    """

    cd = pycrates.CrateData()
    cd.values = pixvals

    cr = pycrates.IMAGECrate()
    cr.name = "IMAGE"
    cr.add_image(cd)

    _add_basic_metadata(cr, 'make_image_crate')
    return cr


# Used by write_columns
#
__kernel_mapping = {
    "text": "text/simple",
    "simple": "text/simple",
    "dtf": "text/dtf",
    "raw": "text/raw",
    "fits": None
}


def write_columns(fname, *args, **kwargs):
    """Write out arrays as columns to the file fname.

    Parameters
    ----------
    fname : str
        The name of the output file.
    *args
        The column data to write out (NumPy arrays, Python lists, a
        dictionary, or NumPy structured array).  A single column is
        assumed to have a consistent data type, and columns will be
        padded to match the longest column length (the pad value
        depends on the column type; e.g. 0 for numeric columns and the
        empty string for string columns). If a single argument is
        given then it can be a dictionary, or structured array, from
        which the columns are taken.
    colnames : list, optional
        When the input is a dictionary or structured array, this is
        a list of columns to use (and so should match or be a subset
        of the column names or keys). If no names are given then the
        columns will be called 'col1', 'col2', up to 'coln' (where n
        is the number of arrays sent in).
    format : {'text', 'fits', 'simple', 'dtf', 'raw'}, optional
        The format of the file. The default is 'text'. The 'simple'
        argument has the same meaning as 'text'. See "ahelp dmascii"
        for more information on the ASCII file formats supported by
        CIAO tools and libraries, including Crates.
    sep : character, optional
        The column separator to use when the format is not 'fits'.
        The default is ' '.
    comment : character, optional
        Comment lines start with this when the format is not 'fits'.
        The default is '#'.
    clobber : bool, optional
      If the output file exists then it will be overwritten (if True)
      or cause the routine to raise an IOError (when set to False).
      The default is True.

    See Also
    --------
    make_table_crate, write_arrays

    Examples
    --------

    >>> write_columns('cols.dat', a, b)
    >>> write_columns('cols.dat', a, b, colnames=['x','y'])
    >>> write_columns('cols.dat', a, b, colnames=['x','y'],
    ...               format='fits')
    >>> write_columns('cols.dat', a, b, colnames=['x','y'],
    ...               clobber=False)

    >>> d = { "x": a, "y": b, "z": a + b }
    >>> write_columns('cols.dat', d)
    >>> write_columns('cols.dat', d, colnames=["x", "y"])

    """

    # We repeat some usage checks that make_table_crate() does so that
    # we give a more user-friendly error message than if it came from a
    # routine the user did not directly call.
    #
    if len(args) == 0:
        raise TypeError("write_columns() takes at least two arguments (1 given)")

    fmt = kwargs.pop("format", "text")

    try:
        kernel = __kernel_mapping[fmt]
    except KeyError:
        raise TypeError("format argument sent '{}', must be one of {}".format(fmt, ", ".join(__kernel_mapping.keys())))

    colsep = kwargs.pop("sep", " ")
    if len(colsep) != 1:
        raise TypeError("sep argument must be a single character, sent '{}'".format(colsep))

    comment = kwargs.pop("comment", "#")
    if len(comment) != 1:
        raise TypeError("comment argument must be a single character, sent '{}'".format(comment))

    clobber = kwargs.pop("clobber", True)

    for k in kwargs.keys():
        if k != "colnames":
            raise TypeError("write_columns() got an unexpected keyword argument '{}'".format(k))

    cr = make_table_crate(*args, **kwargs)

    oname = fname
    if kernel is not None:
        # In CIAO 4.4 release 1, keywords are written out for ASCII formats
        # when the comment option is set. Since most people will use the
        # default comment option we avoid this by only including the comment
        # value if not '#'; this is a hack. Is this still true?
        if comment == '#':
            oname += "[opt kernel={},sep='{}']".format(kernel, colsep)
        else:
            oname += "[opt kernel={},sep='{}',comment={}]".format(kernel, colsep, comment)

    cr.write(oname, clobber=clobber)


def write_arrays(filename, args, fields=None, sep=' ', comment='#',
                 clobber=False, linebreak='\n', format='%g'):
    """Write a list of arrays to an ASCII file.

    Parameters
    ----------
    filename : str
        The name of the file to create.
    args : list
        The list of arrays, where each element represents a column of
        data.
    fields : list of str, optional
        The column names to use. If not given then the names 'col1',
        'col2', ... will be used.
    sep : str, optional
        The character used to separate columns.
    comment : str, optional
        The comment character (at the start of a line).
    clobber : bool, optional
        Should the file be over-written if it already exists?
    linebreak : str, optional
        The characters used to indicate a line break.
    format : str, optional
        The format string used to convert each column element into a
        string.

    See Also
    --------
    make_table_crate, write_columns

    Examples
    --------

    >>> a = [0, 1, 2, 3, 4]
    >>> b = [1, 2, 3, 4, 5]
    >>> c = [1, 2, 4, 8, 16]
    >>> write_arrays('out.dat', [a, b, c], fields=['a', 'b', 'c'],
    ...              clobber=True)
    """
    if os.path.isfile(filename) and not clobber:
        raise IOError("file '{}' exists and clobber is not set".format(filename))

    if not np.iterable(args) or len(args) == 0:
        raise IOError('please supply array(s) to write to file')

    if not np.iterable(args[0]):
        raise IOError('please supply array(s) to write to file')

    size = len(args[0])
    for arg in args:
        if not np.iterable(arg):
            raise IOError('please supply array(s) to write to file')
        elif len(arg) != size:
            raise IOError('not all arrays are of equal length')

    args = np.column_stack(np.asarray(args))

    with open(filename, 'w') as f:
        if fields is not None:
            f.write(comment + sep.join(fields) + linebreak)

        lines = []
        for arg in args:
            line = [format % elem for elem in arg]
            lines.append(sep.join(line))

        f.write(linebreak.join(lines))

        # add a newline at end
        f.write(linebreak)


_image_scalings = {
    "none": None,
    "arcsinh": np.arcsinh,
    "asinh": np.arcsinh,
    "sqrt": np.sqrt,
    "square": np.square,
    "log10": np.log10,
    "log": np.log
}


def scale_image_crate(cr, scaling="arcsinh"):
    """Scale the pixel values in the image crate.

    This changes the pixel values stored in the image crate
    but retains other metadata, such as WCS mapping.

    Parameters
    ----------
    cr
        The IMAGECrate to change.
    scaling : optional
        The default value is 'arcsinh', and the list of supported
        values is given in the Notes section below.

    See Also
    --------
    smooth_image_crate

    Notes
    -----
    The supported scaling values, and their meanings, are

    'none'
        This does not change the pixel values.
    'arcsinh'
        The pixel values are replaced by arcsinh(values).
    'asinh'
        The same as 'arcsinh'.
    'sqrt'
        Take the square root of the pixel values.
    'square'
        Take the square of the pixel values.
    'log10'
        The pixel values are replaced by log10(values).
    'log'
        This is similar to 'log10' but uses the natural
        logarithm.

    This routine modifies the data in the input crate, it does
    *NOT* return a copy of the crate.

    Examples
    --------

    >>> cr = read_file('img.fits')
    >>> scale_image_crate(cr, 'log10')

    """

    if not isinstance(cr, pycrates.IMAGECrate):
        raise ValueError("First argument must be an image crate.")

    # Short cut
    if scaling == "none":
        return

    ivals = pycrates.copy_piximgvals(cr)

    try:
        sfunc = _image_scalings[scaling]

    except KeyError:
        raise ValueError("Invalid scaling value of '{}': must be one of\n  {}".format(
            scaling, " ".join(_image_scalings.keys())))

    pycrates.set_piximgvals(cr, sfunc(ivals))


_image_smooth = {
    "none": None,
    "gauss": sm.gsmooth,
    "boxcar": sm.bsmooth,
    "tophat": sm.tsmooth,
    "image": sm.ismooth,
    "file": sm.fsmooth
}


def smooth_image_crate(cr, stype, *args, **kwargs):
    """Smooth the pixel values in the crate.

    This changes the pixel values stored in the image crate
    but retains other metadata, such as WCS mapping.

    Parameters
    ----------
    cr
        The IMAGECrate to change.
    stype : str
        The type of smoothing to apply. The list of supported
        values is given in the Notes section below.
    *args, **kwargs
        The supported arguments depend on the value of the
        'stype' argument.

    See Also
    --------
    scale_image_crate

    Notes
    -----
    The supported smoothing types, and their arguments, are given
    below, where function indicates which function from
    ciao_contrib.smooth is used to smooth the image (it also
    determines the meaning of the "args and kwargs" column):

    ======= =========== ======== =================================
    stype   smoothing   function args and kwargs
    ======= =========== ======== =================================
    none    none
    gauss   gaussian    gsmooth  sigma, hwidth=5
    boxcar  box-car     bsmooth  radius
    tophat  top-hat     tsmooth  radius
    file    by file     fsmooth  filename, norm=True, origin=None
    image   by image    ismooth  kernel, norm=True, origin=None
    ======= =========== ======== =================================

    Numeric values such as sigma and radius refer to logical
    pixels, and not SKY or WCS units.

    This routine modifies the data in the input crate, it does
    *NOT* return a copy of the crate.

    Examples
    --------

    Smooth the data with a gaussian with a 3-pixel sigma, using
    a box half-width of 5 sigmaL

    >>> cr = read_file('img.fits')
    >>> smooth_image_crate(cr, 'gauss', 3)

    Change to use a bow half-width of 7 sigma:

    >>> cr = read_file('img.fits')
    >>> smooth_image_crate(cr, 'gauss', sigma=3, hwidth=7)

    Smooth the pixel values in chandra.img by the image stored in
    xmm_psf.fits:

    >>> cr = read_file('chandra.img')
    >>> smooth_image_crate(cr, 'file', 'xmm_psf.fits')

    Create a three-by-three kernel and use it to smooth the image
    stored in cr:

    >>> kern = np.asarray([0, 1, 0, 1, 2, 1, 0, 1, 0]).reshape(3, 3)
    >>> smooth_image_crate(cr, 'image', kern)

    """

    if not isinstance(cr, pycrates.IMAGECrate):
        raise ValueError("First argument must be an image crate.")

    # Short cut
    if stype == "none":
        return

    ivals = pycrates.copy_piximgvals(cr)

    try:
        sfunc = _image_smooth[stype]

    except KeyError:
        raise ValueError("Invalid smooth value of '{}': must be one of\n  {}".format(
            stype, " ".join(_image_smooth.keys())))

    nvals = sfunc(ivals, *args, **kwargs)
    pycrates.set_piximgvals(cr, nvals)


# Coordinate-conversion code

class SimpleCoordTransform:
    """Simple coordinate transforms between image coordinate systems.

    Parameters
    ----------
    inval : str or IMAGECrate
        The input file or data.

    Notes
    -----
    This class is only tested on CIAO-produced image files, and so
    there is no guarantee it will work correctly on other images.


    """

    # The mapping between Transform class name and the user-friendly
    # label.
    _coord_mapping = {
        # In CIAO 4.6 we now have the WCSTransform class; the WCSTANTransform
        # version is still supported for now but is assumed to be deprecated.
        'WCSTANTransform': 'world',
        'WCSTransform': 'world',
        'LINEAR2DTransform': 'physical'
    }

    # The mapping between user-supplied coordinate-system name and
    # the internal names (case insensitive).
    _sys_mapping = {
        "world": "world", "eqpos": "world",
        "physical": "physical", "sky": "physical",
        "logical": "logical", "image": "logical"
    }

    def __init__(self, inval):
        """Create the object."""

        if hasattr(inval, "get_axisnames") and hasattr(inval, "get_transform"):
            crate = inval
            fname = crate.get_filename()
        else:
            crate = pycrates.IMAGECrate(inval, mode="r")
            fname = inval

        axes = crate.get_axisnames()
        if axes is None or len(axes) == 0:
            raise ValueError("No axes found in {}".format(fname))

        # get_transform is case-sensitive
        self.axes = [n.split('(')[0] for n in axes]
        self.transforms = {}
        for n in self.axes:
            try:
                tr = crate.get_transform(n).copy()
            except ValueError:
                raise ValueError("Unable to find the transformation for {}".format(n))

            try:
                ctype = self._coord_mapping[tr.get_className()]
            except KeyError:
                continue

            try:
                self.transforms[ctype]
                raise ValueError("Found multiple {} coordinate systems in {}".format(ctype, fname))

            except KeyError:
                self.transforms[ctype] = {"name": n, "type": ctype,
                                          "transform": tr}

        try:
            world = self.transforms["world"]
            physical = self.transforms["physical"]

        except KeyError as ke:
            raise ValueError("Unable to find the {} system in {}".format(ke.args[0], fname))

        # self.conversions[fromsys][tosys]
        #
        self.conversions = {}
        self.conversions["world"] = {
            "world": None,
            "physical": {"direction": "invert", "transforms": [world]},
            "logical": {"direction": "invert", "transforms": [world, physical]}
        }
        self.conversions["physical"] = {
            "world": {"direction": "apply", "transforms": [world]},
            "physical": None,
            "logical": {"direction": "invert", "transforms": [physical]}
        }
        self.conversions["logical"] = {
            "world": {"direction": "apply", "transforms": [physical, world]},
            "physical": {"direction": "apply", "transforms": [physical]},
            "logical": None
        }

    def _validate_coordsys(self, cname):
        "Raise a ValueError if cname is invalid, returns the internal name"

        try:
            return self._sys_mapping[cname.lower()]

        except KeyError:
            raise ValueError("Invalid coordinate-system name: " +
                             "{}".format(cname))

    # Unfortunately I did not note why I only do this point-by-point rather
    # than send in all the points at once. There have been issues with checking
    # coordinate dimensionality, that have been fixed in CIAO 4.5, that
    # may mean that we can go back to just handling vectors, but for now
    # keep as is.
    #
    def _convert(self, direction, mappings, x, y):
        """Convert a single (x,y) using the direction and mappings."""

        # Need to make sure x and y are float to avoid Transform bug
        # when inputs are integer (forces output to be integer)
        pt = [[x * 1.0, y * 1.0]]
        for trinfo in mappings:
            pt = getattr(trinfo["transform"], direction)(pt)

        return pt[0, :]

    def convert(self, fromsys, tosys, x, y):
        """Convert image coordinates.

        Parameters
        ----------
        fromsys, tosys : str
            The names of the coordinate system used by x,y
            (fromsys) and the return value (tosys). The supported
            values are: "world" or "eqpos", "physical" or "sky",
            and "logical" or "image".
        x, y : array of coordinates
            The coordinate values to use. They are expected to have
            the same shape.

        Returns
        -------
        xc, yc
            The converted coordinate values.

        Examples
        --------

        >>> xc, yc = iconv.convert('sky', 'logical', x, y)

        """

        v3("Coordinate conversion of {},{} from {} to {}".format(x, y, fromsys, tosys))
        fsys = self._validate_coordsys(fromsys)
        tsys = self._validate_coordsys(tosys)
        try:
            cinfo = self.conversions[fsys][tsys]

        except KeyError as ke:
            raise ValueError("Unable to find transforms for {} (unexpected)".format(ke.args[0]))

        v3(" . conversion info = {}".format(cinfo))
        if cinfo is None:
            return (np.asarray(x), np.asarray(y))

        d = cinfo["direction"]
        trs = cinfo["transforms"]

        xin = np.asarray(x)
        yin = np.asarray(y)

        # what was I going to do with this?
        # otype = np.common_type(xin, yin)

        # Could presumably be a lot more clever with array manipulation here
        b = np.broadcast(xin, yin)
        v3(" . to convert {}".format(b))
        out = np.asarray([self._convert(d, trs, u, v) for (u, v) in b])
        v3(" . answer = {}".format(out))
        xout = out[:, 0].copy().reshape(b.shape)
        yout = out[:, 1].copy().reshape(b.shape)
        return xout, yout


# TODO: this needs to be updated to support the new coordinate format
#       in ds9 release 7.5
#
def read_ds9_contours(fname, coords=None, fromsys=None, tosys=None):
    """Read in coordinates from a DS9 *.con file.

    The optional arguments can be used to convert the coordinates
    from the input system (which is not specified in the file).

    Parameters
    ----------
    fname : str
        The name of the ds9 contour file. At present only the original
        format - coordinates only - is supported; that is, the new
        coordinate format introduced in DS9 7.5 which allows users
        to customize each level is not supported.
    coords : str or IMAGECrate, optional
        If given then it is the image file (either name or data) to
        use to provide the coordinate mapping.
    fromsys, tosys : optional
        Only used if coords is not None. The arguments specify the
        coordinate system of the coordinates in fname (fromsys)
        and the coordinate system to return (tosys). The valid
        values for these arguments are: "world" or "eqpos",
        "physical" or "sky", and "logical" or "image".

    Returns
    -------
    xcoords, ycoords : list of NumPy arrays
        The contour coordinates. The return values are lists, where
        each element refers to a single contour (so the coordinates of
        the first component are given by xcoords[0] and ycoords[0]).

    Notes
    -----
    The only supported format is that of DS9 prior to release 7.5,
    and consists of two columns of floating-point numbers, with blank
    lines used to separate each component.

    Examples
    --------

    >>> xall, yall = read_ds9_contours("ds9.con")
    >>> print("Number of segments: {}".format(len(xall)))

    The contours have been saved in SKY coordinates and are to
    be converted to celestial coordinates using the WCS transformation
    information in the file image.fits:

    >>> ra, dec = read_ds9_contours('ds9.con', fname='image.fits',
    ...                             fromsys='sky', tosys='world')

    """

    xall = []
    yall = []
    x = []
    y = []

    if None in [coords, fromsys, tosys]:
        tr = None
    else:
        tr = SimpleCoordTransform(coords)

    with open(fname, "r") as fh:
        for l in fh.readlines():
            l = l.strip()
            if l == '':
                if len(x) == 0:
                    raise ValueError("Unexpected blank line: read in x=\n{}\n".format(xall))

                if tr is None:
                    xo = np.asarray(x)
                    yo = np.asarray(y)
                else:
                    (xo, yo) = tr.convert(fromsys, tosys, x, y)

                xall.append(xo)
                yall.append(yo)

                x = []
                y = []

            else:
                toks = l.split()
                if len(toks) != 2:
                    raise ValueError("Unable to parse line: '{}'".format(l))

                x.append(float(toks[0]))
                y.append(float(toks[1]))

    if len(x) != 0:
        if tr is None:
            xo = np.asarray(x)
            yo = np.asarray(y)
        else:
            (xo, yo) = tr.convert(fromsys, tosys, x, y)

        xall.append(xo)
        yall.append(yo)

    if len(xall) == 0:
        raise ValueError("No data read in from: {}".format(fname))

    return (xall, yall)

# End
