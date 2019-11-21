#
#  Copyright (C) 2010, 2011, 2012, 2014, 2015, 2016, 2019
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

"""Find the version numbers and release dates of the Chandra CALDB.
"""

import os
import copy
import socket
import time

from html.parser import HTMLParser
from urllib.request import urlopen
from urllib.error import URLError

import pycrates

from ciao_contrib import logger_wrapper as lw


__all__ = (
    "check_caldb_version",
    "get_caldb_dir",
    "get_caldb_releases",
    "get_caldb_installed",
    "get_caldb_installed_version",
    "get_caldb_installed_date"
)

lgr = lw.initialize_module_logger('caldb')
v3 = lgr.verbose3


release_notes_url = "https://cxc.cfa.harvard.edu/caldb/downloads/releasenotes.html"


def todate(txt):
    """Convert text to time.

    This is intended to convert a time string, as reported by the
    CALDB web pages, to a time object.

    Parameters
    ----------
    txt : str or None
        The time string.

    Returns
    -------
    val : time object or str or None
        If the input can be converted to a time object then that
        object is returned, otherwise the input is returned unchanged.
    """

    if txt is None:
        return None

    try:
        return time.strptime(txt + "UTC", "%Y-%m-%dT%H:%M:%S%Z")
    except ValueError:
        return txt


# The current version has the main data in a td with class=mainbar
# but this is hopefully going to change RSN for a div (as this comment
# was written a long time ago it obviously hasn't happened).
#
class CALDBReleaseParser(HTMLParser):
    """Extract relevant fields from the CIAO CALDB web page.

    Parse the CALDB release-notes HTML page for
    release information on the CALDB.

    Raises
    ------
    IOError
        This can be caused if the result is empty (at least for the
        CALDB release column); the page can not be parsed (e.g. it
        does not match the expected contents). The error messages
        are not 'user friendly' since they may reveal the internal
        state of the object to make debugging easier.

    Examples
    --------

    The use is, where h is a string containing the HTML to parse:

    >>> p = CALDBReleaseParser()
    >>> p.feed(h)
    >>> p.close()

    and then the p.releases field is a dictionary where the keys are
    the various CALDB release types (e.g. CALDB, SDP, CIAO, and L3)
    and the values are tuples of (version number, date) where the
    version number is a string and the date is a time object.

    """

    state = "need-table"
    open_mode = {"need-table":
                 {"tag": "table",
                  "attribute": ("id", "caldbver"),
                  "newstate": "check-header"
                  },
                 }

    close_mode = {"check-header": {"tag": "tr",
                                   "newstate": "store-data"},
                  "store-data": {"tag": "table",
                                 "newstate": "finished"}
                  }

    store = []
    row_store = None
    item_store = None

    def close(self):
        HTMLParser.close(self)
        if self.state != "finished":
            raise IOError("incorrectly-nested tables; state={}".format(self.state))

        st = self.store

        def make(i):
            return [(s[0], s[i]) for s in st if s[i] is not None]

        self.releases = {"CALDB": make(1),
                         "SDP": make(2),
                         "CIAO": make(3),
                         "L3": make(4)}

        if len(self.releases["CALDB"]) == 0:
            raise IOError("No CALDB release information found!")

    def handle_starttag(self, tag, attrs):
        if self.state == "store-data":
            # Could do the storing via a pseudo state machine as we do with
            # finding the table, but just hard code the logic for now
            #
            if self.row_store is None:
                if tag == "tr":
                    self.row_store = []
                else:
                    raise IOError("A new row has started with the tag: {}".format(tag))
            if tag == "td":
                if self.item_store is None:
                    self.item_store = ""
                else:
                    raise IOError("A new item has started but the item_store=[{}]".format(self.item_store))
            return

        if self.state not in self.open_mode:
            return

        tbl = self.open_mode[self.state]

        if tag != tbl["tag"] or \
                ("attribute" in tbl and tbl["attribute"] not in attrs):
            return

        if "newstate" in tbl:
            self.state = tbl["newstate"]

    def handle_endtag(self, tag):
        if self.state == "store-data":
            if tag == "td":
                item = self.item_store.strip()
                if item.lower() in ["n/a", "not released publicly"]:
                    self.row_store.append(None)
                else:
                    self.row_store.append(item)
                self.item_store = None

            elif tag == "tr":
                r = self.row_store
                if len(r) != 5:
                    raise IOError("Unable to parse row: {0}".format(r))
                self.store.append((r[0],
                                   todate(r[1]),
                                   todate(r[2]),
                                   todate(r[3]),
                                   todate(r[4])))

                self.row_store = None

        if self.state not in self.close_mode:
            return

        tbl = self.close_mode[self.state]
        if tag != tbl["tag"]:
            return

        self.state = tbl["newstate"]

    def handle_data(self, data):
        if self.state == "store-data" and self.item_store is not None:
            ds = data.strip()
            if ds is not None:
                if self.item_store == "":
                    self.item_store = ds
                else:
                    self.item_store += " {0}".format(ds)


