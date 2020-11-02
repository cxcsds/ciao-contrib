#
#  Copyright (C) 2018, 2020
#            Smithsonian Astrophysical Observatory
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
Support downloading data from URLs in CIAO.

A collection of routines related to data download used in CIAO.

retrieve_url
------------

CIAO 4.11 does not include any SSL support, instead relying on the OS.
This can cause problems on certain platforms. So try with Python and
then fall through to curl or wget. This can hopefully be removed for
CIAO 4.12 or later, but kept in just for now.

find_downloadable_files
-----------------------

Given a URL of a directory, return the files and sub-directories
available. This requires that the web server supports the Apache
mod_autoindex functionality, and is written for accessing the
Chandra Data Archive. Support for other web sites is not guaranteed.

find_all_downloadable_files
---------------------------

Similar to find_downloadble_files but recurses through all sub-directories.

ProgressBar
-----------

Display a "progress" bar, indicating the progress of a download.
This has very-limited functionality.

download_progress
-----------------

Download a URL to a file, supporting

  - continuation of a previous partial download
  - a rudimentary progress bar to display progress

Stability
---------

This is an internal module, and so the API it provides is not
considered stable (e.g. we may remove this module at any time). Use
at your own risk.

"""

import os
import sys
import ssl
import time

from io import BytesIO
from subprocess import check_output

import urllib.error
import urllib.request
import http.client

from html.parser import HTMLParser

import ciao_contrib.logger_wrapper as lw

logger = lw.initialize_module_logger("downloadutils")

v0 = logger.verbose0
v1 = logger.verbose1
v2 = logger.verbose1
v3 = logger.verbose3
v4 = logger.verbose4


__all__ = ('retrieve_url',
           'find_downloadable_files',
           'find_all_downloadable_files',
           'ProgressBar',
           'download_progress')


def manual_download(url):
    """Try curl then wget to query the URL.

    Parameters
    ----------
    url : str
        The URL for the query; see construct_query

    Returns
    -------
    ans : StringIO instance
        The response

    """

    v3("Fall back to curl or wget to download: {}".format(url))

    # Should package this up nicely, but hardcode for the moment.
    #
    # It is not clear if this is sufficient to catch "no curl"
    # while allowing errors like "no access to the internet"
    # to not cause too much pointless work.
    #
    args = ['curl', '--silent', '-L', url]
    v4("About to execute: {}".format(args))

    try:
        rsp = check_output(args)

    except FileNotFoundError as exc1:
        v3("Unable to call curl: {}".format(exc1))
        args = ['wget', '--quiet', '-O-', url]
        v4("About to execute: {}".format(args))

        try:
            rsp = check_output(args)

        except FileNotFoundError as exc2:
            v3("Unable to call wget: {}".format(exc2))
            emsg = "Unable to access the URL {}.\n".format(url) + \
                   "Please install curl or wget (and if you " + \
                   "continue to see this message, contact the " + \
                   "CXC HelpDesk)."
            raise RuntimeError(emsg)

    return BytesIO(rsp)


def retrieve_url(url, timeout=None):
    """Handle possible problems retrieving the URL contents.

    Using URLs with the https scheme causes problems for certain OS
    set ups because CIAO 4.11 does not provide SSL support, but relies
    on the system libraries to work. This is "supported" by falling
    over from Python to external tools (curl or wget).

    Parameters
    ----------
    url : str
        The URL to retrieve.
    timeout : optional
        The timeout parameter for the urlopen call; if not
        None then the value is in seconds.

    Returns
    -------
    response : HTTPResponse instance
        The response

    """

    try:
        v3("Retrieving URL: {} timeout={}".format(url, timeout))
        if timeout is None:
            return urllib.request.urlopen(url)
        return urllib.request.urlopen(url, timeout=timeout)

    except urllib.error.URLError as ue:
        v3("Error opening URL: {}".format(ue))
        v3("error.reason = {}".format(ue.reason))

        # Assume this is the error message indicating "no SSL support"
        # There is a new (in CIAO 4.11) message
        # "urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:719)"
        #
        # It appears that the reason attribute can be an object, so
        # for now explicitly convert to a string:
        reason = str(ue.reason)
        if reason.find('unknown url type: https') != -1 or \
           reason.find('CERTIFICATE_VERIFY_FAILED') != -1:
            return manual_download(url)

        # There used to be a check on the reason for the error,
        # converting it into a "user-friendly" message, but this
        # was error prone (the check itself was faulty) and
        # potentially hid useful error information. So just
        # re-raise the error here after logging it.
        #
        raise


class DirectoryContents(HTMLParser):
    """Extract the output of the mod_autoindex Apache directive.

    Limited testing. It assumes that the files are given as links,
    there's no other links on the page, and the parent directory is
    listed as 'parent directory' (after removing the white space and
    converting to lower case). There is special casing to remove links
    where the text does not match the name of the link. This is to
    handle query fragments, which are used to change the ordering of
    the table display rather than be an actual link.

    """

    def __init__(self, *args, **kwargs):
        self.dirs = []
        self.files = []
        self.current = None
        super().__init__(*args, **kwargs)

    def add_link(self):
        """We've found a link, add it to the store"""
        if self.current is None:
            return

        if self.current.endswith('/'):
            store = self.dirs
        else:
            store = self.files

        store.append(self.current)
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag.upper() != 'A':
            return

        # In case we have a missing close tag
        self.add_link()

        attrs = dict(attrs)
        try:
            href = attrs['href']
        except KeyError:
            raise ValueError("Missing href attribute for a tag")

        self.current = href

    def handle_endtag(self, tag):
        # do not expect end tags within <a> here, so we can
        # treat it as the end of the a link if we find it
        # (to support missing end tags).
        #
        if self.current is None:
            return

        self.add_link()

    def handle_data(self, data):
        if self.current is None:
            return

        # Skip the link to the parent directory, and skip any where
        # the text is different to the href (e.g. to catch query-only
        # links which are used to change the display rather than being
        # a link).
        #
        data = data.strip()
        if data.lower() == 'parent directory':
            self.current = None
        elif self.current != data:
            v4(f"Dropping link={self.current} as test={data}")
            self.current = None


