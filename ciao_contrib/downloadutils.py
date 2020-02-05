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

Stability
---------

This is an internal module, and so the API it provides is not
considered stable (e.g. we may remove this module at any time). Use
at your own risk.

"""

import ssl

from io import BytesIO
from subprocess import check_output

import urllib.error
import urllib.request

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
           'find_all_downloadable_files')


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
    response : StringIO instance
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
    there's no other links on the page, and the parent directory
    is listed as 'parent directory' (after removing the white space
    and converting to lower case).
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

        # Skip the link to the parent directory
        data = data.strip()
        if data.lower() == 'parent directory':
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
    """

    no_context = ssl._create_unverified_context()
    req = urllib.request.Request(urlname, headers=headers)
    try:
        with urllib.request.urlopen(req, context=no_context) as rsp:
            html_contents = rsp.read().decode('utf-8')

    except urllib.error.URLError as ue:
        v2("URLError for {}".format(urlname))
        v2(str(ue))
        try:
            emsg = "Unable to reach {}\n{}".format(urlname, ue.reason)
        except KeyError:
            try:
                is404 = ue.code == 404
            except KeyError:
                raise IOError("Unable to access {}\n{}".format(urlname, ue))

            if is404:
                emsg = "There is no directory {}".format(urlname)
            else:
                emsg = "Unable to access {}\ncode={}".format(urlname, ue.code)

        raise IOError(emsg)

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