def get_caldb_releases(timeout=None):
    """Return information on the CIAO CALDB releases.

    Extracts the CIAO CALDB release history from the web page.

    Parameters
    ----------
    timeout : optional
        The timeout option for the urlopen call. If not set then the
        global Python timeout setting will be used. If given then it
        is the maximum time to wait in seconds.

    Returns
    -------
    releases : dict
        The keys are the names "CALDB", "SDP", "CIAO" or "L3",
        and the values are arrays of (version-string, date) tuples.
        There is no guarantee that the lists are in descending order
        of time or version number.

    Raises
    ------
    IOError
        Many network errors are converted to an IOError with a
        simple error message.

    Notes
    -----
    This routine will only work if the computer is on-line and able to
    access the Chandra CALDB pages at

      https://cxc.cfa.harvard.edu/caldb/

    This call turns off certificate validation for the requests since
    there are issues with getting this working on all supported platforms.
    It *only* does it for the calls it makes (i.e. it does not turn
    off validation of any other requests).

    The version-string is "1.2" or "4.2.2" and the date is a time
    object.

    """

    import ssl

    # Note that the SSL context is explicitly
    # set to stop verification, because the CIAO 4.12 release has
    # seen some issues with certificate validation (in particular
    # on Ubuntu and macOS systems).
    #
    context = ssl._create_unverified_context()

    v3("About to download {}".format(release_notes_url))
    try:
        if timeout is None:
            h = urlopen(release_notes_url, context=context)
        else:
            h = urlopen(release_notes_url, context=context, timeout=timeout)

    except URLError as ue:
        v3(" - failed with {}".format(ue))
        # Probably excessive attempt to make a "nice" error message
        #
        if hasattr(ue, "reason"):
            if hasattr(ue.reason, "errno") and \
               ue.reason.errno == socket.EAI_NONAME:
                raise IOError("Unable to reach the CALDB site - is the network down?")
            else:
                raise IOError("Unable to reach the CALDB site - {}".format(ue.reason))

        elif hasattr(ue, "getcode"):
            cval = ue.getcode()
            if cval == 404:
                raise IOError("The CALDB site appears to be unreachable.")
            else:
                raise IOError("The CALDB site returned {}".format(ue))

        else:
            raise IOError("Unable to access the CALDB site - {}".format(ue))

    h = h.read().decode('utf-8')

    try:
        p = CALDBReleaseParser()
        p.feed(h)
        p.close()
    except IOError:
        raise IOError("Unable to parse the CALDB release table.")

    # use a deep copy so that the parser can be cleaned up
    # in case there's a lot of state squirreled away
    # (although have not checked that it actually matters)
    return copy.deepcopy(p.releases)


def get_caldb_dir():
    """Return the location of the CIAO CALDB.

    Returns
    -------
    path : str
        The location of the CIAO CALDB, as given by the CALDB
        environment variable.

    Raises
    ------
    IOError
        If the CALDB environment variable is not defined or does
        not point to a directory.

    """

    caldb = os.getenv("CALDB")
    if caldb is None:
        raise IOError("CALDB environment variable is not defined!")
    elif not os.path.isdir(caldb):
        raise IOError("CALDB directory does not exist: {}".format(caldb))
    else:
        return caldb