def unpack_filelist_html(txt, baseurl):
    """Extract the contents of the page (assumed to be a directory listing).

    Parameters
    ----------
    txt : str
        The HTML contents to parse.
    baseurl : str
        The URL of the page.

    Returns
    -------
    urls : dict
        The keys are directories and files, and the contents are
        a list of absolute URLs (as strings).

    """

    parser = DirectoryContents()
    parser.feed(txt)

    if not baseurl.endswith('/'):
        baseurl += '/'

    dirs = [baseurl + d for d in parser.dirs]
    files = [baseurl + f for f in parser.files]

    return {'directories': dirs, 'files': files}


def find_downloadable_files(urlname, headers):
    """Find the files and directories present in the given URL.

    Report the files present at the given directory, for those
    web servers which support an Apache-like mod_autoindex
    function (i.e. return a HTML file listing the files and
    sub-directories).

    Parameters
    ----------
    urlname : str
        This must represent a directory.
    headers : dict
        The headers to add to the HTTP request (e.g. user-agent).

    Returns
    -------
    urls : dict
        The keys are directories and files, and the contents are
        a list of absolute URLs (as strings).

    See Also
    --------
    find_all_downloadable_files

    Notes
    -----
    This is intended for use with the Chandra Data Archive, and
    so there's no guarantee it will work for other web servers:
    they may not return the necessary information, or use a
    different markup.

    Requests are made with *no* SSL validation (since there are
    problems with CIAO 4.12 installed via ciao-install on a Ubuntu
    machine).

    There is no attempt to make a "nice" error message for a user
    here, as that is better done in the calling code.
    """

    no_context = ssl._create_unverified_context()
    req = urllib.request.Request(urlname, headers=headers)
    with urllib.request.urlopen(req, context=no_context) as rsp:
        html_contents = rsp.read().decode('utf-8')

    return unpack_filelist_html(html_contents, urlname)


