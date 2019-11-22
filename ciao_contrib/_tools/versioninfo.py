#
#  Copyright (C) 2011, 2014, 2015, 2016, 2019
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
Access the CIAO version (both installed and latest available).

Query either the local installation for the installed version
of CIAO, or find out the latest released version by querying
the CXC website.
"""

import glob
import os

from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from ciao_contrib import logger_wrapper as lw


__all__ = ('get_installed_versions', 'get_latest_versions',
           'read_latest_versions', 'check_conda_versions')


lgr = lw.initialize_module_logger('_tools.versioninfo')
v3 = lgr.verbose3
v4 = lgr.verbose4


def read_vfile(fname):
    "Reads the version string from a CIAO version file"

    with open(fname, 'r') as fh:
        cts = fh.readlines()

    # Just take the first line, in case there are any extra new lines
    # in the file, as has happened.
    return cts[0].strip()


def package_name(fname):
    """Return the package name for the given file name"""

    if fname == "VERSION":
        return "CIAO"

    elif fname == "contrib/VERSION.CIAO_scripts":
        return "contrib"

    elif fname.find("_") != -1:
        return fname.split("_")[-1]

    else:
        raise ValueError("Unrecognized file name: {0}".format(fname))


def get_installed_versions(ciao):
    """Return a dictionary of (name, version) pairs for the installed
    CIAO packages, where ciao is the base of the CIAO installation
    (i.e. the value of the $ASCDS_INSTALL environment variable).

    Returns None if no version files can be found (is there is
    either no $ASCDS_INSTALL/VERSION or $ASCDS_INSTALL/VERSION_*)
    which is likely to indicate a conda install.

    """

    vbase = glob.glob(ciao + "/VERSION")
    if vbase == []:
        return None

    # assume there is at least one installed package
    #
    vfiles = glob.glob(ciao + "/VERSION_*")
    if vfiles == []:
        return None

    # do not require the contrib package
    #
    cfile = glob.glob(ciao + "/contrib/VERSION*")

    l = len(ciao) + 1
    return {package_name(vfile[l:]): read_vfile(vfile)
            for vfile in vbase + vfiles + cfile}


def parse_version_file(lines):
    """Given a list of lines, return the parsed contents,
    assuming each line is either empty or

      '<file-head> <version text>'

    Returns a dictionary (key=file-head, value=version text).
    """

    out = {}
    for l in lines:
        l = l.strip()
        if l == "":
            continue
        idx = l.find(" ")
        if idx == -1:
            raise IOError("Unable to parse line: '{0}'".format(l))

        k = l[:idx]
        v = l[idx + 1:]
        if k in out:
            raise ValueError("Multiple copies of {0} found.".format(k))

        out[k] = v

    return out


# def find_ciao_system():
#     """Return the CIAO system value.
#
#     Returns
#     -------
#     system : str
#         The system type. This matches the SYS field from the
#         ciao-control file used by ciao-install.
#
#     Notes
#     -----
#     This is just a simple wrapper around the ciao-type tool.
#     """
#
#     ans = sbp.Popen(["ciao-type"], stdout=sbp.PIPE)
#     ans.wait()
#     if ans.returncode != 0:
#         # is this necessary?
#         raise IOError("Unable to run ciao-type")
#
#     text = ans.stdout.read()
#
#     # Ugly code; what is the better way to do this
#     if not isinstance(text, str):
#         text = text.decode('utf8')
#
#     return text.strip()


def find_ciao_system():
    """Return the CIAO system value.

    Returns
    -------
    system : str
        The system type. This matches the SYS field from the
        ciao-control file used by ciao-install.

    Notes
    -----
    The ciao-type tool does not seem to return the Python version,
    i.e. it does not distinguish the "P3*" variants. So the
    contents of $ASCDS_INSTALL/ciao-type are used.
    """

    # assume that ASCDS_INSTALL is defined
    filename = os.path.join(os.getenv("ASCDS_INSTALL"), "ciao-type")
    with open(filename, "r") as fh:
        cts = fh.read()

    return cts.strip()


