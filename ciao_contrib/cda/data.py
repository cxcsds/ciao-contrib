#
#  Copyright (C) 2010, 2011, 2013, 2014, 2015, 2016, 2017, 2019, 2020, 2021
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
Download publically-available data from the Chandra Data Archive (CDA).

Routines that wrap up HTTPS access to the Chandra Data Archive -
https://cxc.harvard.edu/cdaftp/ - supporting mirror sites under the
assumption that they have the same directory structure and login
support as the CDA.

This code can be used but please be aware that it is not considered
stable, so there may well be API changes.

Example with no screen output:

  out = download_chandra_obsids([1843, 1844])

Example with screen output:

  import ciao_contrib.logger_wrapper as lw
  lw.initialize_logger("download", verbose=1)
  out = download_chandra_obsids([1843, 1844],
             ["vv", "evt1", "asol", "bpix", "mtl"])

"""

import sys
import os
import os.path

import ssl
import urllib.parse
import urllib.request

from operator import itemgetter

import ciao_contrib.logger_wrapper as lw
from ciao_contrib import downloadutils


__init__ = ("download_chandra_obsids", )

BASE_URL = 'https://cxc.cfa.harvard.edu/cdaftp/'

LOGGER = lw.initialize_module_logger("cda.data")

V1 = LOGGER.verbose1
V3 = LOGGER.verbose3

__MIRROR_ENVIRON = "CDA_MIRROR_SITE"


def get_mirror_location(useropt):
    """Returns the mirror location, if set, otherwise None. If useropt
    is not empty or None then this is returned, otherwise the value of
    the CDA_MIRROR_SITE environment variable is returned (if set),
    otherwise returns None.

    Only minor syntactic checks are made (no attempt is made to
    connect to the server).
    """

    if useropt is not None and useropt.strip() != "":
        useropt = useropt.strip()
        V3(f"Using user-defined mirror: {useropt}")
        return useropt

    try:
        ans = os.environ[__MIRROR_ENVIRON].strip()
        if ans != "":
            V3(f"Using ${__MIRROR_ENVIRON}={ans}")
            return ans

    except KeyError:
        pass

    V3("Using CDA HTTPS site")
    return None


# The order of these is important as we want the most specific first -
# e.g. src2 before src.  This list also includes types which are
# special-cased - e.g. oif and vv
#
known_file_types = [
    "oif", "vv", "bpix", "fov", "evt2", "src2",
    "cntr_img", "full_img", "src_img",
    "asol", "eph0", "eph1",
    "aoff", "evt1a", "evt1", "flt", "msk", "mtl", "soff", "stat",
    "arf", "rmf",  # assume these are the correct tokens
    "bias", "pbk",
    "osol", "aqual",
    "sum", "pha2", "dtf", "plt",
    "adat",  # adat71 are PCAD Level 1 ACA image data files,
    "vvref",
    "readme"
]
known_file_types_str = known_file_types[:]
known_file_types_str.sort()
known_file_types_str = " ".join(known_file_types_str)


def extract_file_type(filename):
    """Return the 'type' of the given file, e.g. "evt2", "asol1".

    Returns None for an unrecognized file type.
    """

    if filename == "oif.fits":
        return "oif"
    if filename.lower() == "00readme":
        return "readme"
    if 'vv2' in filename:
        return "vv"
    if 'vvref2' in filename:
        return "vvref"

    for ftype in known_file_types:
        suffix = f'_{ftype}'
        if suffix in filename:
            return ftype

    return None


known_file_formats = ["fits", "jpg", "pdf", "ps", "html", "ascii"]
known_file_formats.sort()


def extract_file_format(filename):
    """Returns "ascii", "fits", "jpg", "pdf", or None depending of the
    file name.
    """

    if filename == "00README":
        return "ascii"

    for fformat in known_file_formats:
        if filename.find(fformat) != -1:
            return fformat

    return None


def create_directory(dname):
    """Create the directory if it does not exist. It will
    create any necessary parent directories.
    """

    if dname == "" or os.path.exists(dname):
        return

    V3(f"Creating directory: '{dname}'")
    if dname[-1] == "/":
        parent = os.path.dirname(dname[:-1])
    else:
        parent = os.path.dirname(dname)

    if not os.path.exists(parent):
        create_directory(parent)

    os.mkdir(dname, 0o777)


class ObsIdFile:
    """A file that is part of a Chandra ObsId.

    It is used to allow the file to be easily downloaded
    rather than as something useful for data analysis.
    """

    def __init__(self, obsid, url):
        """Create a record for the given file.
        """

        # should parse the url and then extract the component properly
        # but do it this way for simplicity
        #
        toks = url.strip().split('/')
        filename = toks[-1]
        if filename == '':
            raise ValueError(f"Sent a directory, not a file: {url}")

        self.obsid = str(obsid)
        self.url = url
        self.filename = filename
        self.filetype = extract_file_type(filename)
        self.fileformat = extract_file_format(filename)

        # work out the subdirectory path for this file; should this
        # be sent in here?
        #
        while True:
            try:
                tok = toks.pop(0)
            except IndexError:
                raise ValueError(f'Expected URL to include /byobsid/ fragment: {url}')

            if tok == 'byobsid':
                break

        if len(toks) < 3:
            raise ValueError(f'Expected more directories: {url}')

        toks.pop(0)

        # can now combine the rest to get the path (dropping the actual
        # file name)
        self.localpath = '/'.join(toks[:-1])

        self.filesize = None

    def is_type(self, types):
        """Given a list of file types, returns True if
        the file is one of these types."""
        return self.filetype in types

    def is_format(self, formats):
        """Given a list of file formats, returns True if
        the file is one of these formats."""
        return self.fileformat in formats

    def get_filesize(self, headers):
        """Returns the file size in bytes.

        The hdr value is added to the request header to enable the
        user-agent to be changed (or any other header).

        This approach is left-over from the previous FTP code,
        where we could get the size easily. This should now
        probably just be folded into the download code.
        """

        if self.filesize is not None:
            return self.filesize

        V3(f"Finding size of: {self.url}")

        req = urllib.request.Request(self.url, headers=headers)
        try:
            no_context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=no_context) as rsp:
                try:
                    size = int(rsp.info().get('content-length', 0))
                except ValueError:
                    size = 0

        except urllib.error.URLError as uerr:
            V3(f"Unable to get size of {self.url} - {uerr}")
            size = 0

        self.filesize = size
        return self.filesize

    def get_download_line_header(self, slabel):
        """Return the start of the download information
        for this object. slabel is a string representation of the
        file size."""

        if self.filetype is None:
            ftype = ""
        else:
            ftype = self.filetype

        return f"  {ftype:8s} {self.fileformat:6s} {slabel:>9s}  "

    def download(self, headers):
        """Download the file.

        The file is written to the location obsid/filename and screen
        output will be displayed to indicate the process of the
        transfer unless the logging verbose level is set to 0.

        If the file already exists AND has a size equal to the archive
        size then we skip. If the size is smaller then we try to
        resume the download. If the size is larger then we skip, but
        with a warning message.

        The return value is a tuple of number of bytes and download
        time in seconds (if nothing is downloaded then the values are
        set to 0).
        """

        verbose = LOGGER.getEffectiveVerbose() > 0

        V3(f"Starting download of {self.filename}")
        size = self.get_filesize(headers)

        if self.localpath != '':
            create_directory(self.localpath)

        outfile = os.path.join(self.localpath, self.filename)

        # Can not use V1 here since do not want to add an end-of-line
        # character
        if verbose:
            slabel = downloadutils.stringify_size(size)
            sys.stdout.write(self.get_download_line_header(slabel))

        return downloadutils.download_progress(self.url,
                                               size,
                                               outfile,
                                               headers=headers,
                                               verbose=verbose)


class ObsId:
    """Access the files for the given obsid.

    This was developed when FTP access was used; it may not be
    so useful now we've switched to HTTP.
    """

    def __init__(self, obsid, base_url, hdr):
        """Store the available files for the given obsid.

        Note that base_url is a string and not parsed URL.
        hdr is the dictionary containing the header keywords
        to add to any request.
        """

        self.obsid = obsid
        self.base_url = base_url
        self.header = hdr

        ostr = str(obsid)
        urlname = f"{base_url}/{ostr[-1]}/{ostr}"
        V3(f"Looking for directory: {urlname}")

        try:
            urls = downloadutils.find_all_downloadable_files(urlname, hdr)

        except urllib.error.HTTPError as herr:
            V3(f"HTTPError for {urlname}")
            V3(str(herr))
            if herr.code == 404:
                emsg = f"There is no directory {urlname}"
            else:
                emsg = f"Unable to access {urlname}\ncode={herr.code}"

            raise IOError(emsg)

        except urllib.error.URLError as uerr:
            V3(f"URLError for {urlname}")
            V3(str(uerr))
            emsg = f"Unable to reach {urlname}\n{uerr.reason}"
            raise IOError(emsg)

        self.files = [ObsIdFile(obsid, url) for url in urls]
        V3(f"Found {len(self.files)} files")

    def filter_files(self, types=None, excludes=None, formats=None):
        """Filter the list of files by the given types and/or formats.

        Parameters
        ----------
        types : sequence of str or None, optional
            What file types to select. If None then all files are
            selected, apart from the excludes setting.
        excludes : sequence of str or None, optional
            What file types to ignore. If None then the types setting
            is used. It is an error to define both types and excludes.
        formats : sequence of str or None, optinal
            What formats to include. If None then all formats are
            selected (after filtering by types or excludes).

        """

        if types is not None and excludes is not None:
            raise TypeError("types and excludes can not be both set")

        V3(f"Before filtering: {len(self.files)} files")

        if types is not None:
            self.files = [f for f in self.files if f.is_type(types)]

        elif excludes is not None:
            self.files = [f for f in self.files if not f.is_type(excludes)]

        if formats is not None:
            self.files = [f for f in self.files if f.is_format(formats)]

        V3(f"After filtering: {len(self.files)} files")

    def get_download_size(self):
        """Get the download size for the files in the ObsId,
        in bytes.

        This is quite expensive as it requires multiple requests
        to the HTTP server (at least the first time).
        """

        return sum([f.get_filesize(self.header) for f in self.files])

    def download(self):
        """Download the files for the ObsId to the current
        working directory.

        The screen output is determined by the logger instance.

        The downloads are done in order of decreasing file size.

        Files we can not download (e.g. doesn't exist or some other
        reason) are skipped. This is to support possible future
        changes in the HTML response from the archive.
        """

        V3(f"Downloading {len(self.files)} files")
        s = self.get_download_size()
        if s == 0:
            V1(f"No files found for ObsId {self.obsid}!")
            return

        size_label = downloadutils.stringify_size(s)
        V1(f"Downloading files for ObsId {self.obsid}, total size is {size_label}.\n")
        V1("  Type     Format      Size  0........H.........1  Download Time Average Rate")
        V1("  ---------------------------------------------------------------------------")

        nbytes = 0
        dtime = 0

        # re-order into decreasing file size; given that
        # get_download_size has been called we can use the
        # filesize attribute.
        #
        order = sorted([(f.filesize, f) for f in self.files],
                       key=itemgetter(0), reverse=True)

        for oelem in order:
            fileobj = itemgetter(1)(oelem)

            try:
                (a, b) = fileobj.download(self.header)
            except urllib.error.URLError as uerr:
                V1(f"SKIPPING {fileobj.filename} as {uerr}")
                continue

            nbytes += a
            dtime += b

        if LOGGER.getEffectiveVerbose() > 0:
            if len(self.files) > 1 and nbytes > 0:
                sys.stdout.write("\n")
                V1(f"      Total download size for ObsId {self.obsid} = {downloadutils.stringify_size(nbytes)}")
                V1(f"      Total download time for ObsId {self.obsid} = {downloadutils.stringify_dt(dtime)}")
            sys.stdout.write("\n")


def get_http_header():
    """Set up the user-agent setting.
    """

    return {'User-Agent': 'cxc/download-chandra-obsid'}


def download_chandra_obsids(obsids,
                            filetypes=None, excludes=None,
                            mirror=None
                            ):
    """Download the obsids from the Chandra Data Archive -
    https://cxc.harvard.edu/cda/ - or a mirror site.

    The data is written to the current working directory using the
    archive layout, so each ObsId has its own directory.

    Parameters
    ----------
    obsids : sequence of int
        The ObsId values to download.
    filetypes : sequence of str or None, optional
        If filetypes is None then all data for each obsid will be
        downloaded, otherwise it is an array of strings determining
        which files to download. See the known_file_types array in
        this module for the list of supported types.
    excludes : sequence of str or None, optional
        Those file types to ignore. It is expected that either (or
        both) filetypes or excludes is None. If they are both given
        then the filetypes setting "wins out" if a filetype is listed
        in both.
    mirror : str or None, optional
        If None then use the CDA HTTPS archive is used (the BASE_URL
        settign), otherwise set it to the name of a mirror archive to
        use that location instead. The value should refer to the
        directory that contains the "byobsid" directory.  The default
        value is equivalent to setting mirror to
        https://cxc.cfa.harvard.edu/cdaftp/. Note that this is not
        tested.

    Returns
    -------
    flags : list of bool
         The return value is an array of booleans that indicate
         whether the ObsId was available in the archive (it does not
         indicate whether any data was downloaded since files are
         skipped if they exist on disk).

    Notes
    -----
    With the move to HTTPS from FTP, the username and userpass
    arguments have been removed as they are now unused.

    This routine does *not* check the CDA_MIRROR_SITE environment
    variable if mirror=None (this is assumed to have been resolved by
    the time the routine has been called).

    The mirror site must have the same directory stucture as the CDA
    starting at the byobsid directory, but it need not contain all the
    data; the routine will just not be able to download the missing
    data sets; i.e. *no* fall over to the CDA archive is provided in
    this case).

    Screen output is controlled by the logging instance. By default
    the logger has no output set up, so you will see no screen
    output. To see the progress bars get displayed as files get
    downloaded try

      import ciao_contrib.logger_wrapper as lw
      lw.initalize_logger("download", verbose=1)

    before calling this routine (the first argument can be any
    string).

    Examples
    --------

    >>> download_chandra_obsid([1843, 1557])

    >>> download_chandra_obsid([1843, 1557], filetypes=['evt2', 'asol'])

    """

    if filetypes is not None and excludes is not None:
        filetypes = list(set(filetypes).difference(set(excludes)))
        excludes = None

    out = []

    if mirror is None:
        sitename = "archive"
        base_url = BASE_URL
    else:
        sitename = "mirror"
        base_url = mirror

    # validate this URL
    check = urllib.parse.urlparse(base_url)
    if check.scheme not in ["https", "http"]:
        raise ValueError(f"Require https/http URL, but sent {base_url}")

    # add on /byobsid
    if not base_url.endswith('/'):
        base_url += '/'

    base_url += "byobsid"

    hdr = get_http_header()

    for obsid in obsids:
        V3(f"Setting up for ObsId {obsid}")
        try:
            oid = ObsId(obsid, base_url, hdr)
        except IOError as ierr:
            V3(f"Unable to cd to ObsId {obsid}: msg={ierr}")
            V1(f"Skipping ObsId {obsid} as it was not found on the {sitename} site.")
            out.append(False)
            continue

        oid.filter_files(types=filetypes, excludes=excludes, formats=None)
        oid.download()
        out.append(True)

    return out

# End