def find_all_downloadable_files(urlname, headers):
    """Find the files present in the given URL, including sub-directories.

    Report the files present at the given directory and
    sub-directory, for those web servers which support an Apache-like
    mod_autoindex function (i.e. return a HTML file listing the files
    and sub-directories).

    Parameters
    ----------
    urlname : str
        This must represent a directory.
    headers : dict
        The headers to add to the HTTP request (e.g. user-agent).

    Returns
    -------
    urls : list of str
        A list of absolute URLs.

    See Also
    --------
    find_downloadable_files

    Notes
    -----
    This is intended for use with the Chandra Data Archive, and
    so there's no guarantee it will work for other web servers:
    they may not return the necessary information, or use a
    different markup.

    Requests are made with *no* SSL validation (since there are
    problems with CIAO 4.12 installed via ciao-install on a Ubuntu
    machine).
    """

    v3("Finding all files available at: {}".format(urlname))
    base = find_downloadable_files(urlname, headers)
    out = base['files']
    todo = base['directories']
    v4("Found sub-directories: {}".format(todo))

    while True:
        v4("Have {} sub-directories to process".format(len(todo)))
        if todo == []:
            break

        durl = todo.pop()
        v3("Recursing into {}".format(durl))
        subdir = find_downloadable_files(durl, headers)
        out += subdir['files']
        v4("Adding sub-directories: {}".format(subdir['directories']))
        todo += subdir['directories']

    return out


class ProgressBar:
    """A very-simple progress "bar".

    This just displays the hash marks for each segment of a
    download to stdout. It is called from the code doing the
    actual download. There is no logic to conditionally display
    the output in this class - for instance based on the
    current verbose setting - since this should be handled
    by the code deciding to call this obejct or not.

    Parameters
    ----------
    size : int
        The number of bytes to download.
    nhash : int
        The number of hashes representing the full download
        (so each hash represents 100/nhash % of the file)
    hashchar : char
        The character to display when a chunk has been
        downloaded.

    Examples
    --------

    The bar is created with the total number of bytes to download,
    then it starts (with an optional number of already-downloaded
    bytes), and each chunk that is added is reported with the add
    method. Once the download has finished the end method is called.

    Note that the methods (start, add, and end) may cause output
    to stdout.

    >>> progress = ProgressBar(213948)
    >>> progress.start()
    ...
    >>> progress.add(8192)
    ...
    >>> progress.add(8192)
    ...
    >>> progress.end()

    """

    def __init__(self, size, nhash=20, hashchar='#'):
        if size < 0:
            raise ValueError("size can not be negative")
        if nhash < 1:
            raise ValueError("must have at least one hash")

        self.size = size
        self.nhash = nhash
        self.hashchar = hashchar

        self.hashsize = size // nhash
        self.hdl = sys.stdout
        self.added = 0
        self.hashes = 0

    def start(self, nbytes=0):
        """Initialize the download.

        Parameters
        ----------
        nbytes : int, optional
            The number of bytes of the file that has already been
            downloaded. If not zero this may cause hash marks to be
            displayed.
        """

        self.added = nbytes
        self.hashes = self.added // self.hashsize
        if self.hashes == 0:
            return

        self.hdl.write(self.hashchar * self.hashes)
        self.hdl.flush()


    def add(self, nbytes):
        """Add the number of bytes for this segment.

        This must only be called after start.

        Parameters
        ----------
        nbytes : int, optional
            The number of bytes added to the file.
        """

        if nbytes < 0:
            raise ValueError("nbytes must be positive")

        if nbytes == 0:
            return

        self.added += nbytes
        hashes = self.added // self.hashsize
        if hashes == self.hashes:
            return

        nadd = hashes - self.hashes
        self.hdl.write(self.hashchar * nadd)
        self.hdl.flush()

        self.hashes = hashes

    def end(self):
        """Finished the download.

        This is mainly to allow for handling of rounding errors.
        """

        nadd = self.nhash - self.hashes
        if nadd <= 0:
            return

        # Don't bother trying to correct for any rounding errors
        # if the file wasn't fully downloaded.
        #
        if self.added < self.size:
            return

        self.hdl.write(self.hashchar * nadd)
        self.hdl.flush()


