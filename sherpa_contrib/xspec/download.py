#
#  Copyright (C) 2026  Smithsonian Astrophysical Observatory
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

"""Access 'extra' model data files for the XSPEC models.

XSPEC 13.0.0 / HEASOFT 6.37 no-longer packages the data files used
by XSPEC models, and instead provides the ftgetmodeldata command
to find and download them. This is based on the contents of the file

  spectral/manager/modelDataFiles.csv

or

  https://heasarc.gsfc.nasa.gov/FTP/software/xspec/spectral/modelDataFiles.csv

This module provides minimal access to this file, and routines to
allow model data files to be downloaded. This supports those XSPEC
models in CIAO 4.19 for which the CXC does not provide the data files
or if new versions are released.

Note that CIAO 4.19 is released with XSPEC 12.15.1 and not 13.0.0 (or
later).

These routines require a CIAO installation where the user has write
access to $ASCDS_INSTALL.

"""

from contextlib import suppress
import csv
from dataclasses import dataclass
from http import client
import logging
from pathlib import Path
from shutil import copyfileobj
from urllib.request import Request, urlopen

from sherpa.astro import xspec
from sherpa.astro.utils.xspec import Version, get_version

import ciao_contrib.logger_wrapper as lw

__all__ = ("download_model_data_version",
           "read_mdel_data_version")

lgr = lw.initialize_module_logger(__name__)
v1 = lgr.verbose1
v2 = lgr.verbose2
v3 = lgr.verbose3
del lgr

debug = logging.getLogger(__name__).debug
info = logging.getLogger(__name__).info
warning = logging.getLogger(__name__).warning


VERSION = "29 November 2026"

BASE_URL = "https://heasarc.gsfc.nasa.gov/FTP/software/xspec/spectral/"
DATA_FILE = "modelDataFiles.csv"

DEFAULT_HDRS = {"User-Agent":
                f"CIAO contrib ftgetmodeldata equivalent {VERSION}"}


def get_model_data_version_path() -> Path:
    """Return the expected location of the model data file.

    There is no check that the file exists.
    """

    base = Path(xspec.get_xspath_manager()).resolve()
    return base / DATA_FILE


def download_model_data_version() -> None:
    """Download modelDataFiles.csv and store it within CIAO.

    This will over-write any file.
    """

    out = get_model_data_version_path()
    v1(f"Writing XSPEC model data files to: {out}")

    url = f"{BASE_URL}{DATA_FILE}"
    v2(f"Querying {url}")

    req = Request(url, headers=DEFAULT_HDRS)
    with urlopen(req) as resp:
        out.write_text(resp.read().decode())

    v3(f"File size: {out.stat().st_size}")


def find_supported_xspec_models() -> list[str]:
    """The names of the supported XSPEC models.

    Returns
    -------
    models : list of str
       The list of the supported model names. Note that the return
       value matches the XSPEC model.dat (e.g. "TBabs" for the XSTBabs
       model).

    """

    def is_proper_subclass(obj, cls):
        if obj in cls:
            return False
        return issubclass(obj, cls)

    valid_names: set[str] = set()
    for clname in dir(xspec):
        if not clname.startswith("XS"):
            continue

        cls = getattr(xspec, clname)
        if is_proper_subclass(cls, (xspec.XSAdditiveModel,
                                    xspec.XSMultiplicativeModel,
                                    xspec.XSConvolutionKernel)):
            if not cls.version_enabled:
                continue

            # At present we do not provide the "de-mangled" name
            # (i.e. the model.dat name) but we can re-create it.
            #
            valid_names.add(cls.__name__[2:])

    return sorted(valid_names)


@dataclass
class XSPECDataRow:
    """A mapping from model to a data file it requires.

    This is read from the modelDataFiles.csv used by XSPEC 13.0.0
    and later, but split by model.

    """

    filename: str
    """The name of the data file.

    The data file is expected to be found in the location returned
    by `sherpa.astro.xspec.get_xspath_model()`.
    """

    model: str | None
    """The model that uses the file, if any.

    This name matches that given in the file returned by
    `get_model_data_version_path()`, and not that used by Sherpa
    (e.g. "apec" rather than "XSapec" or "xsapec").
    """

    model_version: str | None
    """The version of the data file."""

    version_start: Version
    """The start of the XSPEC version range (this drops any patch level)."""

    version_end: Version | None
    """The end of the XSPEC version range (this drops any patch level), af any.

    A value of "Unknown" is converted to `None`.
    """

    release: str
    """The release number (expected to be "1" for current and "0" otherwise)."""

    checksum: str
    """The checksum for the file."""

    filesize: int
    """The file size, in bytes."""