def get_caldb_installed(caldb=None):
    """What CIAO CALDB is installed (version and release date)?

    Parameters
    ----------
    caldb : str, optional
        If set, the directory to search in, otherwise the
        CALDB environment variable is used.

    Returns
    -------
    version, date
        The CIAO CALDB version, as a string, and the release date
        of the version (as a date object) of the installed
        CIAO CALDB.

    See Also
    --------
    get_caldb_installed_date, get_caldb_installed_version

    """

    if caldb is None:
        caldb = get_caldb_dir()
    fname = os.path.join(caldb,
                         "docs/chandra/caldb_version/caldb_version.fits")
    cr = pycrates.TABLECrate(fname, mode='r')

    for cname in ["CALDB_VER", "CALDB_DATE"]:
        if not cr.column_exists(cname):
            raise IOError("Unable to find the {} column in the CALDB version file.".format(cname))

    cversion = pycrates.copy_colvals(cr, "CALDB_VER")[-1]
    cdate = pycrates.copy_colvals(cr, "CALDB_DATE")[-1]

    cversion = cversion.strip()
    cdate = cdate.strip()

    return (cversion, todate(cdate))


def get_caldb_installed_version(caldb=None):
    """What CIAO CALDB is installed (version)?

    Parameters
    ----------
    caldb : str, optional
        If set, the directory to search in, otherwise the
        CALDB environment variable is used.

    Returns
    -------
    version : str
        The CIAO CALDB version, as a string.

    See Also
    --------
    get_caldb_installed, get_caldb_installed_date

    """

    return get_caldb_installed(caldb)[0]


def get_caldb_installed_date(caldb=None):
    """What CIAO CALDB is installed (release date)?

    Parameters
    ----------
    caldb : str, optional
        If set, the directory to search in, otherwise the
        CALDB environment variable is used.

    Returns
    -------
    date
        The release date of the version (as a date object) of the
        installed CIAO CALDB.

    See Also
    --------
    get_caldb_installed, get_caldb_installed_version

    """

    return get_caldb_installed(caldb)[1]


def version_to_tuple(version):
    """Convert CALDB version string to a tuple.

    Parameters
    ----------
    version : str
        A CALDB version string like '4.4.10',

    Returns
    -------
    version : tuple of int
        The tuple of integers representing the input version. The
        number of elements in the tuple depends on the input.
    """

    toks = version.split('.')
    try:
        out = [int(t) for t in toks]
    except ValueError:
        raise ValueError("Invalid version string '{}'".format(version))

    return tuple(out)


def check_caldb_version(version=None):
    """Is the locally-installed Chandra CALDB installation up-to-date?

    The routine requires that the computer is on-line and able to
    access the Chandra CALDB web site: https://cxc.harvard.edu/caldb/

    Parameters
    ----------
    version : str, optional
        The version to compare to the latest released Chandra CALDB
        (as obtained from https://cxc.harvard.edu/caldb/). If not
        set then the version from the locally-installed Chandra CALDB
        is used. The format for the string is integer values separated
        by ".", such as "4.7.2".

    Returns
    -------
    retval : None or (str, str)
        If the installation is up to date then the routine returns
        None, otherwise it returns the tuple
        (version checked against, latest version).

    Raises
    ------
    IOError
        If the version parameter is given but does not match a CALDB
        release.

    """

    # Converting the dotted string form (4.2.1 or 3.2.0.1) to
    # a tuple of integers means we can just use Python's comparison
    # operator and it handles cases like
    #
    # >>> (4,2,1) > (3,2,0,1)
    #     True
    # >>> (4,2,2) > (4,2,2,2)
    #     False
    #
    # We are relying on the CALDB release numbers to be dotted
    # integers, with no alphanumerics (i.e. not 4.4.1a)
    #
    rels = get_caldb_releases()
    if version is None:
        installed_ver = get_caldb_installed_version()
    else:
        installed_ver = version

        # We check against the CALDB release numbers rather than
        # the CALDB ones, since they form the "complete" set.
        # Should perhaps be case insensitive but leave that for
        # a later revision.
        #
        if version not in [v[0] for v in rels["CALDB"]]:
            raise IOError("The input CALDB version '{}' is unknown!".format(version))

    iver = version_to_tuple(installed_ver)
    out = [v for (v, d) in rels["CIAO"] if version_to_tuple(v) > iver]
    if out == []:
        return

    out.sort(reverse=True)
    return (installed_ver, out[0])

# End