def myint(x):
    """Convert to an integer, my way."""
    return int(x + 0.5)


def stringify_dt(dt):
    """Convert a time interval into a "human readable" string.

    Parameters
    ----------
    dt : number
        The number of seconds.

    Returns
    -------
    lbl : str
        The "human readable" version of the time difference.

    Examples
    --------

    >>> stringify_dt(0.2)
    '< 1 s'

    >>> stringify_dt(62.3)
    '1 m 2 s'

    >>> stringify_dt(2402.24)
    '40 m 2 s'

    """

    if dt < 1:
        return "< 1 s"

    d = myint(dt // (24 * 3600))
    dt2 = dt % (24 * 3600)
    h = myint(dt2 // 3600)
    dt3 = dt % 3600
    m = myint(dt3 // 60)
    s = myint(dt3 % 60)

    if d > 0:
        lbl = "%d day" % d
        if d > 1:
            lbl += "s"
        if h > 0:
            lbl += " %d h" % h

    elif h > 0:
        lbl = "%d h" % h
        if m > 0:
            lbl += " %d m" % m

    elif m > 0:
        lbl = "%d m" % m
        if s > 0:
            lbl += " %d s" % s

    else:
        lbl = "%d s" % s

    return lbl


def stringify_size(s):
    """Convert a file size to a text string.

    Parameters
    ----------
    size : int
        File size, in bytes

    Returns
    -------
    filesize : str
        A "nice" representation of the size

    Examples
    --------

    >>> stringify_size(1023)
    '< 1 Kb'

    >>> stringify_size(1024)
    '1 Kb'

    >>> stringify_size(1025)
    '1 Kb'

    >>> stringify_size(54232)
    '53 Kb'

    >>> stringify_size(4545833)
    '4 Mb'

    >>> stringify_size(45458330000)
    '4.2 Gb'

    """

    if s < 1024:
        lbl = "< 1 Kb"
    elif s < 1024 * 1024:
        lbl = "%d Kb" % (myint(s / 1024.0))
    elif s < 1024 * 1024 * 1024:
        lbl = "%d Mb" % (myint(s / (1024 * 1024.0)))
    else:
        lbl = "%.1f Gb" % (s / (1024 * 1024 * 1024.0))

    return lbl


def download_progress(url, size, outfile,
                      headers=None,
                      progress=None,
                      chunksize=8192,
                      verbose=True):
    """Download url and store in outfile, reporting progress.

    The download will use chunks, logging the output to the
    screen, and will not re-download partial data (e.g.
    from a partially-completed earlier attempt). Information
    on the state of the download will be displayed to stdout
    unless verbose is False. This routine requires that
    we already know the size of the file.

    Parameters
    ----------
    url : str
        The URL to download; this must be http or https based.
    size : int
        The file size in bytes.
    outfile : str
        The output file (relative to the current working directory).
        Any sub-directories must already exist.
    headers : dict, optional
        Any additions to the HTTP header in the request (e.g. to
        set 'User-Agent'). If None, a user-agent string of
        "ciao_contrib.downloadutils.download_progress" is
        used).
    progress : ProgressBar instance, optional
        If not specified a default instance (20 '#' marks) is used.
    chunksize : int, optional
        The chunk size to use, in bytes.
    verbose : bool, optional
        Should progress information on the download be written to
        stdout?

    Notes
    -----
    This routine assumes that the HTTP server supports ranged
    requests [1]_, and ignores SSL validation of the request.

    The assumption is that the resource is static (i.e. it hasn't
    been updated since content was downloaded). This means that it
    is possible the output will be invalid, for instance if it
    has increased in length since the last time it was fully
    downloaded, or changed and there was a partial download.

    References
    ----------

    .. [1] https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests

    """

    # I used http.client rather than urllib because I read somewhere
    # that urllib did not handle streaming requests (e.g. it would just
    # read in everything in one go and then you read from the in-memory
    # buffer).
    #
    # From https://stackoverflow.com/a/24900110 - is it still true?
    #
    purl = urllib.request.urlparse(url)
    if purl.scheme == 'https':
        no_context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(purl.netloc, context=no_context)

    elif purl.scheme == 'http':
        conn = http.client.HTTPConnection(purl.netloc)

    else:
        raise ValueError("Unsupported URL scheme: {}".format(url))

    startfrom = 0
    try:
        fsize = os.path.getsize(outfile)
    except OSError:
        fsize = None

    if fsize is not None:
        equal_size = fsize == size
        v3("Checking on-disk file size " +
           "({}) against archive size ".format(fsize) +
           "({}): {}".format(size, equal_size))

        if equal_size:
            if verbose:
                # Ugly, since this is set up to match what is needed by
                # ciao_contrib.cda.data.ObsIdFile.download rather than
                # being generic. Need to look at how messages are
                # displayed.
                #
                sys.stdout.write("{:>20s}\n".format("already downloaded"))
                sys.stdout.flush()

            return (0, 0)

        if fsize > size:
            v0("Archive size is less than disk size for " +
               "{} - {} vs {} bytes.".format(outfile,
                                             size,
                                             fsize))
            return (0, 0)

        startfrom = fsize

    try:
        outfp = open(outfile, 'ab')
    except IOError:
        raise IOError("Unable to create '{}'".format(outfile))

    # Is this seek needed?
    if startfrom > 0 and outfp.tell() == 0:
        outfp.seek(0, 2)

    if progress is None:
        progress = ProgressBar(size)

    if headers is None:
        headers = {'User-Agent':
                   'ciao_contrib.downloadutils.download_progress'}
    else:
        # Ensure we copy the header dictionary, since we are going
        # to add to it. It is assumed that a shallow copy is
        # enough.
        #
        headers = headers.copy()

    # Could hide this if startfrom = 0 and size <= chunksize, but
    # it doesn't seem worth it.
    #
    headers['Range'] = 'bytes={}-{}'.format(startfrom, size - 1)

    time0 = time.time()
    conn.request('GET', url, headers=headers)
    with conn.getresponse() as rsp:

        # Assume that rsp.status != 206 would cause some form
        # of an error so we don't need to check for this here.
        #
        if verbose:
            progress.start(startfrom)

        # Note that the progress bar reflects the expected size, not
        # the actual size; this may not be ideal (but don't expect the
        # sizes to change so it doesn't really matter).
        #
        while True:
            chunk = rsp.read(chunksize)
            if not chunk:
                break

            outfp.write(chunk)
            if verbose:
                progress.add(len(chunk))

        if verbose:
            progress.end()

    time1 = time.time()
    nbytes = outfp.tell()
    outfp.close()

    dtime = time1 - time0
    if verbose:
        rate = (nbytes - startfrom) / (1024 * dtime)
        tlabel = stringify_dt(dtime)
        sys.stdout.write("  {:>13s}  {:.1f} kb/s\n".format(tlabel, rate))

    if size != nbytes:
        v0("WARNING file sizes do not match: expected {} but downloaded {}".format(size, nbytes))

    return (nbytes, dtime)