def get_latest_versions(timeout=None, system=None):
    """Return the latest-released version of CIAO packages.

    This call requires internet access and the ability to
    query pages at https://cxc.harvard.edu/ciao/download/.

    Parameters
    ----------
    timeout : optional
        The timeout parameter for the urlopen call; if not
        None then the value is in seconds.
    system : optional
        The system to check for (e.g. "Linux64", "LinuxU",
        "osxSierra", ...). It should match the SYS value from the
        ciao-control file used by ciao-install. If set to None then
        the system from the CIAO installation is used.

    Returns
    -------
    versioninfo : dict
        The keys are the package name and the values are the
        latest released version for that package.

    Raises
    ------
    IOError
        Various HTTP-related errors are caught and converted to
        IOError exceptions, with the aim of providing more
        user-friendly errors.

    Notes
    -----
    This call turns off certificate validation for the requests since
    there are issues with getting this working on all supported platforms.
    It *only* does it for the calls it makes (i.e. it does not turn
    off validation of any other requests).

    The package names are those returned by the ciaover tool when
    run with the -v option, but in lower case, and the version
    strings have the form:

        <package> <version> <day>, <month> <day of month>, <year>

    where <version> has the form "a.b" or "a.b.c".
    """

    import ssl

    if system is None:
        system = find_ciao_system()

    v3("get_latest_versions for system={}".format(system))

    # To allow for a system-agnostic version file, check for
    # the version-specific and then drop back to the
    # version-agnostic only if it does not exist. Is this OTT?
    #
    base_url = "https://cxc.harvard.edu/ciao/download/"
    system_url = base_url + "ciao_versions.{}.dat".format(system)
    simple_url = base_url + "ciao_versions.dat"

    # Which URL to use? Note that the SSL context is explicitly
    # set to stop verification, because the CIAO 4.12 release has
    # seen some issues with certificate validation (in particular
    # on Ubuntu and macOS systems).
    #
    context = ssl._create_unverified_context()
    def download(url):
        v3(" - trying to download {}".format(url))
        try:
            if timeout is None:
                res = urlopen(url, context=context)
            else:
                res = urlopen(url, timeout=timeout, context=context)
        except HTTPError as he:
            v3(" - caught HTTP error {} for {}".format(he, url))
            if he.code == 404:
                return None

            raise he

        return res.read().decode('utf-8')


    try:
        rsp = download(system_url)
        if rsp is None:
            rsp = download(simple_url)

    except HTTPError as he:
        v3("Re-caught HTTP error {}".format(he))
        raise IOError("Unable to download the CIAO version file")

    except URLError as ue:
        v3("Caught URLError {}".format(ue))
        raise IOError("Unable to download the CIAO version file")

    if rsp is None:
        raise IOError("Unable to download the CIAO version file")

    return parse_version_file(rsp.splitlines())


def read_latest_versions(filename):
    """Read the versions of the latest CIAO packages from the input
    file. The return value is an array of (name, version) strings.

    """

    with open(filename, "r") as fh:
        return parse_version_file(fh.readlines())


def check_conda_versions(ciao):
    """Is the conda environment up to date?

    This is *experimental* and is assumed to be run in an environment
    in which CIAO has been installed via conda.

    Returns True if the environmant is up to date, or False if it needs
    an update.
    """

    import subprocess
    import json

    # Assume we are in a conda environment
    #
    v3("About to run 'conda list'")
    try:
        out = subprocess.run(["conda", "list", "--json"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise IOError("Unable to run the conda tool. Was CIAO installed with conda?")

    js = json.loads(out.stdout)

    # - hardcoding the dependencies, which is not ideal
    #
    packages = ["ciao", "ciao-contrib",
                "sherpa", "xspec-modelsonly",
                "ds9", "xpa",
                "marx",
                "caldb", "caldb_main", "acis_bkg_evt", "hrc_bkg_evt"]

    # Check for the channels used for the packages as, at the time of
    # writing, the exact name has not been finalized, and also it
    # could change over time.
    #
    found = {}
    for found_package in js:
        name = found_package['name']
        if name not in packages:
            continue

        channel = found_package['base_url']
        version = found_package['version']
        v3(" - found {} {} {}".format(name, version, channel))
        found[name] = {'channel': channel, 'version': version}

    if len(found) == 0:
        raise IOError("No CIAO packages found in your conda environment!")

    # Try and upgrade them (as a dry-run)
    #
    names = sorted(list(found.keys()))

    channels = []
    for c in set([v['channel'] for v in found.values()]):
        channels.extend(["-c", c])

    # We use --no-update-deps since the expected users of this
    # functionality are likely to want to know just if the CIAO packages
    # need updating, not any dependency.
    #
    command = ["conda", "update", "--json", "--dry-run", "--no-update-deps"] + \
              channels + names
    v3("Trying to run {}".format(command))

    # we've already run conda so assume it is still around
    out = subprocess.run(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    js = json.loads(out.stdout)

    # map a missing key to a failure (as indicates schema has changed)
    success = js.get('success', False)
    if not js['success']:
        raise IOError("Unable to run {}: {}".format(command, out.stdout))

    # perhaps could just check to see message exists, since if it does
    # it *probably* indicates success, which would be a simpler check
    #
    msg = js.get('message', '')
    if msg == 'All requested packages already installed.':
        v3(" - all packages are up to date")
        print("CIAO (installed via conda) is up to date.")
        return True

    fetch = js.get('actions', {}).get('FETCH', None)
    if fetch is None:
        v3(" - unable to find actions/FETCH in {}".format(js))
        print("It looks like a CIAO package needs to be updated by CIAO but I can't find which.")
        return False

    names = [(f['name'], f['version']) for f in fetch]
    nnames = len(names)
    if nnames == 0:
        v3(" - unable to find FETCH list in {}".format(js))
        print("Unable to find which conda packages need updating")
        return False

    if nnames == 1:
        print("There is one package that needs updating:")
    else:
        print("There are {} packages that need updating:".format(nnames))

    for name, version in names:
        print("  {} : {} -> {}".format(name, found[name]['version'], version))

    print("")
    return False
