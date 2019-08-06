#
#  Copyright (C) 2010, 2011, 2013, 2014, 2015, 2016, 2017, 2019
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
Download publically-available data from the Chandra Data Archive (CDA).

Routines that wrap up FTP access to the Chandra Data Archive -
http://cxc.harvard.edu/cda/ - supporting mirror sites under the
assumption that they have the same directory structure and login
support as the CDA.

This code can be used but please be aware that it is not considered
stable, so there may well be API changes.

Example with no screen output:

  out = download_chandra_obsids([1843,1844])

Example with screen output:

  import ciao_contrib.logger_wrapper as lw
  lw.initialize_logger("download", verbose=1)
  out = download_chandra_obsids([1843,1844],
             ["evt1", "asol", "bpix", "mtl"])

"""

import sys
import os
import os.path
import time
import socket
import ftplib

from urllib.parse import urlparse

import ciao_contrib.logger_wrapper as lw

__init__ = ("download_chandra_obsids", )

DEFAULT_USERNAME = 'anonymous'
DEFAULT_PASSWORD = 'anonymous@ciao_contrib.cda.data'

logger = lw.initialize_module_logger("cda.data")

v0 = logger.verbose0
v1 = logger.verbose1
v3 = logger.verbose3


# Wrapper around a file for writing to write a hash sign every x%
# of the file has been downloaded.
#
# This is based on code from the Tools/scripts/ftpmirror.py in the
# Python distribution.
#
# Hashes are only output if the logging verbosity is set to >= 1,
# although the logger is not used to write out the text.
#
class LoggingFile:

    def __init__(self, fp, filesize, outfp, startfrom=None, nhash=20):
        """nhash is the number of hashes to print (so 100/nhash is the
        percentage of the file content for each #)."""
        if nhash < 1:
            raise ValueError("nhash must be >= 1, sent {}".format(nhash))
        self.fp = fp
        if startfrom is None:
            self.bytes = 0
        else:
            if startfrom > filesize:
                raise ValueError("startfrom > filesize ({} vs {})".format(startfrom, filesize))
            self.bytes = startfrom - 1
        self.hashes = 0
        self.filesize = filesize
        self.nhash = nhash
        self.blocksize = filesize / self.nhash
        self.outfp = outfp

    def write(self, data):
        self.bytes = self.bytes + len(data)
        hashes = int(self.bytes) / self.blocksize
        if logger.getEffectiveVerbose() > 0:
            while hashes > self.hashes:
                self.outfp.write('#')
                self.outfp.flush()
                self.hashes = self.hashes + 1

        self.fp.write(data)

    def close(self):
        # hack around rounding errors
        nh = self.nhash - self.hashes
        if logger.getEffectiveVerbose() > 0:
            if nh > 0 and self.bytes >= self.filesize:
                self.outfp.write('#' * nh)

            self.outfp.flush()


__mirror_environ = "CDA_MIRROR_SITE"


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
        v3("Using user-defined mirror: {}".format(useropt))
        return useropt

    try:
        ans = os.environ[__mirror_environ].strip()
        if ans != "":
            v3("Using ${}={}".format(__mirror_environ, ans))
            return ans

    except KeyError:
        pass

    v3("Using CDA FTP site")
    return None


# NOTE: use of os.path.join for the path manipulation for the FTP site
# is only going to work when the script is run on a machine for which
# the semantics matches that of UNIX, but that is the only supported
# platforms for CIAO.

class ChandraFTP(ftplib.FTP):
    """A container for the ftplib.FTP class, with
    additional fields to help identify mirrors for the
    Chandra Data Archive.
    """

    def __init__(self, host='', user='', passwd='', basedir=''):
        """Connect to a Chandra Data Archive mirror, where basedir is
        the location of the byobsid directory."""

        self.basedir = os.path.join(basedir, 'byobsid')
        v3("ChandraFTP: basedir={}".format(self.basedir))
        v3("Connecting to host={} user={} passwd={}".format(host,
                                                            user,
                                                            passwd))
        ftplib.FTP.__init__(self, host=host, user=user, passwd=passwd)


# The order of these is important as we want the most specific first -
# e.g. src2 before src.  This list also includes types which are
# special-cased - e.g. oif and vv
#
known_file_types = [
    "oif", "vv", "bpix", "fov", "evt2", "src2",
    "cntr_img", "full_img", "src_img",
    "asol", "eph0", "eph1",
    "aoff", "evt1a", "evt1", "flt", "msk", "mtl", "soff", "stat",
    "bias", "pbk",
    "osol", "aqual",
    "sum", "pha2", "dtf", "plt",
    "adat",  # adat71 are PCAD Level 1 ACA image data files,
    "readme"
]
known_file_types_str = known_file_types[:]
known_file_types_str.sort()
known_file_types_str = " ".join(known_file_types_str)


def extract_file_type(fname):
    """Return the 'type' of the given file, e.g. "evt2", "asol1".

    Returns None for an unrecognized file type.
    """

    if fname is None or fname.strip() == "":
        raise ValueError("No file given")
    fn = fname.strip()
    if fn[-1] == "/":
        return None

    if fn == "oif.fits":
        return "oif"
    if fn.lower() == "00readme":
        return "readme"
    if 'vv' in fn:
        return "vv"

    for ft in known_file_types:
        suffix = '_{}'.format(ft)
        if suffix in fn:
            return ft

    return None


known_file_formats = ["fits", "jpg", "pdf", "ps", "html", "ascii"]
known_file_formats.sort()


def extract_file_format(fname):
    """Returns "ascii", "fits", "jpg", "pdf", or None depending of the
    file name."""

    if fname is None or fname.strip() == "":
        raise ValueError("No file given")
    fn = fname.strip()
    if fn[-1] == "/":
        return None

    if fname == "00README":
        return "ascii"

    for ff in known_file_formats:
        if fn.find(ff) != -1:
            return ff

    return None


def create_directory(dname):
    """Create the directory if it does not exist. It will
    create any necessary parent directories.
    """

    if dname == "" or os.path.exists(dname):
        return
    v3("Creating directory: '{}'".format(dname))
    if dname[-1] == "/":
        parent = os.path.dirname(dname[:-1])
    else:
        parent = os.path.dirname(dname)
    if not os.path.exists(parent):
        create_directory(parent)
    os.mkdir(dname, 0o777)


def stringify_size(s):
    "Convert a file size, in bytes, to a text string."

    def myint(f):
        return int(f + 0.5)

    if s < 1024:
        lbl = "< 1 Kb"
    elif s < 1024 * 1024:
        lbl = "%d Kb" % (myint(s / 1024.0))
    elif s < 1024 * 1024 * 1024:
        lbl = "%d Mb" % (myint(s / (1024 * 1024.0)))
    else:
        lbl = "%.1f Gb" % (s / (1024 * 1024 * 1024.0))

    return lbl


def stringify_dt(dt):
    """Convert two times into a text string giving a 'human readable'
    version of the time difference (the dt argument)
    """

    if dt < 1:
        return "< 1 s"

    def myint(f):
        return int(f + 0.5)

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


class ObsIdFile:
    """A file that is part of a Chandra ObsId.

    It is used to allow the file to be easily downloaded via FTP
    rather than as something useful for data analysis.
    """

    def __init__(self, obsid, filename):
        """Create a record for the given file (filename should include
        any path elements after the byobsid directory).
        """

        self.obsid = str(obsid)
        self.filename = filename
        self.filetype = extract_file_type(filename)
        self.fileformat = extract_file_format(filename)

        # assume we are in the byobsid directory (to support mirrors)
        self.path = os.path.join(self.obsid[-1], self.obsid, self.filename)

        self.filesize = None

    def is_type(self, types):
        """Given a list of file types, returns True if
        the file is one of these types."""
        return self.filetype in types

    def is_format(self, formats):
        """Given a list of file formats, returns True if
        the file is one of these formats."""
        return self.fileformat in formats

    def get_filesize(self, ftp):
        """Returns the file size in bytes.

        The ftp object should be a FTP object connected to the
        archive.
        """

        if self.filesize is None:
            # the ftp.size command seems to be returning unreliable
            # results, so manually parse the list output to grab the
            # value, falling back to size if necessary
            #
            path = os.path.join(ftp.basedir, self.path)
            v3("Finding size of: {}".format(path))

            def hdlr(line):
                v3("Looking for a filesize in " + line)
                toks = line.split()
                self.filesize = int(toks[4])

            try:
                ftp.retrlines("LIST " + path, hdlr)
            except Exception:
                v3("Problem parsing LIST for filesize of " + path)
                self.filesize = ftp.size(path)

        return self.filesize

    def get_download_line_header(self, slabel):
        """Return the start of the download information
        for this object. slabel is a string representation of the
        file size."""

        if self.filetype is None:
            ftype = ""
        else:
            ftype = self.filetype

        return "  {0:8s} {1:6s} {2:>9s}  ".format(ftype,
                                                  self.fileformat,
                                                  slabel)

    def download(self, ftp):
        """Download the file given the FTP object ftp,
        which is assumed to be connected to the archive.

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

        verbose = logger.getEffectiveVerbose() > 0

        v3("Starting download of {}".format(self.filename))
        s = self.get_filesize(ftp)

        slabel = stringify_size(s)

        fname = os.path.join(self.obsid, self.filename)
        fpath = os.path.join(ftp.basedir, self.path)
        subdname = os.path.dirname(fname)
        if subdname != "":
            create_directory(subdname)

        try:
            fs = os.path.getsize(fname)
            v3("Checking on-disk file size ({}) against archive size ({}): {}".format(fs, s, fs == s))
            if fs == s:
                lbl = self.get_download_line_header(slabel)
                v1("{}  already downloaded".format(lbl))
                return (0, 0)

            elif fs > s:
                v0("Archive size is less than disk size for {} - {} vs {} bytes.".format(fname, s, fs))
                return (0, 0)
            else:
                startfrom = fs

        except OSError:
            startfrom = None

        try:
            fp = open(fname, 'ab')
        except IOError:
            raise IOError("Unable to create '{}'".format(fname))

        # it is unclear from the documentation whether this seek is needed, but
        # do so just in case
        #
        if startfrom is not None and fp.tell() == 0:
            fp.seek(0, 2)

        # Can not use v1 here since do not want to add an end-of-line character
        if verbose:
            sys.stdout.write(self.get_download_line_header(slabel))

        lfp = LoggingFile(fp, s, sys.stdout, startfrom=startfrom)
        t0 = time.time()
        try:
            if startfrom is None:
                ftp.retrbinary("RETR " + fpath, lfp.write, 8 * 1024)
            else:
                ftp.retrbinary("RETR " + fpath, lfp.write, 8 * 1024, startfrom)
        except ftplib.error_perm as pe:
            if verbose:
                sys.stdout.write("\n")
            v3("download error: {}".format(pe))
            raise IOError("Unable to download {} - file may be unusable".format(fname))

        t1 = time.time()
        bytes = fp.tell()
        fp.close()
        lfp.close()

        dt = t1 - t0
        kb = bytes / 1024.0
        if verbose:
            sys.stdout.write("  {:>13s}  {:.1f} kb/s\n".format(stringify_dt(dt), kb / dt))

        if s != bytes:
            v0("WARNING file sizes do not match: expected {} but downloaded {}".format(s, bytes))

        return (bytes, dt)


class ObsId:
    """Access the files for the given obsid.
    """

    dirnames = ["primary", "secondary", "aspect", "ephem"]

    def __init__(self, obsid, ftp):
        """Store the available files for the given obsid,
        using the FTP object which should be connected to the
        archive.
        """

        self.obsid = obsid
        ostr = str(obsid)
        dname = os.path.join(ftp.basedir, ostr[-1], ostr)
        v3("Looking for directory: {}".format(dname))
        try:
            ftp.cwd(dname)
        except ftplib.error_perm:
            raise IOError("Unable to find the directory for {}".format(obsid))

        if logger.getEffectiveVerbose() > 2:
            v3("Directory contents for ObsId {}".format(obsid))
            ftp.dir("*", "*/*")

        # Hard code the directories rather than use a generic parser
        #
        topfiles = ftp.nlst()
        primfiles = ftp.nlst("primary")
        secfiles = ftp.nlst("secondary")
        ephfiles = ftp.nlst("secondary/ephem")
        aspfiles = ftp.nlst("secondary/aspect")
        infiles = topfiles + primfiles + secfiles + ephfiles + aspfiles

        self.files = [ObsIdFile(obsid, f) for f in infiles
                      if os.path.basename(f) not in self.dirnames]
        v3("Found {} files".format(len(self.files)))

    def filter_files(self, types=None, formats=None):
        """Filter the list of files by the given types and/or formats.
        """

        v3("Before filtering: {} files".format(len(self.files)))
        if types is not None:
            self.files = [f for f in self.files if f.is_type(types)]
        if formats is not None:
            self.files = [f for f in self.files if f.is_format(formats)]

        v3("After filtering: {} files".format(len(self.files)))

    def get_download_size(self, ftp):
        """Get the download size for the files in the ObsId,
        in bytes.

        ftp should be a FTP object connected to the archive.
        """

        return sum([f.get_filesize(ftp) for f in self.files])

    def download(self, ftp):
        """Download the files for the ObsId to the current
        working directory.

        The screen output is determined by the logger instance.
        """

        v3("Downloading {} files".format(len(self.files)))
        s = self.get_download_size(ftp)
        if s == 0:
            v1("No files found for ObsId {}!".format(self.obsid))
            return

        v1("Downloading files for ObsId {}, total size is {}.\n".format(self.obsid, stringify_size(s)))
        v1("  Type     Format      Size  0........H.........1  Download Time Average Rate")
        v1("  ---------------------------------------------------------------------------")

        nbytes = 0
        dt = 0
        for f in self.files:
            (a, b) = f.download(ftp)
            nbytes += a
            dt += b

        if logger.getEffectiveVerbose() > 0:
            if len(self.files) > 1 and nbytes > 0:
                sys.stdout.write("\n")
                v1("      Total download size for ObsId {} = {}".format(self.obsid, stringify_size(nbytes)))
                v1("      Total download time for ObsId {} = {}".format(self.obsid, stringify_dt(dt)))
            sys.stdout.write("\n")


def _parse_mirror(mirror, username=None, userpass=None):
    """Return (ftp site, base directory, username, password) for the given
    mirror argument (see init_ftp and download_chandra_obsids
    for the format of mirror).

    The username and userpass arguments, if set, override any values
    given as part of the mirror FTP URL.

    If no username or password is given then we default to
    DEFAULT_USERNAME and DEFAULT_PASSWORD respectively.
    """

    url = urlparse(mirror)

    # The ftp scheme is required to make it easier to support
    # other schemes (e.g. file:// for local access) in the future.
    if url.scheme != "ftp":
        raise ValueError('The mirror site must begin with ftp://')

    if username is None:
        name = url.username
    else:
        name = username

    if name is None:
        name = DEFAULT_USERNAME

    if userpass is None:
        passwd = url.password
    else:
        passwd = userpass

    if passwd is None:
        passwd = DEFAULT_PASSWORD

    return (url.hostname, url.path, name, passwd)


def init_ftp(mirror=None, username=None, userpass=None):
    """Login to the Chandra archive, anonymously, and return
    a FTP object. The working directory will be set to byobsid/
    from the location given by mirror.

    If mirror is None then it is taken to be

      ftp://cda.cfa.harvard.edu/pub/

    Login details use the username and userpass values if set,
    otherwise values extracted from the mirror (if set), otherwise
    uses the DEFAULT_USERNAME and DEFAULT_PASSWORD values.
    """

    if mirror is None:
        base = 'ftp://cda.cfa.harvard.edu/pub'
    else:
        base = mirror

    (ftpsite, dirname, uname, passwd) = _parse_mirror(base, username, userpass)
    v3("FTP mirror={} ftpsite={} dirname={} name={} password={}".format(base, ftpsite, dirname, uname, passwd))

    v3("Connecting to FTP site")
    ftp = ChandraFTP(host=ftpsite, user=uname, passwd=passwd, basedir=dirname)

    # Not strictly necessary, but should error out if the directory
    # does not exist
    dname = os.path.join(dirname, "byobsid")
    v3("Changing to byobsid directory: {}".format(dname))
    ftp.cwd(dname)

    v3("Connected to server and in byobsid directory")
    return ftp


def download_chandra_obsids(obsids,
                            filetypes=None,
                            mirror=None,
                            username=None,
                            userpass=None
                            ):
    """Download the obsids from the Chandra Data Archive -
    http://chandra.harvard.edu/cda/ - or a mirror site.

    obsids should be a list of obsid values - e.g. [1843, 1557]

    If filetypes is None then all data for each obsid will be
    downloaded, otherwise it is an array of strings determining which
    files to download. See the known_file_types array in this module
    for the list of supported types. An example would be ['evt2',
    'bpix', 'asol'] to download just the level 2 event file, bad-pixel
    file, and aspect solution files.

    The mirror argument, if set to None (the default), means that the
    CDA FTP archive is used. Set it to the name of a mirror archive to
    use that location instead. The value should refer to the directory
    that contains the "byobsid" directory and start with ftp://.  The
    default value is equivalent to setting mirror to
    ftp://cda.cfa.harvard.edu/pub/

    This routine does *not* check the CDA_MIRROR_SITE environment
    variable if mirror=None (this is assumed to have been resolved by
    the time the routine has been called).

    The mirror site must have the same directory stucture as the CDA
    starting at the byobsid directory, but it need not contain all the
    data; the routine will just not be able to download the missing
    data sets; i.e. *no* fall over to the CDA archive is provided in
    this case).

    The username and password for the FTP site uses the username and
    userpass arguments, if given, otherwise the values extracted from
    the mirror argument (if set and included - e.g.
    ftp://anonymous@anonymous:cda.cfa.harvard.edu/pub/), otherwise
    the DEFAULT_USERNAME and DEFAULT_PASSWORD settings are used.

    The return value is an array of booleans that indicate whether the
    ObsId was available in the archive (it does not indicate whether
    any data was downloaded since files are skipped if they exist on
    disk).

    The data is written to the current working directory using the
    archive layout, so each ObsId has its own directory.

    Screen output is controlled by the logging instance. By default
    the logger has no output set up, so you will see no screen
    output. To see the progress bars get displayed as files get
    downloaded try

      import ciao_contrib.logger_wrapper as lw
      lw.initalize_logger("download", verbose=1)

    before calling this routine (the first argument can be
    any string).
    """

    out = []
    try:
        ftp = init_ftp(mirror=mirror, username=username, userpass=userpass)

    except socket.gaierror as ge:
        v3("Unable to log in: msg={0}".format(ge))
        if mirror is None:
            raise IOError("Unable to connect to the Chandra Data Archive.")
        else:
            raise IOError("Unable to connect to the Chandra Data Archive mirror at {0}.".format(mirror))

    if mirror is None:
        sitename = "archive"
    else:
        sitename = "mirror"

    for obsid in obsids:
        v3("Setting up for ObsId {0}".format(obsid))
        try:
            oid = ObsId(obsid, ftp)
        except IOError as ie:
            v3("Unable to cd to ObsId {0}: msg={1}".format(obsid, ie))
            v1("Skipping ObsId {0} as it was not found on the {1} site.".format(obsid, sitename))
            out.append(False)
            continue

        oid.filter_files(types=filetypes, formats=None)
        oid.download(ftp)
        out.append(True)

    ftp.close()
    return out

# End
