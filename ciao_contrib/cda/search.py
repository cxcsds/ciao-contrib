#
#  Copyright (C) 2011, 2015, 2016, 2018, 2019, 2025
#  Smithsonian Astrophysical Observatory
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
Simple searches of the Chandra archive.

Routines that wrap up access to the Simple Image Access (SIA)
endpoint at the Chandra Footprint Server. As of mid 2018
the URL is

    https://cxcfps.cfa.harvard.edu/cda/footprint/cdaview.html

but prior to that it was

    http://cxc.harvard.edu/cda/footprint/cdaview.html

Notes
------

This code can be used but please be aware that it is not
considered stable, so there may well be API changes.

Although the SIA protocol is general, this module is only
designed to work with the Chandra service and may not work
with other access points.

Example
-------

>>> from ciao_contrib.utils import write_columns
>>> sr = search_chandra_archive(8.815, -43.566, size=0.3)
>>> obsinfo = get_chandra_obs(sr)
>>> print(obsinfo['obsid'])
>>> write_columns('search.dat', obsinfo, kernel='simple')

"""

import numpy as np

from xml.etree import ElementTree
from collections import OrderedDict

import coords.format as coords
import coords.utils as cutils

from ciao_contrib.downloadutils import retrieve_url

import ciao_contrib.logger_wrapper as lw

logger = lw.initialize_module_logger("cda.search")

v3 = logger.verbose3
v4 = logger.verbose4
v5 = logger.verbose5

__all__ = (
    "search_chandra_archive",
    "get_chandra_obs",
)


def _mkl(label):
    return '{http://www.ivoa.net/xml/VOTable/v1.1}' + label


def _combl(*ls):
    return "/".join([_mkl(l) for l in ls])


def _get_child(parent, name, attr=None):
    """Returns the VOTable element labelled
    name (this is just the local name, not the full URI),
    for the parent.

    If attr is not None then it is taken to be
      (name, value)
    and this is used as a filter on matching elements.

    A ValueError is raised if there is no matching
    element or multiple matches.
    """

    out = _get_children(parent, name, attr=attr)
    nout = len(out)
    if nout == 1:
        return out[0]

    else:
        if attr is None:
            resource = name
        else:
            (aname, avalue) = attr
            resource = "{}[{}={}]".format(name, aname, avalue)

        if nout == 0:
            raise ValueError("No child called {} of {}".format(resource, parent.tag))

        else:
            raise ValueError("Expected 1 {} child of {} but found {}".format(resource, parent.tag, nout))


def _get_children(parent, name, attr=None):
    """Returns the VOTable elements labelled
    name (this is just the local name, not the full URI),
    for the parent.

    If attr is not None then it is taken to be
      (name, value)
    and this is used as a filter on matching elements.

    The return list can be empty.
    """

    xs = parent.findall(_mkl(name))

    if attr is not None:
        (aname, avalue) = attr
        xs = [x for x in xs if x.get(aname) == avalue]

    return xs


def _get_col_info(fld, csys=None):
    """Given a FIELD return a dictionary
    of information.

    csys, if given, should be a set of COOSYS elements
    from the RESOURCE block (used to identify coordinate-system
    references). This is currently unused.

    Limited/no error checking.
    """

    out = {
        'name': fld.get('name'),
        'format': (fld.get('datatype'), fld.get('arraysize')),
        }

    desc = fld.find(_mkl('DESCRIPTION'))
    if desc is not None:
        out['description'] = desc.text

    def add(n):
        v = fld.get(n)
        if v is not None:
            out[n] = v

    add('unit')
    add('ucd')
    add('utype')

    v5("Parsed FIELD -> {}".format(out))
    return out


def _valconv(val, fmt):
    """Convert a column text representation (val)
    into native Python data types accorting to the
    fmt tuple (the format keyword returned by
    get_col_info).

    """

    (datatype, arraysize) = fmt

    if datatype == 'char':
        if arraysize == '*':
            return val
        else:
            # we cut/extend to the given length,
            # padding on the right if need be
            a = int(arraysize)
            if len(val) >= a:
                return val[:a]
            else:
                return (val + ' ' * a)[:a]

    elif datatype == 'int':
        cfunc = int

    elif datatype in ['float', 'double']:
        cfunc = float

    else:
        raise ValueError("Unrecognized data type: {}".format(datatype))

    if arraysize is None:
        return cfunc(val)

    elif arraysize == '*':
        return [cfunc(v) for v in val.split(',')]

    else:
        raise ValueError("Unsupported arraysize value of {}".format(arraysize))


def read_chandra_siap_table(fname):
    """Read in the data from the Chandra footprint service.

    Parameters
    ----------
    fname : file-like object
        The stream - which is passed to ElementTree.parse - is assumed
        to contain a VOTABLE returned from a SIAP query.

    Returns
    -------
    ans : NumPy structured array or None
        A structured array representing the contents of the VOTABLE,
        unless no matches were found, in which case the return value
        is None.

    Notes
    -----
    This is not guaranteed to work on other forms of VOTABLE,
    such as those from the Hubble footprint service.

    Metadata from the table is currently not returned.
    """

    try:
        vot = ElementTree.parse(fname)
    except ElementTree.ParseError as exc:
        raise OSError("Input is not an XML file.\n{}".format(exc))

    root = vot.getroot()
    if root.tag != _mkl('VOTABLE'):
        raise IOError("Expected VOTABLE but found {} as the root element".format(root.tag))

    res = _get_child(vot, 'RESOURCE', attr=('type', 'results'))

    # Check download status
    st = _get_child(res, 'INFO', attr=('name', 'QUERY_STATUS'))
    if st.get('value') != 'OK':
        raise ValueError("Query failed: {}".format(st.text))

    # Coordnate mapping
    coosys = res.findall('COOSYS')

    # Get column info
    tbl = _get_child(res, 'TABLE', attr=('name', 'SIAP_KEYWORDS'))

    # assume that if there is no nrows parameter that the search found
    # no matches
    nrows = tbl.get('nrows')
    if nrows is None:
        return None
    else:
        nrows = int(nrows)
    cols = [_get_col_info(f, csys=coosys) for f in _get_children(tbl, 'FIELD')]
    ncols = len(cols)

    # Extract the data into Python lists and then convert
    # to NumPy types. Not the most memory efficient but it is assumed
    # that the number of rows is small.
    #
    coldata = {c['name']: [] for c in cols}
    rowctr = 0
    for row in tbl.findall(_combl('DATA', 'TABLEDATA', 'TR')):
        rowctr += 1
        tds = _get_children(row, 'TD')
        if len(tds) != ncols:
            raise ValueError("Expected {} columns in row #{} but found {}".format(ncols, rowctr, len(tds)))

        for (col, colinfo) in zip(tds, cols):
            coldata[colinfo['name']].append(_valconv(col.text,
                                                     colinfo['format']))

    out = OrderedDict()
    for colinfo in cols:
        cname = colinfo['name']
        out[cname] = np.asarray(coldata[cname])
        nr = out[cname].shape[0]
        if nr != nrows:
            raise ValueError("Expected {} rows in column {} but found {}".format(nrows, cname, nr))

    # We could return the ordered dict, or store it in a dictionary along
    # with some meta data. Instead, let's try using a structured array.
    # We could create the array directly, but we do it this way to avoid
    # having to validate all the rows manually and because the code above
    # was already written.
    #
    def mkdtype(k, v):
        if v.ndim == 1:
            return (k, v.dtype)
        else:
            return (k, v.dtype, v.shape[1:])

    dtypes = [mkdtype(k, v) for (k, v) in out.items()]
    sout = np.zeros(nrows, dtype=dtypes)
    for (k, v) in out.items():
        sout[k] = v

    return sout


_fmap = {
    "acis": "ACIS-I,ACIS-S",
    "acis-i": "ACIS-I",
    "acis-s": "ACIS-S",
    "hrc": "HRC-I,HRC-S",
    "hrc-i": "HRC-I",
    "hrc-s": "HRC-S",
    "none": "NONE",
    "letg": "LETG",
    "hetg": "HETG"
}


def _fconv(name, val):
    """Convert one of the instrument or grating values from search_chandra_archives
    into a format usable in the SIA call. Will error out on invalid values.
    """

    try:
        return _fmap[val.lower()]
    except KeyError:
        raise ValueError("Invalid {}: {}".format(name, val))


def construct_query(ra, dec, size,
                    instrument=None):
    """Return the URL for searching the archive.

    Parameters
    ----------
    ra, dec : double
        The location to query, in decimal degrees.
    size : double
        The search radius around the point, in degrees. Any
        observation that falls within this circle will be returned. A
        value of 0 means that the search point must be covered by the
        observation for a match to occur.
    instrument : None or array of str, optional
        If not None, then restrict the search to observations which
        contain the given instrument. Supported values are
        "acis", "acis-i", "acis-s", "hrc", "hrc-i", and "hrc-s".

    Returns
    -------
    url : str
        The URL to query.

    """

    url = "https://cxcfps.cfa.harvard.edu/"
    url += "cgi-bin/cda/footprint/get_vo_table.pl"
    url += "?strict=1&POS={},{}&SIZE={}".format(ra, dec, size)

    if instrument is not None:
        url += "&inst="
        url += ",".join([_fconv("instrument", i)
                         for i in set(instrument)])

    return url


def _make_query(url):
    """Query the footprint server and parse the response.

    Parameters
    ----------
    url : str
        The URL for the query; see construct_query

    Returns
    -------
    ans : None or NumPy structured array
        The response, as a NumPy structured array, if there are
        any rows, otherwise None.

    """

    rsp = retrieve_url(url)
    try:
        ans = read_chandra_siap_table(rsp)
    except OSError as exc:
        raise OSError("There may be a problem with the CXC " +
                      "footprint service.\n{}".format(exc))

    return ans


def search_chandra_archive(ra, dec, size=0.1,
                           instrument=None,
                           grating=None):
    """Find Chandra observations which cover the location.

    This only search publically-available observations, and can
    return multiple rows per observation.

    Parameters
    ----------
    ra, dec : double
        The location to query, in decimal degrees.
    size : double
        The search radius around the point, in degrees. Any
        observation that falls within this circle will be returned. A
        value of 0 means that the search point must be covered by the
        observation for a match to occur.
    instrument : None or array of str, optional
        If not None, then restrict the search to observations which
        contain the given instrument. Supported values are
        "acis", "acis-i", "acis-s", "hrc", "hrc-i", and "hrc-s".
    grating : None or array of str, optional
        If not None, then restrict the search to observations which
        contain the given grating. Supported values are
        "none", "letg", and "hetg".

    Returns
    -------
    ans : None or NumPy structured array
        If there was no match, return None, otherwise the returned
        data.

    Examples
    --------

    >>> ans = search_chandra_archive(47.23, -12.34)

    >>> ans = search_chandra_archive(47.23, -12.34, size=0)

    >>> ans = search_chandra_archive(47.23, -12.34,
                                     instrument=["acis"])

    >>> ans = search_chandra_archive(47.23, -12.34,
                                     instrument=["acis-s", "hrc-s"],
                                     grating=["letg"])

    Notes
    -----
    This routine tries to use Python's inbuilt https support, but
    if this fails it will fall through to trying with curl then wget.

    """

    url = construct_query(ra, dec, size,
                          instrument=instrument)

    if grating is not None:
        # we don't use grating in the query but want to validate
        # the value before making a query
        gfilters = [_fconv("grating", i) for i in set(grating)]
    else:
        gfilters = None

    out = _make_query(url)

    # It appears you can not filter on grating using the SIA
    # interface, so do it manually (if there is any filtering
    # needed).
    #
    nsearch = len(out)
    if out is None or nsearch == 0:
        v3("Search returned no matches")
        return None

    if grating is None:
        v3(f"Search returned {nsearch} rows")
        return out

    v3(f"Original search has {nsearch} rows")
    v3(f"Applying grating filters: {gfilters}")
    idx = False
    for g in gfilters:
        idx |= out['Grating'] == g

    nmatch = idx.sum()
    if nmatch > 0:
        v3(f"Filtering leaves {nmatch} rows")
        return out[idx]

    v3("Filtered out all rows")
    return None


# Why not return a sturctured array?

def get_chandra_obs(sr, ra=None, dec=None, fmt=None):
    """Given the return value from search_chandra_archive,
    return an OrderedDict with the following data, one
    row per observation:

      obsid
      instrument
      grating
      exposure       in ks
      ra             aim point ra in degrees
      dec            aim point dec in degrees
      target         target name
      obsdate
      piname         last name of PI

    If ra and dec are given (as decimal degrees) then we also
    create the column:

      separation     separation of aim point from ra,dec in arcminute

    If fmt is not None then it is used as a format specifier to create
    string versions of the aim point columns; the supported values are
    those of coords.format.deg2ra and coords.format.deg2dec

      rastr          ra in format given by fmt
      decstr         dec in format given by fmt

    The values are stored in Python lists, not NumPy arrays.

    """

    colmap = [('ObsId', 'obsid'),
              ('Instrument', 'instrument'),
              ('Grating', 'grating'),
              ('Exposure', 'exposure'),
              ('RA', 'ra'),
              ('Dec', 'dec'),
              ('target_name', 'target'),
              ('obs_date', 'obsdate'),
              ('pi_last_name', 'piname')]

    seen = set()
    out = OrderedDict()
    for (n1, n2) in colmap:
        out[n2] = []

    # Could use NumPy filtering here but just go for a per-row approach
    # at this time.
    #
    for row in sr:
        obsid = row['ObsId']
        if obsid not in seen:
            for (n1, n2) in colmap:
                out[n2].append(row[n1])

            seen.add(obsid)

    # add in any extra columns
    rr = out['ra']
    dd = out['dec']

    if fmt is not None:
        out['rastr'] = [coords.deg2ra(r, fmt) for r in rr]
        out['decstr'] = [coords.deg2dec(d, fmt) for d in dd]

    if ra is not None and dec is not None:
        out['separation'] = [60 * cutils.point_separation(ra, dec, r, d)
                             for (r, d) in zip(rr, dd)]

    return out

# End