def read_model_data_version() -> list[XSPECDataRow]:
    """Return the XSPEC model data file information.

    Returns
    -------
    rows : list of XSpecDataRow
       The data rows, split up by model, so this differs from how the
       data is stored in the CSV file, and it means that the same file
       can appear in multiple rows. Only models supported by Sherpa
       are included.

    See Also
    --------
    filter_model_data_version, get_model_data_version_path

    Examples
    --------

    Read in the CSV file from the current HEADAS installationL

    >>> all_rows = read_model_data_version()

    Select only the latest models:

    >>> all_rows = read_model_data_version()
    >>> latest_rows = [r for r in all_rows if r.release == '1']

    What rows relate to the XSPEC apec model for the latest release
    (note that this uses the name from the `model.dat` file):

    >>> all_rows = read_model_data_version()
    >>> latest_rows = [r for r in all_rows if r.release == '1']
    >>> apec_rows = [r for r in latest_rows if r.model == 'apec']

    Find the rows for XSPEC version 12.15.1:

    >>> all_rows = read_model_data_version()
    >>> v12151_rows = filter_model_data_version(all_rows, '12.15.1')

    """

    csvfile = get_model_data_version_path()
    if not csvfile.is_file():
        raise OSError("download_model_data_version() has not been called")

    # What XSPEC model names do we need to care about? The check uses
    # the lower-case version of the model name from model.dat.
    #
    valid_names = {m.lower() for m in find_supported_xspec_models()}

    def mk(rec: dict[str, str]) -> list[XSPECDataRow]:
        """Create zero, one, or more values from the row."""

        # Convert the input data to the arguments for XSPECDataRow
        #
        kwargs = {}

        # Explicit version clean up.
        # - convert Unknown to None
        # - drop trailing patch level
        #
        vend = rec['xspec_version_end']
        v2 = None if vend in ["", "Unknown"] else get_version(vend)

        kwargs['version_start'] = get_version(rec['xspec_version_start'])
        kwargs['version_end'] = v2
        kwargs['filesize'] = int(rec['filesize'])

        # Copy over the remaining arguments.
        #
        for name in ["filename", "release", "checksum"]:
            kwargs[name] = rec[name]

        for name in ["model_version"]:
            kwargs[name] = rec[name] if rec[name] != '' else None

        # models can be
        # - empty
        # - a single name
        # - multiple models stored as "mdl1, ..., mdl"
        #
        rmodels = rec['models']
        if rmodels == '':
            mnames = [None]
        else:
            all_mnames = [m.strip() for m in rmodels.split(",")]
            debug("models: %s", str(all_mnames))

            # Filter by those models that Sherpa supports.
            #
            mnames = [m for m in all_mnames if m.lower() in valid_names]
            nall = len(all_mnames)
            nmdl = len(mnames)
            if nmdl < nall:
                debug("- removed %d unsupported models", nall - nmdl)

        return [XSPECDataRow(model=m, **kwargs) for m in mnames]

    # Store those models that have missing data. The assumption is that
    # the CSV has columns for
    #    filename
    #    models
    #    model_version
    #    xspec_version_start
    #    xspec_version_end
    #    release
    #    checksum
    #    filesize
    #
    # What does a version like "12.14.0x" mean (since there was no
    # patch level x release for 12.14.0). It looks like ftgetmodeldata
    # just skips the patch-level value so we will do that too,
    # although the patch level is meant to be included (from a
    # discussion with the HEASARC team).
    #
    out = []
    with csvfile.open(mode='rt') as fh:
        reader = csv.reader(fh)
        header = None

        for row in reader:
            if header is None:
                header = row
                debug("header: %s", header)
                continue

            # Convert to zero to n records.
            #
            toks = dict(zip(header, row))
            debug("file: %s", toks['filename'])
            out.extend(mk(toks))

    return out


def filter_model_data_version(rows: list[XSPECDataRow],
                              version: str
                              ) -> list[XSPECDataRow]:
    """Filter by version number.

    This may not exactly match the filtering used by ftgetmodeldata,
    in particular for when a patch-level is included in the version
    number, or for those cases where the data file does not indicate a
    "cut-off" date for the model. This means that it can return more
    files than are strictly needed.

    Parameters
    ----------
    rows : list of XSPECDataRow
       The model data files to query.
    version : str
       The version to filter on.

    Returns
    -------
    selected : list of XSPECDataRow
       Those models that are valid for the given XSPEC version.

    """

    vcheck = get_version(version)

    out = []
    for row in rows:

        # So we can ask if this the "latest" release or not, which is
        # irrelevant when comparing to a particular version. However,
        # there are cases where the versino range is open and the
        # "latest" flag is used to indicate which is the version to
        # use (but not necessarily for the selected version). Since
        # the data does not indicate a "name" for each file we can not
        # identify these cases (we can try things like "search for a
        # common prefix" but it is not a robust solution). So we just
        # return all of those rows we can not directly remove.
        #
        vstart = row.version_start
        if vstart > vcheck:
            debug("- too new %s", vstart)
            continue

        vend = row.version_end
        if vend is not None and vend < vcheck:
            debug("- too old %s", vend)
            continue

        out.append(row)

    return out


def find_missing_model_data_files(rows: list[XSPECDataRow]
                                  ) -> list[XSPECDataRow]:
    """What XSPEC models are missing data?

    Filters the input list to remove those rows where the data
    file exists and has the correct size.

    Parameters
    ----------
    rows : list of XSPECDataRow
       The list of rows to check.

    Returns
    -------
    missing : list of XSPECDataRow
       The rows that represent missing data files.  Only the first
       appearance of a missing file is returned. This list may be
       empty.

    See Also
    --------
    read_model_data_version

    Examples
    --------

    Find all of the "latest" model data files for the XSPEC models
    supported by Sherpa that are missing:

    >>> all_rows = read_model_data_version()
    >>> latest_rows = [r for r in all_rows if r.release == '1']
    >>> missing_rows = find_missing_model_data_files(latest_rows)

    """

    mpath = Path(xspec.get_xspath_model())
    out = []
    seen = set()
    for row in rows:

        # If we have seen this before (from another model) then
        # skip.
        #
        if row.filename in seen:
            continue

        seen.add(row.filename)

        # Check that the model has the expected size.
        modpath = mpath / row.filename
        with suppress(OSError):
            if modpath.stat().st_size == row.filesize:
                continue

        out.append(row)

    return out


def download_missing_model_data_files(rows: list[XSPECDataRow]
                                      ) -> list[XSPECDataRow]:
    """Download the data files for the XSPEC models.

    This skips any row where the files are already downloaded. This
    is similar to the `ftgetmodeldata
    <https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/help/ftgetmodeldata.html>`_
    tool from HEASARC.

    Parameters
    ----------
    rows : list of XSPECDataRow
       The list of rows to download. If the row represents a data
       file that exists and has the correct size then it is skipped.

    Returns
    -------
    failed : list of XSPECDataRow
       Identify those files that could not be downloaded. This list
       will be empty if all files are installed.

    See Also
    --------
    find_missing_model_data_files, read_model_data_version

    Notes
    -----
    The data files are stored in the directory returned by
    `sherpa.astro.xspec.get_xspath_model()`. There is no support for
    partial downloads as existing files are over-written if they do
    not have the expected file size.

    Examples
    --------

    >>> all_rows = read_model_data_version()
    >>> latest_rows = [r for r in all_rows if r.release == '1']
    >>> missing_rows = download_missing_model_data_files(latest_rows)
    ...

    """

    # Exit early if nothing to do.
    if len(rows) == 0:
        info('No data files to download!')
        return []

    base_url = f"{BASE_URL}modelData"
    Connection = client.HTTPSConnection

    # Does the output directory exist? If this fails then bail out
    # immediately.
    #
    mpath = Path(xspec.get_xspath_model())
    info("Data directory: %s", str(mpath))
    if not mpath.is_dir():
        debug("Creating output directory [%s]", str(mpath))
        mpath.mkdir()
        mpath_exists = True

    errs = []
    seen = set()
    for row in rows:

        # If we have seen this before (from another row) then skip.
        # The seen set is only updated when we successfully download a
        # file. Should we instead set it the first time we try to
        # download a file (in the case of some sort of network error,
        # no permission to write to the output directory, or
        # insufficient disk space)?
        #
        if row.filename in seen:
            continue

        # If the file exists and has the correct size then do nothing.
        #
        out = mpath / row.filename
        debug("Checking %s", str(out))
        with suppress(OSError):
            got = out.stat().st_size
            if got == row.filesize:
                seen.add(row.filename)
                continue

            # If the unlink fails then it will raise an OSError which
            # will be suppressed.
            #
            debug("- file size mis-match: %s vs %d", got, row.filesize)
            out.unlink()

        # Use http.client rather than urllib.request to allow for
        # streaming the response.
        #
        url = f"{base_url}/{row.filename}"
        info("Downloading %s %d", url, row.filesize)
        url_req = Request(url)

        stime = time.localtime()
        conn = Connection(url_req.host)
        conn.request("GET", url_req.selector, headers=DEFAULT_HDRS)
        resp = conn.getresponse()
        with out.open('wb') as outfh:
            debug("- copying %d bytes", row.filesize)
            copyfileobj(resp, outfh)

        etime = time.localtime()
        debug("- download time %.1f s", time.mktime(etime) - time.mktime(stime))

        # Check the download size.
        #
        with suppress(OSError):
            got = out.stat().st_size
            if got == row.filesize:
                seen.add(row.filename)
                continue

            debug("- file size mis-match: %d vs %d", got, row.filesize)

        errs.append(row)

    return errs
