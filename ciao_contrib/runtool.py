#
# Copyright (C) 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023
# Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# TODO
#
#   use try/finally and context generators to make sure resources,
#   such as parameter files, are closed. This has been done in _run()
#   but are there other areas where it could be done?
#

"""Summary
=======

This module allows users to run CIAO command-line tools with parameter files
by calling a function with the name of the tool: for example

  dmcopy("in.fits", "out.fits", clobber=True, option="all")
  print(dmstat(infile="img.fits", centroid=False, verbose=0))

If using an interactive Python session - such as IPython or Sherpa - the
output will be displayed on-screen, so you can just say

  dmstat(infile="img.fits", centroid=False, verbose=0)

Parameters may also be set before running the tool using the syntax
toolname.paramname - e.g. the dmstat call above can be written as

  dmstat.centroid = False
  dmstat.median = True
  dmstat("evt2.fits[bin sky=::1]")

or even

  dmstat.centroid = False
  dmstat.median = True
  dmstat.infile = "evt2.fits[bin sky=::1]"
  dmstat()

Once the tool has been run the parameters can be accessed; for instance

  dmstat("simple.dat", median=True)
  print(f"Median = {dmstat.out_median}")

or

  acis_bkgrnd_lookup("evt2.fits")
  match = acis_bkgrnd_lookup.outfile
  print(f"Found file: {match}")

There is also support for those parameter files which have no associated
tools - e.g. lut, colors, or ardlib. So you can say

  print(f"Location of LUT 'a' is {lut.a}")

but you cannot run these commands. Attempting to do so will result in
an error like

  colors()
  TypeError: 'CIAOParameter' object is not callable

Parameter handling
==================

Names
-----

In the summary, the full parameter names were given, but - as with the
command-line version - the names can be abbreviated to any unique
prefix. This means that the following can also be used:

  print(dmstat("evt2.fits[bin sky=::1]", cen=False, med=True))

or

  dmstat.cent = False
  dmstat.med = True
  dmstat.inf = "evt2.fits[bin sky=::1]"
  dmstat()

The use of an invalid parameter name - both in <toolname>.<parname>
and in the argument list when calling the tool - will result in an
error. For example:

  dmstat.niter = 10
  AttributeError: There is no parameter for dmstat that matches 'niter'

  dmstat.c = True
  AttributeError: Multiple matches for dmstat parameter 'c', choose from:
    centroid clip

When using abbreviations, be aware that some apparently valid names
will conflict with reserved Python keywords; one example is using "in"
for a parameter like "infile". This will result in a Syntax Error.

There is one note for the above: a few parameters can not be represented
as Python identifiers since they contain a '-' character (they are all
ardlib parameters). For these parameters, the name used in this
module has the '-' replaced with '_', so you would use

  ardlib.AXAF_HRC_I_BADPIX_FILE

to refer to the AXAF_HRC-I_BADPIX_FILE parameter of ardlib.

Values
------

Please see the NOTE below for information on how this information is
slightly different for those tools written as shell scripts.

When the module is imported, each tool is set up so that its
parameters are set to the CIAO default values. Once the tool has run,
the settings are updated to match any changes the tool may have made
to the parameter settings (e.g. setting values such as outfile or
out_median).

When a parameter is set for a tool - e.g.

  acis_process_events.infile = "evt2.fits"

then this setting ONLY applies to this routine; it does NOT write the
value to the on-disk parameter file for the tool (unless you use the
write_params method, as described below).

If a tool relies on any other parameter file - e.g. many of the
Chandra instrument tools will implicitly use the ardlib parameter file
- then these settings are obtained using that tools parameter file
(i.e. the file located in the PFILES environment variable), and NOT
from the settings for that tool or parameter file in this module.

Therefore setting

  ardlib.AXAF_ACIS0_BADPIX_FILE = "bpix1.fits[ccd_id=0]"

will *NOT* change the on-disk ardlib parameter file, and hence this
setting will not be used by any tool that needs it. To save the
settings to disk, use the write_params method:

  ardlib.write_params()

will write to the system ardlib.par file and either of

  ardlib.write_params("store")
  ardlib.write_params("store.par")

will write to the file store.par in the current working
directory.

The read_params() can be used to read in settings from a
parameter file - e.g.

  ardlib.read_params()
  ardlib.read_params("store.par")

Converting between Python and parameter types
---------------------------------------------

The parameter types have been converted into Python equivalents using
the following table:

  Parameter type    Python type
  s                 string
  f                 string
  b                 bool
  i                 int
  r                 float

When using string or filename parameters, you do not need to add
quotes around the name if it contains a space - so you can say

  inf = "evt2.fits[energy=500:2000,sky=region(src.reg)][bin sky=::1]"
  dmcopy(inf, "img.fits")

There is some support for converting Python values to the correct
type - e.g. for a boolean parameter you can use one either

- True, 1, "yes", "true", "on", "1"
- False, 0, "no", "false", "off", "0"

bit it is **strongly suggested** that you use the correct Python type
(in this case either True or False) as the conversion of other types
is not guaranteed to work reliably or match the rules used by the CXC
parameter library.

Parameters can be set to None and the system will try to do the right
thing, but it is best to be explicit when possible.

Handling of stacks
------------------

There is limited support for using arrays when setting a parameter
that can accept a stack (see "ahelp stack" for background
information). String and file parameters may be set using an array,
in which case the value is automatically converted into a
comma-separated string.

There is no support for converting a parameter value from a stack into
an array; the stk.build() routine can be used for this.

It is planned to handle stacks that exceed the maximimum parameter
length by using a temporary file to contain the values when the tool
is run; the current behavior in this case should be to throw an error
that the expected and stored parameter values do not match.

An example of use is:

  dmstat.punlearn()
  dmstat.median = False
  dmstat.centroid = False
  dmstat(["file1.img", "file2.img"])

After the above, the dmstat.infile parameter will be set to the string

  "file1.img,file2.img"

NOTE: special case for shell scripts
------------------------------------

There are several tools which are written as shell scripts that do not
support the <@@name.par> syntax for calling a CIAO tool (see the
'ahelp parameter' page for more information on this functionality). Care
should be taken to avoid running multiple copies of these tools at the
same time; if this is likely to happen use the new_pfiles_environment
context handler or the set_pfiles() routine to set up separate user
parameter directories.

The tools for which this is true are: axbary, dmgti, evalpos, fullgarf,
mean_energy_map, pileup_map, tgdetect, and wavdetect.

Displaying the current setting
------------------------------

The print command can be used to display the current parameter settings
of a tool; for instance

  print(dmimgcalc)
  Parameters for dmimgcalc:

  Required parameters:
                infile =                  Input file #1
               infile2 =                  Input file #2
               outfile =                  output file
             operation =                  arithmetic operation

  Optional parameters:
                weight = 1                weight for first image
               weight2 = 1                weight for second image
             lookupTab = ${ASCDS_CALIB}/dmmerge_header_lookup.txt  lookup table
               clobber = False            delete old output
               verbose = 0                output verbosity

The tool also acts as a Python iterator, so you can loop through
the parameter names and values using code like the following:

  for (pname, pval) in dmimgcalc:
      print(f"{pname} = {pval}")

Resetting parameter values
--------------------------

The parameter values for a tool can be reset using the punlearn()
method - e.g.

  dmstat.punlearn()

Parameter redirects
-------------------

There is limited support for setting a parameter value using the
"re-direct" functionality of the parameter library - e.g. values like
")sclmin", which mean use the value of the sclmin parameter of the
tool . Such re-directs can only be used to parameter values from the
same tool, so the value ")dmstat.centroid" is not permitted.

Excluded parameters
-------------------

The following parameters are not included for the tools:

  - the mode parameter

  - any parameter that can only be set to a single value is
    ignored

Parameter constraints
---------------------

There is currently no access to the constraints on a parameter, namely
whether it has a lower- or upper-limit set, or is restricted to a set
of values.

How is the tool run?
====================

The tool is always run with the mode set to 'hl', so that there will
be no querying the user for arguments.

  dmstat.punlearn()
  print(dmstat("img.fits", centroid=False, median=True))

or

  dmstat.punlearn()
  dmstat.infile = "img.fits"
  dmstat.cent = False
  dmstat.med = True
  print(dmstat())

If there was an error running the tool then an IOError will be raised,
otherwise the screen output of the tool will be returned (including
any output to STDERR, since it is possible for a CIAO tool to run
successfully and produce output on the STDERR channel).

To avoid problems with running multiple copies of a tool at the same
time, the tool is run using its own parameter file, supplied using the
"@@<filename>" form of the tool. This should be invisible to users of
this module. The location used for the temporary parameter file is
controlled by the ASCDS_WORK_PATH environment variable.

As noted above in the 'special case for shell scripts' section,
this method is not used for several tools. You may need to use
the new_pfiles_environment() context manager to automate the
creation of a new PFILES environment and directory for each run,
or the set_pfiles() routine to handle this case manually.

Detecting errors
================

An IOError is raised if the tool returns a non-zero exit
status. Unfortunately some CIAO tools still return a zero exit status
when they error out; for such cases it will appear as if the tool ran
successfully. The full screen output is included in the error, with
each line indented for readability at the IPython/Sherpa prompt.

As an example,

  dmcopy("in.fits[cols x", "out.fits")

raises the error

  IOError: An error occurred while running 'dmcopy':

    Failed to open virtual file in.fits[cols x
    # DMCOPY (CIAO 4.5): DM Parse error: unmatched [ or (: [cols x

The PFILES environment variable
===============================

When a tool is run, it is supplied with all the parameter values
so that there should be no problem with multiple versions of the
tool being run at the same time.

However, some tools make use of other parameter files - e.g. many of
the instrument tools such as mkinstmap or mkrmf - and these are
accessed using the standard CIAO parameter system. For standard CIAO
installations this means that the PFILES environment (see "ahelp
parameter" or https://cxc.harvard.edu/ciao/ahelp/parameter.html for
more information) is used.

The module provides a set_pfiles() routine which changes the location
of the user directory for parameter files. See 'help(set_pfiles)' for
more information on this. The get_pfiles() routine provides access to
the current settings.

If you are using any instrument-specific tools it is suggested that
you call set_pfiles() with a unique directory name, rather than with
no argument. The new_pfiles_environment() context manager can be used
to automate this, as it creates a temporary directory which is used to
store the parameter files which is then deleted on exit from the block.
An example of its use is

  with new_pfiles_environment():
      # The following tools are run with a PFILES directory
      # that is automatically deleted at the end of the block
      #
      mki = make_tool("make_tool")
      mki.clobber = True
      mki.pixelgrid = "1:1024:1,1:1024:1"
      mki.maskfile = "msk1.fits"

      for ccd in [0,1,2,3]:
          mki.obsfile = f"asphist{ccd}.fits[asphist]"
          mki.detsubsys = f"ACIS-{ccd}"
          for energy in [1,2,3,4,5]:
              mki(monoenergy=energy,
                  out=f"imap{ccd}_e{energy}.fits")

See 'help(new_pfiles_environment)' for more information.

Using multiple versions of a tool
=================================

You can set up multiple "copies" of a tool using the make_tool
routine. This can be useful if you wish to set up common, but
different, parameter values for a tool. For instance to run the dmstat
tool with median set to False and True you could define two separate
versions dms1 and dms2 using

  dms1 = make_tool("dmstat")
  dms1.median = True
  dms2 = make_tool("dmstat")
  dms2.median = False

and then run them on files

  dms1("src1.dat")
  dms1("src2.dat")

  dms2("src1.dat")
  dms2("src2.dat")

The new_tmpdir() and new_pfiles_environment() context managers can
also be useful when running multiple tools.

Setting the HISTORY record of a file
====================================

The add_tool_history routine allows you to set the HISTORY record of
a file in a format that can be read by the dmhistory tool. This is
useful when writing your own scripts and you want to record the
parameter values used by the script to create any output files.

Verbose level
=============

If the CIAO verbose level is set to 2 then the command-line used to
run the tool is logged, as long as a logging instance has been created
using ciao_contrib.logger_wrapper.initialize_logger. As an example

  from ciao_contrib.logger_wrapper import initialize_logger, set_verbosity

  initialize_logger("myapp")
  set_verbosity(2)
  dmstat.punlearn()
  dmstat("src1.dat[cols x]", median=True, centroid=True)

will create the additional screen output

  Running tool dmstat using:
  >>> dmstat "src1.dat[cols x]" median=yes

Note that the output only lists hidden parameters if they are not set
to their default value.

"""

import sys
import os
import stat
import operator
import subprocess
import time
import tempfile
import errno
import shutil
import glob
import re

from collections import namedtuple
from contextlib import contextmanager

# only used to check for floating-point equality
import numpy as np

import paramio as pio
import stk
import cxcdm

from ciao_contrib.logger_wrapper import initialize_module_logger

# This is to throw out any date-encoded parameter files which end in
# _YYYYMMDD.HH:MM:SS.par.  I could be clever and specialize this
# (e.g. since we know the first digit of month must be 0 or 1) but
# leave that for now.
#
dtime = re.compile(r"_\d{8}\.\d{2}:\d{2}:\d{2}\.par$")

logger = initialize_module_logger("runtool")

v2 = logger.verbose2
v3 = logger.verbose3
v4 = logger.verbose4
v5 = logger.verbose5

ParValue = namedtuple("ParValue",
                      ["name", "type", "help", "default"])
ParSet = namedtuple("ParSet",
                    ["name", "type", "help", "default", "options"])
ParRange = namedtuple("ParRange",
                      ["name", "type", "help", "default", "lo", "hi"])


class UnknownParamError(TypeError):
    """The parameter is not defined for this tool.

    This is just to provide a slightly-more user friendly error
    message than the standard Python error in this case.
    """

    pass


def _from_python(type, value):
    """Return a string representation of value, where
    type is the paramio "type" of the parameter
    (e.g. one of "b", "i", "r", "s", "f").

    A value of None for numeric types is converted to
    INDEF and "" for strings/filenames.
    """

    if type == "b":
        if value is None:
            raise ValueError("boolean values can not be set to None")
        elif value:
            return "yes"
        else:
            return "no"
    elif type in "ir":
        if value is None:
            return "INDEF"
        else:
            return str(value)
    elif value is None:
        return ""
    else:
        return str(value)


def _to_python(type, value):
    """Return the Python representatiopn of the input value, which is
    a string. The type value is the the paramio "type" of the
    parameter (e.g. one of "b", "i", "r", "s", "f").

    Values converted to None: INDEF for numeric types and "" for
    strings.

    Numeric types with a value of '' (or are all spaces) are converted to 0.

    It looks like this is called assuming that value has been retrived
    gvia one of the paramio routines, and so we don't have to deal
    with all the cases we do in CIAOParameter._validate, but it has
    been long enough since I wrote this that I can not guarantee it.

    """

    if type == "b":
        return value == "yes"

    elif type == "i":
        if value == "INDEF":
            return None
        elif str(value).strip() == "":
            return 0
        else:
            return int(value)

    elif type == "r":
        if value == "INDEF":
            return None
        elif str(value).strip() == "":
            return 0.0
        else:
            return float(value)

    elif value == "":
        return None

    elif value is None:
        raise ValueError("Did not expect to be sent None in _to_python")

    else:
        return str(value)


def _values_equal(ptype, val1, val2):
    """Decide whether two values are equal (or nearly equal) for the
    given parameter type (e.g. one of 'b', 'i', 'r', 's', 'f').

    val1 and val2 are assumed to be the output of _to_python(ptype, ...).
    """

    if ptype != "r" or (val1 is None and val2 is None):
        return val1 == val2

    else:
        return np.allclose([val1], [val2])


def _partial_match(matches, query, qtype="s"):
    """Returns the value from matches - an iterable - that has
    query as its unique prefix. The query type is given
    by qtype; it is normally expected to be 's' but can be other
    values; note that prefix matching is only done if ptype is 's'.

    Return values:

      no match         - None
      one match        - (value, True)
      multiple matches - (matches, False)

    """

    if query in matches:
        return (query, True)

    elif qtype != "s":
        return None

    else:
        out = [v for v in matches if v.startswith(query)]
        nout = len(out)
        if nout == 0:
            return None

        elif nout == 1:
            return (out[0], True)

        else:
            return (out, False)


def _time_delta(stime, etime):
    """Returns a "nice" string representing the time
    difference between stime and etime (with etime > stime).
    """

    dt = time.mktime(etime) - time.mktime(stime)
    if dt < 1.0:
        return "< 1 sec"

    def myint(f):
        return int(f + 0.5)

    def stringify(val, unit):
        out = f"{val} {unit}"
        if val > 1:
            out += "s"
        return out

    d = myint(dt // (24 * 3600))
    dt2 = dt % (24 * 3600)
    h = myint(dt2 // 3600)
    dt3 = dt % 3600
    m = myint(dt3 // 60)
    s = myint(dt3 % 60)

    if d > 0:
        lbl = stringify(d, "day")
        if h > 0:
            lbl += f' {stringify(h, "hour")}'

    elif h > 0:
        lbl = stringify(h, "hour")
        if m > 0:
            lbl += f' {stringify(m, "minute")}'

    elif m > 0:
        lbl = stringify(m, "minute")
        if s > 0:
            lbl += f' {stringify(s, "second")}'

    else:
        lbl = stringify(s, "second")

    return lbl


def _value_needs_quoting(val):
    """Returns True if the given value needs quoting when
    used on the command-line as a parameter value.

    """

    # TODO: are there other problem situations/characters?
    #
    sval = str(val)
    for char in ' [(";':
        if char in sval:
            return True

    return False


def _quote_value(val):
    """Given a string representing a parameter value, return the
    string adding quotes if necessary."""

    if _value_needs_quoting(val):
        return f'"{val}"'
    else:
        return val


def _log_par_file_contents(parfile):
    "Log the contents of the given parameter file"

    if logger.getEffectiveVerbose() < 4:
        return

    v4("***** Start of parameter file")
    with open(parfile, "r") as ofh:
        for line in ofh.readlines():
            v4(f"** {line.strip()}")

    v4("***** End of parameter file")


class CIAOPrintableString(str):
    """Wraps strings for "nice" formatting.

    This is intended for interactive use, such as IPython and
    notebooks. Is it still needed?
    """

    def __init__(self, string):
        self.str = string

    def __str__(self):
        return self.str

    def __repr__(self):
        return self.str


def is_an_iterable(val):
    """Return True if this is an iterable but not a string.

    This is a stop-gap routine to handle Python 2.7 to 3.5
    conversion, since in 2.7 strings did not have an __iter__
    method but they do now. Ideally the code would be rewritten
    to avoid this logic.

    Currently unclear what needs to be changed now we have dropped
    Python 2.7 support, so leave in.
    """

    return not isinstance(val, str) and hasattr(val, "__iter__")


# See
#   http://stackoverflow.com/questions/2693883/dynamic-function-docstring
# for some work on adding individualized doc strings to
# class instances
#
# Could add __eq__/__neq__ methods, comparing parameter values
#
class CIAOParameter(object):
    """Simulate a CIAO parameter file. This class lets you set and get
    parameter settings as if you were using the pset/pget command-line
    tools, but using an attribute style - e.g.

      print(f"The green color is {colors.green}")
      ardlib.AXAF_ACIS0_BADPIX_FILE = "bpix.fits[ccd_id=0]"

    To list all the parameters use the print() command, or convert to
    a string; for example

      print(geom)
      txt = f"We have\n\n{geom}"

    As with the command-line tools, the parameters can be specified
    using any unique prefix of the name (case sensitive), so you can
    say

       ardlib.AXAF_ACIS0_B

    to reder to the AXAF_AXIS0_BADPIX_FILE parameter. Using a
    non-unique prefix will result in an error listing the possible
    matches - so using ardlib.AXAF_ACIS0 will throw

    AttributeError: Multiple matches for ardlib parameter 'AXAF_ACIS0', choose from:
      AXAF_ACIS0_QE_FILE AXAF_ACIS0_QEU_FILE AXAF_ACIS0_BADPIX_FILE AXAF_ACIS0_CONTAM_FILE

    and if there is no match - e.g. colors.bob - you see

    AttributeError: There is no parameter for colors that matches 'bob'

    The object is not callable (ie runnable); for that use the CIAOTool
    subclass.

    NOTES
    =====

    Setting a parameter value ONLY changes the object itself; it does
    NOT change the on-disk parameter file. To write the values to disk
    use the write_params() method.

    Any '-' characters in a parameter name are converted to '_'
    instead. At present this only occurs for several ardlib parameters.

    There is limited support for stacks; you can set any file or
    string parameter to an array which is converted to a
    comma-separated set of values. Note that there is no check that
    the parameter accepts stacks (since this is not encoded in the
    parameter file). The stack module can be used to convert a
    parameter value from the stack format into an attay

    """

    def __init__(self, toolname, reqs, opts):
        """reqs is the list of the required parameters for
        the tool, and opts is the list of optional parameters
        (either may be []).

        The reqs and opts arrays are list of named tuples; support
        types are ParValue, ParSet, and ParRange.
        """

        self._toolname = toolname
        self._required = [p.name.replace('-', '_') for p in reqs]
        self._optional = [p.name.replace('-', '_') for p in opts]
        self._parnames = self._required + self._optional

        z1 = list(zip(self._required, reqs))
        z2 = list(zip(self._optional, opts))
        self._store = dict(z1 + z2)

        # we include names that are not mapped just to make it easier
        z1 = list(zip(self._required,
                      [p.name for p in reqs]))
        z2 = list(zip(self._optional,
                      [p.name for p in opts]))
        self._orig_parnames = dict(z1 + z2)

        self._defaults = {pname: self._store[pname].default
                          for pname in self._parnames}
        # should only be accessed via _set/get_param_value
        self._settings = {}
        self._index = 0
        self.punlearn()

    def _get_param_value(self, pname):
        """Returns the parameter value. This should be used instead of
        accessing self._settings directly, and should not be used by
        external code, which should use the <object>.parname
        interface.

        pname must be the full parameter name.
        """

        # at present do nothing extra
        if pname not in self._parnames:
            raise ValueError(f"Invalid parameter name: {pname}")

        val = self._settings[pname]
        return val

    def _set_param_value(self, pname, nval):
        """Sets the parameter value. This should be used instead of
        accessing self._settings directly, and should not be used by
        external code, which should use the <object>.parname
        interface.

        pname must be the full parameter name and nval is assumed to
        be of the correct type (although arrays are converted into
        comma-separated lists here)
        """

        # at present do nothing extra
        if pname not in self._parnames:
            raise ValueError(f"Invalid parameter name: {pname}")

        if is_an_iterable(nval):
            # should really enforce the type constraint for safety
            # here
            svals = [str(v) for v in nval]
            self._settings[pname] = ",".join(svals)

        else:
            self._settings[pname] = nval

    def __repr__(self):
        return f"<CIAO parameter file: {self._toolname}>"

    def _param_as_string(self, pname):
        "Return a string representation of the parameter"

        pi = self._store[pname]
        pval = self._get_param_value(pname)

        # need !s for value to keep booleans as True or False,
        # otherwise gets converted to 0/1; is this a bug in Python 2.6.2?
        # since "{0}".format(True) == "True"
        #       "{0:5}".format(True) == "1    "
        #       "{0!s:5}".format(True) == "True "
        #

        # QUS: do we want to do any manipulation of the data here?
        # if pi.type == "f" and pval is None:
        #     pval = "INDEF"

        if pi.type in "sf" and pval is None:
            pval = ""

        return f"{pname:>20} = {pval!s:<15}  {pi.help}"

    def __str__(self):
        """Return a multi-line output listing the parameter names and values"""
        out = [f"Parameters for {self._toolname}:"]

        if len(self._required) > 0:
            out.extend(["", "Required parameters:"])
        for pname in self._required:
            out.append(self._param_as_string(pname))

        if len(self._required) > 0:
            out.extend(["", "Optional parameters:"])
        for pname in self._optional:
            out.append(self._param_as_string(pname))
        return "\n".join(out)

    # could say @property here, but since we use __setattr__
    # it seems that we can (have to?) trap write access there
    #
    def toolname(self):
        """The name of the tool (or parameter file)"""
        return self._toolname

    def punlearn(self):
        """Reset the parameter values to their default settings"""
        v5(f"Calling punlearn on tool {self._toolname}")
        self._settings = self._defaults.copy()

    def _expand_parname(self, pname):
        """Returns the parameter name that matches pname (using a
        unique sub-string check); if there is no match or multiple
        matches then an UnknownParamError is thrown.

        The check is case sensitive.
        """

        ans = _partial_match(self._parnames, pname)
        if ans is None:
            raise UnknownParamError(
                f"There is no parameter for {self._toolname} that matches '{pname}'")

        elif ans[1]:
            return ans[0]

        else:
            choices = " ".join(ans[0])
            raise UnknownParamError(
                f"Multiple matches for {self._toolname} parameter '{pname}', choose from:\n  {choices}")

    def _validate(self, pname, val, store=True):
        """Check that val is a valid value for the parameter and
        save it (if store is True). pname should be an exact parameter
        name, and not a partial match. val may be a string redirect.
        """

        v5(f"Entering _validate for name={pname} " +
           f"val={val} (type={type(val)}) " +
           f"store={store}")

        pinfo = self._store[pname]
        ptype = pinfo.type

        # pstr is used for informational and error messages only
        #
        is_redirect = str(val).startswith(")")
        if is_redirect:
            pval = self._eval_redirect(val)
            pstr = f"{val} -> {pval}"
        else:
            pval = val
            pstr = str(val)

        isiterable = is_an_iterable(pval)
        if isiterable and ptype in "bir":
            raise ValueError(f"The {self._toolname}.{pname} value can not be set to an array (sent {pstr})")

        v5(f"Validating {self._toolname}.{pname} val={pstr} as ...")
        if ptype == "b":
            v5("... a boolean")
            try:
                porig = pval
                pval = pval.lower()
                if pval in ["no", "false", "off", "0"]:
                    pval = False
                elif pval in ["yes", "true", "on", "1"]:
                    pval = True
                else:
                    raise ValueError(f"The {self._toolname}.{pname} value should be a boolean, not '{porig}'")

            except AttributeError:
                pval = bool(pval)

        elif ptype == "i":
            v5("... an integer")
            if pval == "INDEF":
                pval = None

            elif str(pval).strip() == "":
                pval = 0

            elif pval is not None:
                try:
                    pval = int(pval)
                except (ValueError, TypeError):
                    raise ValueError(f"The {self._toolname}.{pname} parameter must be an integer, sent {pstr}")

        elif ptype == "r":
            v5("... a float")
            if pval == "INDEF":
                pval = None

            elif str(pval).strip() == "":
                pval = 0.0

            elif pval is not None:
                try:
                    pval = float(pval)
                except (ValueError, TypeError):
                    raise ValueError(f"The {self._toolname}.{pname} parameter must be a float, sent {pstr}")

        elif pval == "":
            v5("... a ''")
            pval = None

        elif pval is not None:
            v5("... something else")
            if isiterable:
                # assuming you can't have a stack with an options setting
                pval = [str(v) for v in pval]
            else:
                pval = str(pval)

        if hasattr(pinfo, "lo") and hasattr(pinfo, "hi"):

            v5(f"Validating {self._toolname}.{pname} val={pval} against min/max={pinfo.lo}/{pinfo.hi}")

            if pval is not None:
                if not self._check_param_limit(pname, pval, pinfo.lo, operator.gt):
                    raise ValueError(f"{self._toolname}.{pname} must be >= {pinfo.lo} but set to {pstr}")

                if not self._check_param_limit(pname, pval, pinfo.hi, operator.lt):
                    raise ValueError(f"{self._toolname}.{pname} must be <= {pinfo.hi} but set to {pstr}")

        elif hasattr(pinfo, "options"):

            v5(f"Validating {self._toolname}.{pname} val={pval} against {pinfo.options}")

            matches = _partial_match(pinfo.options, pval, qtype=ptype)
            if matches is None:
                efmt = "The parameter {} was set to {} when it must be one of:\n  {}"
                raise ValueError(efmt.format(pname, pstr, " ".join([str(o) for o in pinfo.options])))

            elif not matches[1]:
                # can only get multiple matches for strings
                raise ValueError("The parameter {} was set to {} which matches:\n  {}".format(pname, pstr, " ".join(matches[0])))

            else:
                pval = matches[0]

            # convert back to Python type
            pval = _to_python(ptype, pval)

        if store:
            if is_redirect:
                nval = val
            else:
                nval = pval

            v5(f"Setting {self._toolname}.{pname} to {nval} ({type(nval)})")
            self._set_param_value(pname, nval)

    def __getattr__(self, parname):
        """Provide support for read using tool.parameter syntax"""
        try:
            pname = self._expand_parname(parname)
        except UnknownParamError as ue:
            raise AttributeError(str(ue)) from None

        return self._get_param_value(pname)

    def __setattr__(self, name, val):
        """Provide support for write using via tool.parameter syntax"""
        if name.startswith("_"):
            object.__setattr__(self, name, val)

        elif name == "toolname":
            raise AttributeError("can not set toolname attribute")

        else:
            try:
                pname = self._expand_parname(name)
            except UnknownParamError as ue:
                raise AttributeError(str(ue)) from None

            self._validate(pname, val, store=True)

    def __len__(self):
        """Return the number of parameters of the tool"""
        return len(self._parnames)

    def __contains__(self, parname):
        """Returns True if parname is a parameter of the tool;
        parname can be any unique prefix of the parameter name."""
        matches = _partial_match(self._parnames, parname)
        return (matches is not None) and matches[1]

    # TODO: check whether the iterator works
    def __iter__(self):
        """Iterate through the parameters of the tool, returning
        (name,value) pairs."""
        return self

    # TODO: check whether the iterator works
    def next(self):
        """Return the next parameter (name,value) pair for the tool."""
        if self._index == len(self._parnames):
            raise StopIteration
        old = self._index
        self._index = old + 1
        pname = self._parnames[old]
        return (pname, self._get_param_value(pname))

    def _create_parfile_copy(self, parfile=None):
        """Copy the parameter file for the given tool into the given
        file name (parfile). If parfile is None then a temporary file
        is created in $ASCDS_WORK_PATH (or the default value if this
        environment variable does not exist).

        It is up to the caller to make sure that this file
        is deleted once it has been finished with (e.g.  in case of
        errors).

        The routine returns the name of the parameter file.
        """

        toolname = self._toolname
        v5(f"_create_parfile_copy called for {toolname} with parfile={parfile}")

        if parfile is None:
            # tmpfile = True
            try:
                tmpdir = os.environ["ASCDS_WORK_PATH"]
            except KeyError:
                v2(f"WARNING: $ASCDS_WORK_PATH is not set, using default temp dir to create a parameter file for {toolname}")
                tmpdir = None
            # Add in the toolname to the suffix to make tracking down what
            # is being run a bit easier
            pfh = tempfile.NamedTemporaryFile(dir=tmpdir,
                                              suffix=f".{toolname}.par",
                                              delete=False,
                                              mode="w")
            parfile = pfh.name[:]

        else:
            # tmpfile = False
            pfh = open(parfile, "w")

        try:
            ofile = pio.paramgetpath(toolname)

            v5(f"Copying par file {ofile} to {parfile}")
            with open(ofile, "r") as ifh:
                for line in ifh.readlines():
                    pfh.write(line)

            pfh.close()

        except Exception:
            v5(f"Deleting par file due to error: {parfile}")
            os.unlink(parfile)
            raise

        return parfile

    def _update_parfile_write(self, parfile, stackfiles):
        """Part of _update_parfile(): here we write out the
        parameters to the given file name.

        stackfiles is the dictionary of temporary files created to store
        long parameter values/stacks; key is the parameter name and
        value is the filename. It is modified by this routine.

        Any new temporary files are created in $ASCDS_WORK_PATH,
        or the default value if this does not exist.
        """

        try:
            tmpdir = os.environ["ASCDS_WORK_PATH"]
        except KeyError:
            # Do not warn because we may not actually use it
            # v2("WARNING: $ASCDS_WORK_PATH is not set, using /tmp to create a parameter file for {}".format(self._toolname))
            tmpdir = None

        v4(f"Opening parameter file with mode=wLH: '{parfile}'")
        try:
            fp = pio.paramopen(parfile, "wLH")

            for pname in self._parnames:
                try:
                    pval = self._get_param_value(pname)
                except KeyError:
                    v5(f"skipping setting parameter {pname} as not set")
                    continue

                oname = self._orig_parnames[pname]
                ptype = self._store[pname].type
                if oname == pname:
                    v5(f"setting parameter {pname} type={ptype} val={pval}")
                else:
                    v5(f"setting parameter {pname}->{oname} type={ptype} val={pval}")

                nval = _from_python(ptype, pval)

                if len(nval) > 1023:
                    if ptype in "bir":
                        raise ValueError(f"Parameter {self._toolname}.{pname} exceeds 1023 characters in length!")

                    # We rely on the calling routine to delete these
                    # files, even in case of an error. The parameter name
                    # is added just to make tracking down information
                    # a bit easier.
                    #
                    sfh = tempfile.NamedTemporaryFile(dir=tmpdir,
                                                      delete=False,
                                                      mode="w",
                                                      suffix=f".{pname}.stk")
                    sname = sfh.name[:]
                    stackfiles[pname] = sname
                    v5(f"setting parameter {pname} via an external stack file: {sname}")

                    # Not sure if a really long file name is okay in a stack file
                    # but the only other solution is to exit with an error.
                    #
                    for s in stk.build(nval):
                        sfh.write(s)
                        sfh.write("\n")

                    sfh.close()

                    # NOTE:
                    #   use @- rather than @ so that the path to the stack file
                    #   is not included into the stack output. It is expected
                    #   that the user has set the paths correctly if required.
                    #
                    #   This may be changed back to just @, depending on how
                    #   testing goes.
                    #      pio.pset(fp, oname, "@" + sname)
                    pio.pset(fp, oname, "@-" + sname)

                else:
                    pio.pset(fp, oname, nval)

            pio.pset(fp, "mode", "hl")
            pio.paramclose(fp)

        except Exception as ee:
            # Try to provide a helpful message to the user. The
            # paramio module raises Exceptions, so we want to
            # replace these by some generic text, but leave
            # anything more-specific alone.
            #
            if type(ee) == Exception:
                raise IOError("Unable to write to parameter file:\n" +
                              f"  {parfile}") from ee

            raise

    def _update_parfile_verify(self, parfile, stackfiles):
        """Part of _update_parfile(): here we verify that the
        parameters in parfile are the expected values.

        stackfiles is the dictionary of temporary files created to store
        long parameter values/stacks.

        Note that if an external stack file is used we do not currently
        validate its values (it should be, for safety, but isn't).

        Coming back to this code now: why is it needed? Is it really
        an internal check to ensure we haven't messed anything up, or
        is there some need for these checks? At the moment (Oct 5
        2021) I have decided to remove the error check as it fails for
        re-directs.

        """

        v5("Verifying parameter settings")
        try:
            fp = pio.paramopen(parfile, "rH")

            for pname in self._parnames:

                try:
                    # pval = "@" + stackfiles[pname]
                    pval = "@-" + stackfiles[pname]
                    v5(f"parameter {pname} has been set to an " +
                       "external stack file")

                except KeyError:
                    try:
                        pval = self._get_param_value(pname)

                    except KeyError:
                        v5("skipping verifying parameter " +
                           f"{pname} as not set")
                        continue

                oname = self._orig_parnames[pname]
                ptype = self._store[pname].type
                if oname == pname:
                    v5(f"verifying parameter {pname} type={ptype} is val={pval}")
                else:
                    v5(f"verifying parameter {pname}<-{oname} type={ptype} is val={pval}")

                oval = _to_python(ptype, pio.pget(fp, oname))

                # darn: need to deal with re-directs and environment
                # variables; this is a hack and probably want to
                # re-think this a bit
                #
                # Env. variable expansion only happens if the value
                # is enclosed in {}, so
                #    $ASCDS_CALIB
                # is left alone but
                #    ${ASCDS_CALIB}
                # is expanded by pio.pget(). For now just rely on
                # any text begining with ${ as meaning it should be
                # expanded.
                #
                if str(pval).startswith(")"):
                    nval = _to_python(ptype, pio.pget(fp, pval[1:]))
                    pstr = f"{pval} -> {nval}"
                    pval = nval

                elif str(pval).startswith("${"):
                    nval = os.path.expandvars(pval)
                    pstr = f"{pval} -> {nval}"
                    pval = nval

                else:
                    pstr = pval

                if not _values_equal(ptype, oval, pval):
                    # raise IOError(f"Unable to store {self._toolname}.{pname}, should be\n    '{pstr}' ({type(pval)})\n  but parameter file contains\n    '{oval}' ({type(oval)})")
                    v2(f"When writing {self._toolname}.{pname}, expected '{pstr}' but found '{oval}'")

            pio.paramclose(fp)

        except Exception as ee:
            # The paramio module throws Exceptions, so try and clean
            # those up but leave more-specific exceptions alone.
            #
            if type(ee) == Exception:
                raise IOError("Unable to check values in parameter " +
                              f"file:\n  {parfile}") from ee

            raise

    def _update_parfile(self, parfile):
        """Update the supplied file, which is assumed to be a
        copy of the parameter file for this tool, with the
        contents of the current parameter settings.

        parfile should either be the name of the tool or
        end in .par; a ValueError is thrown if this does not
        hold.

        Parameters which are too long to be set with paramio.pset will
        be stored using an external stack file. In this case the
        routine returns a dictionary where the keys are the names of
        these parameters and the values the file names (which should
        be deleted after use). The dictionary will be empty if no
        long parameters are found.

        """

        if parfile != self._toolname and not parfile.endswith(".par"):
            raise ValueError(f"parfile argument is not the tool name nor does it end in .par ({parfile})")

        v5(f"_update_parfile[{self._toolname}] called for {parfile}")

        stackfiles = {}
        try:
            self._update_parfile_write(parfile, stackfiles)
            self._update_parfile_verify(parfile, stackfiles)

        except Exception:

            # ensure any temporary stack files are cleaned up
            for sname in stackfiles.values():
                try:
                    v5(f"Deleting temporary stack file due to error: {sname}")
                    os.unlink(sname)
                except OSError:
                    pass

            raise

        v5(f"_update_parfile[{self._toolname}] returning {stackfiles}")
        return stackfiles

    def _get_command_line_args(self, simplify=True, nameall=False, quote=False):
        """Return an array of tuples (parname, parval) for the
        tool.

        If nameall is False (the default) then parname will be None
        for parameters that do not need their name included (so
        automatic parameters that are not empty).

        If simplify is True (the default) then only those hidden
        parameters that are not set to their default value will
        be included.

        Parameter values are not quoted unless quote is True (the
        default is False).

        Parameter names are converted from Python to their actual names
        (only relevant for the ardlib parameters).

        """

        out = []
        use_name = nameall
        for pname in self._required:
            oname = self._orig_parnames[pname]
            pval = self._get_param_value(pname)
            ptype = self._store[pname].type

            pval = _from_python(ptype, pval)
            if pval == "":
                use_name = True

            if not use_name:
                oname = None

            if quote:
                pval = _quote_value(pval)

            out.append((oname, pval))

        for pname in self._optional:
            oname = self._orig_parnames[pname]
            pval = self._get_param_value(pname)
            if simplify and self._defaults[pname] == pval:
                continue

            ptype = self._store[pname].type
            pval = _from_python(ptype, pval)
            if quote:
                pval = _quote_value(pval)

            out.append((oname, pval))

        return out

    def _display_command_line(self, simplify=True):
        """Log - at a verbose level of 2 - the command line that would
        be entered by a user. Note that we include all parameters,
        even if they match their default values, unless simplify is
        True.

        This does not try to do anything clever with parameter values
        which have been written out as a temporary stack file; the
        screen output will use the '@-<filename>' value rather than try
        to convert it back to a comma-separated list.

        """

        if logger.getEffectiveVerbose() < 2:
            return

        out = [f">>> {self._toolname}"]
        for (pname, pval) in self._get_command_line_args(simplify=simplify, quote=True):
            if pname is None:
                outstr = pval
            else:
                outstr = f"{pname}={pval}"

            out.append(outstr)

        v2(f"Running tool {self._toolname} using:")
        v2(" ".join(out))

    def write_params(self, parfile=None):
        """Write the current parameter settings to a
        parameter file. If parfile is None then the default
        parameter file for the tool is used, otherwise
        parfile is expected to be the name of the file (if
        it does not exist it is created).

        If parfile is given and does not end in '.par' then
        the suffix is automatically appended to the file.

        Any parameters longer than 1023 characters are written
        out, as a stack, to a temporary file and replaced
        by "@-<name of temporary file>". A dictionary of
        these parameters is returned, with the key being the
        parameter name and the value the name of the relevant
        temporary file. It is the users responsibility to delete
        these temporary files.

        If there are no long parameters then the routine returns
        None.
        """

        if parfile is None or parfile in [self._toolname, f'{self._toolname}.par']:
            pname = self._toolname

        else:
            pname = parfile
            if not pname.endswith(".par"):
                pname += ".par"
            self._create_parfile_copy(pname)

        stackfiles = self._update_parfile(pname)
        if pname == self._toolname:
            msg = f"Wrote to the {self._toolname} parameter file"
        else:
            msg = f"Wrote parameters for {self._toolname} to {pname}"

        v3(msg)

        if len(stackfiles) == 0:
            return None
        else:
            v3("Parameters contain temporary stacks:")
            for (k, v) in stackfiles.items():
                v3(f"   {self._toolname}.{k} -> @-{v}")

            return stackfiles

    def read_params(self, parfile=None):
        """Read the parameter settings from the on-disk parameter file
        and use them to update the settings of the object.  If parfile
        is None then the default parameter file for the tool is used,
        otherwise parfile is expected to be the name of the parameter
        file to use (if it does not end in .par then the suffix is
        automatically appended).
        """

        if parfile is None:
            pname = self._toolname

        else:
            pname = parfile
            if not pname.endswith(".par"):
                pname += ".par"

        try:
            fp = pio.paramopen(pname, "rH")
            for pn in self._settings:
                on = self._orig_parnames[pn]
                # QUS: should we do type conversion here, rather than
                # go through the whole __setattr__ work?
                nval = pio.pget(fp, on)
                setattr(self, pn, nval)

            pio.paramclose(fp)

        except Exception as ee:
            # The paramio module throws Exceptions, so try and clean
            # those up but leave more-specific exceptions alone.
            #
            if type(ee) == Exception:
                raise IOError("Unable to read from parameter file:" +
                              f"\n  {pname}")
            else:
                raise

        if pname == self._toolname:
            msg = f"Read from the {self._toolname} parameter file"
        else:
            msg = f"Read parameters for {self._toolname} from {pname}"

        v3(msg)


# This is a base class; you are expected to use one of
#
#    CIAOToolParFile
#    CIAOToolDirect
#
class CIAOTool(CIAOParameter):
    """Run a CIAO tool using a Python object/function, with
    read/write access to the parameter values. For example

      dmcopy("in.fits[col3>2.2][cols col2,col2]",
             "out.dat[kernel text/simple]", clobber=True)

    which can also be written as

      dmcopy.infile = "in.fits[col3>2.2][cols col2,col2]"
      dmcopy.outfile = "out.dat[kernel text/simple]"
      dmcopy(clob=True)

    The call returns the screen output of the tool (both the stdout
    and stderr channels). This can be stored in a variable or - if
    called from an interactive Python session such as IPython or
    Sherpa - it can be automatically displayed, e.g.

     dmstat("sources.dat[z=0.3:0.8][cols z,lx,kt]", median=True)

    If the return value is empty (including all spaces) then None
    is returned.

    As with the command-line parameter interface, parameters can be
    named using a unique prefix; for instance the use of clob above
    to set the clobber parameter.

    After running the tool, the parameter values can be inspected:
    for instance

      dmstat("evt2.fits[energy=500:7000,sky=region(src.reg)][bin sky=::1]",
             cent=False, med=True)
      print(f"Median = {dmstat.out_median}")

    If the tool returns a non-zero status code indicating an error
    then an IOError will be raised.
    """

    def __repr__(self):
        return f"<CIAO tool: {self._toolname}>"

    def _eval_redirect(self, pval):
        """Return the value pval, which can be a
        'redirect' - e.g. ")parname" - or a normal value.

        At present there is only support for redirects within
        the same tool. This *can* return None.
        """

        if str(pval).startswith(")"):
            v5(f"Expanding redirect: input={pval}")
            # the '-'/'_' replacement is prob. not worth doing
            newpar = pval[1:].replace('-', '_')
            if newpar in self._settings:
                newval = self._eval_redirect(self._get_param_value(newpar))
                v5(f" -> {newval}")
                return newval

            raise ValueError(f"Parameter redirect value of {pval} is not supported")

        return pval

    def _check_param_limit(self, pname, pval, plimit, op):
        """Check that pval (the value of the parameter pname)
        returns True for op(pval, plimit) OR that pval == plimit.

        Returns True if it is valid (or there is no limit), False if not.

        op is expected to be either operator.lt or operator.gt. You
        use operator.gt when plimit is the parameter minimum and
        operator.lt when it is the parameter maximum

        The check is skipped if plimit is None (either on input or after
        expanding any redirects), and True is returned.

        We assume that pval is an actual value - ie not a redirect.

        pval can be None, which will likely cause the check to fail
        (but this is not guaranteed), particularly on post-Python 2.7
        systems.
        """

        if plimit is None:
            return True

        lim = self._eval_redirect(plimit)
        if lim is None:
            return True

        return pval == lim or op(pval, lim)

    def _validate_parameters(self):
        """Checks that the parameter settings are valid. This
        uses the stored value for each parameter, otherwise
        the parameter is not checked.

        A ValueError is thrown if there is an error.
        """

        # Loop through the approx order in the parameter file
        #
        for pname in self._parnames:
            self._validate(pname, self._get_param_value(pname), store=False)

    def _process_argument_list(self, args, kwargs):
        """Check that the input args/kwargs are correct and set the
        values for the supplied parameters.

        We no longer exit if the required args are not supplied in
        args/kwargs, since the user may have set them using
           toolname.paramname = ...
        or want to use the default values.

        The values are also validated here.

        """

        toolname = self._toolname
        parnames = self._parnames

        if len(args) > len(parnames):
            raise TypeError(f"{toolname} takes at most {len(parnames)} arguments ({len(args)} given)")

        # We validate the arguments in order; not completely clear it is
        # worth it, but there may be some redirected parameters for which
        # this order makes sense (in particular for range checks).
        #
        store = dict(zip(parnames, args))
        store.update(kwargs)

        nstore = {}
        for (pname, pval) in store.items():
            parname = self._expand_parname(pname)
            nstore[parname] = pval

        for pname in [pn for pn in self._parnames if pn in nstore]:
            pval = nstore[pname]
            v5(f"Setting parameter {pname} to {pval} [from {type(pval)}]")
            self._validate(pname, pval, store=True)

    def punlearn(self):
        self._runtimes = None
        CIAOParameter.punlearn(self)

    def get_runtime_details(self):
        """Returns a dictionary of the information on the last time the
        routine was called. The keywords are

          args   - the command-line arguments for the tool as a list of
                   tuples (parname, parval).
          start  - the start time as returned by time.localtime()
          end    - the end time as returned by time.localtime()
          delta  - a string giving the run time in a "nice" format
                   (e.g. '< 1 sec', '1 minute 34 seconds')
          code   - the return code (0 for success, otherwise an error)
          output - the screen output

        and keywords may not be present if the tool has not been
        run since initialization or the last call to punlearn(),
        or execution of the tool failed.

        The time values are not intended to give an accurate
        representation of the runtime of the tool.

        """

        rval = {}
        if self._runtimes is not None:
            for (k, v) in self._runtimes.items():
                rval[k] = v

        return rval

    def __call__(self, *args, **kwargs):
        """Run the tool. Returns the stdout and stderr of the tool as a single
        string on success (or None if the contents are empty/only contain
        spaces), otherwise throws an IOError. The parameter settings
        of the object are updated to reflect any changes made by the tool.

        """

        raise NotImplementedError


class CIAOToolParFile(CIAOTool):
    """Run a CIAO tool using a separate parameter file (@@ syntax).

    See the help for CIAOTool for information on this
    class.

    """

    def _run(self, parfile):
        """Run the tool, using the given parameter file.

        Returns the return code and the screen output of the tool.

        """

        # We include mode=hl in both the parameter file and explicitly on
        # the command line to try and catch those tools that do not handle
        # parameter redirects; the error message may be confusing but at
        # least it should not appear to hang. Hopefully these are all now
        # instances of CIAOToolDirect instead, but leave in just in case.
        #
        self._runtimes = None

        args = self._get_command_line_args(simplify=False, nameall=True)
        stime = time.localtime()
        v4(f"Starting {self._toolname} at {time.asctime(stime)}")
        self._runtimes = {"start": stime, "args": args}

        # As stderr is merged into stdout, only need to care about the
        # first item returned by communicate.
        proc = subprocess.Popen([self._toolname,
                                 f"@@{parfile}",
                                 "mode=hl"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out = proc.communicate()
        sout = out[0].decode()

        etime = time.localtime()
        rval = proc.returncode
        self._runtimes["code"] = rval

        v4(f"{self._toolname} finished at {time.asctime(etime)}")
        self._runtimes["end"] = etime
        self._runtimes["delta"] = _time_delta(stime, etime)
        self._runtimes["output"] = sout
        v4(f"Run time = {self._runtimes['delta']}")
        v4(f"Return code = {rval}")
        return (rval, sout)

    def __call__(self, *args, **kwargs):

        # processing the argument list also validates them
        self._process_argument_list(args, kwargs)

        parfile = self._create_parfile_copy()
        stackfiles = {}
        try:
            stackfiles = self._update_parfile(parfile)
            self._display_command_line()
            _log_par_file_contents(parfile)
            (rval, sout) = self._run(parfile)
            _log_par_file_contents(parfile)

            if rval == 0:
                self.read_params(parfile)
                for pname in stackfiles:
                    oval = self._get_param_value(pname)
                    v5(f"Replacing {self._toolname}.{pname} = {oval}")
                    nval = stk.build(oval)
                    if len(nval) == 1:
                        nval = nval[0]

                    v5(f"  by {nval}")
                    self._set_param_value(pname, nval)

                txt = sout.rstrip()
                if txt == "":
                    retval = None
                else:
                    retval = CIAOPrintableString(txt)

            else:
                sep = "\n  "
                smsg = sep.join(sout.rstrip().split("\n"))
                raise IOError(f"An error occurred while running '{self._toolname}':{sep}{smsg}")

        finally:
            for v in stackfiles.values():
                v5(f"Deleting stack file: {v}")
                os.unlink(v)

            v5(f"Deleting par file: {parfile}")
            os.unlink(parfile)

        return retval


# TODO: look at wrapping calls to these tools in a
# new_pfiles_envionment context. The issue is whether we want to
# allow the user to over-ride this (e.g. because she has already
# done it)?
#
class CIAOToolDirect(CIAOTool):
    """Run a CIAO tool directly. This is for those tools
    that do not support the @@foo.par syntax for accessing
    an external parameter file. Care should be taken when
    running multiple instances of these tools, since there
    is the possibility that multiple writes or reads of the
    same parameter file could be made.

    See the help for CIAOTool for information on this
    class.

    """

    def _run(self):
        """Run the tool, giving all the parameter on the command line.

        Returns the return code and the screen output of the tool.

        At present there is no attempt to automatically create stack
        files for those parameters that are too long as is done in
        CIAOToolParFile.

        """

        self._runtimes = None

        args = self._get_command_line_args(simplify=False, nameall=True)
        v5(f"Argument list for {self._toolname} = \n{args}")
        pargs = [self._toolname, "mode=hl"]
        pargs.extend([f"{name}={val}" for (name, val) in args])
        stime = time.localtime()
        v4(f"Starting {self._toolname} at {time.asctime(stime)}")
        self._runtimes = {"start": stime, "args": args}

        # As stderr is merged into stdout, only need to care about the
        # first item returned by communicate.
        proc = subprocess.Popen(pargs,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out = proc.communicate()
        sout = out[0].decode()

        etime = time.localtime()
        rval = proc.returncode
        self._runtimes["code"] = rval

        v4(f"{self._toolname} finished at {time.asctime(etime)}")
        self._runtimes["end"] = etime
        self._runtimes["delta"] = _time_delta(stime, etime)
        self._runtimes["output"] = sout
        v4(f"Run time = {self._runtimes['delta']}")
        v4(f"Return code = {rval}")
        return (rval, sout)

    def __call__(self, *args, **kwargs):

        # processing the argument list now validates them too
        self._process_argument_list(args, kwargs)
        # self._validate_parameters()

        self._display_command_line()
        (rval, sout) = self._run()

        if rval == 0:
            # Assume there is a par file we can read from
            # NOTE: this means that settings don't persist in quite
            # the same way as they do for CIAOToolParFile instances
            # (e.g. hidden params will be reset).
            #
            self.read_params()
            txt = sout.rstrip()
            if txt == "":
                retval = None
            else:
                retval = CIAOPrintableString(txt)

        else:
            sep = "\n  "
            smsg = sep.join(sout.rstrip().split("\n"))
            raise IOError(f"An error occurred while running '{self._toolname}':{sep}{smsg}")

        return retval


def get_pfiles(userdir=True):
    """Returns the user portion of the PFILES environment variable
    when userdir is True, otherwise the system portion. If the value
    is empty returns None, otherwise it is an array of directories.
    """

    if "PFILES" not in os.environ:
        raise IOError("The PFILES environment variable is not set.")

    pfiles = os.environ["PFILES"]
    paths = pfiles.split(";")
    if len(paths) != 2:
        raise IOError(f"Expected the PFILES environment variable to contain 1 ';' character, but found {len(paths) - 1}")

    if userdir:
        rval = paths[0]
    else:
        rval = paths[1]

    if rval == "":
        return None
    else:
        return rval.split(":")


def set_pfiles(userdir=None, userdirs=None):
    """Set the user directory of the PFILES environment variable. This
    only affects tools called from within this Python session. It can
    be particularly useful when using tools which access ancillary
    parameter files - such as the ardlib parameter file used by
    many of the instrument tools (e.g. mkinstmap) - to make sure
    that they pick up the right settings.

    If userdir is not None, the value is checked to see if it is a
    directory, and the routine will raise an IOError if it does not
    exist or is not a directory. If userdirs is not None then it is
    taken to be an array of directories - sush as that returned by
    get_pfiles() - each of which is checked for and then used to set
    up the user path. The userdir argument is used if both are not
    None.

    If userdir and userdirs are None then the user directory is
    removed from the PFILES setting. This can be useful to avoid
    problems with running multiple copies of the tool at the same time
    but is not normally needed when using the commands provided by
    this module, since they take care to make sure each tool is called
    with all its parameters in order to avoid this issue (this is only
    strictly true for those tools supported by the CIAOToolParFile
    class; those in the CIAOToolDirect class may have problems when
    multiple instances are run at the same time with the same PFILES
    setting).

    """

    if "PFILES" not in os.environ:
        raise IOError("The PFILES environment variable is not set.")

    pfiles = os.environ["PFILES"]
    paths = pfiles.split(";")
    if len(paths) != 2:
        raise IOError(f"Expected the PFILES environment variable to contain 1 ';' character, but found {len(paths) - 1}")

    syspath = paths[1]

    if userdir is None and userdirs is None:
        newpath = ""

    else:
        if userdir is None:
            udirs = userdirs
        else:
            udirs = [userdir]

        for dname in udirs:
            if os.path.isdir(dname):
                continue

            elif os.path.exists(dname):
                raise IOError(f"{dname} exists but is not a directory")

            else:
                raise IOError(f"{dname} does not exist")

        newpath = ":".join(udirs)

    os.environ["PFILES"] = f"{newpath};{syspath}"


# Context managers for
#  a) creating a temporary directory that will be deleted
#     on exit
#  b) creating a temporary directory and use it for the user component
#     of the PFILES environment variable; this directory is cleaned up
#     on exit and the previous PFILES setting restored
#

@contextmanager
def new_tmpdir(dirname=None, tmpdir=None):
    """A context manager which creates a new temporary directory
    and ensures that it is removed on exit. The name of the
    directory is returned so it can be used as

      with new_tmpdir() as tdir:
          # Run evalpos using this as the tmpdir parameter
          epos = make_tool("evalpos")
          epos(..., tmpdir=tdir)

    If dirname is None then a randomly-generated directory name is
    used; this may not be ideal if a large amount of data is placed in
    the directory (it depends on where tempfile.mkdtemp places the
    directory). This directory will be placed in tmpdir (if not None),
    or $ASCDS_WORK_PATH, or the default value - tempfile.gettempdir() - if
    this environment variable does not exist.  Unlike dirname, tmpdir
    must already exist.

    If dirname is not None then:

      a) it can not refer to an existing path
      b) if it is not absolute then it is converted into an
         absolute path using the current working directory.

    Unlike tempfile.mkdtemp() there is no guarantee that this directory
    is created safely or with permissions valid only for the user.

    This is a simpler version of

       http://bugs.python.org/issue5178

    """

    if dirname is None:
        if tmpdir is None:
            try:
                tmpdir = os.environ["ASCDS_WORK_PATH"]
            except KeyError:
                tmpdir = tempfile.gettempdir()

        try:
            dname = tempfile.mkdtemp(dir=tmpdir, prefix="tmpdir")
        except OSError as ose:
            if ose.errno == errno.ENOENT:
                raise IOError(f"The directory tmpdir={tmpdir} does not exist!")
            elif ose.errno == errno.ENOTDIR:
                raise IOError(f"The tmpdir={tmpdir} argument does not refer to a directory!")
            else:
                raise ose

    else:
        dname = os.path.abspath(dirname)
        if os.path.exists(dname):
            raise IOError(f"Already exists: {dname}")

        else:
            os.makedirs(dname)

    try:
        yield dname

    finally:
        # There has been at least one reported case when the rmtree fails
        # because the directory is not empty. So it might make sense
        # to catch any errors here, except that the belief is that the
        # failure was because the .par file did not have write
        # permission - due to a since-fixed error in new_pfiles_environment
        # - so it is better to keep as is and inform us of any problems.
        #
        shutil.rmtree(dname)


def _copy_par_file(parfile, dirname):
    """Copy parfile to the directory dirname.

    This also makes sure that the copied file has write
    permission since it is intended to be used when paccess
    (or whatever approach is currently in use) fails
    and a manual copy is required.
    """

    # v5("Copying {} to {}".format(parfile, dirname))
    shutil.copy2(parfile, dirname)
    parname = os.path.basename(parfile)
    nfile = os.path.join(dirname, parname)
    st = os.stat(nfile)
    nmode = st.st_mode | stat.S_IWUSR
    # v5(" .. and changing mode from {} to {}".format(st.st_mode, nmode))
    os.chmod(nfile, nmode)


@contextmanager
def new_pfiles_environment(ardlib=True,
                           copyuser=True,
                           dirname=None,
                           tmpdir=None):
    """A context manager which creates a new parameter directory,
    copies over the existing ardlib parameter file to it (if ardlib is
    True), and then sets the PFILES env. var to use this directory
    (for the user path). The block of code is executed and then the
    temporary parameter directory is removed and the preceeding PFILES
    setting is restored.

    The options are, along with their default values:

        ardlib   = True
        copyuser = True
        dirname  = None
        tmpdir   = None

    This is particularly useful if you are going to run multiple
    copies of the same tool, whether with Python's multiprocessing
    module or by running several copies of your code at the same
    time. If you do not use this routine, or a similar technique, then
    you run the risk of an inconsistent or invalid parameter file, and
    hence invalid results, because the file has been changed by
    different processes.  The example below shows how you can use this
    context manager to avoid this problem.

    If the copyuser argument is True then, prior to executing the
    block of code, the user parameter directory (or directories) are
    scanned for any parameter files that are not available in the
    system path and these .par files are copied over. This is to
    support those users who use the user path to set up custom tools
    and scripts (these really should be added to the system part of
    the path, but it's sometimes easier just to add to the user part
    of the path). There is the potential for a race condition here (in
    that if an external process is editing a parameter file whilst it
    is being copied the result may be an invalid parameter file).

    See the new_tmpdir context manager for details of how the
    temporary directory is created (the dirname and tmpdir arguments
    are passed through for this).

    An example of use:

      # The asphist/mkinstmap/mkexpmap call below will use their own
      # PFILES directory and so will not collide with other runs of
      # these tools (or changes to the default ardlib parameter file
      # since this has been copied over to the new directory)
      #
      def getemap(ccd, gridstr):
          with new_pfiles_environment(ardlib=True):
              afile = f"asphist{ccd}.fits"
              ah = make_tool("asphist")
              ah(infile="asol1.fits", outfile=afile,
                 evtfile=f"evt2.fits[ccd_id={ccd}]",
                 clobber=True)

              ifile = f"imap{ccd}.fits"
              mki = make_tool("mkinstmap")
              mki(outfile=ifile, monoenergy=1.7, pixelgrid="1:1024:1,1:1024:1",
                  obsfile=afile+"[asphist]", detsubsys=f"ACIS-{ccd}",
                  maskfile="msk1.fits", clobber=True)

              efile = f"emap{ccd}.fits"
              mke = make_tool("mkexpmap")
              mke(asphistfile=afile, outfile=efile, instmapfile=ifile,
                  xygrid=gridstr, clobber=True)


    """

    # I did think about just adding the new directory to the start of
    # the user path, but then any existing parameter files in the
    # pre-existing directories will be used, which is not what we
    # want. So we seem to be stuck with this awkward set up for now.
    #
    # There is a possibility of file corruption here, since we could
    # copy a parameter file as it is being edited by another process.
    # For now keep as an acceptable risk since the user has this
    # possibility at the shell prompt when run.
    #
    # A helpdesk user had problems using fluximage after starting
    # LHEASOFT and CIAO, where resetting the original PFILES
    # environment in the finally block causes a failure with an error
    # message about being unable to find a directory which has been
    # randomly generated. There have been problems in repeating the
    # issue, so rather than resolve this, we manually store and restore
    # the full PFILES environment variable rather than use set_pfiles,
    # since we assume that if it was valid before hand then it should
    # be valid afterward too.
    #
    ardlibpath = pio.paramgetpath('ardlib')
    odirs = get_pfiles()
    origpfiles = os.environ['PFILES']
    v5(f"About to overide user PFILES setting: {odirs} from {origpfiles}")

    with new_tmpdir(dirname=dirname, tmpdir=tmpdir) as dname:

        v5(f"Setting up {dname} as new user PFILES directory")
        set_pfiles(dname)

        try:

            if copyuser and odirs is not None:
                v5(f"Checking parameter directories: {odirs}")
                null = open(os.devnull, 'wb')

                # We scan through all the directories in reverse order
                # (to try and mimic the priority of the parameter library)
                # and copy over any interesting parameter files we find.
                #
                # As noted, there are issues with this, including
                #  - how to actually find and copy .par values
                #  - what happens if there are problems copying over .par
                #    files (seen in a multi-threaded case which had
                #    temporary .par files [from runtool] appearing within
                #    the directory from which we are copying, so the code
                #    tried to copy them over, but the file was deleted before
                #    the copy, causing a crash)
                #
                # Note
                #   if copyuser=True and ardlib=True then the ardlib file may
                #   be copied twice, which seems wasteful.
                #
                for od in odirs[::-1]:
                    v5(f"Checking in: {od}")
                    # we want to exclude the 'backup copies' that
                    # get stored, so reject any name that
                    # ends in "_YYYYMMDD.HH:MM:SS.par"
                    #
                    for pname in glob.glob(f"{od}/*.par"):
                        bname = os.path.basename(pname)
                        if dtime.search(bname) is not None:
                            continue

                        v5(f"Checking file: {bname}")
                        bname = bname[:-4]
                        try:
                            # Used to use pio.paramgetpath since this
                            # just finds the parameter file;
                            # pio.pacccess will also copy it, which we
                            # don't want here. However, paramgetpath
                            # will error out if the parameter file is
                            # invalid, as some FTOOLS parameter files
                            # are. So, we have moved to using the
                            # following approach, using an
                            # un-advertised feature of the parameter
                            # library (attempt 2). This also fails, so
                            # left with the following, which is not
                            # ideal and makes me think that we should
                            # either just copy everything or drop the
                            # approach completely.
                            #
                            # Attempt 1:
                            #  pio.paramgetpath(bname)
                            #   - catch Exception
                            #
                            # Attempt 2:
                            #  phdl = pio.paramopen(bname, "r>") # restrict search to system path
                            #  pio.paramclose(phdl)
                            #  - catch IOError
                            #
                            subprocess.check_call(['paccess', bname],
                                                  stdout=null, stderr=null)

                        except subprocess.CalledProcessError:
                            v5(f"Copying over {pname} as not in system path (or paccess failed)")
                            try:
                                _copy_par_file(pname, dname)
                            except IOError as ioe:
                                v5(f"WARNING: skipping copy of {pname} because of: {ioe}")

            if ardlib:
                # Question: why not try the paccess route here first?
                # If the user has asked for ardlib to be copied then
                # error out if it can't be (unlike the generic file copy above)
                #
                v5(f"About to copy over ardlib parameter file: {ardlibpath}")
                _copy_par_file(ardlibpath, dname)

            yield dname

        finally:
            v5(f"About to restore PFILES setting to {origpfiles}")
            os.environ['PFILES'] = origpfiles


def add_comment_lines(infile, comments):
    """Add the text in comments to infile as a COMMENT (adding to the
    most-interesting block). comments can either be a string or
    an array of strings.

    infile is a string. If comments is the empty array then nothing
    is done, but empty comments are added (so comments=[] does nothing
    but comments=[""] will add a blank comment line)
    """

    if isinstance(comments, str):
        cs = [comments]
    else:
        cs = comments

    if cs == []:
        return

    v4(f"Adding comments to {infile}")
    bl = cxcdm.dmBlockOpen(infile, update=True)
    try:
        for comment in cs:
            v4(f"COMMENT: {comment}")
            cxcdm.dmBlockWriteComment(bl, 'COMMENT', comment)

    finally:
        cxcdm.dmBlockClose(bl)


def add_tool_history(infiles, toolname, params,
                     toolversion=None, tmpdir=None):
    """Add a CIAO history block to each of the files in infiles saying
    that toolname was run with the given set of parameters (a
    key/value dictionary). If infiles is a single string then it is
    assumed to be the name of a single file.

    A comment line is also added saying

        <toolname> version <toolversion>

    when toolversion is not None.

    The process is done with a temporary PFILES environment (using the
    new_pfiles_environment context manager, passing through the tmpdir
    argument) to avoid problems with clobbering an existing parameter
    file.
    """

    msg = f"Adding HISTORY record for {toolname} "
    if toolversion is not None:
        msg += f"({toolversion}) "

    v2(msg)
    v3(f"Params: {params}")

    # special case a single file
    if isinstance(infiles, str):
        infiles = [infiles]

    tool = make_tool('dmhistory')
    with new_pfiles_environment(ardlib=False, copyuser=False, tmpdir=tmpdir):
        # would like to just say
        # pio.pset(toolname, params)
        # but for now do it manually
        #
        pio.punlearn(toolname)
        fp = pio.paramopen(toolname, "wL")
        for (k, v) in params.items():
            v3(f"Checking parameter <{k}> value <{v}> type={type(v)}")
            if isinstance(v, bool):
                if v:
                    val = "yes"
                else:
                    val = "no"
            else:
                val = str(v)

            v3(f" -> {k}={v}")
            pio.pset(fp, k, val)

        pio.paramclose(fp)

        if toolversion is not None:
            comments = [f"{toolname} version {toolversion}"]
        else:
            comments = None

        for infile in infiles:
            v2(f"Adding history to {infile}")
            if comments is not None:
                add_comment_lines(infile, comments)

            tool(infile=infile, tool=toolname, action="put")


parinfo = {}


# We use list_tools rather than the more semantically-correct name
# list_parameters as it is probably less confusing for the intended
# audience, and to match make_tool
#
def list_tools(tools=True, params=True):
    """Returns a list of parameter files used by this
    module.

    If tools is True then the list includes those parameter files
    that have an associated exectuable (ie are a "tool").

    If params is True then the list includes those parameter files
    which do not have a tool (so just a parameter file).
    """

    allowed = []
    if tools:
        allowed.append(True)
    if params:
        allowed.append(False)

    out = [pname for (pname, pi) in parinfo.items()
           if pi["istool"] in allowed]
    out.sort()
    return out


# Those tools which can not be run using <toolname> @@foo.par.
# This is believed to be correct as of June 2017 (CIAO 4.9).
#
_no_par_file = ["axbary", "dmgti", "evalpos", "fullgarf",
                "mean_energy_map", "pileup_map", "tgdetect",
                "wavdetect"]


def make_tool(toolname):
    """Returns an object that can be used to call the
    given toolname.
    """

    if toolname in parinfo:
        pi = parinfo[toolname]
        if pi["istool"]:
            if toolname in _no_par_file:
                cfunc = CIAOToolDirect
            else:
                cfunc = CIAOToolParFile
        else:
            cfunc = CIAOParameter

        return cfunc(toolname, pi["req"], pi["opt"])

    raise ValueError(f"The tool '{toolname}' is not available.")

# Auto-generated code follows
#
parinfo['acis_bkgrnd_lookup'] = {
    'istool': True,
    'req': [ParValue("infile","f","Event file for which you want background files",None)],
    'opt': [ParValue("outfile","f","ACIS background file(s) to use",None),ParSet("blname","s","What block identifier should be added to the filename?",'none',["none","name","number","cfitsio"]),ParRange("verbose","i","Debug level (0=no debug information)",0,0,5)],
    }


parinfo['acis_build_badpix'] = {
    'istool': True,
    'req': [ParValue("pbkfile","f","Parameter block file",None),ParValue("berrfile","f","Bias error files",None),ParValue("calibfile","f","Calibration bad pixel file",None),ParValue("biasfile","f","Bias images",None),ParValue("evt0file","f","L0 Event lists",'none'),ParValue("obsfile","f","Observation parameter file or acis event-datafile",None),ParValue("outfile","f","Output filename",None)],
    'opt': [ParRange("maxerr","i","Maximum no. of bias parity errors to record per exposure",10,1,100),ParValue("usrfile","f","User-specified supplemental bad-pixel file (NONE -- none -- <filename>)",'none'),ParValue("bitflag","s","A 32-character string where 0=exclude pixel, 1=include pixel, but not its neighbors, and 2=include pixel and its neighbors",'00000000000000122221100020022222'),ParValue("procbias","b","Process bias image data",True),ParRange("biasthresh","i","Minimum bias offset for invalid pixels in adu",6,3,4000),ParValue("writebias","b","Output faint+bias bias images",False),ParValue("outbias","f","Prefix for faint+bias bias images",None),ParValue("clobber","b","Overwrite if file exists",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['acis_check_pha_range'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input ACIS event file",None)],
    'opt': [ParValue("mskfile","f","ACIS mask file, *_msk1.fits",None),ParSet("binsize","i","Block size used to estimate gain",128,[1,2,4,8,16,32,64,128,256]),ParRange("verbose","i","Tool chatter",1,0,5)],
    }


parinfo['acis_detect_afterglow'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file or stack",None),ParValue("outfile","f","Output event file",None)],
    'opt': [ParValue("logfile","f","Log filename",'stdout'),ParSet("pha_rules","s","Pha criteria for subsequent events",'LTEQ',["LT","LTEQ","EQ","NONE"]),ParSet("fltgrade_rules","s","Fltgrade criteria for subsequent events",'NONE',["LT","LTEQ","EQ","NONE"]),ParRange("maxchain","i","Maximum number of exposures for a single flaring event",16,2,1024),ParRange("verbose","i","Debug level",0,0,5),ParValue("clobber","b","Overwrite output file if it exists",False)],
    }


parinfo['acis_fef_lookup'] = {
    'istool': True,
    'req': [ParValue("infile","f","Source file (event or spectrum)",None),ParSet("chipid","s","ACIS chip number",'none',["none","NONE","0","1","2","3","4","5","6","7","8","9"]),ParRange("chipx","i","ACIS chip x coordinate",1,1,1024),ParRange("chipy","i","ACIS chip y coordinate",1,1,1024)],
    'opt': [ParValue("outfile","s","FEF file to use",None),ParValue("quality","b","Should you use the FEF file (if no use mkacisrmf)?",False),ParRange("verbose","i","Verbose level",0,0,5)],
    }


parinfo['acis_find_afterglow'] = {
    'istool': True,
    'req': [ParValue("infile","s","Name of input event-data file(s)",None),ParValue("outfile","s","Name of output bad-pixel file",None),ParValue("badpixfile","s","Name of input bad-pixel file",None),ParValue("maskfile","s","Name of input mask file",None),ParValue("statfile","s","Name of input exposure-statistics file",None)],
    'opt': [ParRange("expnowindow","i","Number of frames in the sliding time window",10,1,100),ParRange("probthresh","r","Minimum post-trials significance of potential afterglows (1 sigma = 0.159, 2 sigma = 0.0228, and 3 sigma = 0.00135)",0.001,1e-10,0.1),ParRange("cntthresh","i","Minimum number of events in an afterglow",4,2,10),ParRange("regwidth","i","Size of reference region (e.g., 7 pixels x 7 pixels)",7,3,255),ParRange("nfpixreg","i","Size of the pixel region for calculation of the Nominal Fluence",32,16,256),ParRange("nfrepeat","i","Number of iterations during calculation of Nominal Fluence",10,1,30),ParRange("tolerance","r","Tolerance for series calculations",1.0e-15,1e-16,1e-06),ParValue("runhotpix","b","Run the hot pixel portion of the algorithm?",True),ParValue("clobber","b","Overwrite output file if it exists?",False),ParRange("verbose","i","Amount of messages produced (0=none, 5=all)",0,0,5)],
    }


parinfo['acis_process_events'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file or stack",None),ParValue("outfile","f","Output event file name",None),ParValue("acaofffile","f","aspect offset file ( NONE | none | <filename>)",'NONE')],
    'opt': [ParValue("apply_cti","b","Apply CTI adjustment?",True),ParValue("apply_tgain","b","Apply time-dependent gain adjustment?",True),ParValue("obsfile","f","obs.par file for output file keywords ( NONE | none | <filename>)",'NONE'),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("logfile","f","debug log file ( STDOUT | stdout | <filename>)",'stdout'),ParValue("gradefile","f","grade mapping file ( NONE | none | CALDB | <filename>)",'CALDB'),ParValue("grade_image_file","f","grade image file for cti correcting graded mode ( NONE | none | CALDB | <filename>)",'CALDB'),ParValue("gainfile","f","acis gain file ( NONE | none | CALDB | <filename>)",'CALDB'),ParValue("badpixfile","f","acis bad pixel file ( NONE | none | <filename>)",'NONE'),ParValue("threshfile","f","split threshold file ( NONE | none | CALDB | <filename>)",'CALDB'),ParValue("ctifile","f","acis CTI file ( NONE | none | CALDB | <filename>)",'CALDB'),ParValue("tgainfile","f","gain adjustment file ( NONE | none | CALDB | <filename>)",'CALDB'),ParValue("mtlfile","s","Mission time line file with FP_TEMP data",'NONE'),ParValue("eventdef","s","output format definition",')stdlev1'),ParValue("doevtgrade","b","Determine event flight grade?",True),ParValue("check_vf_pha","b","Check very faint pixels?",False),ParRange("trail","r","Trail fraction",0.027,0,1),ParValue("calculate_pi","b","perform pha->pi conversion? (requires gain file)",True),ParRange("pi_bin_width","r","Width of Pi bin in eV",14.6,1,100),ParRange("pi_num_bins","i","Number of values to bin energy into",1024,256,32767),ParRange("max_cti_iter","i","Maximum iterations for the CTI adjustment of each event",15,1,20),ParRange("cti_converge","r","The convergence criterion for each CTI-adjusted pixel in adu",0.1,0.1,1),ParValue("clobber","b","Overwrite output event file if it already exists?",False),ParRange("verbose","i","level of debug detail (0=none, 5=most)",0,0,5),ParSet("stop","s","where to end transformations",'sky',["chip","tdet","det","tan","sky","none"]),ParRange("rand_seed","i","random seed (for pixlib), 0 = use time dependent seed",1,0,None),ParValue("rand_pha","b","Randomize the pha value used in gain calculations",True),ParSet("pix_adj","s","Sub-pixel adjustment algorithm",'EDSER',["EDSER","CENTROID","RANDOMIZE","NONE"]),ParValue("subpixfile","f","Name of input sub-pixel calibration file",'CALDB'),ParValue("stdlev1","s","TE faint modes event definition string",'{d:time,l:expno,s:ccd_id,s:node_id,s:chip,s:tdet,f:det,f:sky,s:phas,l:pha,l:pha_ro,f:energy,l:pi,s:fltgrade,s:grade,x:status}'),ParValue("grdlev1","s","TE graded event format definition string",'{d:time,l:expno,s:ccd_id,s:node_id,s:chip,s:tdet,f:det,f:sky,l:pha,l:pha_ro,s:corn_pha,f:energy,l:pi,s:fltgrade,s:grade,x:status}'),ParValue("cclev1","s","CC faint event format definition string",'{d:time,d:time_ro,l:expno,s:ccd_id,s:node_id,s:chip,s:tdet,f:det,f:sky,f:sky_1d,s:phas,l:pha,l:pha_ro,f:energy,l:pi,s:fltgrade,s:grade,x:status}'),ParValue("ccgrdlev1","s","cc graded event format definition string",'{d:time,d:time_ro,l:expno,s:ccd_id,s:node_id,s:chip,s:tdet,f:det,f:sky,f:sky_1d,l:pha,l:pha_ro,s:corn_pha,f:energy,l:pi,s:fltgrade,s:grade,x:status}'),ParValue("cclev1a","s","Lev1.5 CC faint event format definition string",'{d:time,d:time_ro,l:expno,s:ccd_id,s:node_id,s:chip,f:chipy_tg,f:chipy_zo,s:tdet,f:det,f:sky,f:sky_1d,s:phas,l:pha,l:pha_ro,f:energy,l:pi,s:fltgrade,s:grade,f:rd,s:tg_m,f:tg_lam,f:tg_mlam,s:tg_srcid,s:tg_part,s:tg_smap,x:status}'),ParValue("ccgrdlev1a","s","lev1.5 cc graded event format definition string",'{d:time,d:time_ro,l:expno,s:ccd_id,s:node_id,s:chip,f:chipy_tg,f:chipy_zo,s:tdet,f:det,f:sky,f:sky_1d,l:pha,l:pha_ro,s:corn_pha,f:energy,l:pi,s:fltgrade,s:grade,f:rd,s:tg_m,f:tg_lam,f:tg_mlam,s:tg_srcid,s:tg_part,s:tg_smap,x:status}')],
    }


parinfo['acis_set_ardlib'] = {
    'istool': True,
    'req': [ParValue("badpixfile","f","Bad pixel file for the observation",None)],
    'opt': [ParValue("absolutepath","b","Use an absolute path in the parameter file",True),ParValue("ardlibfile","f","Parameter file to change",'ardlib'),ParRange("verbose","i","Verbosity (0 for no screen output)",1,0,5)],
    }


parinfo['acis_streak_map'] = {
    'istool': True,
    'req': [ParValue("infile","f","Evt file",None),ParValue("fovfile","f","FOV file",None),ParValue("bkgroot","f","Output background file root",None),ParValue("regfile","f","Output streak region file",None)],
    'opt': [ParRange("nsigma","r","Std. dev. multiple used in identifying rows with sources",6,1,None),ParRange("msigma","r","Std. dev. multiple used in identifying non-streak cols",6,1,None),ParRange("ssigma","r","Std. dev. multiple used to identify real src on streak (-1 = no srcs)",-1,-1,None),ParValue("dither","i","Number of dither pixels",35),ParValue("binsize","i","Size of source-free row bins (counts)",1),ParRange("k1","r","Source free row calculation factor k1",1.0,0,None),ParRange("k2","r","Source free row calculation factor k2",2.0,0,None),ParValue("tmppath","s","Temporary file path",'${ASCDS_WORK_PATH}'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug level (0-5)",0,0,5)],
    }


parinfo['acisreadcorr'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset/block specification",None),ParValue("aspect","f","Aspect file",None),ParValue("x","r","Sky X position (pixels)",None),ParValue("y","r","Sky Y position (pixels)",None)],
    'opt': [ParValue("dx","r","Chip X tolerance diameter (pixels)",None),ParValue("dy","r","Chip Y tolerance diameter (pixels)",None),ParValue("bkg","f","Background PI spectrum file",None),ParValue("bgroup","r","Min counts for PI group",10),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("random","i","random seed (0 use time)",0),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['aconvolve'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("outfile","f","Output file name",None),ParValue("kernelspec","s","Kernel specification",None)],
    'opt': [ParValue("writekernel","b","Output kernel",False),ParValue("kernelfile","f","Output kernel file name",'./.'),ParValue("writefft","b","Write fft outputs",False),ParValue("fftroot","f","Root name for FFT files",'./.'),ParSet("method","s","Convolution method",'slide',["slide","fft"]),ParSet("edges","s","Edge treatment",'wrap',["nearest","constant","mirror","wrap","renorm"]),ParValue("const","r","Constant value to use at edges with edges=constant",0),ParValue("pad","b","Pad data axes to next power of 2^n",False),ParValue("center","b","Center FFT output",False),ParSet("normkernel","s","Normalize the kernel",'area',["none","area","max"]),ParValue("clobber","b","Clobber existing output",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['acrosscorr'] = {
    'istool': True,
    'req': [ParValue("infile1","f","Input file name #1",None),ParValue("infile2","f","Input file name #2 (none=autocorrelate)",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParValue("crop","b","Crop output to size of infile1",False),ParValue("pad","b","Pad data to size of infile1 + infile2",False),ParValue("center","b","Center output",False),ParValue("clobber","b","Clobber existing output file",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['addresp'] = {
    'istool': True,
    'req': [ParValue("infile","f","RMF files",None),ParValue("arffile","f","ARF files",None),ParValue("phafile","f","PHA files",None),ParValue("outfile","f","merged RMF or RSP file",None),ParValue("outarf","f","merged ARF file",None)],
    'opt': [ParSet("type","s","output type",'rmf',["rmf","rsp"]),ParSet("method","s","ARF merge method",'avg',["sum","avg"]),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/addresp_header_lookup.txt'),ParRange("thresh","r","low threshold of energy cut-off probability",1e-06,0,None),ParValue("clobber","b","overwrite existing output file (yes|no)?",False),ParRange("verbose","i","verbosity level (0 = no display)",0,0,5)],
    }


parinfo['aplimits'] = {
    'istool': True,
    'req': [ParRange("prob_false_detection","r","Upper limit on the probability of a type I error",.1,0,1),ParRange("prob_missed_detection","r","Upper limit on the probability of a type II error",.5,0,1),ParValue("outfile","f","Filename of output file",None),ParRange("T_s","r","Exposure time in source aperture",1,0,None),ParRange("A_s","r","Geometric area of source aperture",1,0,None),ParRange("bkg_rate","r","Background count rate",None,0,None),ParRange("m","i","Number of counts in background aperture",None,0,None),ParRange("T_b","r","Exposure time in background aperture",1,0,None),ParRange("A_b","r","Geometric area of background aperture",1,0,None)],
    'opt': [ParRange("max_counts","i","Background count number above which the uncertainty on the background is ignored",50,0,None),ParRange("maxfev","i","Maximal number of function evaluations in numerical root finding",500,0,None),ParRange("verbose","i","Debug Level(0-5)",1,0,5),ParValue("clobber","b","OK to overwrite existing output file?",False)],
    }


parinfo['apowerspectrum'] = {
    'istool': True,
    'req': [ParValue("infilereal","f","Input file name for real part",None),ParValue("infileimag","f","Input file name for imaginary part",None),ParValue("outfile","f","File name for output",None)],
    'opt': [ParValue("pad","b","Pad data array to next power of 2",False),ParValue("center","b","Center 0 frequency at center of array",False),ParSet("scale","s","Output scale",'linear',["linear","log","db"]),ParValue("crop","b","Crop output at Nyquist frequency",False),ParValue("clobber","b","Delete existing output",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['apply_fov_limits'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outfile","f","Output image",None)],
    'opt': [ParRange("binsize","r","Image binning factor",None,0,None),ParValue("fovfile","f","Input FOV file",None),ParSet("datatype","s","Data type for outfile",'i4',["i2","i4"]),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level (0-5)",1,0,5)],
    }


parinfo['aprates'] = {
    'istool': True,
    'req': [ParRange("n","i","Source counts",None,0,None),ParRange("A_s","r","Source area [arcsec]",None,0,None),ParRange("alpha","r","Source PSF fraction",1,0,1),ParRange("T_s","r","Source exposure time [sec]",None,0,None),ParRange("E_s","r","Source average exposure [cm^2 sec]",None,0,None),ParRange("eng_s","r","Average energy in src region [ergs]",None,0,None),ParRange("flux_s","r","Average flux in src region [ergs/cm^2/s]",None,0,None),ParRange("m","i","Background counts",None,0,None),ParRange("A_b","r","Background area [arcsec]",None,0,None),ParRange("beta","r","Background PSF fraction",0,0,1),ParRange("T_b","r","Background exposure time [sec]",None,0,None),ParRange("E_b","r","Background average exposure [cm^2 sec]",None,0,None),ParRange("eng_b","r","Average energy in bkg region [ergs]",None,0,None),ParRange("flux_b","r","Average flux in bkg region [ergs/cm^2/s]",None,0,None),ParRange("conf","r","Confidence region",0.68,0,1),ParValue("outfile","f","Output parameter file name",None)],
    'opt': [ParRange("resolution","r","Resolution of errors",0.01,0,1),ParSet("pdf","s","Method to estimate errors",'alternate',["gaussian","alternate"]),ParValue("max_counts","i","Maximum (rn-m)/(rf-g) before switching to Gaussian",50),ParValue("itermax","i","Maximum number of iterations to determine PDF grid",100),ParValue("nsigma","r","Number of sigma from S_mle to evaluate PDF",5.0),ParValue("pmin","r","Ratio of PDF peak to extreme",1.0e-5),ParValue("clobber","b","Overwrite output file if it already exists?",False),ParRange("verbose","i","Tool verbosity",0,0,5)],
    }


parinfo['ardlib'] = {
    'istool': False,
    'req': [ParValue("ArdlibDataPath","s","Directory containing data files",'$ASCDS_CALIB'),ParValue("GENERIC_EFFAREA_FILE","f","Enter effective area file",'xrt_ea_v2_0.fits'),ParValue("GENERIC_VIGNET_FILE","f","Enter vignetting file",'/dev/null'),ParValue("AXAF_EFFAREA_FILE_0001","f","Enter AXAF eff-area file 0001",'CALDB'),ParValue("AXAF_EFFAREA_FILE_0010","f","Enter AXAF eff-area file 0010",'CALDB'),ParValue("AXAF_EFFAREA_FILE_0100","f","Enter AXAF eff-area file 0100",'CALDB'),ParValue("AXAF_EFFAREA_FILE_1000","f","Enter AXAF eff-area file 1000",'CALDB'),ParValue("AXAF_EFFAREA_FILE_1111","f","Enter AXAF eff-area file 1111",'CALDB'),ParValue("AXAF_VIGNET_FILE_0001","f","Enter AXAF vignet file 0001",'CALDB'),ParValue("AXAF_VIGNET_FILE_0010","f","Enter AXAF vignet file 0010",'CALDB'),ParValue("AXAF_VIGNET_FILE_0100","f","Enter AXAF vignet file 0100",'CALDB'),ParValue("AXAF_VIGNET_FILE_1000","f","Enter AXAF vignet file 1000",'CALDB'),ParValue("AXAF_VIGNET_FILE_1111","f","Enter AXAF vignet file 1111",'CALDB'),ParValue("AXAF_ACIS0_QE_FILE","f","Enter ACIS-0 Mean QE File",'CALDB'),ParValue("AXAF_ACIS1_QE_FILE","f","Enter ACIS-1 Mean QE File",'CALDB'),ParValue("AXAF_ACIS2_QE_FILE","f","Enter ACIS-2 Mean QE File",'CALDB'),ParValue("AXAF_ACIS3_QE_FILE","f","Enter ACIS-3 Mean QE File",'CALDB'),ParValue("AXAF_ACIS4_QE_FILE","f","Enter ACIS-4 Mean QE File",'CALDB'),ParValue("AXAF_ACIS5_QE_FILE","f","Enter ACIS-5 Mean QE File",'CALDB'),ParValue("AXAF_ACIS6_QE_FILE","f","Enter ACIS-6 Mean QE File",'CALDB'),ParValue("AXAF_ACIS7_QE_FILE","f","Enter ACIS-7 Mean QE File",'CALDB'),ParValue("AXAF_ACIS8_QE_FILE","f","Enter ACIS-8 Mean QE File",'CALDB'),ParValue("AXAF_ACIS9_QE_FILE","f","Enter ACIS-9 Mean QE File",'CALDB'),ParValue("AXAF_ACIS0_QEU_FILE","f","Enter ACIS-0 Uniformity file",'CALDB'),ParValue("AXAF_ACIS1_QEU_FILE","f","Enter ACIS-1 Uniformity file",'CALDB'),ParValue("AXAF_ACIS2_QEU_FILE","f","Enter ACIS-2 Uniformity file",'CALDB'),ParValue("AXAF_ACIS3_QEU_FILE","f","Enter ACIS-3 Uniformity file",'CALDB'),ParValue("AXAF_ACIS4_QEU_FILE","f","Enter ACIS-4 Uniformity file",'CALDB'),ParValue("AXAF_ACIS5_QEU_FILE","f","Enter ACIS-5 Uniformity file",'CALDB'),ParValue("AXAF_ACIS6_QEU_FILE","f","Enter ACIS-6 Uniformity file",'CALDB'),ParValue("AXAF_ACIS7_QEU_FILE","f","Enter ACIS-7 Uniformity file",'CALDB'),ParValue("AXAF_ACIS8_QEU_FILE","f","Enter ACIS-8 Uniformity file",'CALDB'),ParValue("AXAF_ACIS9_QEU_FILE","f","Enter ACIS-9 Uniformity file",'CALDB'),ParValue("AXAF_ACIS0_BADPIX_FILE","f","Enter ACIS-0 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS1_BADPIX_FILE","f","Enter ACIS-1 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS2_BADPIX_FILE","f","Enter ACIS-2 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS3_BADPIX_FILE","f","Enter ACIS-3 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS4_BADPIX_FILE","f","Enter ACIS-4 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS5_BADPIX_FILE","f","Enter ACIS-5 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS6_BADPIX_FILE","f","Enter ACIS-6 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS7_BADPIX_FILE","f","Enter ACIS-7 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS8_BADPIX_FILE","f","Enter ACIS-8 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS9_BADPIX_FILE","f","Enter ACIS-9 Bad Pixel File",'CALDB'),ParValue("AXAF_ACIS0_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS1_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS2_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS3_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS4_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS5_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS6_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS7_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS8_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_ACIS9_CONTAM_FILE","f","Enter ACIS Contamination File",'CALDB'),ParValue("AXAF_HRC-I_QE_FILE","f","Enter HRC-I Mean QE file",'CALDB'),ParValue("AXAF_HRC-I_QEU_FILE","f","Enter HRC-I Mean QE file",'CALDB'),ParValue("AXAF_HRC-I_BADPIX_FILE","f","Enter HRC-I Badpix file",'NONE'),ParValue("AXAF_HRC-S1_QE_FILE","f","Enter HRC-S1 Mean QE file",'CALDB'),ParValue("AXAF_HRC-S2_QE_FILE","f","Enter HRC-S2 Mean QE file",'CALDB'),ParValue("AXAF_HRC-S3_QE_FILE","f","Enter HRC-S3 Mean QE file",'CALDB'),ParValue("AXAF_HRC-S1_QEU_FILE","f","Enter HRC-S1 QE Uniformity file",'CALDB'),ParValue("AXAF_HRC-S2_QEU_FILE","f","Enter HRC-S2 QE Uniformity file",'CALDB'),ParValue("AXAF_HRC-S3_QEU_FILE","f","Enter HRC-S3 QE Uniformity file",'CALDB'),ParValue("AXAF_HRC-S_BADPIX_FILE","f","Enter HRC-S Badpix file",'NONE'),ParValue("AXAF_HETG_1000_FILE","f","Enter HETG 1000 efficiency file",'CALDB'),ParValue("AXAF_HETG_0100_FILE","f","Enter HETG 0100 efficiency file",'CALDB'),ParValue("AXAF_HETG_0010_FILE","f","Enter HETG 0010 efficiency file",'CALDB'),ParValue("AXAF_HETG_0001_FILE","f","Enter HETG 0001 efficiency file",'CALDB'),ParValue("AXAF_LETG_1000_FILE","f","Enter LETG 1000 efficiency file",'CALDB'),ParValue("AXAF_LETG_0100_FILE","f","Enter LETG 0100 efficiency file",'CALDB'),ParValue("AXAF_LETG_0010_FILE","f","Enter LETG 0010 efficiency file",'CALDB'),ParValue("AXAF_LETG_0001_FILE","f","Enter LETG 0001 efficiency file",'CALDB'),ParValue("AXAF_HETG_1100_LSF_FILE","f","Enter MEG LSF parameter file",'CALDB'),ParValue("AXAF_HETG_0011_LSF_FILE","f","Enter HEG LSF parameter file",'CALDB'),ParValue("AXAF_LETG_1111_LSF_FILE","f","Enter LEG LSF parameter file",'CALDB'),ParValue("AXAF_RMF_FILE","f","Enter CCD RMF p3resp file",'CALDB'),ParValue("AXAF_GAIN_FILE","f","Gain File",'CALDB')],
    'opt': [],
    }


parinfo['arestore'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("psffile","f","File with PSf information",None),ParValue("outfile","f","Output file name",None),ParValue("numiter","i","Number of iterations to perform",None)],
    'opt': [ParValue("psf_x_center","i","X coordinate of PSF center in logical coordinates",None),ParValue("psf_y_center","i","Y coordinate of PSF center in logical coordinates",None),ParValue("clobber","b","Remove existing output file if it exists?",False),ParRange("verbose","i","Amount of tool chatter",0,0,5)],
    }


parinfo['arfcorr'] = {
    'istool': True,
    'req': [ParValue("infile","f","input image file",None),ParValue("arf","f","input ARF",None),ParValue("outfile","f","output PSF image or PSF_FRAC table",None),ParValue("region","f","source region",None),ParValue("x","r","image centroid, sky x coordinate",None),ParValue("y","r","image centroid, sky y coordinate",None)],
    'opt': [ParValue("energy","r","energy in keV (0 = read from ARF)",None),ParRange("e_step","i","energy stepsize (read every 'e_step' row from ARF)",50,1,None),ParRange("radlim","r","radius at which PSF artificially drops to 0 (multiplies last radius)",2.0,1,None),ParRange("nsubpix","i","subpixelation (1d) of ecf model pixels to choose image pix value",5,1,None),ParRange("nfracpix","i","subpixelation (1d) of ecf pixels when calculating psffrac",1,1,None),ParValue("ecffile","f","ecf file",'${CALDB}/data/chandra/default/reef/hrmaD1996-12-20reefN0001.fits'),ParValue("tmpdir","s","Directory for temp. files",'${ASCDS_WORK_PATH}'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug level (0-5)",0,0,5)],
    }


parinfo['asp_offaxis_corr'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input ASPSOL file - updated in place",None),ParValue("instrume","s","Instrument",None)],
    'opt': [ParValue("geompar","s","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Debug Level(0-5)",0,0,5)],
    }


parinfo['asphist'] = {
    'istool': True,
    'req': [ParValue("infile","f","Aspect Solution List Files",None),ParValue("outfile","f","Aspect Histogram Output File",None),ParValue("evtfile","f","Event List Files",None),ParValue("dtffile","f","Live Time Correction List Files for HRC",None)],
    'opt': [ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("res_xy","r","Aspect Resolution x and y in arcsec",0.5),ParValue("res_roll","r","Aspect Resolution roll in arcsec",600.),ParValue("max_bin","r","Maximal number of bins",10000.),ParValue("clobber","b","Clobber output",False),ParRange("verbose","i","Verbose",0,0,5)],
    }


parinfo['axbary'] = {
    'istool': True,
    'req': [ParValue("infile","f","input event file",None),ParValue("orbitfile","f","input orbit ephemeris file",None),ParValue("outfile","f","output file",None)],
    'opt': [ParValue("ra","r","RA to be used for barycenter corrections",None),ParValue("dec","r","Dec to be used for barycenter corrections",None),ParValue("refframe","s","Reference frame to be used",'INDEF'),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['bkg_fixed_counts'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outroot","f","Output filename root",None),ParValue("pos","f","Input position or file with RA and Dec columns",None),ParRange("min_counts","i","Minimum number of counts in background region",10,0,None)],
    'opt': [ParValue("src_region","f","Input stack of source region files",None),ParValue("fovfile","f","Input field-of-view file",None),ParValue("max_radius","r","Maximum background radius, None=unrestricted",None),ParRange("inner_ecf","r","PSF ECF for inner annulus radius (pixels)",0.95,0.9,0.99),ParRange("energy","r","Energy to simulate the PSF (kev)",1.0,0.3,10),ParRange("verbose","i","Amount of tool chatter",1,0,5),ParValue("clobber","b","Overwrite output files if they already exist?",False)],
    }


parinfo['blanksky'] = {
    'istool': True,
    'req': [ParValue("evtfile","f","Source event file",None),ParValue("outfile","f","Output directory path + file name for output files",None)],
    'opt': [ParValue("asolfile","f","Source aspect solution file(s)",None),ParValue("stowedbg","b","Use ACIS stowed background files?",False),ParSet("weight_method","s","Method to calculate background scale factor",'particle',["particle","time","particle-rate"]),ParValue("bkgparams","s","Optional argument for background scaling, default is [pi=300:500] for HRC and [energy=9000:12000] for ACIS",'default'),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParRange("random","i","Random seed, 0=clock time",0,0,None),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['blanksky_image'] = {
    'istool': True,
    'req': [ParValue("bkgfile","f","blanksky background event file",None),ParValue("outroot","f","root of output files",None),ParValue("imgfile","f","reference image file",None)],
    'opt': [ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['blanksky_sample'] = {
    'istool': True,
    'req': [ParValue("infile","f","source event file (observation or PSF)",None),ParValue("bkgfile","f","blanksky background file",None),ParValue("bkgout","f","Output directory path + file name for output file",None)],
    'opt': [ParValue("psf_bkg_out","f","Output directory path + file name for merged PSF+bkg file",None),ParValue("regionfile","f","region file to replace infile events with background events",None),ParValue("fill_out","f","Output directory path + file name for substituting events with background events",None),ParValue("reproject","b","Reproject background events to match PSF coordinates",False),ParValue("asolfile","f","PSF aspect solution file(s)",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParRange("random","i","Random seed, 0=clock time",0,0,None),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['calquiz'] = {
    'istool': True,
    'req': [ParValue("infile","f","File to get meta data from",None),ParValue("telescope","s","telescope",None),ParValue("instrument","s","instrument",None),ParValue("product","s","data product",None)],
    'opt': [ParValue("calfile","s","caldb specifier",'CALDB'),ParValue("outfile","s","File(s) found",None),ParValue("echo","b","Print returned cal-files to screen?",False),ParValue("echo_qual","b","return quality value",False),ParValue("echo_fidel","b","return fidelity value?",False),ParRange("verbose","i","verbosity level (0 = no display)",0,0,5)],
    }


parinfo['celldetect'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file",None),ParValue("outfile","f","Output source list",None)],
    'opt': [ParValue("psffile","f","single psf file or list of psf files",None),ParValue("expstk","f","list of exposure map files",None),ParValue("regfile","f","ASCII regions file",'none'),ParValue("clobber","b","Overwrite exiting outputs?",False),ParValue("thresh","r","Source threshold",3),ParRange("snr_diminution","r","Diminution on SNR threshold - range (< 0 to 1) - Allows fine grained cell sliding",1.0,0,1),ParValue("findpeaks","b","Find local peaks?",True),ParValue("centroid","b","Compute source centroids?",True),ParValue("ellsigma","r","Size of output source ellipses (in sigmas)",3),ParValue("expratio","r","cutoff ratio for source cell exposure variation",0),ParValue("fixedcell","i","Fixed cell size to use (0 for variable cell)",0),ParValue("xoffset","i","Offset of x axis from data center",None),ParValue("yoffset","i","Offset of y axis from data center",None),ParValue("cellfile","f","Output cell size image stack name",None),ParValue("maxlogicalwindow","i","Max logical window",8192),ParValue("bkgfile","f","Background file name",None),ParValue("bkgvalue","r","Background count/pixel",0),ParValue("bkgerrvalue","r","Background error",0),ParValue("convolve","b","Use convolution?",False),ParValue("snrfile","f","SNR output file name (for convolution only)",None),ParRange("verbose","i","Log verbosity level",0,0,5),ParValue("log","b","Make a celldetect.log file?",False)],
    }


parinfo['centroid_map'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input counts image",None),ParValue("outfile","f","Output map file",None)],
    'opt': [ParRange("numiter","i","Number of centroid iterations",1,1,None),ParValue("sitefile","f","Input initial site locations",None),ParSet("scale","s","Scaling applied to pixel values when computing centroid",'linear',["linear","sqrt","squared","asinh"]),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove outfile if it already exists?",True)],
    }


parinfo['chandra_repro'] = {
    'istool': True,
    'req': [ParValue("indir","f","Input directory",'./'),ParValue("outdir","f","Output directory (default = $indir/repro)",None)],
    'opt': [ParValue("root","s","Root for output filenames",None),ParValue("badpixel","b","Create a new bad pixel file?",True),ParValue("process_events","b","Create a new level=2 event file?",True),ParValue("destreak","b","Destreak the ACIS-8 chip?",True),ParValue("set_ardlib","b","Set ardlib.par with the bad pixel file?",True),ParValue("check_vf_pha","b","Clean ACIS background in VFAINT data?",False),ParSet("pix_adj","s","Pixel randomization: default|edser|none|randomize",'default',["default","edser","none","randomize","centroid"]),ParValue("tg_zo_position","s","Method to determine gratings 0th order location: evt2|detect|R.A. & Dec.",'evt2'),ParValue("asol_update","b","If necessary, apply boresight correction to aspect solution file?",True),ParValue("pi_filter","b","Apply PI background filter to HRC-S+LETG data?",True),ParValue("cleanup","b","Cleanup intermediate files on exit",True),ParValue("clobber","b","Clobber existing file",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['color_color'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input ARF file",None),ParValue("outfile","f","Output file name",None),ParValue("model","s","Sherpa model expression",'xsphabs.abs1*xspowerlaw.pwrlaw'),ParValue("param1","s","Model parameter for 1st axis",'pwrlaw.PhoIndex'),ParValue("grid1","s","Model parameter grid for 1st axis",'1,2,3,4'),ParValue("param2","s","Model parameter for 2nd axis",'abs1.nH'),ParValue("grid2","s","Model grid for 2nd axis",'0.01,0.1,0.2,0.5,1,10'),ParValue("soft","s","Soft energy band LO:HI or csc (0.5:1.2)",'csc'),ParValue("medium","s","Medium energy band LO:HI or csc (1.2:2.0)",'csc'),ParValue("hard","s","Hard energy band LO:HI or csc (2.0:7.0)",'csc')],
    'opt': [ParValue("rmffile","f","Input RMF file (use diagnonal if blank or none)",None),ParRange("plot_oversample","i","Over sample grid when plotting",20,0,None),ParValue("outplot","f","Output file name for plot",'clr.png'),ParValue("showplot","b","Display plot? (close to continue)",True),ParRange("random_seed","i","Random seed (-1 = randomly select)",-1,-1,None),ParValue("clobber","b","Remove outfile and outplot files if they already exist?",True),ParRange("verbose","i","Tool chatter level",1,0,5)],
    }


parinfo['colors'] = {
    'istool': False,
    'req': [],
    'opt': [ParValue("aliceblue","s","Color triple",'0.941176 0.972549 1'),ParValue("antiquewhite","s","Color triple",'0.980392 0.921569 0.843137'),ParValue("antiquewhite1","s","Color triple",'1 0.937255 0.858824'),ParValue("antiquewhite2","s","Color triple",'0.933333 0.874510 0.800000'),ParValue("antiquewhite3","s","Color triple",'0.803922 0.752941 0.690196'),ParValue("antiquewhite4","s","Color triple",'0.545098 0.513725 0.470588'),ParValue("aquamarine","s","Color triple",'0.498039 1 0.831373'),ParValue("aquamarine1","s","Color triple",'0.498039 1 0.831373'),ParValue("aquamarine2","s","Color triple",'0.462745 0.933333 0.776471'),ParValue("aquamarine3","s","Color triple",'0.400000 0.803922 0.666667'),ParValue("aquamarine4","s","Color triple",'0.270588 0.545098 0.454902'),ParValue("azure","s","Color triple",'0.941176 1 1'),ParValue("azure1","s","Color triple",'0.941176 1 1'),ParValue("azure2","s","Color triple",'0.878431 0.933333 0.933333'),ParValue("azure3","s","Color triple",'0.756863 0.803922 0.803922'),ParValue("azure4","s","Color triple",'0.513725 0.545098 0.545098'),ParValue("beige","s","Color triple",'0.960784 0.960784 0.862745'),ParValue("bisque","s","Color triple",'1 0.894118 0.768627'),ParValue("bisque1","s","Color triple",'1 0.894118 0.768627'),ParValue("bisque2","s","Color triple",'0.933333 0.835294 0.717647'),ParValue("bisque3","s","Color triple",'0.803922 0.717647 0.619608'),ParValue("bisque4","s","Color triple",'0.545098 0.490196 0.419608'),ParValue("black","s","Color triple",'0 0 0'),ParValue("blanchedalmond","s","Color triple",'1 0.921569 0.803922'),ParValue("blue","s","Color triple",'0 0 1'),ParValue("blue1","s","Color triple",'0 0 1'),ParValue("blue2","s","Color triple",'0 0 0.933333'),ParValue("blue3","s","Color triple",'0 0 0.803922'),ParValue("blue4","s","Color triple",'0 0 0.545098'),ParValue("blueviolet","s","Color triple",'0.541176 0.168627 0.886275'),ParValue("brightaquamarine","s","Color triple",'0.207843 0.870588 0.768627'),ParValue("brightcyan","s","Color triple",'0 1 1'),ParValue("brightyellow","s","Color triple",'1 1 0'),ParValue("brown","s","Color triple",'0.647059 0.164706 0.164706'),ParValue("brown1","s","Color triple",'1 0.250980 0.250980'),ParValue("brown2","s","Color triple",'0.933333 0.231373 0.231373'),ParValue("brown3","s","Color triple",'0.803922 0.200000 0.200000'),ParValue("brown4","s","Color triple",'0.545098 0.137255 0.137255'),ParValue("burlywood","s","Color triple",'0.870588 0.721569 0.529412'),ParValue("burlywood1","s","Color triple",'1 0.827451 0.607843'),ParValue("burlywood2","s","Color triple",'0.933333 0.772549 0.568627'),ParValue("burlywood3","s","Color triple",'0.803922 0.666667 0.490196'),ParValue("burlywood4","s","Color triple",'0.545098 0.450980 0.333333'),ParValue("cadetblue","s","Color triple",'0.372549 0.619608 0.627451'),ParValue("cadetblue1","s","Color triple",'0.596078 0.960784 1'),ParValue("cadetblue2","s","Color triple",'0.556863 0.898039 0.933333'),ParValue("cadetblue3","s","Color triple",'0.478431 0.772549 0.803922'),ParValue("cadetblue4","s","Color triple",'0.325490 0.525490 0.545098'),ParValue("chartreuse","s","Color triple",'0.498039 1 0'),ParValue("chartreuse1","s","Color triple",'0.498039 1 0'),ParValue("chartreuse2","s","Color triple",'0.462745 0.933333 0'),ParValue("chartreuse3","s","Color triple",'0.400000 0.803922 0'),ParValue("chartreuse4","s","Color triple",'0.270588 0.545098 0'),ParValue("chocolate","s","Color triple",'0.823529 0.411765 0.117647'),ParValue("chocolate1","s","Color triple",'1 0.498039 0.141176'),ParValue("chocolate2","s","Color triple",'0.933333 0.462745 0.129412'),ParValue("chocolate3","s","Color triple",'0.803922 0.400000 0.113725'),ParValue("chocolate4","s","Color triple",'0.545098 0.270588 0.074510'),ParValue("coral","s","Color triple",'1 0.498039 0.313725'),ParValue("coral1","s","Color triple",'1 0.447059 0.337255'),ParValue("coral2","s","Color triple",'0.933333 0.415686 0.313725'),ParValue("coral3","s","Color triple",'0.803922 0.356863 0.270588'),ParValue("coral4","s","Color triple",'0.545098 0.243137 0.184314'),ParValue("cornflowerblue","s","Color triple",'0.392157 0.584314 0.929412'),ParValue("cornsilk","s","Color triple",'1 0.972549 0.862745'),ParValue("cornsilk1","s","Color triple",'1 0.972549 0.862745'),ParValue("cornsilk2","s","Color triple",'0.933333 0.909804 0.803922'),ParValue("cornsilk3","s","Color triple",'0.803922 0.784314 0.694118'),ParValue("cornsilk4","s","Color triple",'0.545098 0.533333 0.470588'),ParValue("cyan","s","Color triple",'0 1 1'),ParValue("cyan1","s","Color triple",'0 1 1'),ParValue("cyan2","s","Color triple",'0 0.933333 0.933333'),ParValue("cyan3","s","Color triple",'0 0.803922 0.803922'),ParValue("cyan4","s","Color triple",'0 0.545098 0.545098'),ParValue("darkgoldenrod","s","Color triple",'0.721569 0.525490 0.043137'),ParValue("darkgoldenrod1","s","Color triple",'1 0.725490 0.058824'),ParValue("darkgoldenrod2","s","Color triple",'0.933333 0.678431 0.054902'),ParValue("darkgoldenrod3","s","Color triple",'0.803922 0.584314 0.047059'),ParValue("darkgoldenrod4","s","Color triple",'0.545098 0.396078 0.031373'),ParValue("darkgreen","s","Color triple",'0 0.392157 0'),ParValue("darkkhaki","s","Color triple",'0.741176 0.717647 0.419608'),ParValue("darkolivegreen","s","Color triple",'0.333333 0.419608 0.184314'),ParValue("darkolivegreen1","s","Color triple",'0.792157 1 0.439216'),ParValue("darkolivegreen2","s","Color triple",'0.737255 0.933333 0.407843'),ParValue("darkolivegreen3","s","Color triple",'0.635294 0.803922 0.352941'),ParValue("darkolivegreen4","s","Color triple",'0.431373 0.545098 0.239216'),ParValue("darkorange","s","Color triple",'1 0.549020 0'),ParValue("darkorange1","s","Color triple",'1 0.498039 0'),ParValue("darkorange2","s","Color triple",'0.933333 0.462745 0'),ParValue("darkorange3","s","Color triple",'0.803922 0.400000 0'),ParValue("darkorange4","s","Color triple",'0.545098 0.270588 0'),ParValue("darkorchid","s","Color triple",'0.600000 0.196078 0.800000'),ParValue("darkorchid1","s","Color triple",'0.749020 0.243137 1'),ParValue("darkorchid2","s","Color triple",'0.698039 0.227451 0.933333'),ParValue("darkorchid3","s","Color triple",'0.603922 0.196078 0.803922'),ParValue("darkorchid4","s","Color triple",'0.407843 0.133333 0.545098'),ParValue("darksalmon","s","Color triple",'0.913725 0.588235 0.478431'),ParValue("darkseagreen","s","Color triple",'0.560784 0.737255 0.560784'),ParValue("darkseagreen1","s","Color triple",'0.756863 1 0.756863'),ParValue("darkseagreen2","s","Color triple",'0.705882 0.933333 0.705882'),ParValue("darkseagreen3","s","Color triple",'0.607843 0.803922 0.607843'),ParValue("darkseagreen4","s","Color triple",'0.411765 0.545098 0.411765'),ParValue("darkslateblue","s","Color triple",'0.282353 0.239216 0.545098'),ParValue("darkslategray","s","Color triple",'0.184314 0.309804 0.309804'),ParValue("darkslategray1","s","Color triple",'0.592157 1 1'),ParValue("darkslategray2","s","Color triple",'0.552941 0.933333 0.933333'),ParValue("darkslategray3","s","Color triple",'0.474510 0.803922 0.803922'),ParValue("darkslategray4","s","Color triple",'0.321569 0.545098 0.545098'),ParValue("darkslategrey","s","Color triple",'0.184314 0.309804 0.309804'),ParValue("darkturquoise","s","Color triple",'0 0.807843 0.819608'),ParValue("darkviolet","s","Color triple",'0.580392 0 0.827451'),ParValue("deeppink","s","Color triple",'1 0.078431 0.576471'),ParValue("deeppink1","s","Color triple",'1 0.078431 0.576471'),ParValue("deeppink2","s","Color triple",'0.933333 0.070588 0.537255'),ParValue("deeppink3","s","Color triple",'0.803922 0.062745 0.462745'),ParValue("deeppink4","s","Color triple",'0.545098 0.039216 0.313725'),ParValue("deepskyblue","s","Color triple",'0 0.749020 1'),ParValue("deepskyblue1","s","Color triple",'0 0.749020 1'),ParValue("deepskyblue2","s","Color triple",'0 0.698039 0.933333'),ParValue("deepskyblue3","s","Color triple",'0 0.603922 0.803922'),ParValue("deepskyblue4","s","Color triple",'0 0.407843 0.545098'),ParValue("dimgray","s","Color triple",'0.411765 0.411765 0.411765'),ParValue("dimgrey","s","Color triple",'0.411765 0.411765 0.411765'),ParValue("dodgerblue","s","Color triple",'0.117647 0.564706 1'),ParValue("dodgerblue1","s","Color triple",'0.117647 0.564706 1'),ParValue("dodgerblue2","s","Color triple",'0.109804 0.525490 0.933333'),ParValue("dodgerblue3","s","Color triple",'0.094118 0.454902 0.803922'),ParValue("dodgerblue4","s","Color triple",'0.062745 0.305882 0.545098'),ParValue("firebrick","s","Color triple",'0.698039 0.133333 0.133333'),ParValue("firebrick1","s","Color triple",'1 0.188235 0.188235'),ParValue("firebrick2","s","Color triple",'0.933333 0.172549 0.172549'),ParValue("firebrick3","s","Color triple",'0.803922 0.149020 0.149020'),ParValue("firebrick4","s","Color triple",'0.545098 0.101961 0.101961'),ParValue("floralwhite","s","Color triple",'1 0.980392 0.941176'),ParValue("forestgreen","s","Color triple",'0.133333 0.545098 0.133333'),ParValue("gainsboro","s","Color triple",'0.862745 0.862745 0.862745'),ParValue("ghostwhite","s","Color triple",'0.972549 0.972549 1'),ParValue("gold","s","Color triple",'1 0.843137 0'),ParValue("gold1","s","Color triple",'1 0.843137 0'),ParValue("gold2","s","Color triple",'0.933333 0.788235 0'),ParValue("gold3","s","Color triple",'0.803922 0.678431 0'),ParValue("gold4","s","Color triple",'0.545098 0.458824 0'),ParValue("goldenrod","s","Color triple",'0.854902 0.647059 0.125490'),ParValue("goldenrod1","s","Color triple",'1 0.756863 0.145098'),ParValue("goldenrod2","s","Color triple",'0.933333 0.705882 0.133333'),ParValue("goldenrod3","s","Color triple",'0.803922 0.607843 0.113725'),ParValue("goldenrod4","s","Color triple",'0.545098 0.411765 0.078431'),ParValue("gray","s","Color triple",'0.745098 0.745098 0.745098'),ParValue("gray0","s","Color triple",'0 0 0'),ParValue("gray1","s","Color triple",'0.011765 0.011765 0.011765'),ParValue("gray10","s","Color triple",'0.101961 0.101961 0.101961'),ParValue("gray100","s","Color triple",'1 1 1'),ParValue("gray11","s","Color triple",'0.109804 0.109804 0.109804'),ParValue("gray12","s","Color triple",'0.121569 0.121569 0.121569'),ParValue("gray13","s","Color triple",'0.129412 0.129412 0.129412'),ParValue("gray14","s","Color triple",'0.141176 0.141176 0.141176'),ParValue("gray15","s","Color triple",'0.149020 0.149020 0.149020'),ParValue("gray16","s","Color triple",'0.160784 0.160784 0.160784'),ParValue("gray17","s","Color triple",'0.168627 0.168627 0.168627'),ParValue("gray18","s","Color triple",'0.180392 0.180392 0.180392'),ParValue("gray19","s","Color triple",'0.188235 0.188235 0.188235'),ParValue("gray2","s","Color triple",'0.019608 0.019608 0.019608'),ParValue("gray20","s","Color triple",'0.200000 0.200000 0.200000'),ParValue("gray21","s","Color triple",'0.211765 0.211765 0.211765'),ParValue("gray22","s","Color triple",'0.219608 0.219608 0.219608'),ParValue("gray23","s","Color triple",'0.231373 0.231373 0.231373'),ParValue("gray24","s","Color triple",'0.239216 0.239216 0.239216'),ParValue("gray25","s","Color triple",'0.250980 0.250980 0.250980'),ParValue("gray26","s","Color triple",'0.258824 0.258824 0.258824'),ParValue("gray27","s","Color triple",'0.270588 0.270588 0.270588'),ParValue("gray28","s","Color triple",'0.278431 0.278431 0.278431'),ParValue("gray29","s","Color triple",'0.290196 0.290196 0.290196'),ParValue("gray3","s","Color triple",'0.031373 0.031373 0.031373'),ParValue("gray30","s","Color triple",'0.301961 0.301961 0.301961'),ParValue("gray31","s","Color triple",'0.309804 0.309804 0.309804'),ParValue("gray32","s","Color triple",'0.321569 0.321569 0.321569'),ParValue("gray33","s","Color triple",'0.329412 0.329412 0.329412'),ParValue("gray34","s","Color triple",'0.341176 0.341176 0.341176'),ParValue("gray35","s","Color triple",'0.349020 0.349020 0.349020'),ParValue("gray36","s","Color triple",'0.360784 0.360784 0.360784'),ParValue("gray37","s","Color triple",'0.368627 0.368627 0.368627'),ParValue("gray38","s","Color triple",'0.380392 0.380392 0.380392'),ParValue("gray39","s","Color triple",'0.388235 0.388235 0.388235'),ParValue("gray4","s","Color triple",'0.039216 0.039216 0.039216'),ParValue("gray40","s","Color triple",'0.400000 0.400000 0.400000'),ParValue("gray41","s","Color triple",'0.411765 0.411765 0.411765'),ParValue("gray42","s","Color triple",'0.419608 0.419608 0.419608'),ParValue("gray43","s","Color triple",'0.431373 0.431373 0.431373'),ParValue("gray44","s","Color triple",'0.439216 0.439216 0.439216'),ParValue("gray45","s","Color triple",'0.450980 0.450980 0.450980'),ParValue("gray46","s","Color triple",'0.458824 0.458824 0.458824'),ParValue("gray47","s","Color triple",'0.470588 0.470588 0.470588'),ParValue("gray48","s","Color triple",'0.478431 0.478431 0.478431'),ParValue("gray49","s","Color triple",'0.490196 0.490196 0.490196'),ParValue("gray5","s","Color triple",'0.050980 0.050980 0.050980'),ParValue("gray50","s","Color triple",'0.498039 0.498039 0.498039'),ParValue("gray51","s","Color triple",'0.509804 0.509804 0.509804'),ParValue("gray52","s","Color triple",'0.521569 0.521569 0.521569'),ParValue("gray53","s","Color triple",'0.529412 0.529412 0.529412'),ParValue("gray54","s","Color triple",'0.541176 0.541176 0.541176'),ParValue("gray55","s","Color triple",'0.549020 0.549020 0.549020'),ParValue("gray56","s","Color triple",'0.560784 0.560784 0.560784'),ParValue("gray57","s","Color triple",'0.568627 0.568627 0.568627'),ParValue("gray58","s","Color triple",'0.580392 0.580392 0.580392'),ParValue("gray59","s","Color triple",'0.588235 0.588235 0.588235'),ParValue("gray6","s","Color triple",'0.058824 0.058824 0.058824'),ParValue("gray60","s","Color triple",'0.600000 0.600000 0.600000'),ParValue("gray61","s","Color triple",'0.611765 0.611765 0.611765'),ParValue("gray62","s","Color triple",'0.619608 0.619608 0.619608'),ParValue("gray63","s","Color triple",'0.631373 0.631373 0.631373'),ParValue("gray64","s","Color triple",'0.639216 0.639216 0.639216'),ParValue("gray65","s","Color triple",'0.650980 0.650980 0.650980'),ParValue("gray66","s","Color triple",'0.658824 0.658824 0.658824'),ParValue("gray67","s","Color triple",'0.670588 0.670588 0.670588'),ParValue("gray68","s","Color triple",'0.678431 0.678431 0.678431'),ParValue("gray69","s","Color triple",'0.690196 0.690196 0.690196'),ParValue("gray7","s","Color triple",'0.070588 0.070588 0.070588'),ParValue("gray70","s","Color triple",'0.701961 0.701961 0.701961'),ParValue("gray71","s","Color triple",'0.709804 0.709804 0.709804'),ParValue("gray72","s","Color triple",'0.721569 0.721569 0.721569'),ParValue("gray73","s","Color triple",'0.729412 0.729412 0.729412'),ParValue("gray74","s","Color triple",'0.741176 0.741176 0.741176'),ParValue("gray75","s","Color triple",'0.749020 0.749020 0.749020'),ParValue("gray76","s","Color triple",'0.760784 0.760784 0.760784'),ParValue("gray77","s","Color triple",'0.768627 0.768627 0.768627'),ParValue("gray78","s","Color triple",'0.780392 0.780392 0.780392'),ParValue("gray79","s","Color triple",'0.788235 0.788235 0.788235'),ParValue("gray8","s","Color triple",'0.078431 0.078431 0.078431'),ParValue("gray80","s","Color triple",'0.800000 0.800000 0.800000'),ParValue("gray81","s","Color triple",'0.811765 0.811765 0.811765'),ParValue("gray82","s","Color triple",'0.819608 0.819608 0.819608'),ParValue("gray83","s","Color triple",'0.831373 0.831373 0.831373'),ParValue("gray84","s","Color triple",'0.839216 0.839216 0.839216'),ParValue("gray85","s","Color triple",'0.850980 0.850980 0.850980'),ParValue("gray86","s","Color triple",'0.858824 0.858824 0.858824'),ParValue("gray87","s","Color triple",'0.870588 0.870588 0.870588'),ParValue("gray88","s","Color triple",'0.878431 0.878431 0.878431'),ParValue("gray89","s","Color triple",'0.890196 0.890196 0.890196'),ParValue("gray9","s","Color triple",'0.090196 0.090196 0.090196'),ParValue("gray90","s","Color triple",'0.898039 0.898039 0.898039'),ParValue("gray91","s","Color triple",'0.909804 0.909804 0.909804'),ParValue("gray92","s","Color triple",'0.921569 0.921569 0.921569'),ParValue("gray93","s","Color triple",'0.929412 0.929412 0.929412'),ParValue("gray94","s","Color triple",'0.941176 0.941176 0.941176'),ParValue("gray95","s","Color triple",'0.949020 0.949020 0.949020'),ParValue("gray96","s","Color triple",'0.960784 0.960784 0.960784'),ParValue("gray97","s","Color triple",'0.968627 0.968627 0.968627'),ParValue("gray98","s","Color triple",'0.980392 0.980392 0.980392'),ParValue("gray99","s","Color triple",'0.988235 0.988235 0.988235'),ParValue("green","s","Color triple",'0 1 0'),ParValue("green1","s","Color triple",'0 1 0'),ParValue("green2","s","Color triple",'0 0.933333 0'),ParValue("green3","s","Color triple",'0 0.803922 0'),ParValue("green4","s","Color triple",'0 0.545098 0'),ParValue("greenyellow","s","Color triple",'0.678431 1 0.184314'),ParValue("grey","s","Color triple",'0.745098 0.745098 0.745098'),ParValue("grey0","s","Color triple",'0 0 0'),ParValue("grey1","s","Color triple",'0.011765 0.011765 0.011765'),ParValue("grey10","s","Color triple",'0.101961 0.101961 0.101961'),ParValue("grey100","s","Color triple",'1 1 1'),ParValue("grey11","s","Color triple",'0.109804 0.109804 0.109804'),ParValue("grey12","s","Color triple",'0.121569 0.121569 0.121569'),ParValue("grey13","s","Color triple",'0.129412 0.129412 0.129412'),ParValue("grey14","s","Color triple",'0.141176 0.141176 0.141176'),ParValue("grey15","s","Color triple",'0.149020 0.149020 0.149020'),ParValue("grey16","s","Color triple",'0.160784 0.160784 0.160784'),ParValue("grey17","s","Color triple",'0.168627 0.168627 0.168627'),ParValue("grey18","s","Color triple",'0.180392 0.180392 0.180392'),ParValue("grey19","s","Color triple",'0.188235 0.188235 0.188235'),ParValue("grey2","s","Color triple",'0.019608 0.019608 0.019608'),ParValue("grey20","s","Color triple",'0.200000 0.200000 0.200000'),ParValue("grey21","s","Color triple",'0.211765 0.211765 0.211765'),ParValue("grey22","s","Color triple",'0.219608 0.219608 0.219608'),ParValue("grey23","s","Color triple",'0.231373 0.231373 0.231373'),ParValue("grey24","s","Color triple",'0.239216 0.239216 0.239216'),ParValue("grey25","s","Color triple",'0.250980 0.250980 0.250980'),ParValue("grey26","s","Color triple",'0.258824 0.258824 0.258824'),ParValue("grey27","s","Color triple",'0.270588 0.270588 0.270588'),ParValue("grey28","s","Color triple",'0.278431 0.278431 0.278431'),ParValue("grey29","s","Color triple",'0.290196 0.290196 0.290196'),ParValue("grey3","s","Color triple",'0.031373 0.031373 0.031373'),ParValue("grey30","s","Color triple",'0.301961 0.301961 0.301961'),ParValue("grey31","s","Color triple",'0.309804 0.309804 0.309804'),ParValue("grey32","s","Color triple",'0.321569 0.321569 0.321569'),ParValue("grey33","s","Color triple",'0.329412 0.329412 0.329412'),ParValue("grey34","s","Color triple",'0.341176 0.341176 0.341176'),ParValue("grey35","s","Color triple",'0.349020 0.349020 0.349020'),ParValue("grey36","s","Color triple",'0.360784 0.360784 0.360784'),ParValue("grey37","s","Color triple",'0.368627 0.368627 0.368627'),ParValue("grey38","s","Color triple",'0.380392 0.380392 0.380392'),ParValue("grey39","s","Color triple",'0.388235 0.388235 0.388235'),ParValue("grey4","s","Color triple",'0.039216 0.039216 0.039216'),ParValue("grey40","s","Color triple",'0.400000 0.400000 0.400000'),ParValue("grey41","s","Color triple",'0.411765 0.411765 0.411765'),ParValue("grey42","s","Color triple",'0.419608 0.419608 0.419608'),ParValue("grey43","s","Color triple",'0.431373 0.431373 0.431373'),ParValue("grey44","s","Color triple",'0.439216 0.439216 0.439216'),ParValue("grey45","s","Color triple",'0.450980 0.450980 0.450980'),ParValue("grey46","s","Color triple",'0.458824 0.458824 0.458824'),ParValue("grey47","s","Color triple",'0.470588 0.470588 0.470588'),ParValue("grey48","s","Color triple",'0.478431 0.478431 0.478431'),ParValue("grey49","s","Color triple",'0.490196 0.490196 0.490196'),ParValue("grey5","s","Color triple",'0.050980 0.050980 0.050980'),ParValue("grey50","s","Color triple",'0.498039 0.498039 0.498039'),ParValue("grey51","s","Color triple",'0.509804 0.509804 0.509804'),ParValue("grey52","s","Color triple",'0.521569 0.521569 0.521569'),ParValue("grey53","s","Color triple",'0.529412 0.529412 0.529412'),ParValue("grey54","s","Color triple",'0.541176 0.541176 0.541176'),ParValue("grey55","s","Color triple",'0.549020 0.549020 0.549020'),ParValue("grey56","s","Color triple",'0.560784 0.560784 0.560784'),ParValue("grey57","s","Color triple",'0.568627 0.568627 0.568627'),ParValue("grey58","s","Color triple",'0.580392 0.580392 0.580392'),ParValue("grey59","s","Color triple",'0.588235 0.588235 0.588235'),ParValue("grey6","s","Color triple",'0.058824 0.058824 0.058824'),ParValue("grey60","s","Color triple",'0.600000 0.600000 0.600000'),ParValue("grey61","s","Color triple",'0.611765 0.611765 0.611765'),ParValue("grey62","s","Color triple",'0.619608 0.619608 0.619608'),ParValue("grey63","s","Color triple",'0.631373 0.631373 0.631373'),ParValue("grey64","s","Color triple",'0.639216 0.639216 0.639216'),ParValue("grey65","s","Color triple",'0.650980 0.650980 0.650980'),ParValue("grey66","s","Color triple",'0.658824 0.658824 0.658824'),ParValue("grey67","s","Color triple",'0.670588 0.670588 0.670588'),ParValue("grey68","s","Color triple",'0.678431 0.678431 0.678431'),ParValue("grey69","s","Color triple",'0.690196 0.690196 0.690196'),ParValue("grey7","s","Color triple",'0.070588 0.070588 0.070588'),ParValue("grey70","s","Color triple",'0.701961 0.701961 0.701961'),ParValue("grey71","s","Color triple",'0.709804 0.709804 0.709804'),ParValue("grey72","s","Color triple",'0.721569 0.721569 0.721569'),ParValue("grey73","s","Color triple",'0.729412 0.729412 0.729412'),ParValue("grey74","s","Color triple",'0.741176 0.741176 0.741176'),ParValue("grey75","s","Color triple",'0.749020 0.749020 0.749020'),ParValue("grey76","s","Color triple",'0.760784 0.760784 0.760784'),ParValue("grey77","s","Color triple",'0.768627 0.768627 0.768627'),ParValue("grey78","s","Color triple",'0.780392 0.780392 0.780392'),ParValue("grey79","s","Color triple",'0.788235 0.788235 0.788235'),ParValue("grey8","s","Color triple",'0.078431 0.078431 0.078431'),ParValue("grey80","s","Color triple",'0.800000 0.800000 0.800000'),ParValue("grey81","s","Color triple",'0.811765 0.811765 0.811765'),ParValue("grey82","s","Color triple",'0.819608 0.819608 0.819608'),ParValue("grey83","s","Color triple",'0.831373 0.831373 0.831373'),ParValue("grey84","s","Color triple",'0.839216 0.839216 0.839216'),ParValue("grey85","s","Color triple",'0.850980 0.850980 0.850980'),ParValue("grey86","s","Color triple",'0.858824 0.858824 0.858824'),ParValue("grey87","s","Color triple",'0.870588 0.870588 0.870588'),ParValue("grey88","s","Color triple",'0.878431 0.878431 0.878431'),ParValue("grey89","s","Color triple",'0.890196 0.890196 0.890196'),ParValue("grey9","s","Color triple",'0.090196 0.090196 0.090196'),ParValue("grey90","s","Color triple",'0.898039 0.898039 0.898039'),ParValue("grey91","s","Color triple",'0.909804 0.909804 0.909804'),ParValue("grey92","s","Color triple",'0.921569 0.921569 0.921569'),ParValue("grey93","s","Color triple",'0.929412 0.929412 0.929412'),ParValue("grey94","s","Color triple",'0.941176 0.941176 0.941176'),ParValue("grey95","s","Color triple",'0.949020 0.949020 0.949020'),ParValue("grey96","s","Color triple",'0.960784 0.960784 0.960784'),ParValue("grey97","s","Color triple",'0.968627 0.968627 0.968627'),ParValue("grey98","s","Color triple",'0.980392 0.980392 0.980392'),ParValue("grey99","s","Color triple",'0.988235 0.988235 0.988235'),ParValue("honeydew","s","Color triple",'0.941176 1 0.941176'),ParValue("honeydew1","s","Color triple",'0.941176 1 0.941176'),ParValue("honeydew2","s","Color triple",'0.878431 0.933333 0.878431'),ParValue("honeydew3","s","Color triple",'0.756863 0.803922 0.756863'),ParValue("honeydew4","s","Color triple",'0.513725 0.545098 0.513725'),ParValue("hotpink","s","Color triple",'1 0.411765 0.705882'),ParValue("hotpink1","s","Color triple",'1 0.431373 0.705882'),ParValue("hotpink2","s","Color triple",'0.933333 0.415686 0.654902'),ParValue("hotpink3","s","Color triple",'0.803922 0.376471 0.564706'),ParValue("hotpink4","s","Color triple",'0.545098 0.227451 0.384314'),ParValue("indianred","s","Color triple",'0.803922 0.360784 0.360784'),ParValue("indianred1","s","Color triple",'1 0.415686 0.415686'),ParValue("indianred2","s","Color triple",'0.933333 0.388235 0.388235'),ParValue("indianred3","s","Color triple",'0.803922 0.333333 0.333333'),ParValue("indianred4","s","Color triple",'0.545098 0.227451 0.227451'),ParValue("ivory","s","Color triple",'1 1 0.941176'),ParValue("ivory1","s","Color triple",'1 1 0.941176'),ParValue("ivory2","s","Color triple",'0.933333 0.933333 0.878431'),ParValue("ivory3","s","Color triple",'0.803922 0.803922 0.756863'),ParValue("ivory4","s","Color triple",'0.545098 0.545098 0.513725'),ParValue("khaki","s","Color triple",'0.941176 0.901961 0.549020'),ParValue("khaki1","s","Color triple",'1 0.964706 0.560784'),ParValue("khaki2","s","Color triple",'0.933333 0.901961 0.521569'),ParValue("khaki3","s","Color triple",'0.803922 0.776471 0.450980'),ParValue("khaki4","s","Color triple",'0.545098 0.525490 0.305882'),ParValue("lavender","s","Color triple",'0.901961 0.901961 0.980392'),ParValue("lavenderblush","s","Color triple",'1 0.941176 0.960784'),ParValue("lavenderblush1","s","Color triple",'1 0.941176 0.960784'),ParValue("lavenderblush2","s","Color triple",'0.933333 0.878431 0.898039'),ParValue("lavenderblush3","s","Color triple",'0.803922 0.756863 0.772549'),ParValue("lavenderblush4","s","Color triple",'0.545098 0.513725 0.525490'),ParValue("lawngreen","s","Color triple",'0.486275 0.988235 0'),ParValue("lemonchiffon","s","Color triple",'1 0.980392 0.803922'),ParValue("lemonchiffon1","s","Color triple",'1 0.980392 0.803922'),ParValue("lemonchiffon2","s","Color triple",'0.933333 0.913725 0.749020'),ParValue("lemonchiffon3","s","Color triple",'0.803922 0.788235 0.647059'),ParValue("lemonchiffon4","s","Color triple",'0.545098 0.537255 0.439216'),ParValue("lightblue","s","Color triple",'0.678431 0.847059 0.901961'),ParValue("lightblue1","s","Color triple",'0.749020 0.937255 1'),ParValue("lightblue2","s","Color triple",'0.698039 0.874510 0.933333'),ParValue("lightblue3","s","Color triple",'0.603922 0.752941 0.803922'),ParValue("lightblue4","s","Color triple",'0.407843 0.513725 0.545098'),ParValue("lightcoral","s","Color triple",'0.941176 0.501961 0.501961'),ParValue("lightcyan","s","Color triple",'0.878431 1 1'),ParValue("lightcyan1","s","Color triple",'0.878431 1 1'),ParValue("lightcyan2","s","Color triple",'0.819608 0.933333 0.933333'),ParValue("lightcyan3","s","Color triple",'0.705882 0.803922 0.803922'),ParValue("lightcyan4","s","Color triple",'0.478431 0.545098 0.545098'),ParValue("lightgoldenrod","s","Color triple",'0.933333 0.866667 0.509804'),ParValue("lightgoldenrod1","s","Color triple",'1 0.925490 0.545098'),ParValue("lightgoldenrod2","s","Color triple",'0.933333 0.862745 0.509804'),ParValue("lightgoldenrod3","s","Color triple",'0.803922 0.745098 0.439216'),ParValue("lightgoldenrod4","s","Color triple",'0.545098 0.505882 0.298039'),ParValue("lightgoldenrodyellow","s","Color triple",'0.980392 0.980392 0.823529'),ParValue("lightgray","s","Color triple",'0.827451 0.827451 0.827451'),ParValue("lightgrey","s","Color triple",'0.827451 0.827451 0.827451'),ParValue("lightpink","s","Color triple",'1 0.713725 0.756863'),ParValue("lightpink1","s","Color triple",'1 0.682353 0.725490'),ParValue("lightpink2","s","Color triple",'0.933333 0.635294 0.678431'),ParValue("lightpink3","s","Color triple",'0.803922 0.549020 0.584314'),ParValue("lightpink4","s","Color triple",'0.545098 0.372549 0.396078'),ParValue("lightsalmon","s","Color triple",'1 0.627451 0.478431'),ParValue("lightsalmon1","s","Color triple",'1 0.627451 0.478431'),ParValue("lightsalmon2","s","Color triple",'0.933333 0.584314 0.447059'),ParValue("lightsalmon3","s","Color triple",'0.803922 0.505882 0.384314'),ParValue("lightsalmon4","s","Color triple",'0.545098 0.341176 0.258824'),ParValue("lightseagreen","s","Color triple",'0.125490 0.698039 0.666667'),ParValue("lightskyblue","s","Color triple",'0.529412 0.807843 0.980392'),ParValue("lightskyblue1","s","Color triple",'0.690196 0.886275 1'),ParValue("lightskyblue2","s","Color triple",'0.643137 0.827451 0.933333'),ParValue("lightskyblue3","s","Color triple",'0.552941 0.713725 0.803922'),ParValue("lightskyblue4","s","Color triple",'0.376471 0.482353 0.545098'),ParValue("lightslateblue","s","Color triple",'0.517647 0.439216 1'),ParValue("lightslategray","s","Color triple",'0.466667 0.533333 0.600000'),ParValue("lightslategrey","s","Color triple",'0.466667 0.533333 0.600000'),ParValue("lightsteelblue","s","Color triple",'0.690196 0.768627 0.870588'),ParValue("lightsteelblue1","s","Color triple",'0.792157 0.882353 1'),ParValue("lightsteelblue2","s","Color triple",'0.737255 0.823529 0.933333'),ParValue("lightsteelblue3","s","Color triple",'0.635294 0.709804 0.803922'),ParValue("lightsteelblue4","s","Color triple",'0.431373 0.482353 0.545098'),ParValue("lightyellow","s","Color triple",'1 1 0.878431'),ParValue("lightyellow1","s","Color triple",'1 1 0.878431'),ParValue("lightyellow2","s","Color triple",'0.933333 0.933333 0.819608'),ParValue("lightyellow3","s","Color triple",'0.803922 0.803922 0.705882'),ParValue("lightyellow4","s","Color triple",'0.545098 0.545098 0.478431'),ParValue("limegreen","s","Color triple",'0.196078 0.803922 0.196078'),ParValue("linen","s","Color triple",'0.980392 0.941176 0.901961'),ParValue("magenta","s","Color triple",'1 0 1'),ParValue("magenta1","s","Color triple",'1 0 1'),ParValue("magenta2","s","Color triple",'0.933333 0 0.933333'),ParValue("magenta3","s","Color triple",'0.803922 0 0.803922'),ParValue("magenta4","s","Color triple",'0.545098 0 0.545098'),ParValue("maroon","s","Color triple",'0.690196 0.188235 0.376471'),ParValue("maroon1","s","Color triple",'1 0.203922 0.701961'),ParValue("maroon2","s","Color triple",'0.933333 0.188235 0.654902'),ParValue("maroon3","s","Color triple",'0.803922 0.160784 0.564706'),ParValue("maroon4","s","Color triple",'0.545098 0.109804 0.384314'),ParValue("mediumaquamarine","s","Color triple",'0.400000 0.803922 0.666667'),ParValue("mediumblue","s","Color triple",'0 0 0.803922'),ParValue("mediumforestgreen","s","Color triple",'0.419608 0.556863 0.137255'),ParValue("mediumgoldenrod","s","Color triple",'0.721569 0.486275 0.043137'),ParValue("mediumorchid","s","Color triple",'0.729412 0.333333 0.827451'),ParValue("mediumorchid1","s","Color triple",'0.878431 0.400000 1'),ParValue("mediumorchid2","s","Color triple",'0.819608 0.372549 0.933333'),ParValue("mediumorchid3","s","Color triple",'0.705882 0.321569 0.803922'),ParValue("mediumorchid4","s","Color triple",'0.478431 0.215686 0.545098'),ParValue("mediumpurple","s","Color triple",'0.576471 0.439216 0.858824'),ParValue("mediumpurple1","s","Color triple",'0.670588 0.509804 1'),ParValue("mediumpurple2","s","Color triple",'0.623529 0.474510 0.933333'),ParValue("mediumpurple3","s","Color triple",'0.537255 0.407843 0.803922'),ParValue("mediumpurple4","s","Color triple",'0.364706 0.278431 0.545098'),ParValue("mediumseagreen","s","Color triple",'0.235294 0.701961 0.443137'),ParValue("mediumslateblue","s","Color triple",'0.482353 0.407843 0.933333'),ParValue("mediumspringgreen","s","Color triple",'0 0.980392 0.603922'),ParValue("mediumturquoise","s","Color triple",'0.282353 0.819608 0.800000'),ParValue("mediumvioletred","s","Color triple",'0.780392 0.082353 0.521569'),ParValue("midnightblue","s","Color triple",'0.098039 0.098039 0.439216'),ParValue("mintcream","s","Color triple",'0.960784 1 0.980392'),ParValue("mistyrose","s","Color triple",'1 0.894118 0.882353'),ParValue("mistyrose1","s","Color triple",'1 0.894118 0.882353'),ParValue("mistyrose2","s","Color triple",'0.933333 0.835294 0.823529'),ParValue("mistyrose3","s","Color triple",'0.803922 0.717647 0.709804'),ParValue("mistyrose4","s","Color triple",'0.545098 0.490196 0.482353'),ParValue("moccasin","s","Color triple",'1 0.894118 0.709804'),ParValue("navajowhite","s","Color triple",'1 0.870588 0.678431'),ParValue("navajowhite1","s","Color triple",'1 0.870588 0.678431'),ParValue("navajowhite2","s","Color triple",'0.933333 0.811765 0.631373'),ParValue("navajowhite3","s","Color triple",'0.803922 0.701961 0.545098'),ParValue("navajowhite4","s","Color triple",'0.545098 0.474510 0.368627'),ParValue("navy","s","Color triple",'0 0 0.501961'),ParValue("navyblue","s","Color triple",'0 0 0.501961'),ParValue("oldlace","s","Color triple",'0.992157 0.960784 0.901961'),ParValue("olivedrab","s","Color triple",'0.419608 0.556863 0.137255'),ParValue("olivedrab1","s","Color triple",'0.752941 1 0.243137'),ParValue("olivedrab2","s","Color triple",'0.701961 0.933333 0.227451'),ParValue("olivedrab3","s","Color triple",'0.603922 0.803922 0.196078'),ParValue("olivedrab4","s","Color triple",'0.411765 0.545098 0.133333'),ParValue("orange","s","Color triple",'1 0.647059 0'),ParValue("orange1","s","Color triple",'1 0.647059 0'),ParValue("orange2","s","Color triple",'0.933333 0.603922 0'),ParValue("orange3","s","Color triple",'0.803922 0.521569 0'),ParValue("orange4","s","Color triple",'0.545098 0.352941 0'),ParValue("orangered","s","Color triple",'1 0.270588 0'),ParValue("orangered1","s","Color triple",'1 0.270588 0'),ParValue("orangered2","s","Color triple",'0.933333 0.250980 0'),ParValue("orangered3","s","Color triple",'0.803922 0.215686 0'),ParValue("orangered4","s","Color triple",'0.545098 0.145098 0'),ParValue("orchid","s","Color triple",'0.854902 0.439216 0.839216'),ParValue("orchid1","s","Color triple",'1 0.513725 0.980392'),ParValue("orchid2","s","Color triple",'0.933333 0.478431 0.913725'),ParValue("orchid3","s","Color triple",'0.803922 0.411765 0.788235'),ParValue("orchid4","s","Color triple",'0.545098 0.278431 0.537255'),ParValue("palegoldenrod","s","Color triple",'0.933333 0.909804 0.666667'),ParValue("palegreen","s","Color triple",'0.596078 0.984314 0.596078'),ParValue("palegreen1","s","Color triple",'0.603922 1 0.603922'),ParValue("palegreen2","s","Color triple",'0.564706 0.933333 0.564706'),ParValue("palegreen3","s","Color triple",'0.486275 0.803922 0.486275'),ParValue("palegreen4","s","Color triple",'0.329412 0.545098 0.329412'),ParValue("paleturquoise","s","Color triple",'0.686275 0.933333 0.933333'),ParValue("paleturquoise1","s","Color triple",'0.733333 1 1'),ParValue("paleturquoise2","s","Color triple",'0.682353 0.933333 0.933333'),ParValue("paleturquoise3","s","Color triple",'0.588235 0.803922 0.803922'),ParValue("paleturquoise4","s","Color triple",'0.400000 0.545098 0.545098'),ParValue("palevioletred","s","Color triple",'0.858824 0.439216 0.576471'),ParValue("palevioletred1","s","Color triple",'1 0.509804 0.670588'),ParValue("palevioletred2","s","Color triple",'0.933333 0.474510 0.623529'),ParValue("palevioletred3","s","Color triple",'0.803922 0.407843 0.537255'),ParValue("palevioletred4","s","Color triple",'0.545098 0.278431 0.364706'),ParValue("papayawhip","s","Color triple",'1 0.937255 0.835294'),ParValue("peachpuff","s","Color triple",'1 0.854902 0.725490'),ParValue("peachpuff1","s","Color triple",'1 0.854902 0.725490'),ParValue("peachpuff2","s","Color triple",'0.933333 0.796078 0.678431'),ParValue("peachpuff3","s","Color triple",'0.803922 0.686275 0.584314'),ParValue("peachpuff4","s","Color triple",'0.545098 0.466667 0.396078'),ParValue("peru","s","Color triple",'0.803922 0.521569 0.247059'),ParValue("pink","s","Color triple",'1 0.752941 0.796078'),ParValue("pink1","s","Color triple",'1 0.709804 0.772549'),ParValue("pink2","s","Color triple",'0.933333 0.662745 0.721569'),ParValue("pink3","s","Color triple",'0.803922 0.568627 0.619608'),ParValue("pink4","s","Color triple",'0.545098 0.388235 0.423529'),ParValue("plum","s","Color triple",'0.866667 0.627451 0.866667'),ParValue("plum1","s","Color triple",'1 0.733333 1'),ParValue("plum2","s","Color triple",'0.933333 0.682353 0.933333'),ParValue("plum3","s","Color triple",'0.803922 0.588235 0.803922'),ParValue("plum4","s","Color triple",'0.545098 0.400000 0.545098'),ParValue("powderblue","s","Color triple",'0.690196 0.878431 0.901961'),ParValue("purple","s","Color triple",'0.627451 0.125490 0.941176'),ParValue("purple1","s","Color triple",'0.607843 0.188235 1'),ParValue("purple2","s","Color triple",'0.568627 0.172549 0.933333'),ParValue("purple3","s","Color triple",'0.490196 0.149020 0.803922'),ParValue("purple4","s","Color triple",'0.333333 0.101961 0.545098'),ParValue("red","s","Color triple",'1 0 0'),ParValue("red1","s","Color triple",'1 0 0'),ParValue("red2","s","Color triple",'0.933333 0 0'),ParValue("red3","s","Color triple",'0.803922 0 0'),ParValue("red4","s","Color triple",'0.545098 0 0'),ParValue("rosybrown","s","Color triple",'0.737255 0.560784 0.560784'),ParValue("rosybrown1","s","Color triple",'1 0.756863 0.756863'),ParValue("rosybrown2","s","Color triple",'0.933333 0.705882 0.705882'),ParValue("rosybrown3","s","Color triple",'0.803922 0.607843 0.607843'),ParValue("rosybrown4","s","Color triple",'0.545098 0.411765 0.411765'),ParValue("royalblue","s","Color triple",'0.254902 0.411765 0.882353'),ParValue("royalblue1","s","Color triple",'0.282353 0.462745 1'),ParValue("royalblue2","s","Color triple",'0.262745 0.431373 0.933333'),ParValue("royalblue3","s","Color triple",'0.227451 0.372549 0.803922'),ParValue("royalblue4","s","Color triple",'0.152941 0.250980 0.545098'),ParValue("saddlebrown","s","Color triple",'0.545098 0.270588 0.074510'),ParValue("salmon","s","Color triple",'0.980392 0.501961 0.447059'),ParValue("salmon1","s","Color triple",'1 0.549020 0.411765'),ParValue("salmon2","s","Color triple",'0.933333 0.509804 0.384314'),ParValue("salmon3","s","Color triple",'0.803922 0.439216 0.329412'),ParValue("salmon4","s","Color triple",'0.545098 0.298039 0.223529'),ParValue("sandybrown","s","Color triple",'0.956863 0.643137 0.376471'),ParValue("seagreen","s","Color triple",'0.180392 0.545098 0.341176'),ParValue("seagreen1","s","Color triple",'0.329412 1 0.623529'),ParValue("seagreen2","s","Color triple",'0.305882 0.933333 0.580392'),ParValue("seagreen3","s","Color triple",'0.262745 0.803922 0.501961'),ParValue("seagreen4","s","Color triple",'0.180392 0.545098 0.341176'),ParValue("seashell","s","Color triple",'1 0.960784 0.933333'),ParValue("seashell1","s","Color triple",'1 0.960784 0.933333'),ParValue("seashell2","s","Color triple",'0.933333 0.898039 0.870588'),ParValue("seashell3","s","Color triple",'0.803922 0.772549 0.749020'),ParValue("seashell4","s","Color triple",'0.545098 0.525490 0.509804'),ParValue("sienna","s","Color triple",'0.627451 0.321569 0.176471'),ParValue("sienna1","s","Color triple",'1 0.509804 0.278431'),ParValue("sienna2","s","Color triple",'0.933333 0.474510 0.258824'),ParValue("sienna3","s","Color triple",'0.803922 0.407843 0.223529'),ParValue("sienna4","s","Color triple",'0.545098 0.278431 0.149020'),ParValue("skyblue","s","Color triple",'0.529412 0.807843 0.921569'),ParValue("skyblue1","s","Color triple",'0.529412 0.807843 1'),ParValue("skyblue2","s","Color triple",'0.494118 0.752941 0.933333'),ParValue("skyblue3","s","Color triple",'0.423529 0.650980 0.803922'),ParValue("skyblue4","s","Color triple",'0.290196 0.439216 0.545098'),ParValue("slateblue","s","Color triple",'0.415686 0.352941 0.803922'),ParValue("slateblue1","s","Color triple",'0.513725 0.435294 1'),ParValue("slateblue2","s","Color triple",'0.478431 0.403922 0.933333'),ParValue("slateblue3","s","Color triple",'0.411765 0.349020 0.803922'),ParValue("slateblue4","s","Color triple",'0.278431 0.235294 0.545098'),ParValue("slategray","s","Color triple",'0.439216 0.501961 0.564706'),ParValue("slategray1","s","Color triple",'0.776471 0.886275 1'),ParValue("slategray2","s","Color triple",'0.725490 0.827451 0.933333'),ParValue("slategray3","s","Color triple",'0.623529 0.713725 0.803922'),ParValue("slategray4","s","Color triple",'0.423529 0.482353 0.545098'),ParValue("slategrey","s","Color triple",'0.439216 0.501961 0.564706'),ParValue("snow","s","Color triple",'1 0.980392 0.980392'),ParValue("snow1","s","Color triple",'1 0.980392 0.980392'),ParValue("snow2","s","Color triple",'0.933333 0.913725 0.913725'),ParValue("snow3","s","Color triple",'0.803922 0.788235 0.788235'),ParValue("snow4","s","Color triple",'0.545098 0.537255 0.537255'),ParValue("springgreen","s","Color triple",'0 1 0.498039'),ParValue("springgreen1","s","Color triple",'0 1 0.498039'),ParValue("springgreen2","s","Color triple",'0 0.933333 0.462745'),ParValue("springgreen3","s","Color triple",'0 0.803922 0.400000'),ParValue("springgreen4","s","Color triple",'0 0.545098 0.270588'),ParValue("steelblue","s","Color triple",'0.274510 0.509804 0.705882'),ParValue("steelblue1","s","Color triple",'0.388235 0.721569 1'),ParValue("steelblue2","s","Color triple",'0.360784 0.674510 0.933333'),ParValue("steelblue3","s","Color triple",'0.309804 0.580392 0.803922'),ParValue("steelblue4","s","Color triple",'0.211765 0.392157 0.545098'),ParValue("tan","s","Color triple",'0.823529 0.705882 0.549020'),ParValue("tan1","s","Color triple",'1 0.647059 0.309804'),ParValue("tan2","s","Color triple",'0.933333 0.603922 0.286275'),ParValue("tan3","s","Color triple",'0.803922 0.521569 0.247059'),ParValue("tan4","s","Color triple",'0.545098 0.352941 0.168627'),ParValue("thistle","s","Color triple",'0.847059 0.749020 0.847059'),ParValue("thistle1","s","Color triple",'1 0.882353 1'),ParValue("thistle2","s","Color triple",'0.933333 0.823529 0.933333'),ParValue("thistle3","s","Color triple",'0.803922 0.709804 0.803922'),ParValue("thistle4","s","Color triple",'0.545098 0.482353 0.545098'),ParValue("tomato","s","Color triple",'1 0.388235 0.278431'),ParValue("tomato1","s","Color triple",'1 0.388235 0.278431'),ParValue("tomato2","s","Color triple",'0.933333 0.360784 0.258824'),ParValue("tomato3","s","Color triple",'0.803922 0.309804 0.223529'),ParValue("tomato4","s","Color triple",'0.545098 0.211765 0.149020'),ParValue("turquoise","s","Color triple",'0.250980 0.878431 0.815686'),ParValue("turquoise1","s","Color triple",'0 0.960784 1'),ParValue("turquoise2","s","Color triple",'0 0.898039 0.933333'),ParValue("turquoise3","s","Color triple",'0 0.772549 0.803922'),ParValue("turquoise4","s","Color triple",'0 0.525490 0.545098'),ParValue("violet","s","Color triple",'0.933333 0.509804 0.933333'),ParValue("violetred","s","Color triple",'0.815686 0.125490 0.564706'),ParValue("violetred1","s","Color triple",'1 0.243137 0.588235'),ParValue("violetred2","s","Color triple",'0.933333 0.227451 0.549020'),ParValue("violetred3","s","Color triple",'0.803922 0.196078 0.470588'),ParValue("violetred4","s","Color triple",'0.545098 0.133333 0.321569'),ParValue("wheat","s","Color triple",'0.960784 0.870588 0.701961'),ParValue("wheat1","s","Color triple",'1 0.905882 0.729412'),ParValue("wheat2","s","Color triple",'0.933333 0.847059 0.682353'),ParValue("wheat3","s","Color triple",'0.803922 0.729412 0.588235'),ParValue("wheat4","s","Color triple",'0.545098 0.494118 0.400000'),ParValue("white","s","Color triple",'1 1 1'),ParValue("whitesmoke","s","Color triple",'0.960784 0.960784 0.960784'),ParValue("yellow","s","Color triple",'1 1 0'),ParValue("yellow1","s","Color triple",'1 1 0'),ParValue("yellow2","s","Color triple",'0.933333 0.933333 0'),ParValue("yellow3","s","Color triple",'0.803922 0.803922 0'),ParValue("yellow4","s","Color triple",'0.545098 0.545098 0'),ParValue("yellowgreen","s","Color triple",'0.603922 0.803922 0.196078')],
    }


parinfo['combine_grating_spectra'] = {
    'istool': True,
    'req': [ParValue("infile","f","Source PHA1/PHA2 grating spectra to combine; enter list or '@stack'",None),ParValue("outroot","f","Root name for output file(s)",None)],
    'opt': [ParValue("add_plusminus","b","Combine +/- orders (yes) after summing signed-order and part?",False),ParSet("garm","s","Grating arm (HEG, MEG, LEG, or 'all')",'all',["HEG","MEG","LEG","all"]),ParSet("order","s","Grating diffraction order (1,2,3,-1,-2,-3, or 'all')",'all',["1","2","3","-1","-2","-3","all"]),ParValue("arf","f","Source ARF files to combine; enter list or '@stack'",None),ParValue("rmf","f","Source RMF files to combine; enter list or '@stack'",None),ParValue("bkg_pha","f","Background PHA files to combine; enter list or '@stack'",None),ParSet("bscale_method","s","How are BACKSCAL and background counts computed?",'counts',["asca","time","counts"]),ParSet("exposure_mode","s","Sum or average exposure times?",'sum',["avg","sum"]),ParValue("object","s","Specify the OBJECT keyword in the combined output",None),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['combine_spectra'] = {
    'istool': True,
    'req': [ParValue("src_spectra","f","Source PHA files to combine; enter list or '@stack'",None),ParValue("outroot","f","Root name for output files",None)],
    'opt': [ParValue("src_arfs","f","Source ARF files to combine; enter list or '@stack'",None),ParValue("src_rmfs","f","Source RMF files to combine; enter list or '@stack'",None),ParValue("bkg_spectra","f","Background PHA files to combine; enter list or '@stack'",None),ParValue("bkg_arfs","f","Background ARF files to combine; enter list or '@stack'",None),ParValue("bkg_rmfs","f","Background RMF files to combine; enter list or '@stack'",None),ParSet("method","s","Sum or average PHA exposures?",'sum',["sum","avg"]),ParSet("bscale_method","s","How are BACKSCAL and background counts computed?",'asca',["asca","time","counts"]),ParSet("exp_origin","s","Write combined PHA or ARF exposure time to header(s) (pha, arf)",'pha',["pha","arf"]),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['convert_ds9_region_to_ciao_stack'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input ds9 region file in physical coordinates",None),ParValue("outfile","f","Output CIAO stack of regions",None)],
    'opt': [ParRange("verbose","i","Amount of tool chatter",1,0,5),ParValue("clobber","b","Remove outfile if it already exists?",False)],
    }


parinfo['correct_periscope_drift'] = {
    'istool': True,
    'req': [ParValue("infile","f","input aspect solution file",None),ParValue("evtfile","f","event file",None),ParValue("outfile","f","corrected/output aspect solution file",None),ParRange("x","r","src sky x",None,1,None),ParRange("y","r","src sky y",None,1,None),ParRange("radius","r","src circle radius in pixels",None,0,None)],
    'opt': [ParValue("corr_plot_root","f","prefix for correction evaluation plots",'corr'),ParRange("src_min_counts","r","minimum src counts",250,0,None),ParRange("corr_poly_degree","i","Degree of sherpa fit polynomial",2,1,8),ParValue("clobber","b","Overwrite the output file if it exists?",False),ParRange("verbose","i","Debug level (0=no debug information)",2,0,5)],
    }


parinfo['create_bkg_map'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("fovfile","f","Input fov file",None),ParValue("expmap","f","Input exposure map",None),ParValue("outfile","f","Output background image",None),ParValue("xygrid","s","Exposure map grid syntax x0:x1:#nx,x0:x1:ny",None)],
    'opt': [ParValue("outimgfile","f","Output image file",None),ParValue("outstreakmap","f","Output streak map file",None),ParValue("outlowfreqmap","f","Output low frequency map file",None),ParValue("tmpdir","s","Directory for temp. files",'${ASCDS_WORK_PATH}'),ParValue("expcorr","b","Is final background exposure corrected?",True),ParRange("scale","i","scale in pixels for dmimgpm",64,0,None),ParValue("smoothing_kernel","s","Smoothing kernel for HRC data",'lib:tophat(2,1,3,3)'),ParValue("clobber","b","Clobber existing output?",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['csmooth'] = {
    'istool': True,
    'req': [ParValue("infile","f","input file name",None),ParValue("sclmap","f","image of user-supplied map of smoothing scales",None),ParValue("outfile","f","output file name",None),ParValue("outsigfile","f","output significance image",'.'),ParValue("outsclfile","f","output scales [kernel sizes] image",'.'),ParSet("conmeth","s","Convolution method.",'fft',["slide","fft"]),ParSet("conkerneltype","s","Convolution kernel type.",'gauss',["gauss","tophat"]),ParValue("sigmin","r","minimal significance, S/N ratio",4),ParRange("sigmax","r","maximal significance, S/N ratio",5,4,None),ParValue("sclmin","r","initial (minimal) smoothing scale [pixel]",None),ParRange("sclmax","r","maximal smoothing scale [pixel]",None,"INDEF",None),ParSet("sclmode","s","compute smoothing scales or user user-supplied map",'compute',["compute","user"])],
    'opt': [ParValue("stepzero","r","initial stepsize",0.01),ParSet("bkgmode","s","background treatment",'local',["local","user"]),ParValue("bkgmap","f","user-supplied input background image",None),ParValue("bkgerr","f","user-supplied input background error image",None),ParValue("clobber","b","clobber existing output",False),ParRange("verbose","i","verbosity of processing comments",0,0,5)],
    }


parinfo['dax'] = {
    'istool': False,
    'req': [],
    'opt': [ParValue("outdir","f","Location of the output files for dax",'${ASCDS_WORK_PATH}/ds9_dax.${USER}'),ParValue("tile","b","Change ds9 into tile mode when adding new images?",False),ParValue("progress_bar","b","Show progress bar when tasks are running?",True),ParValue("random_seed","i","Random seed for any tasks the require one",-1),ParValue("prism","b","Launch prism to view output tables?",False)],
    }


parinfo['deflare'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input light curve file",None),ParValue("outfile","f","Output GTI file",None),ParSet("method","s","Choose flare-cleaning method",'clean',["clean","sigma"])],
    'opt': [ParValue("nsigma","r","method=clean 'clip', method=sigma: no. of sigma about the mean to use to clip data",3),ParValue("plot","b","Plot light curve and histograms of values?",False),ParValue("save","f","PostScript file to save plot as?",None),ParSet("rateaxis","s","Should count-rate be on 'y' or 'x' axis of top plot?",'y',["x","y"]),ParSet("pattern","s","Pattern to use in plot for filled regions representing excluded time intervals",'solid',["nofill","solid","updiagonal","downdiagonal","horizontal","vertical","crisscross","grid","polkadot"]),ParValue("good_color","s","Color to use in plot to draw 'good' data points",'lime'),ParValue("exclude_color","s","Color to use in plot for excluded time intervals",'red'),ParValue("minlength","r","lc_sigma_clip: min. no. of consecutive time bins which must pass rate filter",3),ParValue("mean","r","lc_clean: mean count rate (ct/s)",0),ParValue("stddev","r","lc_clean 'sigma': standard deviation of signal",0),ParValue("scale","r","lc_clean: scale factor about the mean rate",1.2),ParValue("minfrac","r","lc_clean: minimum fraction of good bins",0.1),ParRange("verbose","i","Debug level",1,0,5)],
    }


parinfo['destreak'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset/block specification",None)],
    'opt': [ParValue("max","s","streak threshold  syntax:  m  OR  m:m:m:m",None),ParRange("max_rowloss_fraction","r","Maximum fraction of avg streaks/node/frame",5.0e-5,3e-05,1),ParValue("num_sigma","r","Sigma value for determining streak threshold",1.0),ParValue("filter","b","Discard tagged events",True),ParValue("mask","s","Filter to select candidate streak events",'[status=0,grade=0,2:4,6]'),ParValue("ccd_id","s","CCD ID to filter",'8'),ParValue("ccd_col","s","CCD ID column name",'ccd_id'),ParValue("node_col","s","Node ID column name ('none' for single node)",'node_id'),ParValue("exptime","r","frame time (s) (reads EXPTIME if no pos. value given)",-1),ParValue("countfile","f","filename for event row-count distribution",None),ParValue("fracfile","f","filename for cumulative streak contam function",None),ParValue("timefile","f","filename for exposure time lost per row",None),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['detilt'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input L2 HRC-S/LETG event list file",None),ParValue("outfile","f","Output file",None),ParValue("tilt","r","residual dispersion angle (deg/Ang)",0)],
    'opt': [ParRange("verbose","i","Debug level",0,0,5),ParValue("clobber","b","Clobber outfile if it already exists?",False)],
    }


parinfo['dewiggle'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input L2 HRC-S/LETG event list file",None),ParValue("outfile","f","Output file",None)],
    'opt': [ParValue("wfile","f","Wiggle correction file",'${ASCDS_CONTRIB}/data/wigglecorrection.dat'),ParRange("verbose","i","Debug level",0,0,5),ParValue("clobber","b","Clobber outfile if it already exists?",False)],
    }


parinfo['dither_region'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input aspect solution or histogram file(s)",None),ParValue("region","s","Region specification",None),ParValue("outfile","f","Output file name",None),ParValue("wcsfile","f","WCS File",None)],
    'opt': [ParValue("maskfile","f","Mask file",None),ParValue("psffile","f","PSF Image file",None),ParValue("gtifile","f","GTI File",None),ParValue("dtffile","f","DTF File",None),ParValue("imapfile","f","Stack of Instrument files",None),ParValue("tolerance","r","Tolerance of aspect solution [arcsec]",None),ParRange("resolution","r","Binning resolution of region [pixels]",1,0,None),ParRange("maxpix","i","Maximum number of pixels regardless of resolution",1000,1,None),ParValue("convex","b","Use convex hull around aspect histogram?",False),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("ardlibpar","f","Parameter file for ARDLIB files",'ardlib'),ParValue("detsubsysmod","s","Detector sybsystem modifier",None),ParRange("verbose","i","Tool verbosity",0,0,5),ParValue("clobber","b","Remove outfile if it already exists",False)],
    }


parinfo['dmappend'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset name",None)],
    'opt': [ParRange("verbose","i","Debug Level",0,0,5)],
    }


parinfo['dmarfadd'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input list of files",None),ParValue("outfile","f","Output dataset name",None)],
    'opt': [ParValue("clobber","b","Clobber existing output?",False),ParRange("verbose","i","Debug Level",0,0,5)],
    }


parinfo['dmcontour'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("levels","s","Contour levels",None),ParValue("outfile","f","Output contour region file name",None)],
    'opt': [ParRange("verbose","i","Amount of verbose output sent to the screen",0,0,5),ParValue("clobber","b","Remove output file if already exists",False)],
    }


parinfo['dmcoords'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None)],
    'opt': [ParValue("asolfile","f","Input aspect solution file",'none'),ParValue("option","s","Conversion option",None),ParRange("chip_id","i","Chip ID number",None,0,9),ParValue("chipx","r","Chip X [pixel]",None),ParValue("chipy","r","Chip Y [pixel]",None),ParValue("tdetx","r","TDETX [pixel]",None),ParValue("tdety","r","TDETY [pixel]",None),ParValue("detx","r","FPC X [pixel]",None),ParValue("dety","r","FPC Y [pixel]",None),ParValue("x","r","Sky X [pixel]",None),ParValue("y","r","Sky Y [pixel]",None),ParValue("logicalx","r","X coordinate in binned image [pixel]",None),ParValue("logicaly","r","Y coordinate in binned image [pixel]",None),ParValue("ra","s","RA [deg or hh:mm:ss]",None),ParValue("dec","s","Dec [deg or dd:mm:ss]",None),ParRange("theta","r","Off axis angle [arcmin]",None,0,10800),ParRange("phi","r","Azimuthal angle [deg]",None,0,360),ParValue("order","i","Grating order",0),ParValue("energy","r","Energy [keV]",1.0),ParValue("wavelength","r","Wavelength [A]",0),ParValue("ra_zo","s","RA of zero order",None),ParValue("dec_zo","s","Dec of zero order",None),ParValue("celfmt","s","RA and Dec format [deg or hms] (xx.xx or xx:xx:xx.x)",'hms'),ParValue("detector","s","Detector (ACIS or HRC-I or HRC-S)",None),ParValue("grating","s","Grating",None),ParValue("fpsys","s","FP convention",None),ParValue("sim","s","SIM position (eg 0.0 0.0 -190.6)",None),ParValue("displace","s","STF displacement (X,Y,Z,AX,AY,AZ)",None),ParValue("ra_nom","s","Nominal pointing RA [deg or hh:mm:ss]",None),ParValue("dec_nom","s","Nominal dec [deg or dd:mm:ss]",None),ParValue("roll_nom","s","Nominal roll [deg]",None),ParValue("ra_asp","s","Instantaneous pointing RA [deg]",None),ParValue("dec_asp","s","Instantaneous pointing Dec [deg]",None),ParValue("roll_asp","s","Instantaneous Aspect roll [deg]",None),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Debug Level",0,0,5)],
    }


parinfo['dmcopy'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset name",None)],
    'opt': [ParValue("kernel","s","Output file format type",'default'),ParValue("option","s","Option - force output type",None),ParRange("verbose","i","Debug Level",0,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['dmdiff'] = {
    'istool': True,
    'req': [ParValue("infile1","f","1st input file name",None),ParValue("infile2","f","2nd input file name",None)],
    'opt': [ParValue("outfile","f","Output file name (NONE|none|stdout|stderr|<filename>)",None),ParValue("tolfile","f","Tolerance file name",None),ParValue("keys","b","Check header keywords?",True),ParValue("data","b","Check table or image data?",True),ParValue("subspaces","b","Check subspaces?",True),ParValue("units","b","Check units?",True),ParValue("comments","b","Check comments?",True),ParValue("wcs","b","Check wcs?",True),ParValue("missing","b","Check for missing header keys?",True),ParValue("error_on_value","b","Return error when values are different?",True),ParValue("error_on_comment","b","Return error when comments are different?",True),ParValue("error_on_unit","b","Return error when units are different?",True),ParValue("error_on_range","b","Return error when out of tolfile range?",True),ParValue("error_on_datatype","b","Return error when datatypes are different?",True),ParValue("error_on_wcs","b","Return error when wcs's are different?",True),ParValue("error_on_subspace","b","Return error when subspaces are different?",True),ParValue("error_on_missing","b","Return error when header key is missing?",True),ParRange("verbose","i","Debug Level(0-5)",1,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['dmellipse'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file",None),ParValue("outfile","f","Output region file",None),ParValue("fraction","s","Ellipse at what fraction(s)",None)],
    'opt': [ParSet("shape","s","Shape of region",'ellipse',["ellipse","rotbox"]),ParValue("x_centroid","r","Default X-centroid to use (physical coords)",None),ParValue("y_centroid","r","Default Y-centroid to use (physical coords)",None),ParValue("angle","r","Default angle [deg]",None),ParValue("ellipticity","r","Default ellipticity",None),ParValue("xcol","s","X column name from input table",None),ParValue("ycol","s","Y column name from input table",None),ParValue("zcol","s","Optional Z column name from input table",None),ParValue("fix_centroid","b","Fix centroid?",False),ParValue("fix_angle","b","Fix angle?",False),ParValue("fix_ellipticity","b","Fix ellipticity?",False),ParRange("tolerance","r","Tolerance on fraction",0.001,0,1),ParRange("minstep","r","Minimum step size [pixels]",0.001,0,1),ParRange("maxwalk","i","Maximum number of equal-fraction walks",10,1,None),ParRange("step","r","Initial step size [pixels]",1,0,None),ParValue("normalize","b","Normalize by sum of pixels",True),ParValue("clobber","b","Remove outfile if it exists",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['dmextract'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outfile","f","Enter output file name",None)],
    'opt': [ParValue("bkg","f","Background region file or fixed background (counts/pixel/s) subtraction",None),ParValue("error","s","Method for error determination(gaussian|gehrels|<variance file>)",'gaussian'),ParValue("bkgerror","s","Method for background error determination(gaussian|gehrels|<variance file>)",'gaussian'),ParValue("bkgnorm","r","Background normalization",1.0),ParValue("exp","f","Exposure map image file",None),ParValue("bkgexp","f","Background exposure map image file",None),ParValue("sys_err","r","Fixed systematic error value for SYS_ERR keyword",0),ParSet("opt","s","Output file type",'pha1',["pha1","pha2","ltc1","ltc2","generic","generic2"]),ParValue("defaults","f","Instrument defaults file",'${ASCDS_CALIB}/cxo.mdb'),ParValue("wmap","s","WMAP filter/binning (e.g. det=8 or default)",None),ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['dmfilth'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file",None),ParValue("outfile","f","Enter output file name",None),ParSet("method","s","Interpolation method",'GLOBAL',["POLY","DIST","GLOBAL","POISSON","BILINT"]),ParValue("srclist","s","List of sources to fill in",None),ParValue("bkglist","s","List of background regions",None)],
    'opt': [ParRange("randseed","i","Seed for random number generator",1,0,65536),ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['dmgroup'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset name",None),ParValue("outfile","f","Output dataset name",None),ParSet("grouptype","s","Grouping type",'NONE',["NONE","BIN","SNR","NUM_BINS","NUM_CTS","ADAPTIVE","ADAPTIVE_SNR","BIN_WIDTH","MIN_SLOPE","MAX_SLOPE","BIN_FILE"]),ParValue("grouptypeval","r","Grouping type value",0),ParValue("binspec","s","Binning specification",None),ParValue("xcolumn","s","Name of x-axis",None),ParValue("ycolumn","s","Name of y-axis",None)],
    'opt': [ParValue("tabspec","s","Tab specification",None),ParValue("tabcolumn","s","Name of tab column",None),ParValue("stopspec","s","Stop specification",None),ParValue("stopcolumn","s","Name of stop column",None),ParValue("errcolumn","s","Name of error column",None),ParValue("clobber","b","Clobber existing output file?",False),ParRange("verbose","i","Verbosity level",0,0,5),ParRange("maxlength","r","Maximum size of groups (in channels)",0,0,None)],
    }


parinfo['dmgroupreg'] = {
    'istool': True,
    'req': [ParValue("infile","f","DS9 region input file",None),ParValue("srcoutfile","f","Output file for CIAO source regions",None),ParValue("bkgoutfile","f","Output file for CIAO background regions",None)],
    'opt': [ParValue("exclude","b","Explicitly exclude source regions from background regions?",True),ParRange("verbose","i","Debug Level (0-5)",0,0,5),ParValue("clobber","b","Clobber existing files?",False)],
    }


parinfo['dmgti'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input MTL file",None),ParValue("outfile","f","Output GTI file",None),ParValue("userlimit","s","User defined limit string",None)],
    'opt': [ParValue("mtlfile","f","Optional output smoothed/filtered MTL file",'none'),ParValue("lkupfile","f","Lookup table defining which MTL columns to check against (NONE|none|<filename>)",'none'),ParValue("smooth","b","Smooth the input MTL data?",True),ParValue("clobber","b","Clobber output file if it exists?",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['dmhedit'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("filelist","f","Edit list file name",None),ParValue("operation","s","Operation",None),ParValue("key","s","Keyword",None),ParValue("value","s","Value for keyword",None)],
    'opt': [ParSet("datatype","s","Keyword data type",'indef',["string","double","float","long","short","ulong","ushort","boolean","indef"]),ParValue("unit","s","Unit for keyword",None),ParValue("comment","s","Comment for keyword",None),ParRange("verbose","i","Verbosity Level(0-5)",0,0,5)],
    }


parinfo['dmhistory'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file to get history from",None),ParValue("tool","s","Tool name to extract history",None)],
    'opt': [ParValue("outfile","f","Output file [stdout|stderr|FILENAME]",'stdout'),ParValue("expand","b","Replace stacks in output string?",True),ParSet("action","s","What to do with history",'get',["get","put","pset"]),ParValue("clobber","b","Remove output file if it exists?",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['dmimg2jpg'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name (red image if true color)",None),ParValue("greenfile","f","Green color channel file name",'none'),ParValue("bluefile","f","Blue color channel file name",'none'),ParValue("outfile","f","Output jpg file name",None)],
    'opt': [ParValue("lutfile","f","Colormap file",')lut.grey'),ParValue("colorstretch","r","Color lookup strech factor",1),ParValue("colorshift","i","Color lookup table shift",0),ParValue("invert","b","Invert colors",False),ParSet("scalefunction","s","Scaling function",'log',["log","linear","power","asinh"]),ParValue("scaleparam","r","Scaling parameter (for non-linear scalefunction)",3),ParValue("minred","r","Minimum value for the red color channel",None),ParValue("mingreen","r","Minimum value for the green color channel",None),ParValue("minblue","r","Minimum value for the blue color channel",None),ParValue("maxred","r","Maximum value for the red color channel",None),ParValue("maxgreen","r","Maximum value for the green color channel",None),ParValue("maxblue","r","Maximum value for the blue color channel",None),ParValue("regionfile","f","Region overlay file",None),ParValue("regioncolor","s","Region color triple",')colors.green'),ParSet("regionopt","s","Option of region shape drawing method (individal|combine)",'individual',["individual","combine"]),ParValue("showaimpoint","b","Put crosshair at aimpoint",False),ParValue("showlabel","b","Label the contours?",False),ParValue("showgrid","b","Show grid on image",False),ParValue("gridcolor","s","Grid color triple",')colors.white'),ParValue("gridsize","r","Gridsize [arcsec]",120),ParRange("fontsize","i","Font label size",2,1,3),ParValue("psfile","f","Optional post script file name",None),ParRange("verbose","i","Level of verbose output",0,0,5),ParValue("clobber","b","Clobber existing outputs?",False)],
    }


parinfo['dmimgadapt'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None),ParSet("function","s","Filter function",'tophat',["tophat","box","gaussian","cone","pyramid","walrewop","exp","lor","mex","hemisphere","quad"]),ParRange("minrad","r","Min. radius/scale",0.5,0,None),ParRange("maxrad","r","Max. radius/scale",10,0,None),ParValue("numrad","r","Number of radii/scales",20),ParSet("radscale","s","Radii/scale spacing",'log',["linear","log"]),ParRange("counts","r","Number of counts in filter",None,0,None)],
    'opt': [ParValue("inradfile","f","Input file w/ predetermined radii",None),ParValue("innormfile","f","Input file w/ predetermined normalizations",None),ParValue("sumfile","f","Image with total counts in filter",None),ParValue("normfile","f","Image with kernel normalization",None),ParValue("radfile","f","Image with smoothing radii/scales",None),ParRange("verbose","i","Tool verbosity",0,0,5),ParValue("clobber","b","Clobber existing output?",False)],
    }


parinfo['dmimgblob'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None),ParValue("threshold","r","Image blob threshold",None)],
    'opt': [ParValue("srconly","b","Deal only w/ values >= threshold?",False),ParValue("clobber","b","Clobber existing files",False),ParRange("verbose","i","Tool verbosity",0,0,0)],
    }


parinfo['dmimgcalc'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file #1",None),ParValue("infile2","f","Input file #2",None),ParValue("outfile","f","output file",None),ParValue("operation","s","arithmetic operation",None)],
    'opt': [ParValue("weight","r","weight for first image",1),ParValue("weight2","r","weight for second image",1),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("clobber","b","delete old output",False),ParRange("verbose","i","output verbosity",0,0,5)],
    }


parinfo['dmimgdist'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file",None),ParValue("outfile","f","Output ASCII region file",None)],
    'opt': [ParValue("tolerance","r","Tolerance on fraction",0),ParValue("clobber","b","Remove outfile if it exists",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['dmimgfilt'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None),ParSet("function","s","Filter function",'mean',["min","max","mean","median","mode","mid","sigma","extreme","locheq","kuwahara","unsharp","range","variance","nmode","q10","q25","q33","q67","q75","q90","qxx","mcv","sum","rclip","peak","ridge","valley","plain","count","olympic","pmean","mu3","mu4","jitter","rms","nslope","3sigmean","3sigmedian"]),ParValue("mask","s","masking filter",None)],
    'opt': [ParRange("numiter","i","Number of iterations to loop over",1,1,None),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParRange("randseed","i","Seed for random seed generator",0,0,65535),ParRange("verbose","i","Tool verbosity",0,0,5),ParValue("clobber","b","Clobber existing output?",False),ParValue("box3","s","Box: 3x3",'box(0,0,3,3)'),ParValue("box5","s","Box: 5x5",'box(0,0,5,5)'),ParValue("box7","s","Box: 7x7",'box(0,0,7,7)'),ParValue("circle3","s","Circle: r=3",'circle(0,0,3)'),ParValue("circle5","s","Circle: r=5",'circle(0,0,5)'),ParValue("circle7","s","Circle: r=7",'circle(0,0,7)'),ParValue("annulus5_3","s","Annulus: o=5,i=3",'annulus(0,0,3,5)'),ParValue("annulus7_5","s","Annulus: o=7,i=5",'annulus(0,0,5,7)'),ParValue("annulus7_3","s","Annulus: o=7,i=3",'annulus(0,0,3,7)'),ParValue("bann5_3","s","Box Annulus: o=5,i=3",'box(0,0,5,5)-box(0,0,3,3)'),ParValue("bann7_3","s","Box Annulus: o=7,i=3",'box(0,0,7,7)-box(0,0,3,3)'),ParValue("bann7_5","s","Box Annulus: o=7,i=5",'box(0,0,7,7)-box(0,0,5,5)')],
    }


parinfo['dmimghist'] = {
    'istool': True,
    'req': [ParValue("infile","f","input file or stack",None),ParValue("outfile","f","output file or stack",None),ParValue("hist","s","binning specification or stack [a]:[b][:c]|c|<filename>",None)],
    'opt': [ParValue("strict","b","ignore counts outside of binning range",False),ParValue("clobber","b","delete old output",False),ParRange("verbose","i","output verbosity",0,0,5)],
    }


parinfo['dmimghull'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file",None),ParValue("outfile","f","Output FITS region file",None)],
    'opt': [ParValue("tolerance","r","Exclude values equal to and below this value",0),ParValue("clobber","b","Overwrite outfile if it exists",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['dmimglasso'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None),ParValue("xpos","r","Starting X-location",None),ParValue("ypos","r","Starting Y-location",None),ParValue("low_value","r","Minimum threshold",None),ParValue("high_value","r","Maximum threshold",None)],
    'opt': [ParSet("coord","s","Coordinate system of xpos,ypos",'physical',["physical","logical"]),ParSet("value","s","Hi/low values",'absolute',["absolute","percent","delta"]),ParRange("maxdepth","i","Maximum recursion depth",10000,1,None),ParValue("clobber","b","Clobber existing files",False),ParRange("verbose","i","Tool verbosity",0,0,0)],
    }


parinfo['dmimgpick'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input table file",None),ParValue("imgfile","f","Input image file",None),ParValue("outfile","f","Output file name",None),ParSet("method","s","Interpolation method",'weight',["average","weight","minimum","maximum","closest","furthest"])],
    'opt': [ParValue("clobber","b","Remove outfile if it already exists",False),ParRange("verbose","i","Tool verbosity",0,0,5)],
    }


parinfo['dmimgpm'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output Poisson mean",None)],
    'opt': [ParValue("expfile","f","Exposure file",None),ParValue("outexpfile","f","Output Exposure file",None),ParValue("maxbin","i","Maximum bin in histogram",49),ParValue("xhalf","i","X axis half-width",64),ParValue("yhalf","i","Y axis half-width",64),ParValue("clobber","b","clobber old outputs",False),ParRange("verbose","i","tool verbosity",0,0,5)],
    }


parinfo['dmimgproject'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None),ParSet("axis","s","Axis to project along",'y',["x","y"])],
    'opt': [ParRange("verbose","i","Tool verbosity",0,0,0),ParValue("clobber","b","Clobber existing output?",False)],
    }


parinfo['dmimgreproject'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input table file name",None),ParValue("imgfile","f","Input image to match",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParSet("method","s","Interpolation method",'weight',["weight","closest","furthest","min","max","first","last"]),ParRange("verbose","i","Tool verbosity",0,0,0),ParValue("clobber","b","Clobber existing output?",False)],
    }


parinfo['dmimgthresh'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset/block specification",None)],
    'opt': [ParValue("expfile","f","Exposure map file",None),ParValue("cut","s","Threshold value",None),ParValue("value","r","Replacement value",0.0),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['dmjoin'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file",None),ParValue("joinfile","f","Input join file",None),ParValue("outfile","f","Output file",None),ParValue("join","s","Join col",None)],
    'opt': [ParSet("interpolate","s","Interpolate mode",'linear',["linear","first","last","closest","furthest","minimum","maximum"]),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber",False)],
    }


parinfo['dmkeypar'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("keyword","s","Keyword to retrieve",None)],
    'opt': [ParValue("echo","b","Print keyword value to screen?",False),ParValue("exist","b","Keyword existence",False),ParValue("value","s","Keyword value",None),ParValue("rval","r","Keyword value -- real",None),ParValue("ival","i","Keyword value -- integer",None),ParValue("sval","s","Keyword value -- string",None),ParValue("bval","b","Keyword value -- boolean",False),ParSet("datatype","s","Keyword data type",'null',["string","real","integer","boolean","null"]),ParValue("unit","s","Keyword unit",None),ParValue("comment","s","Keyword comment",None)],
    }


parinfo['dmlist'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("opt","s","Option",'data')],
    'opt': [ParValue("outfile","f","Output file (optional)",None),ParValue("rows","s","Range of table rows to print (min:max)",None),ParValue("cells","s","Range of array indices to print (min:max)",None),ParRange("verbose","i","Debug Level(0-5)",0,0,5)],
    }


parinfo['dmmakepar'] = {
    'istool': True,
    'req': [ParValue("input","f","input file",None),ParValue("output","f","output parameter file or STDOUT",None)],
    'opt': [ParValue("template","f","template file",None),ParSet("case","s","output keyword case",'lower',["upper","lower","same"]),ParRange("verbose","i","verbose mode",0,0,5),ParValue("clobber","b","overwrite existing output file",False)],
    }


parinfo['dmmakereg'] = {
    'istool': True,
    'req': [ParValue("region","s","Input region string",None),ParValue("outfile","f","Output virtual filename",None)],
    'opt': [ParValue("append","b","Create or Append",False),ParSet("kernel","s","Output file format type",'fits',["FITS","fits","ASCII","ascii"]),ParValue("wcsfile","f","File with coordinate mapping",'none'),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber existing file (in create mode)",False)],
    }


parinfo['dmmaskbin'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image to be binned",None),ParValue("maskfile","f","Binning mask",None),ParValue("outfile","f","Output file",None)],
    'opt': [ParValue("errfile","f","Input error file to compute SNR",None),ParValue("snrfile","f","Output SNR file",None),ParRange("verbose","i","Tool chatter level",0,0,0),ParValue("clobber","b","Remove files if they exist?",False)],
    }


parinfo['dmmaskfill'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input table with data to be filled from",None),ParValue("maskfile","f","Masked image to be filled",None),ParValue("outfile","f","Output file",None)],
    'opt': [ParRange("verbose","i","Tool chatter level",0,0,0),ParValue("clobber","b","Remove files if they exist?",False)],
    }


parinfo['dmmerge'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset name",None)],
    'opt': [ParValue("outBlock","s","Output block name(1st blkname to be duplicated)",None),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("columnList","s","Column list",None),ParValue("clobber","b","Clobber existing file[y/n]",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['dmnautilus'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output file name",None),ParRange("snr","r","SNR limit",0,0,None)],
    'opt': [ParRange("method","i","Number of subimages required to be above SNR threshold",0,0,4),ParValue("inerrfile","f","Input error on image",None),ParValue("outmaskfile","f","Output mask image",None),ParValue("outsnrfile","f","Output SNR image",None),ParValue("outareafile","f","Output area image",None),ParRange("verbose","i","Tool verbosity",0,0,0),ParValue("clobber","b","Clobber outputs",False)],
    }


parinfo['dmpaste'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("pastefile","f","Input paste file lists",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParValue("clobber","b","clobber existing output",False),ParRange("verbose","i","verbosity of processing comments",0,0,5)],
    }


parinfo['dmradar'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output file name",None),ParRange("snr","r","SNR limit",0,0,None),ParValue("xcenter","r","X coordinate of center of grid (physical pixels)",0),ParValue("ycenter","r","Y coordinate of center of grid (physical pixels)",0)],
    'opt': [ParRange("method","i","Number of subimages required to be above SNR threshold",4,0,4),ParSet("shape","s","Shape of region to use",'pie',["pie","epanda","bpanda","box"]),ParRange("rinner","r","Minimum inner radius (physical pixels)",5,0,None),ParRange("router","r","Outer radius range, (physical pixels)",1000,0,None),ParRange("astart","r","Starting angle, degrees CCW +X axis",0,0,360),ParRange("arange","r","Range of angles, degrees CCW from astart",360,0,360),ParRange("ellipticity","r","Ellipticity of shape (1=circle,0=line)",1,0,1),ParRange("rotang","r","Rotation angle of shape",0,0,360),ParRange("minradius","r","Minimum allowed radius (phys pixels)",0.5,0,None),ParRange("minangle","r","Minimum allowed angle (degrees)",1,0,None),ParValue("inerrfile","f","Input error on image",None),ParValue("outmaskfile","f","Output mask image",None),ParValue("outsnrfile","f","Output SNR image",None),ParValue("outareafile","f","Output area image",None),ParRange("verbose","i","Tool verbosity",0,0,5),ParValue("clobber","b","Clobber outputs",False)],
    }


parinfo['dmreadpar'] = {
    'istool': True,
    'req': [ParValue("input","f","input parameter file",None),ParValue("output","f","output file",None)],
    'opt': [ParValue("template","f","template file",None),ParSet("case","s","output keyword case",'upper',["upper","lower","same"]),ParRange("verbose","i","verbose mode",0,0,5),ParValue("clobber","b","overwrite existing keywords in output file",False)],
    }


parinfo['dmregrid'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Enter output file name",None),ParValue("bin","s","Binning specification",None),ParValue("rotangle","s","CCW rotation angle in degrees about rotation center",'0'),ParValue("rotxcenter","s","x coordinate of rotation center",'0'),ParValue("rotycenter","s","y coordinate of rotation center",'0'),ParValue("xoffset","s","x offset",'0'),ParValue("yoffset","s","y offset",'0'),ParRange("npts","i","Number of points in pixel (0='exact' algorithm)",0,0,999)],
    'opt': [ParSet("coord_sys","s","Coordinate system of bin parameter",'logical',["logical","physical"]),ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['dmregrid2'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParRange("resolution","i","Number of point per side to evaluate",1,0,None),ParSet("method","s","Average value",'sum',["sum","average"]),ParValue("theta","r","Rotation angle (CCW from +X axis)",None),ParValue("rotxcenter","r","Center of rotation in X",None),ParValue("rotycenter","r","Center of rotation in Y",None),ParValue("xoffset","r","Shift in X direction",0),ParValue("yoffset","r","Shift in Y direction",0),ParValue("xscale","r","Scaling in X-direction",1),ParValue("yscale","r","Scaling in Y-direction",1),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("clobber","b","Clobber existing files",False),ParRange("verbose","i","Tool verbosity",0,0,5)],
    }


parinfo['dmsort'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset name",None),ParValue("outfile","f","Output dataset name",None),ParValue("keys","s","Sorted column name",None)],
    'opt': [ParValue("copyall","b","Copy all the blocks?",True),ParValue("clobber","b","Clobber existing file?",False),ParRange("verbose","i","Verbose mode?",0,0,5)],
    }


parinfo['dmstat'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file specification",None)],
    'opt': [ParValue("centroid","b","Calculate centroid if image?",True),ParValue("median","b","Calculate median value?",False),ParValue("sigma","b","Calculate the population standard deviation?",True),ParValue("clip","b","Calculate stats using sigma clipping?",False),ParValue("nsigma","r","Number of sigma to clip",3),ParRange("maxiter","i","Maximum number of iterations",20,1,None),ParRange("verbose","i","Verbosity level",1,0,5),ParValue("out_columns","s","Output Column Label",None),ParValue("out_min","s","Output Minimum Value",None),ParValue("out_min_loc","s","Output Minimum Location Value",None),ParValue("out_max","s","Output Maximum Value",None),ParValue("out_max_loc","s","Output Maximum Location Value",None),ParValue("out_mean","s","Output Mean Value",None),ParValue("out_median","s","Output Median Value",None),ParValue("out_sigma","s","Output Sigma Value",None),ParValue("out_sum","s","Output Sum of Values",None),ParValue("out_good","s","Output Number Good Values",None),ParValue("out_null","s","Output Number Null Values",None),ParValue("out_cnvrgd","s","Converged?",None),ParValue("out_cntrd_log","s","Output Centroid Log Value",None),ParValue("out_cntrd_phys","s","Output Centroid Phys Value",None),ParValue("out_sigma_cntrd","s","Output Sigma Centroid Value",None)],
    }


parinfo['dmtabfilt'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input table file name",None),ParValue("colname","s","Column to smooth",None),ParValue("outfile","f","Output file name",None),ParSet("function","s","Filter function",'peak',["min","max","mean","median","mode","mid","sigma","extreme","unsharp","range","variance","nmode","q25","q33","q67","q75","sum","rclip","peak","valley","count","olympic","pmean","mu3","mu4","jitter","rms","nslope"]),ParValue("mask","s","masking filter",None)],
    'opt': [ParRange("verbose","i","Tool verbosity",0,0,5),ParValue("clobber","b","Clobber existing output?",True)],
    }


parinfo['dmtcalc'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file",None),ParValue("outfile","f","Output file",None),ParValue("expression","s","expression(s) to evaluate",None)],
    'opt': [ParValue("clobber","b","Clobber output file if it exists?",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['dmtype2split'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input type II file",None),ParValue("outfile","f","Enter output file name(s)",None)],
    'opt': [ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['download_obsid_caldb'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outdir","f","Output CALDB directory",'${ASCDS_INSTALL}/CALDB')],
    'opt': [ParValue("background","b","Should the ACIS|HRC background files be downloaded?",False),ParValue("missing","b","Only check for missing CALDB files in outdir/ directory?",False),ParValue("clobber","b","Should existing CALDB data files be downloaded again?",False),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['ecf_calc'] = {
    'istool': True,
    'req': [ParValue("infile","f","input source file",None),ParValue("outfile","f","output FITS table with ECF information",None),ParRange("radius","r","radius of ECF region",20,0,None),ParRange("xpos","r","x-position of extraction center",4096.5,0,None),ParRange("ypos","r","y-position of extraction center",4096.5,0,None),ParRange("binsize","r","pixel binning factor",1.0,0,None),ParValue("fraction","s","ECF to determine radii",'0.01,0.025,0.05,0.075,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.85,0.9,0.95,0.99')],
    'opt': [ParValue("plot","b","show plot of ECF vs. Radius?",False),ParValue("clobber","b","OK to overwrite existing output file?",False)],
    }


parinfo['eff2evt'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outfile","f","Output event file",None)],
    'opt': [ParValue("energy","r","Energy, None = use column in file [eV]",None),ParValue("pbkfile","f","Parameter block file for ACIS dead area",None),ParValue("dafile","f","Dead area file",'CALDB'),ParValue("rmfimg","f","RMF, Must be an image (ie rmfimg output)",None),ParRange("rmfcut","r","RMF probability cutoff",0.01,0,1),ParValue("mirror","s","ARDLIB mirror",'HRMA'),ParValue("detsubsysmod","s","ARDLIB modifier for detector",None),ParValue("ardlibpar","s","ARDLIB parameter name",'ardlib'),ParValue("geompar","s","PIXLIB parameter name",'geom'),ParValue("clobber","b","Remove outfile if it already exists?",False),ParRange("verbose","i","Chatter level",0,0,5)],
    }


parinfo['energy_hue_map'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input counts image",None),ParValue("energymap","f","Input energy map image",None),ParValue("outroot","f","Output directory+root name",None)],
    'opt': [ParSet("colorsys","s","Color system",'hsv',["hsv","hls","hisv"]),ParValue("min_energy","r","Minimum energy value",None),ParValue("max_energy","r","Maximum energy value",None),ParValue("min_counts","r","Minimum counts value",None),ParValue("max_counts","r","Maximum counts value",None),ParSet("energy_scale","s","Energy scaling function",'linear',["linear","log","asinh","sqrt","square"]),ParSet("counts_scale","s","Counts scaling function",'asinh',["linear","log","asinh","sqrt","square"]),ParRange("min_hue","r","Minimum hue",0,0,1),ParRange("max_hue","r","Maximum hue, 0.833=purple",0.833,0,1),ParRange("min_sat","r","Minimum saturation",0,0,1),ParRange("max_sat","r","Maximum saturation",1,0,1),ParRange("contrast","r","Contrast in intensity",1,0,10),ParRange("bias","r","Bias in intensity",0.5,0,1),ParValue("show_plot","b","",False),ParValue("clobber","b","Remove output files if they already exist?",False),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['evalpos'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image files",None),ParValue("ra","s","Input right ascension",None),ParValue("dec","s","Input declination",None)],
    'opt': [ParValue("output","r","Output value (last in stack)",None),ParValue("tmpdir","f","Directory for temp. files",'${ASCDS_WORK_PATH}'),ParRange("verbose","i","Chatter level",0,0,5)],
    }


parinfo['find_chandra_obsid'] = {
    'istool': True,
    'req': [ParValue("arg","s","RA, ObsId, or name of source",None),ParValue("dec","s","Dec of source if arg is not the ObsId/name",None)],
    'opt': [ParRange("radius","r","Radius for search overlap in arcmin",1.0,0,None),ParSet("download","s","What ObsIDs should be downloaded?",'none',["none","ask","all"]),ParSet("instrument","s","Choice of instrument",'all',["all","acis","hrc","acisi","aciss","hrci","hrcs"]),ParSet("grating","s","Choice of grating",'all',["all","none","letg","hetg","any"]),ParSet("detail","s","Columns to display",'basic',["basic","obsid","all"]),ParValue("mirror","s","Use this instead of the CDA FTP site",None),ParRange("verbose","i","Verbose level",1,0,5)],
    }


parinfo['find_mono_energy'] = {
    'istool': True,
    'req': [ParValue("arffile","f","Input ARF file",None),ParValue("rmffile","f","Input RMF file",None),ParValue("model","s","Sherpa model expression",'xsphabs.abs1*xspowerlaw.pwrlaw'),ParValue("paramvals","s","Model parameter values",'pwrlaw.PhoIndex=2.0;abs1.nH=0.1'),ParValue("band","s","Energy band (CSC name, eg soft, or colon separated elo:ehi)",None)],
    'opt': [ParSet("metric","s","Metric used to compute characteristic energy",'mean',["mean","max"]),ParValue("energy","f","Output energy",None),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['flux_obs'] = {
    'istool': True,
    'req': [ParValue("infiles","s","Input events files",None),ParValue("outroot","f","Root of output files",None)],
    'opt': [ParValue("bands","s","Energy bands, comma-separated list, min:max:center in keV or ultrasoft, soft, medium, hard, broad, wide, CSC",'default'),ParValue("xygrid","s","xygrid for output or filename",None),ParRange("maxsize","i","Maximum image width or height in pixels",None,1,None),ParRange("binsize","r","Image binning factor",None,0,None),ParValue("asolfiles","s","Input aspect solutions",None),ParValue("badpixfiles","s","Input bad pixel files",None),ParValue("maskfiles","s","Input mask files",None),ParValue("dtffiles","s","Input dtf files for HRC observations",None),ParSet("units","s","Units for the exposure map",'default',["default","area","time"]),ParValue("expmapthresh","s","Remove low-exposure regions? '2%' excludes pixels where exposure is < 2% of the maximum",'1.5%'),ParSet("background","s","Method for background removal (HRC-I)",'default',["default","time","particle","none"]),ParValue("bkgparams","s","Optional argument for background subtraction",'[pi=300:500]'),ParRange("psfecf","r","If set, create PSF map with this ECF",None,0,1),ParSet("psfmerge","s","How are the PSF maps combined?",'min',["exptime","expmap","min","max","mean","median","mid"]),ParRange("random","i","random seed (0 = use time dependent seed)",0,0,None),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("cleanup","b","Delete intermediary files?",True),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level",1,0,5)],
    }


parinfo['fluximage'] = {
    'istool': True,
    'req': [ParValue("infile","s","Input events file",None),ParValue("outroot","f","Root of output files",None)],
    'opt': [ParValue("bands","s","Energy bands, comma-separated list, min:max:center in keV or ultrasoft, soft, medium, hard, broad, wide, CSC",'default'),ParValue("xygrid","s","xygrid for output or filename",None),ParRange("binsize","r","Image binning factor",None,0,None),ParValue("asolfile","f","Input aspect solutions",None),ParValue("badpixfile","f","Input bad pixel file",None),ParValue("maskfile","f","Input mask file",None),ParValue("dtffile","f","Input dtf file for HRC observations",None),ParSet("units","s","Units for the exposure map",'default',["default","area","time"]),ParValue("expmapthresh","s","Remove low-exposure regions? '2%' excludes pixels where exposure is < 2% of the maximum",'1.5%'),ParSet("background","s","Method for background removal (HRC-I)",'default',["default","time","particle","none"]),ParValue("bkgparams","s","Optional argument for background subtraction",'[pi=300:500]'),ParRange("psfecf","r","If set, create PSF map with this ECF",None,0,1),ParRange("random","i","random seed (0 = use time dependent seed)",0,0,None),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("cleanup","b","Delete intermediary files?",True),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level",1,0,5)],
    }


parinfo['fullgarf'] = {
    'istool': True,
    'req': [ParValue("phafile","f","Input PHA file (Type I or II)",None),ParRange("pharow","i","Row in Type II PHA file (ignored if Type I)",1,0,99),ParValue("evtfile","f","Event file",None),ParValue("asol","f","Aspect offsets file",None),ParValue("engrid","f","Energy grid spec",None),ParValue("dtffile","s","Dead time correction factor; ACIS->evt file; HRC -> dtf file",')evtfile'),ParValue("badpix","f","Bad pixel file; (filename|NONE|CALDB)",None),ParValue("rootname","s","Output rootname",None),ParValue("maskfile","s","NONE, or name of ACIS window mask file",None)],
    'opt': [ParValue("dafile","s","NONE, CALDB, or name of ACIS dead-area calibration file",'CALDB'),ParValue("osipfile","s","NONE or Name of fits file with order sorting info",'CALDB'),ParValue("ardlibqual","s","Additional ardlib qualifiers",None),ParValue("clobber","b","Clobber existing output files? This is passed to ALL child processes.",False),ParRange("verbose","i","Control the level of diagnostic output. 0=>least.",0,0,5)],
    }


parinfo['geom'] = {
    'istool': False,
    'req': [],
    'opt': [ParValue("instruments","s","Instrument geometry ARD",'CALDB'),ParValue("aimpoints","s","Aimpoints ARD",'CALDB'),ParValue("tdet","s","TDET systems ARD",'CALDB'),ParValue("sky","s","SKY systems ARD",'CALDB'),ParValue("shell","s","Grating Shell systems ARD",'CALDB'),ParValue("obsfile","s","file containing start time/date for the CALDB above",None)],
    }


parinfo['get_dither_parameters'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input aspect solution file",None)],
    'opt': [ParSet("method","s","Method to estimate dither parameters",'fold',["fold","fit","fft"]),ParValue("dety_amplitude","r","Amplitude in DETY direction [arcsec]",None),ParValue("detz_amplitude","r","Amplitude in the DETZ direction [arcsec]",None),ParValue("dety_period","r","Period in DETY direction [sec]",None),ParValue("detz_period","r","Period in DETZ direction [sec]",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['get_fov_limits'] = {
    'istool': True,
    'req': [ParValue("infile","f","The FOV file to use",None)],
    'opt': [ParRange("pixsize","r","Pixel size",1,0,None),ParValue("dmfilter","s","DM filter syntax to match FOV file",None),ParValue("xygrid","s","xygrid parameter for mkexpmap to match FOV file",None),ParRange("verbose","i","Debug Level (0-5)",1,0,5)],
    }


parinfo['get_sky_limits'] = {
    'istool': True,
    'req': [ParValue("image","f","Image for which you want to know the binning",None)],
    'opt': [ParRange("precision","i","Precision [# decimal points] for output numbers",1,0,None),ParValue("dmfilter","s","DM filter syntax to match image",None),ParValue("xygrid","s","xygrid parameter for mkexpmap to match image",None),ParRange("verbose","i","Debug Level (0-5)",1,0,5)],
    }


parinfo['get_src_region'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output source region file",None)],
    'opt': [ParValue("binning","s","binning specification [a]:[b][:c] | c",'1'),ParValue("sigma_factor","r","sigma factor",5),ParValue("niter","i","number of iterations",5),ParValue("invert","b","invert region logic",False),ParValue("clobber","b","Clobber output file if it exists?",False),ParRange("verbose","i","Verbosity level (0=none, 5=most)",0,0,5)],
    }


parinfo['glvary'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file specification",None),ParValue("outfile","f","Output: probabilities as a function of m",None),ParValue("lcfile","f","Output: resulting light curve",None),ParValue("effile","f","Input file efficiency factors",None)],
    'opt': [ParValue("probfile","f","Input probability file for background",'NONE'),ParRange("frac","r","Fraction of events to be included in subsample",1.0,0,1),ParRange("seed","i","Seed for random subsample selection",1,None,1),ParRange("mmax","i","Maximum number of model bins",None,None,3600),ParValue("mmin","i","Minimum number of model bins",None),ParRange("nbin","i","Number of bins to use in light curve",0,None,10800),ParValue("mintime","i","Range of binnings, maximum resolution in seconds",50),ParValue("clobber","b","Overwrite output files if they exist?",False),ParRange("verbose","i","Tool chatter level",0,0,0)],
    }


parinfo['gti_align'] = {
    'istool': True,
    'req': [ParValue("times","f","Input GTI file or time filter string",None),ParValue("statfile","f","Input exposure statistics, stat1.fits, file",None),ParValue("outfile","f","Output GTI file",None)],
    'opt': [ParValue("evtfile","f","Event file used to correctly order the per chip GTIs",None),ParValue("clobber","b","Overwrite existing output file if it exists?",False),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['hexgrid'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output hexagon grid image",None),ParRange("sidelen","r","Side length of hexagons",10,3,None)],
    'opt': [ParValue("binimg","f","Output image file",None),ParValue("xref","r","X coordinate of reference point (image coordinates)",0),ParValue("yref","r","Y coordinate of reference point (image coordinates)",0),ParRange("verbose","i","Tool chatter level",0,0,5),ParValue("clobber","b","Remove outfile if it already exists?",False)],
    }


parinfo['hrc_bkgrnd_lookup'] = {
    'istool': True,
    'req': [ParValue("infile","f","The file for which you want a background file",None),ParSet("caltype","s","What type of background file?",'event',["event","spectrum"])],
    'opt': [ParValue("outfile","f","HRC background file to use",None),ParSet("blname","s","What block identifier should be added to the filename?",'none',["none","name","number","cfitsio"]),ParRange("verbose","i","Debug level (0=no debug information)",0,0,5)],
    }


parinfo['hrc_build_badpix'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input (ARD) bad pixel file",'CALDB'),ParValue("outfile","f","Output (Level 1) bad pixel file",None),ParValue("obsfile","f","Input observation parameter file",None),ParValue("degapfile","f","Input degap file (NONE | none | COEFF | <filename>)",'CALDB')],
    'opt': [ParValue("cfu1","r","u axis 1st order cor. factor",1.0),ParValue("cfu2","r","u axis 2nd order cor. factor",0.0),ParValue("cfv1","r","v axis 1st order cor. factor",1.0),ParValue("cfv2","r","v axis 2nd order cor. factor",0.0),ParValue("logfile","f","Output debug log file (<filename>, NONE, STDOUT)",'STDOUT'),ParValue("clobber","b","Overwrite output file(s) if already exists?",False),ParRange("verbose","i","Debug level (0-5)",0,0,5)],
    }


parinfo['hrc_dtfstats'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file",None),ParValue("outfile","f","Output file",None),ParValue("gtifile","f","File containing GTI to filter on (<filename>|NONE)",'NONE')],
    'opt': [ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("maincol","s","Name of the deadtime factor column",'DTF'),ParValue("errcol","s","Name of the deadtime factor error column",'DTF_ERR'),ParValue("chisqlim","r","Limit for the variability test",5),ParValue("clobber","b","Clobber the output file if it exists",False),ParRange("verbose","i","Verbose level.",0,0,5)],
    }


parinfo['hrc_process_events'] = {
    'istool': True,
    'req': [ParValue("infile","f","input level 0 event file/stack",None),ParValue("outfile","f","output level 1 file",None),ParValue("badpixfile","f","bad pixel file ( NONE | none | <filename>)",'NONE'),ParValue("acaofffile","f","aspect offset file ( NONE | none | <filename>)",'NONE')],
    'opt': [ParValue("obsfile","f","obs.par file for output file keywords ( NONE | none | <filename>)",'NONE'),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("do_ratio","b","perform ratio validity checks",True),ParValue("do_amp_sf_cor","b","perform amp_sf correction (y/n) ?",True),ParValue("gainfile","f","gain correction image file ( NONE | none | <filename>)",'CALDB'),ParValue("ADCfile","f","ADC correction table file ( NONE | none | <filename>)",'NONE'),ParValue("degapfile","f","degap factors (NONE | none | COEFF | <filename>)",'CALDB'),ParValue("hypfile","f","Hyperbolic test coefficients file ( NONE | none | <filename>)",'CALDB'),ParValue("ampsfcorfile","f","caldb file for amp_sf_correction( NONE | none | <filename>)",'CALDB'),ParValue("tapfile","f","tap ring test coefficients file ( NONE | none | <filename>)",'CALDB'),ParValue("ampsatfile","f","ADC saturation test file ( NONE | none | <filename>)",'CALDB'),ParValue("evtflatfile","f","Event flatness test file ( NONE | none | <filename>)",'CALDB'),ParValue("badfile","f","output level 1 bad event file",'lev1_bad_evts.fits'),ParValue("logfile","f","debug log file (STDOUT | stdout | <filename>)",'stdout'),ParValue("eventdef","s","output format definition",')stdlev1'),ParValue("badeventdef","s","output format definition",')badlev1'),ParRange("grid_ratio","r","charge ratio",0.5,0,1),ParRange("pha_ratio","r","pha ratio",0.5,0,1),ParValue("wire_charge","i","turn on center wire test (-1=off,0=on)",0),ParValue("cfu1","r","u axis 1st order cor. factor",1.0),ParValue("cfu2","r","u axis 2nd order cor. factor",0.0),ParValue("cfv1","r","v axis 1st order cor. factor",1.0),ParValue("cfv2","r","v axis 2nd order cor. factor",0.0),ParValue("amp_gain","r","amp gain",75.0),ParRange("rand_seed","i","random seed (for pixlib), 0 = use time dependent seed",1,0,32767),ParSet("rand_pix_size","r","pixel randomization width (-size..+size), 0.0=no randomization",0.0,[0,0.5]),ParSet("start","s","start transformations at",'coarse',["coarse","chip","tdet"]),ParSet("stop","s","end transformations at",'sky',["none","chip","tdet","det","sky"]),ParValue("stdlev1","s","event format definition string",'{d:time,s:crsv,s:crsu,s:amp_sf,s:av1,s:av2,s:av3,s:au1,s:au2,s:au3,l:raw,s:chip,l:tdet,f:det,f:sky,f:samp,s:pha,s:pi,s:sumamps,s:chip_id,x:status}'),ParValue("badlev1","s","event format definition string",'{d:time,s:crsu,s:crsv,s:au1,s:au2,s:au3,s:av1,s:av2,s:av3,f:samp,s:pha}'),ParValue("hsilev1","s","event format definition string",'{d:time,s:crsu,s:crsv,s:au1,s:au2,s:au3,s:av1,s:av2,s:av3,s:chipx,s:chipy,s:tdetx,s:tdety,s:x,s:y,l:fpz,f:samp,s:pha,s:vstat,s:estat}'),ParValue("simlev1","s","sim event definition string",'{l:tick,i:scifr,i:mjf,s:mnf,s:evtctr,s:crsu,s:crsv,s:au1,s:au2,s:au3,s:av1,s:av2,s:av3,s:tdetx,s:tdety,f:samp,s:pha,s:vstat,s:estat}'),ParValue("fltlev1","s","event format definition string",'{d:time,s:crsv,s:crsu,s:amp_sf,s:av1,s:av2,s:av3,s:au1,s:au2,s:au3,s:chipx,s:chipy,l:tdetx,l:tdety,s:detx,s:dety,s:x,s:y,f:samp,s:pha,s:sumamps,s:chip_id,l:status}'),ParValue("clobber","b","Overwrite output event file if it already exists?",False),ParRange("verbose","i","level of debug detail (0=none, 5=most)",0,0,5)],
    }


parinfo['imagej_lut'] = {
    'istool': False,
    'req': [],
    'opt': [ParValue("amber","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/amber.lut'),ParValue("auxctq","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/auxctq.lut'),ParValue("blue_orange","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/blue_orange.lut'),ParValue("blue_orange_icb","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/blue_orange_icb.lut'),ParValue("brain","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/brain.lut'),ParValue("brgbcmyw","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/brgbcmyw.lut'),ParValue("cells","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cells.lut'),ParValue("cequal","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cequal.lut'),ParValue("cmy-cyan","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cmy-cyan.lut'),ParValue("cmy-magneta","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cmy-magneta.lut'),ParValue("cmy-yellow","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cmy-yellow.lut'),ParValue("cmy","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cmy.lut'),ParValue("cold","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cold.lut'),ParValue("cti_ras","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/cti_ras.lut'),ParValue("edges","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/edges.lut'),ParValue("gem-16","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/gem-16.lut'),ParValue("gem-256","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/gem-256.lut'),ParValue("gold","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/gold.lut'),ParValue("gyr_centre","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/gyr_centre.lut'),ParValue("heart","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/heart.lut'),ParValue("hue","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/hue.lut'),ParValue("hue_ramps_08","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/hue_ramps_08.lut'),ParValue("hue_ramps_16","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/hue_ramps_16.lut'),ParValue("icool","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/icool.lut'),ParValue("iman","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/iman.lut'),ParValue("invert_gray","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/invert_gray.lut'),ParValue("isocontour","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/isocontour.lut'),ParValue("log_down","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/log_down.lut'),ParValue("log_up","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/log_up.lut'),ParValue("mixed","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/mixed.lut'),ParValue("neon-blue","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/neon-blue.lut'),ParValue("neon-green","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/neon-green.lut'),ParValue("neon-magenta","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/neon-magenta.lut'),ParValue("neon-red","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/neon-red.lut'),ParValue("pastel","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pastel.lut'),ParValue("rgb-blue","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/rgb-blue.lut'),ParValue("rgb-green","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/rgb-green.lut'),ParValue("rgb-red","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/rgb-red.lut'),ParValue("royal","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/royal.lut'),ParValue("sepia","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/sepia.lut'),ParValue("siemens","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/siemens.lut'),ParValue("smart","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/smart.lut'),ParValue("split_blackblue_redwhite","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/split_blackblue_redwhite.lut'),ParValue("split_blackwhite_ge","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/split_blackwhite_ge.lut'),ParValue("split_blackwhite_warmmetal","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/split_blackwhite_warmmetal.lut'),ParValue("split_bluered_warmmetal","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/split_bluered_warmmetal.lut'),ParValue("system_lut","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/system_lut.lut'),ParValue("thal_16","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/thal_16.lut'),ParValue("thal_256","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/thal_256.lut'),ParValue("thallium","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/thallium.lut'),ParValue("topography","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/topography.lut'),ParValue("unionjack","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/unionjack.lut'),ParValue("vivid","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vivid.lut'),ParValue("warhol","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/warhol.lut')],
    }


parinfo['imgmoment'] = {
    'istool': True,
    'req': [ParValue("infile","s","Input image",None)],
    'opt': [ParValue("x_mu","r","X-centroid",None),ParValue("y_mu","r","Y-centroid",None),ParValue("m_0_0","r","0th moment",None),ParValue("m_0_1","r","M_0_1 moment",None),ParValue("m_1_0","r","M_1_0 moment",None),ParValue("m_1_1","r","M_1_1 moment",None),ParValue("m_0_2","r","M_0_2 moment",None),ParValue("m_2_0","r","M_2_0 moment",None),ParValue("m_1_2","r","M_1_2 moment",None),ParValue("m_2_1","r","M_2_1 moment",None),ParValue("m_2_2","r","M_2_2 moment",None),ParValue("phi","r","Angle from moment",None),ParValue("eccen","r","Eccentricity from moment",None),ParValue("xsig","r","1 sigma in X axis after rotation by phi",None),ParValue("ysig","r","1 sigma in Y axis after rotation by phi",None)],
    }


parinfo['lim_sens'] = {
    'istool': True,
    'req': [ParValue("infile","f","Enter background file name",None),ParValue("psffile","f","Enter PSF file name",None),ParValue("outfile","f","Enter output file name",None)],
    'opt': [ParValue("expfile","f","Exposure file",None),ParValue("rbkfile","f","Random background map name",None),ParValue("bscale","i","alpha * Es value",5),ParValue("snr_limit","r","Signal to Noise ratio",3),ParValue("const_r","b","Use a constant background ratio (bscale^2 - 1)?",False),ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['lut'] = {
    'istool': False,
    'req': [],
    'opt': [ParValue("a","s","Color lookup table",'${ASCDS_CALIB}/a.lut'),ParValue("aips","s","Color lookup table",'${ASCDS_CALIB}/aips.lut'),ParValue("b","s","Color lookup table",'${ASCDS_CALIB}/b.lut'),ParValue("bb","s","Color lookup table",'${ASCDS_CALIB}/bb.lut'),ParValue("blue","s","Color lookup table",'${ASCDS_CALIB}/blue.lut'),ParValue("color","s","Color lookup table",'${ASCDS_CALIB}/color.lut'),ParValue("cool","s","Color lookup table",'${ASCDS_CALIB}/cool.lut'),ParValue("green","s","Color lookup table",'${ASCDS_CALIB}/green.lut'),ParValue("grey","s","Color lookup table",'${ASCDS_CALIB}/grey.lut'),ParValue("halley","s","Color lookup table",'${ASCDS_CALIB}/halley.lut'),ParValue("heaob","s","Color lookup table",'${ASCDS_CALIB}/heaob.lut'),ParValue("heat","s","Color lookup table",'${ASCDS_CALIB}/heat.lut'),ParValue("hsv","s","Color lookup table",'${ASCDS_CALIB}/hsv.lut'),ParValue("i8","s","Color lookup table",'${ASCDS_CALIB}/i8.lut'),ParValue("rainbow1","s","Color lookup table",'${ASCDS_CALIB}/rainbow1.lut'),ParValue("rainbow2","s","Color lookup table",'${ASCDS_CALIB}/rainbow2.lut'),ParValue("ramp","s","Color lookup table",'${ASCDS_CALIB}/ramp.lut'),ParValue("red","s","Color lookup table",'${ASCDS_CALIB}/red.lut'),ParValue("sls","s","Color lookup table",'${ASCDS_CALIB}/sls.lut'),ParValue("staircase","s","Color lookup table",'${ASCDS_CALIB}/staircase.lut'),ParValue("standard","s","Color lookup table",'${ASCDS_CALIB}/standard.lut')],
    }


parinfo['make_instmap_weights'] = {
    'istool': True,
    'req': [ParValue("outfile","f","Instrument map weighting file",None),ParValue("model","s","Sherpa model definition string",None),ParValue("paramvals","s","';' delimited string of (parameter=value) pairs",None),ParRange("emin","r","Energy range lower bound for flux (keV)",None,0,None),ParValue("emax","r","Energy range upper bound for flux (keV)",None),ParValue("ewidth","r","Energy bin-size for flux (keV)",None)],
    'opt': [ParSet("abund","s","set XSpec solar abundance",'angr',["angr","feld","aneb","grsa","wilm","lodd"]),ParSet("xsect","s","set XSpec photoelectric cross-section",'vern',["bcmc","obcm","vern"]),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level?",3,0,5)],
    }


parinfo['make_psf_asymmetry_region'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset",None),ParValue("outfile","f","Output region file name",None),ParRange("x","r","X coordinate of source (SKY)",None,0.5,65536.5),ParRange("y","r","Y coordinate of source (SKY)",None,0.5,65535.5)],
    'opt': [ParSet("format","s","Format for output region file",'ciao',["ciao","ds9"]),ParValue("display","b","Display infile with region in ds9?",False),ParRange("verbose","i","Screen verbosity",1,0,5),ParValue("clobber","b","Clobber existing file?",False)],
    }


parinfo['map2reg'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input map image",None),ParValue("outfile","f","Output region file",None)],
    'opt': [ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use (None:use all available)",None),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove output file if it already exists?",False)],
    }


parinfo['mean_energy_map'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input ACIS event file",None),ParValue("outfile","f","Output image file name",None),ParRange("binsize","r","Image binning size",None,0,None)],
    'opt': [ParValue("pbkfile","f","Parameter block filename for dead area calibration",None),ParValue("tmpdir","f","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParRange("verbose","i","Tool chatter",0,0,5),ParValue("clobber","b","Removing existing files?",False)],
    }


parinfo['merge_obs'] = {
    'istool': True,
    'req': [ParValue("infiles","s","Input events files",None),ParValue("outroot","f","Root of output files",None)],
    'opt': [ParValue("bands","s","Energy bands, comma-separated list, min:max:center in keV or ultrasoft, soft, medium, hard, broad, wide, CSC",'default'),ParValue("xygrid","s","xygrid for output or filename",None),ParRange("maxsize","i","Maximum image width or height in pixels",None,1,None),ParRange("binsize","r","Image binning factor",None,0,None),ParValue("asolfiles","s","Input aspect solutions",None),ParValue("badpixfiles","s","Input bad pixel files",None),ParValue("maskfiles","s","Input mask files",None),ParValue("dtffiles","s","Input dtf files for HRC observations",None),ParValue("refcoord","s","Reference coordinates or evt2 file",None),ParSet("units","s","Units for the exposure map",'default',["default","area","time"]),ParValue("expmapthresh","s","Remove low-exposure regions? '2%' excludes pixels where exposure is < 2% of the maximum",'1.5%'),ParSet("background","s","Method for background removal (HRC-I)",'default',["default","time","particle","none"]),ParValue("bkgparams","s","Optional argument for background subtraction",'[pi=300:500]'),ParRange("psfecf","r","If set, create PSF map with this ECF",None,0,1),ParSet("psfmerge","s","How are the PSF maps combined?",'min',["exptime","expmap","min","max","mean","median","mid"]),ParRange("random","i","random seed (0 = use time dependent seed)",0,0,None),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("cleanup","b","Delete intermediary files?",True),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level",1,0,5)],
    }


parinfo['merge_too_small'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input map",None),ParValue("outfile","f","Output map",None)],
    'opt': [ParSet("method","s","Apply minval threshold to area of region or counts in region?",'counts',["counts","area"]),ParValue("imgfile","f","Input counts image file, required for method=counts",None),ParValue("binimg","f","Optional output image file",None),ParRange("minvalue","i","Minimum counts or area (logical pixels)",0,0,None),ParRange("verbose","i","Tool chatter level",0,0,5),ParValue("clobber","b","Remove outfile if it already exists?",False)],
    }


parinfo['mkacisrmf'] = {
    'istool': True,
    'req': [ParValue("infile","f","scatter/rsp matrix file",' '),ParValue("outfile","f","RMF output file",' '),ParValue("wmap","f","WMAP file",' '),ParValue("energy","s","energy grid in keV (lo:hi:bin)",' '),ParValue("channel","s","channel grids in pixel (min:max:bin)",' '),ParSet("chantype","s","channel type",'PI',["PI","PHA"]),ParRange("ccd_id","i","filter CCD-ID",None,0,9),ParValue("chipx","i","filter chipx in pixel",None),ParValue("chipy","i","filter chipy in pixel",None),ParValue("gain","f","gain file",'CALDB')],
    'opt': [ParValue("asolfile","f","aspect solution file or a stack of asol files",None),ParValue("obsfile","f","obs file",')wmap'),ParValue("logfile","f","log file",None),ParValue("contlvl","i","# contour level",100),ParValue("geompar","f","pixlib geometry parameter file",'geom'),ParRange("thresh","r","low threshold of energy cut-off probability",1e-06,0,None),ParValue("clobber","b","overwrite existing output file (yes|no)?",False),ParRange("verbose","i","verbosity level (0 = no display)",0,0,5)],
    }


parinfo['mkarf'] = {
    'istool': True,
    'req': [ParValue("asphistfile","f","Aspect Histogram File",None),ParValue("outfile","f","Output File Name",None),ParValue("sourcepixelx","r","Source X Pixel",None),ParValue("sourcepixely","r","Source Y Pixel",None),ParValue("engrid","f","Energy grid spec",None),ParValue("obsfile","s","Name of fits file with obs info (evt file -- include extension)",None),ParValue("pbkfile","s","NONE, or the name of the parameter block file",None),ParValue("detsubsys","s","Detector Name",None),ParSet("grating","s","Grating for zeroth order ARF",'NONE',["NONE","LETG","HETG"]),ParValue("maskfile","s","NONE, or name of ACIS window mask file",'NONE'),ParRange("verbose","i","Verbosity",0,0,5)],
    'opt': [ParValue("dafile","s","NONE, CALDB, or name of ACIS dead-area calibration file",'CALDB'),ParValue("mirror","s","Mirror Name",'HRMA'),ParValue("ardlibparfile","s","name of ardlib parameter file",'ardlib.par'),ParValue("geompar","s","Parameter file for Pixlib Geometry files",'geom'),ParValue("clobber","b","Overwrite existing files?",False)],
    }


parinfo['mkexpmap'] = {
    'istool': True,
    'req': [ParValue("asphistfile","f","Aspect Histogram File",None),ParValue("outfile","f","Output File Name",None),ParValue("instmapfile","f","Name of Instrument Map",None),ParValue("xygrid","s","grid specification syntax x0:x1:#nx,x0:x1:ny",None),ParValue("useavgaspect","b","Use Average Aspect Pointing",False)],
    'opt': [ParValue("normalize","b","Normalize exposure map by exposure time",True),ParValue("geompar","s","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Verbosity",0,0,5),ParValue("clobber","b","Overwrite existing files?",False)],
    }


parinfo['mkgarf'] = {
    'istool': True,
    'req': [ParValue("asphistfile","f","Aspect Histogram File (include extension)",None),ParValue("outfile","f","Output File Name",None),ParValue("order","i","Enter Grating order",1),ParValue("sourcepixelx","r","Source X Pixel",None),ParValue("sourcepixely","r","Source Y Pixel",None),ParValue("engrid","f","Energy grid spec",None),ParValue("obsfile","s","Name of fits file with obs info (include extension)",None),ParValue("osipfile","s","NONE or Name of fits file with order sorting info",'CALDB'),ParValue("maskfile","s","NONE, or name of ACIS window mask file",'NONE'),ParValue("detsubsys","s","Detector Name",None),ParSet("grating_arm","s","Enter Grating Arm",None,["HEG","MEG","LEG"]),ParValue("pbkfile","s","NONE, or the name of the parameter block file",None)],
    'opt': [ParValue("mirror","s","Mirror Name",'hrma'),ParValue("dafile","s","NONE, CALDB, or name of ACIS dead-area calibration file",'CALDB'),ParValue("ardlibparfile","s","name of ardlib parameter file",'ardlib.par'),ParValue("geompar","s","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Verbosity",0,0,5),ParValue("clobber","b","Overwrite existing files?",False)],
    }


parinfo['mkgrmf'] = {
    'istool': True,
    'req': [ParValue("outfile","f","Output File Name",None),ParValue("wvgrid_arf","s","Enter ARF side wavelength grid [angstroms]",'compute'),ParValue("wvgrid_chan","s","Enter channel-side wavelength grid [angstroms]",'compute'),ParValue("order","i","Enter Grating order",1),ParValue("obsfile","s","Name of fits file with obs info",None),ParValue("regionfile","s","File containing extraction region",None),ParValue("srcid","i","SrcID",1),ParValue("detsubsys","s","Detector Name (e.g., ACIS-S3)",None),ParSet("grating_arm","s","Enter Grating Arm",None,["HEG","MEG","LEG","NONE"])],
    'opt': [ParValue("threshold","r","Enter RMF threshold",1e-06),ParValue("diagonalrmf","b","Compute diagonal RMF?",False),ParValue("ardlibparfile","s","name of ardlib parameter file",'ardlib.par'),ParValue("geompar","s","Parameter file for Pixlib Geometry files",'geom'),ParValue("mirror","s","Mirror Name",'HRMA'),ParRange("verbose","i","Verbosity",0,0,5),ParValue("clobber","b","Overwrite existing files?",True)],
    }


parinfo['mkinstmap'] = {
    'istool': True,
    'req': [ParValue("outfile","f","Output File Name",None),ParValue("spectrumfile","s","Energy Spectrum File (see docs)",'NONE'),ParRange("monoenergy","r","Energy for mono-chromatic map [keV]",1,0.1,10),ParValue("pixelgrid","s","Pixel grid specification x0:x1:#nx,y0:y1:#ny",None),ParValue("obsfile","s","Name of fits file + extension with obs info",None),ParValue("detsubsys","s","Detector Name",None),ParSet("grating","s","Grating for zeroth order ARF",'NONE',["NONE","LETG","HETG"]),ParValue("maskfile","s","NONE, or name of ACIS window mask file",'NONE'),ParValue("pbkfile","s","NONE, or the name of the parameter block file",None)],
    'opt': [ParValue("mirror","s","Mirror Name",'HRMA'),ParValue("dafile","s","NONE, CALDB, or name of ACIS dead-area calibration file",'CALDB'),ParValue("ardlibparfile","s","name of ardlib parameter file",'ardlib.par'),ParValue("geompar","s","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Verbosity",0,0,5),ParValue("clobber","b","Overwrite existing files?",False)],
    }


parinfo['mkpsfmap'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output image file name",None),ParValue("energy","r","Energy of PSF to lookup [keV]",None),ParValue("spectrum","f","Spectrum file [keV vs weight] if energy=None",None),ParRange("ecf","r","ECF of PSF to lookup",None,0,1)],
    'opt': [ParValue("psffile","f","PSF Calibration file",'CALDB'),ParSet("units","s","Units of output image",'arcsec',["arcsec","logical","physical"]),ParValue("geompar","f","Pixlib geometry file",'geom.par'),ParValue("clobber","b","Clobber files?",False)],
    }


parinfo['mkregmap'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file",None),ParValue("regions","f","Input stack of regions",None),ParValue("outfile","f","Output map file",None)],
    'opt': [ParValue("binimg","f","Output binned image",None),ParValue("coord","s","Image coodinate name",'sky'),ParValue("clobber","b","Remove outfile if it already exists?",False),ParRange("verbose","i","Tool chatter level",1,0,5)],
    }


parinfo['mkrmf'] = {
    'istool': True,
    'req': [ParValue("infile","f","name of FEF input file",None),ParValue("outfile","f","name of RMF output file",None),ParValue("axis1","s","axis-1(name=lo:hi:btype)",None),ParValue("axis2","s","axis-2(name=lo:hi:btype)",None)],
    'opt': [ParValue("logfile","f","name of log file",'STDOUT'),ParValue("weights","f","name of weight file",None),ParRange("thresh","r","low threshold of energy cut-off probability",1e-5,0,None),ParValue("outfmt","s","RMF output format (legacy|cxc)",'legacy'),ParValue("clobber","b","overwrite existing output file (yes|no)?",False),ParRange("verbose","i","verbosity level (0 = no display)",0,0,5),ParValue("axis3","s","axis-3(name=lo:hi:btype)",'none'),ParValue("axis4","s","axis-4(name=lo:hi:btype)",'none'),ParValue("axis5","s","axis-5(name=lo:hi:btype)",'none')],
    }


parinfo['mktgresp'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input type-II PHA file",None),ParValue("evtfile","f","Input event file",None),ParValue("outroot","f","Output root name for RMF and ARF files",None)],
    'opt': [ParValue("orders","s","Input list of grating orders (None uses values in infile",'INDEF'),ParValue("wvgrid_arf","s","Enter ARF side wavelength grid [angstroms]",'compute'),ParValue("wvgrid_chan","s","Enter channel-side wavelength grid [angstroms]",'compute'),ParValue("asolfile","f","Input aspect solution file(s)",None),ParValue("bpixfile","f","Input bad pixel list",None),ParValue("mskfile","f","Input detector mask file",None),ParValue("dtffile","f","Input dead time factors file (HRC only)",None),ParValue("dafile","f","Input dead area calibration file",'CALDB'),ParValue("osipfile","f","Input order sorting calibration file",'CALDB'),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use (None:use all available)",None),ParRange("verbose","i","Tool chatter",1,0,5),ParValue("clobber","b","Clobber existing files?",False)],
    }


parinfo['mkwarf'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input detector WMAP",None),ParValue("outfile","f","Output weighted ARF file",None),ParValue("weightfile","f","Output FEF weights",None),ParValue("spectrumfile","f","Input Spectral weighting file (<filename>|NONE)",None),ParValue("egridspec","s","Output energy grid [kev]",None),ParValue("pbkfile","f","Parameter block file",None)],
    'opt': [ParRange("threshold","r","Percent threshold cut for FEF regions",0,0,1),ParValue("feffile","f","FEF file",'CALDB'),ParValue("mskfile","f","Mask file",None),ParValue("asolfile","f","Stack of aspect solution files",None),ParValue("mirror","s","ARDLIB Mirror specification",'HRMA'),ParValue("detsubsysmod","s","Detector sybsystem modifier",None),ParValue("dafile","f","Dead area file",'CALDB'),ParValue("ardlibpar","f","Parameter file for ARDLIB files",'ardlib'),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("clobber","b","Clobber existing outputs",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['modelflux'] = {
    'istool': True,
    'req': [ParValue("arf","f","Ancillary Response File (ARF)",None),ParValue("rmf","f","Response File (RMF)",None),ParValue("model","s","Sherpa model definition string",None),ParValue("paramvals","s","';' delimited string of (parameter=value) pairs",None),ParValue("emin","r","Energy range lower bound for flux (keV)",None),ParValue("emax","r","Energy range upper bound for flux (keV)",None)],
    'opt': [ParValue("absmodel","s","Absorption model for calculating unabsorbed flux",None),ParValue("absparams","s","';' delimited string of (parameter=value) pairs for absorption model used to calculate unabsorbed flux",None),ParValue("abund","s","XSPEC abundance table (if relevant to absorption model)",'angr'),ParValue("oemin","r","Energy range lower bound for rate (keV), default=emin",None),ParValue("oemax","r","Energy range upper bound for rate (keV), default=emax",None),ParValue("rate","r","count rate in counts s^-1, default=1.0",1.0),ParValue("pflux","r","photon flux in energy range in photon cm^-2 s^-1",None),ParValue("flux","r","energy flux in energy range in erg cm^-2 s^-1",None),ParValue("urate","r","Unabsorbed count rate in counts s^-1 (if absmodel defined)",None),ParValue("upflux","r","Unabsorbed photon flux in energy range in photon cm^-2 s^-1 (if absmodel defined)",None),ParValue("uflux","r","Unabsorbed energy flux in energy range in erg cm^-2 s^-1 (if absmodel defined)",None),ParSet("opt","s","input type: (use this to determine the others)",'rate',["rate","flux","pflux"]),ParRange("verbose","i","verbosity setting",1,0,5)],
    }


parinfo['monitor_photom'] = {
    'istool': True,
    'req': [ParValue("infile","f","ACA image data file",None),ParValue("outfile","f","Output light curve",None)],
    'opt': [ParValue("dark_ratio","r","Dark ratio",0.005),ParValue("min_dark_limit","r","Minimum warm pixel dark current",80.0),ParValue("min_dark_meas","i","Minimum warm pixel measurements",10),ParValue("max_dither_motion","i","Maximum possible dither motion (pixels)",10),ParRange("verbose","i","Amount of tool chatter",0,0,5),ParValue("clobber","b","Remove output file if it already exists?",False)],
    }


parinfo['mtl_build_gti'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input MTL file",None),ParValue("outfile","f","Output GTI file",None),ParValue("mtlfile","f","Output smoothed/filtered MTL file",None)],
    'opt': [ParValue("userlimit","s","Optional user defined limit string",None),ParValue("lkupfile","f","Lookup table defining which MTL columns to check against (NONE|none|<filename>)",'${ASCDS_CALIB}/gti_test.fits'),ParValue("smooth","b","Smooth the input MTL data?",True),ParValue("clobber","b","Clobber output file if it exists?",False),ParRange("verbose","i","Debug level",0,0,5)],
    }


parinfo['multi_chip_gti'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file to match GTI order",None),ParValue("i0_gti","f","GTI file for ACIS-I0 (CCD_ID=0)",None),ParValue("i1_gti","f","GTI file for ACIS-I1 (CCD_ID=1)",None),ParValue("i2_gti","f","GTI file for ACIS-I2 (CCD_ID=2)",None),ParValue("i3_gti","f","GTI file for ACIS-I3 (CCD_ID=3)",None),ParValue("s0_gti","f","GTI file for ACIS-S0 (CCD_ID=4)",None),ParValue("s1_gti","f","GTI file for ACIS-S1 (CCD_ID=5)",None),ParValue("s2_gti","f","GTI file for ACIS-S2 (CCD_ID=6)",None),ParValue("s3_gti","f","GTI file for ACIS-S3 (CCD_ID=7)",None),ParValue("s4_gti","f","GTI file for ACIS-S4 (CCD_ID=8)",None),ParValue("s5_gti","f","GTI file for ACIS-S5 (CCD_ID=9)",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParValue("tmpdir","f","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParRange("verbose","i","Tool chatter",1,0,5),ParValue("clobber","b","Overwrite existing output file?",False)],
    }


parinfo['obsid_search_csc'] = {
    'istool': True,
    'req': [ParValue("obsid","s","Chandra Observation ID",None),ParValue("outfile","f","Name of output table (TSV format)",None)],
    'opt': [ParValue("columns","s","List of columns to include",'INDEF'),ParSet("download","s","Download data products for which sources?",'none',["none","ask","all"]),ParValue("root","f","Output root for data products",'./'),ParValue("bands","s","Comma separated list of CSC band names taken from broad, soft, medium, hard, ultrasoft, wide. Blank retrieves all",'broad,wide'),ParValue("filetypes","s","Comma separated list of CSC filetypes.  Blank retrieves all",'regevt,pha,arf,rmf,lc,psf,regexp'),ParSet("catalog","s","Version of catalog",'csc2',["csc2","csc1","current"]),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove existing outfile if it exists?",False)],
    }


parinfo['pathfinder'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output map image",None)],
    'opt': [ParValue("minval","r","Minimum pixel value to consider in input image.",0),ParSet("direction","s","Directions to follow gradient",'diagonal',["diagonal","perpendicular"]),ParValue("debugreg","f","Diagnostic region file",None),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove output file if it already exists?",False)],
    }


parinfo['pfold'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file",None),ParValue("outfile","f","Output file",None),ParValue("periodgrid","s","Grid to search for periods",None)],
    'opt': [ParValue("dtffile","f","Dead-time factor/efficiency",None),ParValue("pdot","r","Periods derivative",None),ParValue("nphase","i","Number of phase bins",10),ParValue("tzero","r","Time of zero-phase",None),ParValue("clobber","b","Remove existing output files",False)],
    }


parinfo['pileup_map'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input counts image",None),ParValue("outfile","f","Output pileup image",None)],
    'opt': [ParValue("clobber","b","Remove existing output?",False),ParRange("verbose","i","Tool chatter",0,0,5)],
    }


parinfo['psf_contour'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file or image",None),ParValue("outroot","f","Output directory and root filename",None),ParValue("pos","s","Position: coordinate or input file with columns RA and DEC",None)],
    'opt': [ParSet("method","s","Region creating algorithm",'contour',["contour","lasso","fitted_ellipse","ecf_ellipse","convex_hull"]),ParRange("energy","r","Monochromatic energy to simulate PSF",1.0,0.3,10),ParRange("fraction","r","Target fraction of the PSF to include",0.9,0.6,0.95),ParRange("tolerance","r","Tolerance on fraction",0.01,0.0001,0.1),ParRange("flux","r","Photon flux to simulate",0.01,1e-07,0.01),ParValue("fovfile","f","Input field of view file",None),ParValue("marx_root","f","Directory where MARX is installed",'${MARX_ROOT}'),ParValue("random_seed","i","PSF random seed, -1: current time",-1),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use (None:use all available)",None),ParRange("verbose","i","Amount of tool chatter",1,0,5),ParValue("clobber","b","Delete output file if it already exists?",False)],
    }


parinfo['psf_project_ray'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("outfile","f","Output pseudo-event file",None),ParValue("evtfile","f","Reference Event List",None)],
    'opt': [ParSet("detector","s","Detect configuration",'ACIS-I',["ACIS-I","ACIS-S","HRC-I","HRC-S"]),ParValue("asolfile","f","Aspect solution file, needed if simulated dither",None),ParValue("simx","r","Over-ride SIM X location",None),ParValue("simy","r","Over-ride SIM Y location",None),ParValue("simz","r","Over-ride SIM Z location",None),ParValue("defocus","r","Amount of defocus",0),ParRange("xblur","r","Amount to Gaussian blur x-positions [arcsec]",0,0,None),ParRange("yblur","r","Amount to Gaussian blur y-positions [arcsec]",')xblur',0,None),ParRange("ablur","r","Rotation angle for Gaussian blur [deg]",0,-90,90),ParSet("blur_coord","s","Coordinate system to apply blur",'sky',["sky","det"]),ParValue("lcfile","f","Light-curve file used to generate times",None),ParValue("randseed","r","Random seed",0),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("ardlibpar","f","Parameter file for ARDLIB files",'ardlib.par'),ParValue("detsubsysmod","s","Detector sybsystem modifier",'BPMASK=0'),ParValue("clobber","b","Clobber existing file",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['psfsize_srcs'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image or event file",None),ParValue("pos","s","Input position:  either filename or ra,dec",None),ParValue("outfile","f","Output table",None)],
    'opt': [ParValue("energy","s","Monochromatic energy to use in PSF lookup [keV]",'broad'),ParRange("ecf","r","Encircled counts fraction (psf fraction)",0.9,0,1),ParValue("psffile","f","REEF Caldb filename",'CALDB'),ParRange("verbose","i","Tool chatter level",0,0,5),ParValue("clobber","b","Removing existing files?",False)],
    }


parinfo['r4_header_update'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file.  File is modified in place",None)],
    'opt': [ParValue("pbkfile","f","Parameter block filename.  If blank will try to locate from infile",None),ParValue("asolfile","f","Aspect solution file(s).  If blank will try to locate from infile",None),ParRange("verbose","i","Amount of tool chatter",0,0,5)],
    }


parinfo['rank_roi'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file",None),ParValue("roifiles","f","Stack of ROI files",None),ParValue("outfile","f","Output file name temple, must include {:04d}",None)],
    'opt': [ParSet("method","s","Metric to use to assign overlap area",'max',["max","min","big","small","bright","faint"]),ParValue("clobber","b","OK to overwrite existing output files?",False),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['readout_bkg'] = {
    'istool': True,
    'req': [ParValue("indir","f","Input directory; should contain primary/ and secondary/ subdirs",None),ParValue("outfile","f","Output background file",None)],
    'opt': [ParValue("tmpdir","f","Temporary directory",'${ASCDS_WORK_PATH}'),ParRange("random","i","Random seed, 0=clock time",0,0,None),ParValue("check_vf_pha","b","Clean ACIS background in VFAINT data?",False),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove existing output file?",False)],
    }


parinfo['reg2tgmask'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input ds9 region file",None),ParValue("srcfile","f","Input original FITS region file",'CALDB'),ParValue("outfile","f","Output FITS region file",None)],
    'opt': [ParValue("clobber","b","Clobber existing output if it exists?",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['regphystocel'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input region file in physical coordinates",None),ParValue("outfile","f","Output ds9 format region file in celestial coordinates",None)],
    'opt': [ParValue("wcsfile","f","Image or event file with WCS if not in infile",None),ParValue("text","s","Column or keyword to use for region title",None),ParValue("tag","s","Columns or keywords to use for region tags",None),ParValue("clobber","b","Remove outfile if it already exists?",False),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['reproject_aspect'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file with duplicate srcs",None),ParValue("refsrcfile","f","Input file with reference srcs",None),ParValue("updfile","f","Either input asol file, or file with WCS to be updated",None),ParValue("outfile","f","Output asol file",None)],
    'opt': [ParValue("wcsfile","f","Input file with WCS used in transform",None),ParRange("radius","r","radius used to match sources (arcsec)",12,0,None),ParRange("residlim","r","src pairs with residuals > residlim are dropped (arcsec)",2,0,None),ParRange("residfac","r","src pairs with residuals > residfac * position error are dropped",0,0,None),ParRange("residtype","i","residfac applies to: (0) each residual, (1) avg residuals",0,0,1),ParSet("method","s","reproject method: rot/scale/trans (rst) or translate (trans)",'rst',["rst","trans"]),ParValue("logfile","f","debug log file ( STDOUT | stdout | <filename>)",'STDOUT'),ParValue("clobber","b","Overwrite existing output dataset with same name?",False),ParRange("verbose","i","debug level (0-5)",0,0,5)],
    }


parinfo['reproject_events'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset/block specification",None),ParValue("match","f","Match file",'none')],
    'opt': [ParValue("aspect","f","Aspect file",None),ParValue("random","i","random seed (0 use time, -1 no randomize)",-1),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['reproject_image'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("matchfile","f","Reference image",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParRange("resolution","i","Number of point per side to evaluate",1,0,None),ParSet("method","s","Average value",'sum',["sum","average"]),ParSet("coord_sys","s","Coordinate system to match images in",'world',["world","logical","physical"]),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("clobber","b","Clobber existing files",False),ParRange("verbose","i","Tool verbosity",0,0,5)],
    }


parinfo['reproject_image_grid'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image file name",None),ParValue("outfile","f","Output file name",None),ParRange("xsize","i","X-Size of output image in image pixels",1,1,None),ParRange("ysize","i","Y-Size of output image in image pixels",1,1,None),ParValue("xcenter","s","X-Center of image in coord_sys",None),ParValue("ycenter","s","Y-Center of image in coord_sys",None),ParRange("theta","r","Angle between world coord north and output y axis",0,0,360),ParValue("pixelsize","s","Pixel size",None)],
    'opt': [ParRange("resolution","i","Number of point per side to evaluate",1,0,None),ParSet("method","s","Average value",'sum',["sum","average"]),ParSet("coord_sys","s","Coordinate system to match images in",'world',["world","logical","physical"]),ParValue("lookupTab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("clobber","b","Clobber existing files",False),ParRange("verbose","i","Tool verbosity",0,0,5)],
    }


parinfo['reproject_obs'] = {
    'istool': True,
    'req': [ParValue("infiles","f","Input events files",None),ParValue("outroot","f","Root of output files",None)],
    'opt': [ParValue("asolfiles","f","Input aspect solutions",None),ParValue("merge","b","Merge event files?",True),ParValue("refcoord","s","Reference coordinates or evt2 file",None),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use",None),ParValue("linkfiles","b","Link (rather than copy) files?",True),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level",1,0,5)],
    }


parinfo['rmfimg'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input dataset/block specification",None),ParValue("outfile","f","Output dataset/block specification",None)],
    'opt': [ParValue("arf","f","ARF file (optional)",None),ParValue("arfout","f","ARF output image (may be blank)",None),ParValue("product","b","Multiply RMF and ARF in output",False),ParRange("verbose","i","Debug Level(0-5)",0,0,5),ParValue("clobber","b","Clobber existing file",False)],
    }


parinfo['roi'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input src list",None),ParValue("fovregion","s","Input field of view region",None),ParValue("streakregion","s","Input streak region",None),ParValue("outsrcfile","f","Output source list",None),ParSet("radiusmode","s","Background radius computation method",'mul',["add","mul","area"]),ParRange("bkgradius","r","Background radius",3,0,None)],
    'opt': [ParSet("group","s","Make 1 srcregion per group or per individual source",'group',["group","individual","exclude"]),ParSet("targetbkg","s","Make background around all sources or just target?",'all',["all","target"]),ParValue("srcfactor","r","Amount added or multipled by to expand excluded overlapping source region",0),ParSet("srcfunction","s","Add srcfactor or multiply srcfactor?",'add',["add","mul"]),ParValue("bkgfactor","r","Amount added or multipled by to expand src region excluded from bkg region",0),ParSet("bkgfunction","s","Add bkgfactor or multiply bkgfactor?",'add',["add","mul"]),ParSet("bkgfactarg","s","Apply bkgfactor to all srcs in bkg or just to target?",'target',["all","target"]),ParRange("maxpix","i","Maximum number of pixels when intersecting",None,1,None),ParRange("fovres","r","Pixellation resulolution for fov check",1,0,1),ParRange("streakres","r","Pixellation resulolution for streak check",0.25,0,1),ParValue("ignore_streaksrc","b","Ignore streak region for source list ?",True),ParValue("compute_conf","b","Compute the various confused states between the sources and backgrounds",True),ParValue("evtfile","f","Event File (# counts per region)",None),ParValue("num_srcs","i","Number of sources output",None),ParValue("clobber","b","Remove existing output files?",False),ParRange("verbose","i","tool verbosity",0,0,0)],
    }


parinfo['search_csc'] = {
    'istool': True,
    'req': [ParValue("pos","s","Input position.  RA, Dec, eg: 246.59955,-24.415158 or name, M81",None),ParRange("radius","r","Search radius [default: arcmin]",0,0,60),ParValue("outfile","f","Name of output table (TSV format)",None)],
    'opt': [ParSet("radunit","s","Units of search radius",'arcmin',["arcmin","arcsec","deg"]),ParValue("columns","s","List of columns to return",'INDEF'),ParValue("sensitivity","b","Retrieve Limiting sensitivity for each energy band?",False),ParSet("download","s","Download data products for which sources?",'none',["none","ask","all"]),ParValue("root","f","Output root for data products",'./'),ParValue("bands","s","Comma separated list of CSC band names taken from broad, soft, medium, hard, ultrasoft, wide. Blank retrieves all",'broad,wide'),ParValue("filetypes","s","Comma separated list of CSC filetypes.  Blank retrieves all",'regevt,pha,arf,rmf,lc,psf,regexp'),ParSet("catalog","s","Version of catalog",'csc2',["csc2","csc1","current"]),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove existing outfile if it exists?",False)],
    }


parinfo['simulate_psf'] = {
    'istool': True,
    'req': [ParValue("infile","f","Event or Image file",None),ParValue("outroot","f","Output root name",None),ParRange("ra","r","Right Asscension of source [deg]",0,0,360),ParRange("dec","r","Declination of source [deg]",0,-90,90),ParValue("spectrumfile","f","3 column spectrum file [kev vs. photon/cm^2/sec]",None)],
    'opt': [ParRange("monoenergy","r","Monochromatic energy [keV]",None,0,10),ParValue("flux","r","Flux value for spectrum or monochromatic energy",None),ParSet("simulator","s","Which tool to simulate HRMA?",'marx',["marx","file"]),ParValue("rayfile","f","Use existing rays file",None),ParSet("projector","s","Which tool to project",'marx',["marx","psf_project_ray"]),ParRange("random_seed","i","PSF random seed, -1: current time",-1,-1,1073741824),ParRange("blur","r","Blur (marx.AspectBlur or psf_project_ray.xblur) [arcsec]",0.07,0,None),ParValue("readout_streak","b","MARX Simulate readout streak (ACIS)",False),ParValue("pileup","b","MARX Run pileup module (ACIS)",False),ParValue("ideal","b","Should MARX use idealized detectors (QE=1) be used?",True),ParValue("extended","b","Should MARX detectors be extended beyond their physical edges?",True),ParRange("binsize","r","Image bin size [pix]",1,0,None),ParRange("numsig","r","Number of sigma to make image",7,1,None),ParValue("minsize","i","Minimum image size [pix]",None),ParRange("numiter","i","Number of simulations to combine together",1,1,None),ParRange("numrays","i","Number of rays to simulate",None,0,None),ParValue("keepiter","b","Keep files from each iteration?",False),ParValue("asolfile","f","Aspect solution file: blank=autofind, none=omit",None),ParValue("marx_root","f","Directory where MARX is installed",'${MARX_ROOT}'),ParRange("verbose","i","Chatter level of tool",1,0,5)],
    }


parinfo['sky2tdet'] = {
    'istool': True,
    'req': [ParValue("infile","s","Input image in sky (x,y) coordinates",None),ParValue("asphistfile","s","Input aspect histogram file",None),ParValue("outfile","s","Output TDET  WMAP file",None)],
    'opt': [ParRange("bin","i","Binning factor",1,1,None),ParValue("geompar","s","Pixlib geometry file",'geom'),ParRange("verbose","i","Verbosity",0,0,5),ParValue("clobber","b","Remove existing files?",False)],
    }


parinfo['skyfov'] = {
    'istool': True,
    'req': [ParValue("infile","f","Name of input file, event list, image fits, or obi par file",None),ParValue("outfile","f","Name of output file",None)],
    'opt': [ParValue("logfile","f","Name of log file",'STDOUT'),ParValue("kernel","s","Output file format, ASCII or FITS",'FITS'),ParValue("mskfile","f","Mask file to retain active windows of chips",None),ParValue("aspect","f","Aspect file or a stack of aspect file list",None),ParValue("geompar","f","Pixlib geometry parameter file",'geom'),ParSet("method","s","Two methods that estimate the dither range.",'minmax',["minmax","convexhull"]),ParValue("clobber","b","Overwrite existing outfile (yes|no)?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['specextract'] = {
    'istool': True,
    'req': [ParValue("infile","f","Source event file(s)",None),ParValue("outroot","f","Output directory path + root name for output files",None)],
    'opt': [ParValue("bkgfile","f","Background event file(s)",None),ParValue("asp","f","Source aspect solution or histogram file(s)",None),ParValue("dtffile","s","Input DTF files for HRC observations",None),ParValue("mskfile","f","Maskfile (input to mkwarf)",None),ParValue("rmffile","f","rmffile input for CALDB",'CALDB'),ParValue("badpixfile","f","Bad pixel file for the observation",None),ParValue("dafile","f","Dead area file (input to mkwarf)",'CALDB'),ParValue("bkgresp","b","Create background ARF and RMF?",True),ParValue("weight","b","Should response files be weighted?",True),ParValue("weight_rmf","b","Should RMF also be weighted?",False),ParSet("resp_pos","s","Unweighted response position determination method",'REGION',["MAX","CENTROID","REGEXTENT","REGION"]),ParValue("refcoord","s","RA and Dec of responses?",None),ParValue("correctpsf","b","Apply point source aperture correction to ARF?",False),ParValue("combine","b","Combine ungrouped output spectra and responses?",False),ParValue("readout_streakspec","b","Is the source extraction region for the ACIS readout streak?",False),ParSet("grouptype","s","Spectrum grouping type (same as grouptype in dmgroup)",'NUM_CTS',["NONE","BIN","SNR","NUM_BINS","NUM_CTS","ADAPTIVE","ADAPTIVE_SNR","BIN_WIDTH","MIN_SLOPE","MAX_SLOPE","BIN_FILE"]),ParValue("binspec","s","Spectrum grouping specification (NONE,1:1024:10,etc)",'15'),ParSet("bkg_grouptype","s","Background spectrum grouping type (NONE, BIN, SNR, NUM_BINS, NUM_CTS, or ADAPTIVE)",'NONE',["NONE","BIN","SNR","NUM_BINS","NUM_CTS","ADAPTIVE"]),ParValue("bkg_binspec","s","Background spectrum grouping specification (NONE,10,etc)",None),ParValue("energy","s","Energy grid",'0.3:11.0:0.01'),ParValue("channel","s","RMF binning attributes",'1:1024:1'),ParValue("energy_wmap","s","Energy range for (dmextract) WMAP input to mkacisrmf",'300:2000'),ParValue("binarfcorr","s","Detector pixel binnning factor for (arfcorr) to determine size and scale of PSF to derive aperture corrections at each energy step.",'1'),ParValue("binwmap","s","Binning factor for (dmextract) WMAP input to mkacisrmf",'tdet=8'),ParValue("binarfwmap","s","Binning factor for (sky2tdet) WMAP input to mkwarf",'1'),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Debug Level(0-5)",1,0,5)],
    }


parinfo['splitobs'] = {
    'istool': True,
    'req': [ParValue("indir","f","Input obsid level directory",None),ParValue("outroot","f","Output directory root name",')indir')],
    'opt': [ParRange("verbose","i","Tool Chatter",1,0,5),ParValue("clobber","b","Remove and overwrite files if they already exist?",False)],
    }


parinfo['src_psffrac'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image or event file",None),ParValue("region","s","Input circular region",None),ParValue("outfile","f","Output table",None)],
    'opt': [ParValue("energy","s","Monochromatic energy to use in PSF lookup [keV]",'broad'),ParValue("psffile","f","REEF Caldb filename",'CALDB'),ParRange("verbose","i","Tool chatter level",0,0,5),ParValue("clobber","b","Removing existing files?",False)],
    }


parinfo['srcextent'] = {
    'istool': True,
    'req': [ParValue("srcfile","f","Source file, FITS image or FITS events list",None),ParValue("outfile","f","Output file, FITS table",None),ParValue("psffile","f","PSF file, FITS image or FITS events list (optional)",None),ParValue("regfile","f","Region File, ellipse or circle, in FITS or ASCII (required for events list)",None)],
    'opt': [ParValue("shape","s","source shape [gaussian,disk]",'gaussian'),ParValue("x0","r","estimate of x-position [sky]",None),ParValue("y0","r","estimate of y-position [sky]",None),ParValue("srcsize","r","crude estimate of source size [arcseconds]. -1 => use theta approximation.",-1),ParRange("theta","r","off-axis angle to get approx psf size as estimate of source size [arcminutes]",0,0,55),ParValue("imgsize","r","size of image [arcseconds]",0),ParValue("binfactor","i","image binning factor",0),ParValue("mincounts","i","minimum counts threshold inside ellipse",15),ParValue("minthresh","i","minimum counts threshold for source file",6),ParValue("sigmafactor","r","ratio of desired sigma to wavdetect guess e.g. 1.6/3.0",0.533),ParValue("psfblur","r","Additional aspect blur to add in quadrature to PSF ellipse axes size (ACIS-only)",0.1873),ParValue("clobber","b","clobber output file",False),ParRange("verbose","i","verbosity setting",3,0,5)],
    }


parinfo['srcflux'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("pos","s","Input source position: filename or RA,Dec",None),ParValue("outroot","f","Output root name",None)],
    'opt': [ParValue("bands","s","Energy bands",'default'),ParSet("regions","s","Method to determine regions",'simple',["simple","optimized","user"]),ParValue("srcreg","f","Stack of source regions",None),ParValue("bkgreg","f","Stack of background regions",None),ParValue("bkgresp","b","Create background ARF and RMF?",True),ParSet("psfmethod","s","PSF calibration method",'ideal',["ideal","psffile","arfcorr","quick","marx"]),ParValue("psffile","f","Input psf image",None),ParRange("conf","r","Confidence interval",0.9,0,1),ParRange("binsize","r","Image bin sizes",1,0,None),ParValue("rmffile","f","RMF file, if blank or none will be created with specextract",None),ParValue("arffile","f","ARF file, if blank or none will be created with specextract",None),ParValue("model","s","Sherpa model definition string",'xspowerlaw.pow1'),ParValue("paramvals","s","';' delimited string of (parameter=value) pairs",'pow1.PhoIndex=2.0'),ParValue("absmodel","s","Absorption model for calculating unabsorbed flux",'xsphabs.abs1'),ParValue("absparams","s","';' delimited string of (parameter=value) pairs for absorption model used to calculate unabsorbed flux",'abs1.nH=%GAL%'),ParSet("abund","s","set XSpec solar abundance",'angr',["angr","feld","aneb","grsa","wilm","lodd"]),ParValue("pluginfile","f","User plugin file name",None),ParValue("fovfile","f","Field of view file",None),ParValue("asolfile","f","Aspect solution file(s)",None),ParValue("mskfile","f","Mask file",None),ParValue("bpixfile","f","Bad pixel file",None),ParValue("dtffile","f","Live Time Correction List Files for HRC",None),ParValue("ecffile","f","REEF calibration file",'CALDB'),ParValue("marx_root","f","Directory where MARX is installed",'${MARX_ROOT}'),ParValue("parallel","b","Run processes in parallel?",True),ParValue("nproc","i","Number of processors to use",None),ParValue("tmpdir","s","Directory for temporary files",'${ASCDS_WORK_PATH}'),ParValue("random_seed","i","PSF random seed, -1: current time",-1),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level",1,0,5)],
    }


parinfo['sso_freeze'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file or stack",None),ParValue("scephemfile","f","Input spacecraft ephemeris file",None),ParValue("ssoephemfile","f","Input solar system object file",None),ParValue("outfile","f","Output event file name",None)],
    'opt': [ParValue("asolfile","f","Input aspect solution file",None),ParValue("ocsolfile","f","Output asol in OC coordinates",None),ParValue("logfile","f","debug log file ( STDOUT | stdout | <filename>)",'STDOUT'),ParValue("scale","r","Image pixel scale (km/pixel, 0=angular coords)",0),ParValue("lookuptab","f","lookup table",'${ASCDS_CALIB}/dmmerge_header_lookup.txt'),ParValue("clobber","b","Overwrite existing output dataset with same name?",False),ParRange("verbose","i","debug level (0-5)",0,0,5)],
    }


parinfo['statmap'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("mapfile","f","Input map file",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParValue("column","s","Column name to compute statistics",'energy'),ParSet("statistic","s","Which statistic to compute?",'median',["median","mean","min","max","sum","count"]),ParValue("xcolumn","s","Column to use for the X-coordinate",'x'),ParValue("ycolumn","s","Column to use for the Y-coordinate",'y'),ParValue("clobber","b","Remove output file if it already exists?",False),ParRange("verbose","i","Amount of tool chatter",1,0,5)],
    }


parinfo['stk_build'] = {
    'istool': True,
    'req': [ParValue("infile","f","Stack to expand",None),ParValue("outfile","f","Output file name",None)],
    'opt': [ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['stk_count'] = {
    'istool': True,
    'req': [ParValue("infile","f","Stack to expand",None)],
    'opt': [ParValue("count","s","Number of elements in stack",None),ParValue("echo","b","Print stack count value to screen?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['stk_read_num'] = {
    'istool': True,
    'req': [ParValue("infile","f","Stack to expand",None),ParValue("num","i","Number of stack element to read",1)],
    'opt': [ParValue("outelement","s","Name of num'th element in stack",None),ParValue("echo","b","Print name of element to screen?",False),ParRange("verbose","i","Verbosity level",0,0,5)],
    }


parinfo['stk_where'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("match","s","Match this value",None)],
    'opt': [ParValue("simple","b","Simple exact string match, no=regular-expressions",True),ParValue("case","b","Case-insenstive search?",False),ParValue("echo","b","Print output result to screen",False),ParRange("verbose","i","Tool chatter level",0,0,5),ParValue("outnum","i","Output position matched in stack",None),ParValue("outcount","i","Output number of matches in stack",0)],
    }


parinfo['symmetrize'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input L2 HRC-S/LETG event list file",None),ParValue("outfile","f","Output file",None)],
    'opt': [ParValue("sfile","f","Symmetry correction file",'${ASCDS_CONTRIB}/data/eefracIDEAL09.symm78corr'),ParRange("verbose","i","Debug level",0,0,5),ParValue("clobber","b","Clobber outfile if it already exists?",False)],
    }


parinfo['tg_choose_method'] = {
    'istool': True,
    'req': [ParValue("infile","f","Required input 'src1a' file name, as produced by tg_findzo",None)],
    'opt': [ParSet("method","s","Output of selected program's name: tgdetect or tg_findzo",'unknown',["tgdetect","tg_findzo","unknown","none"]),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['tg_create_mask'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file or stack",None),ParValue("outfile","f","Output region file or stack",None),ParValue("input_pos_tab","f","Input table with zero order positions or stack",None),ParSet("grating_obs","s","Observed grating type (header_value|HETG|HEG|MEG|LETG)",'header_value',["HETG","HEG","MEG","LETG","header_value","HEADER_VALUE"]),ParRange("sA_zero_x","r","Source A - x position of zero order",1,1,65536),ParRange("sA_zero_y","r","Source A - y position of zero order",1,1,65536),ParRange("sB_zero_x","r","Source B - x position of zero order",1,1,65536),ParRange("sB_zero_y","r","Source B - y position of zero order",1,1,65536),ParRange("sC_zero_x","r","Source C - x position of zero order",1,1,65536),ParRange("sC_zero_y","r","Source C - y position of zero order",1,1,65536),ParRange("sD_zero_x","r","Source D - x position of zero order",1,1,65536),ParRange("sD_zero_y","r","Source D - y position of zero order",1,1,65536),ParRange("sE_zero_x","r","Source E - x position of zero order",1,1,65536),ParRange("sE_zero_y","r","Source E - y position of zero order",1,1,65536),ParRange("sF_zero_x","r","Source F - x position of zero order",1,1,65536),ParRange("sF_zero_y","r","Source F - y position of zero order",1,1,65536),ParRange("sG_zero_x","r","Source G - x position of zero order",1,1,65536),ParRange("sG_zero_y","r","Source G - y position of zero order",1,1,65536),ParRange("sH_zero_x","r","Source H - x position of zero order",1,1,65536),ParRange("sH_zero_y","r","Source H - y position of zero order",1,1,65536),ParRange("sI_zero_x","r","Source I - x position of zero order",1,1,65536),ParRange("sI_zero_y","r","Source I - y position of zero order",1,1,65536),ParRange("sJ_zero_x","r","Source J - x position of zero order",1,1,65536),ParRange("sJ_zero_y","r","Source J - y position of zero order",1,1,65536)],
    'opt': [ParValue("input_psf_tab","f","Calibration file with mirror psf vs off-axis angle",'CALDB'),ParSet("detector","s","Detector type: ACIS | HRC-I | HRC-S | header_value",'header_value',["header_value","ACIS","HRC-I","HRC-S"]),ParRange("radius_factor_zero","r","A scale factor which multiplies the app. calculation of the one-sigma zero order radius",50,1,400),ParRange("width_factor_hetg","r","A scale factor which multiplies the one-sigma width of the heg/meg mask in the cross-dispersion direction",35,1,200),ParRange("width_factor_letg","r","A scale factor which multiplies the one-sigma width of the letg mask in the cross-dispersion direction",300,1,300),ParRange("r_astig_max_hetg","r","Max grating r coord (deg, along the dispersion) for HETG astigmatism calc",0.5600000000000001,0,2),ParRange("r_astig_max_letg","r","Max grating r coord (deg, along the dispersion) for LETG astigmatism calc",1.1,0,4),ParRange("r_mask_max_hetg","r","Max grating r coord (deg) for HETG mask (to support offset pointing)",0.992,0,2),ParRange("r_mask_max_letg","r","Max grating r coordinate (deg) for LETG mask (to support offset pointing)",2.1,0,4),ParValue("use_user_pars","b","Use the user defined mask parameters below: yes or no?",False),ParSet("last_source_toread","s","Last source name to be read; character A->J.",'A',["A","B","C","D","E","F","G","H","I","J"]),ParRange("sA_id","i","Source A - source id number",1,1,32767),ParRange("sA_zero_rad","r","Source A - radius of zero order mask",None,0,16384),ParRange("sA_width_heg","r","Source A - width of heg mask in sky pixels",None,0,16384),ParRange("sA_width_meg","r","Source A - width of meg mask in sky pixels",None,0,16384),ParRange("sA_width_leg","r","Source A - width of leg mask in sky pixels",None,0,16384),ParRange("sB_id","i","Source B - source id number",2,1,32767),ParRange("sB_zero_rad","r","Source B - radius of zero order mask",None,0,16384),ParRange("sB_width_heg","r","Source B - width of heg mask in sky pixels",None,0,16384),ParRange("sB_width_meg","r","Source B - width of meg mask in sky pixels",None,0,16384),ParRange("sB_width_leg","r","Source B - width of leg mask in sky pixels",None,0,16384),ParRange("sC_id","i","Source C - source id number",3,1,32767),ParRange("sC_zero_rad","r","Source C - radius of zero order mask",None,0,16384),ParRange("sC_width_heg","r","Source C - width of heg mask in sky pixels",None,0,16384),ParRange("sC_width_meg","r","Source C - width of meg mask in sky pixels",None,0,16384),ParRange("sC_width_leg","r","Source C - width of leg mask in sky pixels",None,0,16384),ParRange("sD_id","i","Source D - source id number",4,1,32767),ParRange("sD_zero_rad","r","Source D - radius of zero order mask",None,0,16384),ParRange("sD_width_heg","r","Source D - width of heg mask in sky pixels",None,0,16384),ParRange("sD_width_meg","r","Source D - width of meg mask in sky pixels",None,0,16384),ParRange("sD_width_leg","r","Source D - width of leg mask in sky pixels",None,0,16384),ParRange("sE_id","i","Source E - source id number",5,1,32767),ParRange("sE_zero_rad","r","Source E - radius of zero order mask",None,0,16384),ParRange("sE_width_heg","r","Source E - width of heg mask in sky pixels",None,0,16384),ParRange("sE_width_meg","r","Source E - width of meg mask in sky pixels",None,0,16384),ParRange("sE_width_leg","r","Source E - width of leg mask in sky pixels",None,0,16384),ParRange("sF_id","i","Source F - source id number",6,1,32767),ParRange("sF_zero_rad","r","Source F - radius of zero order mask",None,0,16384),ParRange("sF_width_heg","r","Source F - width of heg mask in sky pixels",None,0,16384),ParRange("sF_width_meg","r","Source F - width of meg mask in sky pixels",None,0,16384),ParRange("sF_width_leg","r","Source F - width of leg mask in sky pixels",None,0,16384),ParRange("sG_id","i","Source G - source id number",7,1,32767),ParRange("sG_zero_rad","r","Source G - radius of zero order mask",None,0,16384),ParRange("sG_width_heg","r","Source G - width of heg mask in sky pixels",None,0,16384),ParRange("sG_width_meg","r","Source G - width of meg mask in sky pixels",None,0,16384),ParRange("sG_width_leg","r","Source G - width of leg mask in sky pixels",None,0,16384),ParRange("sH_id","i","Source H - source id number",8,1,32767),ParRange("sH_zero_rad","r","Source H - radius of zero order mask",None,0,16384),ParRange("sH_width_heg","r","Source H - width of heg mask in sky pixels",None,0,16384),ParRange("sH_width_meg","r","Source H - width of meg mask in sky pixels",None,0,16384),ParRange("sH_width_leg","r","Source H - width of leg mask in sky pixels",None,0,16384),ParRange("sI_id","i","Source I - source id number",9,1,32767),ParRange("sI_zero_rad","r","Source I - radius of zero order mask",None,0,16384),ParRange("sI_width_heg","r","Source I - width of heg mask in sky pixels",None,0,16384),ParRange("sI_width_meg","r","Source I - width of meg mask in sky pixels",None,0,16384),ParRange("sI_width_leg","r","Source I - width of leg mask in sky pixels",None,0,16384),ParRange("sJ_id","i","Source J - source id number",10,1,32767),ParRange("sJ_zero_rad","r","Source J - radius of zero order mask",None,0,16384),ParRange("sJ_width_heg","r","Source J - width of heg mask in sky pixels",None,0,16384),ParRange("sJ_width_meg","r","Source J - width of meg mask in sky pixels",None,0,16384),ParRange("sJ_width_leg","r","Source J - width of leg mask in sky pixels",None,0,16384),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Verbose level: 0 - no output, 5 - max verbosity",0,0,5),ParValue("clobber","b","Clobber existing outfile?",False)],
    }


parinfo['tg_findzo'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outfile","f","Output source table file",None)],
    'opt': [ParValue("zo_pos_x","s","Initial guess for sky-x position (default=pixel(ra_targ))",'default'),ParValue("zo_pos_y","s","Initial guess for sky-y position (default=pixel(dec_targ))",'default'),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['tg_resolve_events'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outfile","f","Output event file",None),ParValue("regionfile","f","Input region file",None),ParValue("acaofffile","f","Input aspect offset file",None)],
    'opt': [ParValue("logfile","f","Output log (NONE|<filename>|stdout)",'stdout'),ParValue("osipfile","f","Lookup table for order resolving (for acis data only)",'CALDB'),ParRange("osort_lo","r","Order-sorting lower bound fraction; order > m - osort_lo",0.3,0,0.5),ParRange("osort_hi","r","Order-sorting high bound fraction; order <= m + osort_hi",0.3,0,0.5),ParSet("grating_obs","s","Observed grating type (header_value|HETG|HEG|MEG|LETG)",'header_value',["HETG","HEG","MEG","LETG","header_value","HEADER_VALUE"]),ParSet("detector","s","Detector type: ACIS | HRC-I | HRC-S | header_value",'header_value',["ACIS","HRC-I","HRC-S","header_value","HEADER_VALUE"]),ParRange("energy_lo_adj","r","Lower Energy limit factor",1.0,0,10),ParRange("energy_hi_adj","r","Upper Energy limit factor",1.0,0,10),ParRange("rand_seed","i","Random seed (for pixlib), 0 = use time dependent seed",1,0,32767),ParSet("rand_pix_size","r","pixel randomization width (-size..+size), 0.0 = no randomization",0,[0,0.5]),ParValue("eventdef","s","Output format definition",')stdlev1_ACIS'),ParValue("stdlev1","s","",')eventdef'),ParValue("stdlev1_ACIS","s","ACIS event format definition string",'{d:time,i:expno,f:rd,s:chip,s:tdet,f:det,f:sky,s:ccd_id,l:pha,s:pi,f:energy,s:grade,s:fltgrade,s:node_id,s:tg_m,f:tg_lam,f:tg_mlam,s:tg_srcid,s:tg_part,s:tg_smap,x:status}'),ParValue("stdlev1_HRC","s","HRC event format definition string",'{d:time,s:crsu,s:crsv,s:amp_sf,l:raw,f:samp,s:av1,s:av2,s:av3,s:au1,s:au2,s:au3,s:sumamps,f:rd,s:chip,l:tdet,f:det,f:sky,s:chip_id,s:pha,s:pi,s:tg_m,f:tg_lam,f:tg_mlam,s:tg_srcid,s:tg_part,s:tg_smap,x:status}'),ParValue("cclev1a","s","Lev1.5 CC faint event format definition string",'{d:time,d:time_ro,l:expno,s:ccd_id,s:node_id,s:chip,f:chipy_tg,f:chipy_zo,s:tdet,f:det,f:sky,f:sky_1d,s:phas,l:pha,l:pha_ro,f:energy,l:pi,s:fltgrade,s:grade,f:rd,s:tg_m,f:tg_lam,f:tg_mlam,s:tg_srcid,s:tg_part,s:tg_smap,x:status}'),ParValue("ccgrdlev1a","s","lev1.5 cc graded event format definition string",'{d:time,d:time_ro,l:expno,s:ccd_id,s:node_id,s:chip,f:chipy_tg,f:chipy_zo,s:tdet,f:det,f:sky,f:sky_1d,l:pha,l:pha_ro,s:corn_pha,f:energy,l:pi,s:fltgrade,s:grade,f:rd,s:tg_m,f:tg_lam,f:tg_mlam,s:tg_srcid,s:tg_part,s:tg_smap,x:status}'),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParRange("verbose","i","Verbosity level of detail (0=none, 5=most)",0,0,5),ParValue("clobber","b","Clobber outfile if it already exists?",False)],
    }


parinfo['tgdetect'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input L1 event file",None),ParValue("OBI_srclist_file","f","Input source position(s) file from previous OBI or NONE",'NONE'),ParValue("outfile","f","Output source position(s) file name",None)],
    'opt': [ParValue("temproot","s","Path and root file name to be given to temporary files",None),ParValue("keeptemp","b","Keep temporary files?",False),ParValue("keepexit","b","Keep exit status file?",False),ParValue("zo_pos_x","s","Center GZO filter sky X position (default=pixel(ra_nom))",'default'),ParValue("zo_pos_y","s","Center GZO filter sky Y position (default=pixel(dec_nom))",'default'),ParValue("zo_sz_filt_x","s","Size of GZO filter in X pixels (ACIS=400; HRC=1800)",'default'),ParValue("zo_sz_filt_y","s","Size of GZO filter in Y pixels (ACIS=400; HRC=1800)",'default'),ParRange("snr_thresh","r","SNR threshold to select the detected sources",40,3,10000),ParValue("spectrum","f","Spectrum file [keV vs weight] if energy=None",None),ParValue("psffile","f","PSF Calibration file",'CALDB'),ParSet("units","s","Units of output image",'arcsec',["arcsec","logical","physical"]),ParValue("geompar","f","Pixlib geometry file",'geom.par'),ParValue("expstk","f","list of exposure map files",'none'),ParRange("thresh","r","celldetect source threshold",3,3,10000),ParValue("ellsigma","r","Size of output source ellipses (in sigmas)",3.0),ParValue("expratio","r","cutoff ratio for source cell exposure variation",0),ParValue("findpeaks","b","find local peaks for celldetect",True),ParRange("eband","r","energy band, for celldetect",1.4967,0,None),ParRange("eenergy","r","encircled energy of PSF, for celldetect",0.8,0,None),ParValue("celldetect_log","b","make a celldetect log file?",False),ParRange("fixedcell","i","celldetect fixed cell size to use",15,0,999),ParRange("fixedcell_cc_mode","i","celldetect fixed cell size to use for CC mode ACIS data",15,0,999),ParValue("snr_diminution","r","Diminution on SNR threshold - range (< 0 to 1) - Allows fine grained cell sliding",1.0),ParValue("bkgfile","f","background file, for celldetect",'none'),ParRange("bkgvalue","r","background count/pixel, for celldetect",0,0,None),ParRange("bkgerrvalue","r","background error, for celldetect",0,0,None),ParValue("snrfile","f","celldetect snr output file (for convolution only)",'none'),ParValue("convolve","b","use convolutions for celldetect",False),ParRange("xoffset","i","celldetect offset of x axis from optical axis",None,"INDEF","INDEF"),ParRange("yoffset","i","celldetect offset of y axis from optical axis",None,"INDEF","INDEF"),ParValue("cellfile","f","output cell size image file",'none'),ParValue("centroid","b","compute source centroids in celldetection?",True),ParRange("snr_ratio_limit","r","Value of SNR ratio to use as lower limit, for tgidselectsrc",1.0,0,1),ParValue("setsrcid","b","Set src ids in output file?, for tgidselectsrc",True),ParRange("max_separation","r","Maximum allowed separation (arcsec) for sources to match, for tgmatchsrc",3,0,20),ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['tgdetect2'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file",None),ParValue("outfile","f","Output source table file",None)],
    'opt': [ParValue("zo_pos_x","s","Initial guess for sky-x position (default=pixel(ra_targ))",'default'),ParValue("zo_pos_y","s","Initial guess for sky-y position (default=pixel(dec_targ))",'default'),ParValue("unlearn_tgdetect","b","yes = punlearn tgdetect to set all its parameters to defaults",True),ParValue("unlearn_tg_findzo","b","yes = punlearn tg_findzo to set all its parameters to defaults",True),ParValue("temproot","s","Path and root file name to be given to temporary files",None),ParValue("keepexit","b","Keep exit status file?",False),ParValue("clobber","b","OK to overwrite existing output file?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['tgextract'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file (output event file from L1.5 processing)",None),ParValue("outfile","f","If typeII, enter full output file name or '.'; if typeI, enter output rootname",None),ParValue("tg_srcid_list","s","Source ID's to process: 'all', comma list, @file",'all'),ParSet("tg_part_list","s","Grating parts to process: HETG, HEG, MEG, LETG, header_value",'header_value',["HETG","HEG","MEG","LETG","header_value"]),ParValue("tg_order_list","s","Grating diffraction orders to process: 'default', comma list, range list, @file",'default'),ParValue("ancrfile","f","Input ancillary response file name",'none'),ParValue("respfile","f","Input redistribution file name",'none'),ParSet("outfile_type","s","Output file type: typeI (single spectrum) or typeII (multiple spectra)",'pha_typeII',["pha_typeI","pha_typeII"])],
    'opt': [ParValue("inregion_file","f","Input region file.",'none'),ParValue("backfile","f","Input background file name",'none'),ParValue("rowid","s","If rowid column is to be filled in, enter name here",None),ParSet("bin_units","s","Bin units (for bin parameters below): angstrom, eV, keV",'angstrom',["angstrom","eV","keV"]),ParValue("min_bin_leg","s","Minimum dispersion coordinate for LEG, or 'compute'",'compute'),ParValue("max_bin_leg","s","Maximum dispersion coordinate for LEG, or 'compute'",'compute'),ParValue("bin_size_leg","s","Bin size for binning LEG spectra, or 'compute'",'compute'),ParValue("num_bins_leg","s","Number of bins for the output LEG spectra, 'compute'",'compute'),ParValue("min_bin_meg","s","Minimum dispersion coordinate for MEG, or 'compute'",'compute'),ParValue("max_bin_meg","s","Maximum dispersion coordinate for MEG, or 'compute'",'compute'),ParValue("bin_size_meg","s","Bin size for binning MEG spectra, or 'compute'",'compute'),ParValue("num_bins_meg","s","Number of bins for the output MEG spectra, or 'compute'",'compute'),ParValue("min_bin_heg","s","Minimum dispersion coordinate for HEG, or 'compute'",'compute'),ParValue("max_bin_heg","s","Maximum dispersion coordinate for HEG, or 'compute'",'compute'),ParValue("bin_size_heg","s","Bin size for binning HEG spectra, or 'compute'",'compute'),ParValue("num_bins_heg","s","Number of bins for the output HEG spectra, 'compute'",'compute'),ParValue("min_tg_d","s","Minimum tg_d range to include in histogram, or use 'default'",'default'),ParValue("max_tg_d","s","Maximum tg_d range to include in histogram, or use 'default'",'default'),ParValue("extract_background","b","Extract the local background spectrum?",True),ParValue("min_upbkg_tg_d","s","Minimum value of tg_d for the background up spectrum.",'default'),ParValue("max_upbkg_tg_d","s","Maximum value of tg_d for the background up spectrum.",'default'),ParValue("min_downbkg_tg_d","s","Minimum value of tg_d for the background down spectrum.",'default'),ParValue("max_downbkg_tg_d","s","Maximum value of tg_d for the background down spectrum.",'default'),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("clobber","b","OK to overwrite existing output file(s)?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['tgextract2'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input event file (output event file from L1.5 processing)",None),ParValue("outfile","f","Output pha file (for pha2, enter full file name or '.'; for pha1, enter rootname.)",None),ParValue("tg_srcid_list","s","Source ID's to process: 'all', comma list, @file",'1'),ParSet("tg_part_list","s","Grating parts to process: HETG, HEG, MEG, LETG, header_value",'header_value',["HETG","HEG","MEG","LETG","header_value"]),ParValue("tg_order_list","s","Grating diffraction orders to process: 'default', comma list, range list, @file",'default')],
    'opt': [ParSet("opt","s","Output file type: pha1 (single spectrum) or pha2 (multiple spectra)",'pha2',["pha1","pha2"]),ParValue("wav_grid","s","grid specification (use_header| min:max:step| min:max:#bins|pre-defined standard grid)",'use_header'),ParValue("wav_grid_heg","s","pre-defined standard HEG grid",'1.0:21.48:0.0025'),ParValue("wav_grid_meg","s","pre-defined standard MEG grid",'1.0:41.96:0.0050'),ParValue("wav_grid_leg","s","pre-defined standard LETG grid",'1.0:205.80:0.0125'),ParValue("wav_grid_leg_acis","s","pre-defined standard LETG/ACIS grid",'1.0:103.4:0.0125'),ParValue("evt_filter","s","Filter to apply to events for counts spectra",'none'),ParValue("ignore_source_id","b","match source id between regionFile and evtFile?",True),ParSet("error","s","Method for error determination (gaussian|gehrels)",'gaussian',["gaussian","gehrels"]),ParValue("region_file","f","Input region file ( NONE | none | <filename>)",'CALDB'),ParValue("geompar","f","Parameter file for Pixlib Geometry files",'geom'),ParValue("min_tg_d","s","Minimum tg_d for source spectrum, in degrees",'default'),ParValue("max_tg_d","s","Maximum tg_d for source spectrum, in degrees",'default'),ParValue("extract_background","b","Extract the local background spectrum?",True),ParValue("min_upbkg_tg_d","s","Minimum tg_d for upper background spectrum, in degrees",'default'),ParValue("max_upbkg_tg_d","s","Maximum tg_d for upper background spectrum, in degrees",'default'),ParValue("min_downbkg_tg_d","s","Minimum tg_d for down background spectrum, in degrees",'default'),ParValue("max_downbkg_tg_d","s","Maximum tg_d for down background spectrum, in degrees",'default'),ParSet("backscale_method","s","Use events and region, or region-only for backscale",'region',["events","region"]),ParValue("backscale_resolution","i","Amount in pixels to bin in wavelength to improve statistics in backscale",64),ParValue("clobber","b","overwrite any existing output file?",False),ParRange("verbose","i","Verbosity level (0 = no display)",0,0,5)],
    }


parinfo['tgidselectsrc'] = {
    'istool': True,
    'req': [ParValue("infile","f","Name of input src file",None),ParValue("outfile","f","Name of output filtered src file",None),ParRange("snr_ratio_limit","r","Value of SNR ratio to use as lower limit",1.0,0,1)],
    'opt': [ParValue("setsrcid","b","Set src ids?",True),ParValue("clobber","b","Clobber output file?",False),ParRange("verbose","i","Verbose level",0,0,5)],
    }


parinfo['tgmask2reg'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input FITS region file",'CALDB'),ParValue("outfile","f","Output ds9 region file",None)],
    'opt': [ParValue("clobber","b","Clobber existing output if it exists?",False),ParRange("verbose","i","Tool chatter level",0,0,5)],
    }


parinfo['tgmatchsrc'] = {
    'istool': True,
    'req': [ParValue("infile","f","New sources file",None),ParValue("refsrcfile","f","Reference sources file",'NONE'),ParValue("outfile","f","Output file name",'.'),ParRange("max_separation","r","Maximum allowed separation (arcsec) for sources to match",3,0,20)],
    'opt': [ParValue("clobber","b","Clobber output file?",False),ParRange("verbose","i","Debug statement level",0,0,5)],
    }


parinfo['tgsplit'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input TYPE:II pha file",None),ParValue("arffile","f","Input stack of grating ARF files",None),ParValue("rmffile","f","Input stack of grating RMF files",None),ParValue("outroot","f","Output root name",None)],
    'opt': [ParRange("verbose","i","Amount of tool chatter",1,0,5),ParValue("clobber","b","Remove files if they already exist?",False)],
    }


parinfo['update_column_range'] = {
    'istool': True,
    'req': [ParValue("infile","f","File to edit",None)],
    'opt': [ParValue("columns","s","Column names (includes vector columns)",'sky'),ParValue("round","b","Should data ranges be rounded to nearest mid-integer?",True),ParRange("verbose","i","Debug Level (0-5)",1,0,5)],
    }


parinfo['vtbin'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input image",None),ParValue("outfile","f","Output map",None)],
    'opt': [ParValue("binimg","f","Output image file",None),ParSet("shape","s","Shape of local max mask",'box',["box","circle"]),ParRange("radius","r","Radius of local max mask",2.5,0,None),ParValue("sitefile","f","Input site file",None),ParRange("verbose","i","Tool chatter level",1,0,5),ParValue("clobber","b","Remove outfile if it already exists?",False)],
    }


parinfo['vtpdetect'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("expfile","f","Exposure map file name",'none'),ParValue("outfile","f","Source list output file name",None),ParRange("scale","r","Threshold scale factor",1,0,None),ParRange("limit","r","Max. probability of being a false source",1e-06,0,1),ParRange("coarse","i","Minimum number of events per source",10,0,None),ParRange("maxiter","i","Maximum number of iterations to allow",10,0,100)],
    'opt': [ParValue("regfile","f","name for ASCII output region files",'none'),ParValue("ellsigma","r","Size of output source ellipses (in sigmas)",3),ParRange("edge","i","How close to edge of field to reject events",2,0,None),ParValue("superdo","b","Perform Super Voronoi Cell procedure",False),ParRange("maxbkgflux","r","Maximum normalized background flux to fit",0.8,0,None),ParRange("mintotflux","r","Minimum total flux fit range",0.8,0,None),ParRange("maxtotflux","r","Maximum total flux fit range",2.6,0,None),ParRange("mincutoff","r","Minimum total flux cutoff value",1.2,0,10),ParRange("maxcutoff","r","Maximum total flux cutoff value",3,0,10),ParRange("fittol","r","Tolerance on Possion fit",1e-06,0,None),ParRange("fitstart","r","Initial background fit starting scale factor",1.5,0.9,2),ParValue("clobber","b","Overwrite if file exists",False),ParRange("verbose","i","Debug level",0,0,5),ParValue("logfile","f","Debug file name",'stderr')],
    }


parinfo['wavdetect'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("outfile","f","Output source list file name",None),ParValue("scellfile","f","Output source cell image file name",None),ParValue("imagefile","f","Output reconstructed image file name",None),ParValue("defnbkgfile","f","Output normalized background file name",None),ParValue("scales","s","wavelet scales (pixels)",'2.0 4.0'),ParValue("psffile","f","Image of the size of the PSF",None)],
    'opt': [ParValue("regfile","f","ASCII regions output file",None),ParValue("clobber","b","Overwrite existing outputs?",False),ParValue("ellsigma","r","Size of output source ellipses (in sigmas)",3.0),ParValue("interdir","f","Directory for intermediate outputs",'${ASCDS_WORK_PATH}'),ParValue("bkginput","f","Input background file name",None),ParValue("bkgerrinput","b","Use bkginput[2] for background error",False),ParValue("outputinfix","f","Output filename infix",None),ParValue("sigthresh","r","Threshold significance for output source pixel list",1e-06),ParValue("bkgsigthresh","r","Threshold significance when estimating bkgd only",0.001),ParValue("falsesrc","r","Allowed number of false sources per image",-1.0),ParValue("sigcalfile","f","Significance calibration file",'${ASCDS_CALIB}/wtsimresult.fits'),ParValue("exptime","r","Exposure time (if zero, estimate from map itself",0),ParValue("expfile","f","Exposure map file name (blank=none)",None),ParValue("expthresh","r","Minimum relative exposure needed in pixel to analyze it",0.1),ParValue("bkgtime","r","Exposure time for input background file",0),ParValue("maxiter","i","Maximum number of source-cleansing iterations",2),ParValue("iterstop","r","Min frac of pix that must be cleansed to continue",0.0001),ParValue("log","b","Make a log file?",False),ParRange("verbose","i","Log verbosity",0,0,5)],
    }


parinfo['wcs_match'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file with duplicate srcs",None),ParValue("refsrcfile","f","Input file with reference srcs",None),ParValue("outfile","f","Transform file",None)],
    'opt': [ParValue("wcsfile","f","Input file with WCS used in transform",None),ParValue("logfile","f","debug log file ( STDOUT | stdout | <filename>)",'STDOUT'),ParSet("method","s","reproject method: rot/scale/trans (rst) or translate (trans)",'rst',["rst","trans"]),ParRange("radius","r","radius used to match sources (arcsec)",12,0,None),ParSet("select","s","drop/add srcs from transform calc automatically or manually",'auto',["auto","manual"]),ParRange("residlim","r","src pairs with residuals > residlim are dropped (arcsec)",2,0,None),ParRange("residfac","r","src pairs with residuals > residfac * position error are dropped",0,0,None),ParRange("residtype","i","residfac applies to: (0) each residual, (1) avg residuals",0,0,1),ParValue("multimatch","b","Allow multiple matches to reference srcs?",False),ParValue("clobber","b","Overwrite existing output dataset with same name?",False),ParRange("verbose","i","debug level (0-5)",0,0,5)],
    }


parinfo['wcs_update'] = {
    'istool': True,
    'req': [ParValue("infile","f","Either input asol file, or file with WCS to be updated",None),ParValue("outfile","f","Output asol file",None),ParValue("transformfile","f","Input coordinate transform file",None)],
    'opt': [ParValue("wcsfile","f","Input reference WCS file",None),ParValue("logfile","f","debug log file ( STDOUT | stdout | <filename>)",'STDOUT'),ParValue("deltax","r","transform delta_x value (sky pixels)",0),ParValue("deltay","r","transform delta_y value (sky pixels)",0),ParValue("rotang","r","transform rotation angle (degrees)",0),ParValue("scalefac","r","transform scale factor",1),ParValue("clobber","b","Overwrite existing output dataset with same name?",False),ParRange("verbose","i","debug level (0-5)",0,0,5)],
    }


parinfo['wrecon'] = {
    'istool': True,
    'req': [ParValue("infile","f","Input file name",None),ParValue("sourcefile","f","Output source list file name",None),ParValue("scellfile","f","Output source cell image file name",None),ParValue("imagefile","f","Output image file name",None)],
    'opt': [ParValue("regfile","f","ASCII source regions file",None),ParValue("clobber","b","Overwrite exiting outputs?",False),ParValue("ellsigma","r","Size, in sigmas, of output source ellipses",3.0),ParValue("srclist","f","Source input stack file name",None),ParValue("correl","f","Correlation input stack file name",None),ParValue("nbkg","f","Normalized background input stack file name",None),ParValue("bkginput","f","Input background file",None),ParValue("bkgerrinput","b","use input background error from bkginput[2]",False),ParValue("defnbkgfile","f","Default normalized background file name",None),ParValue("fluxfile","f","Flux stack file name",None),ParValue("outputinfix","f","Extra infix for output file names",None),ParValue("xscales","s","X scales",'1.0 1.41 2 2.82 4 5.65 8 11.31 16'),ParValue("yscales","s","Y scales",'1.0 1.41 2 2.82 4 5.65 8 11.31 16'),ParValue("fluxscales","s","Flux scales",'1 3 5 7 9'),ParValue("expfile","f","Exposure map file name",None),ParValue("exptime","r","Exposure time in seconds",0),ParValue("expthresh","r","Exposure threshold",0.1),ParValue("bkgtime","r","Background time in seconds",0),ParValue("psffile","f","PSF image file name",None),ParValue("stall","b","Stall for debugger?",False),ParValue("log","b","Make a log file?",False),ParRange("verbose","i","Log verbosity",0,0,5)],
    }


parinfo['wtransform'] = {
    'istool': True,
    'req': [ParValue("infile","f","input file",None),ParValue("srclist","f","Source list output stack",None),ParValue("correl","s","Correlation image output stack",None),ParValue("nbkg","s","Normalized background image output stack",None)],
    'opt': [ParValue("bkg","s","Plain background image output stack",None),ParValue("thresh","s","threshold image stack",None),ParValue("outputinfix","f","Output filename infix",None),ParValue("exptime","r","Exposure time",0),ParValue("expfile","s","Exposure file",None),ParSet("expcor","s","Exposure correction",'fast',["none","fast","full"]),ParValue("expthresh","r","Exposure threshold",0.1),ParValue("bkgtime","r","Background exposure time",0),ParValue("bkginput","s","Input background file",None),ParValue("bkgerrinput","b","use input background error from bkginput[2]",False),ParValue("xscales","s","X wavelet scales",'2.0'),ParValue("yscales","s","Y wavelet scales",'2.0'),ParValue("clobber","b","overwrite existing outputs",False),ParValue("correlerr","b","Output correlation error image",True),ParValue("nbkgerr","b","Output normalized background error image",True),ParValue("bkgerr","b","Output plain background error image",False),ParValue("maxiter","i","maximum iteration count",2),ParValue("iterstop","r","iteration stop fraction",0.0001),ParValue("sigthresh","r","significance for source detection",1e-06),ParValue("bkgsigthresh","r","significance for data cleansing",0.001),ParValue("falsesrc","r","allowed number of false sources per image",-1.0),ParValue("sigcalfile","f","Significance calibration file",'${ASCDS_CALIB}/wtsimresult.fits'),ParValue("log","b","Make a log file?",False),ParRange("verbose","i","Verbosity of output (0..5)",0,0,5),ParValue("stall","b","stall for debugger",False)],
    }


parinfo['ximage_lut'] = {
    'istool': False,
    'req': [],
    'opt': [ParValue("bb","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/ximage_bb.lut'),ParValue("blue1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/blue1.lut'),ParValue("blue2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/blue2.lut'),ParValue("blue3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/blue3.lut'),ParValue("blue4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/blue4.lut'),ParValue("bluebase1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase1.lut'),ParValue("bluebase2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase2.lut'),ParValue("bluebase3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase3.lut'),ParValue("bluebase4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase4.lut'),ParValue("bluebase5","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase5.lut'),ParValue("bluebase6","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase6.lut'),ParValue("bluebase7","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase7.lut'),ParValue("bluebase8","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase8.lut'),ParValue("bluebase9","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluebase9.lut'),ParValue("bluyel","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/bluyel.lut'),ParValue("brown","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/brown.lut'),ParValue("eyellow1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/eyellow1.lut'),ParValue("gray1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/gray1.lut'),ParValue("gray2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/gray2.lut'),ParValue("green1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green1.lut'),ParValue("green2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green2.lut'),ParValue("green3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green3.lut'),ParValue("green4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green4.lut'),ParValue("green5","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green5.lut'),ParValue("green6","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green6.lut'),ParValue("green7","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green7.lut'),ParValue("green8","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green8.lut'),ParValue("green9","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/green9.lut'),ParValue("invgray","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/invgray.lut'),ParValue("invgray1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/invgray1.lut'),ParValue("invspec","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/invspec.lut'),ParValue("pink1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pink1.lut'),ParValue("pink2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pink2.lut'),ParValue("pink3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pink3.lut'),ParValue("pink4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pink4.lut'),ParValue("pinkbase1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pinkbase1.lut'),ParValue("pinkbase2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pinkbase2.lut'),ParValue("pinkbase3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pinkbase3.lut'),ParValue("pinkbase4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pinkbase4.lut'),ParValue("pinkbase5","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/pinkbase5.lut'),ParValue("purby","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/purby.lut'),ParValue("purple1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/purple1.lut'),ParValue("purple2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/purple2.lut'),ParValue("purple3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/purple3.lut'),ParValue("purple4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/purple4.lut'),ParValue("puryb","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/puryb.lut'),ParValue("red1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/red1.lut'),ParValue("red2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/red2.lut'),ParValue("redbase1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/redbase1.lut'),ParValue("redbase2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/redbase2.lut'),ParValue("redbase3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/redbase3.lut'),ParValue("redbase4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/redbase4.lut'),ParValue("redbase5","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/redbase5.lut'),ParValue("redbase6","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/redbase6.lut'),ParValue("rgb4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/rgb4.lut'),ParValue("rgb6","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/rgb6.lut'),ParValue("spectrum","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/spectrum.lut'),ParValue("vt1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt1.lut'),ParValue("vt2","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt2.lut'),ParValue("vt3","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt3.lut'),ParValue("vt4","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt4.lut'),ParValue("vt5","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt5.lut'),ParValue("vt6","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt6.lut'),ParValue("vt7","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/vt7.lut'),ParValue("yellow1","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/yellow1.lut'),ParValue("yy","f","Color Lookup Table",'${ASCDS_CONTRIB}/data/yy.lut')],
    }



# Add the routines to the module symbol table
#
__all__ = ["get_pfiles", "set_pfiles",
           "new_tmpdir", "new_pfiles_environment",
           "add_tool_history",
           "list_tools", "make_tool"]

for toolname in list_tools():
    setattr(sys.modules[__name__], toolname, make_tool(toolname))
    __all__.append(toolname)

# Now, some tools added that don't use par files and are thus not
# handled by this tool.
# However, that's a fine distinction that users might not appreciate.
# Thus, we add them here, so that least there is a helpful message
# if they try to use it.
# The list of tools is manually curated and believed to be correct
# as of COA 4.14 (see https://github.com/cxcsds/ciao-contrib/issues/643#issue-1419049281)
# We are not adding all scripts, just those that a casual user might expect here.
# In particular, ds9* and install_marx clearly interact with non-Python systems
# and as such we believe that users would not look for thme here.
no_par_file_tools = [
    'acis_clear_status_bits',
    'check_ciao_caldb',
    'check_ciao_version',
    'convert_xspec_script',
    'convert_xspec_user_model',
    'splitroi',
    'summarize_status_bits',
    'tg_bkg'
]

def make_no_par_file_message(toolname):
    '''Make a dummy function that raises an error with a helpful message when called.'''
    def no_parfile(*args, **kwargs):
        '''CIAO tools without parameter file.

        This is a dummy function that will raise an error when called and
        advice to call the CIAO tool using
        `subprocess.run()` from the Python standard library.
        '''
        raise NotImplementedError(f"{toolname} does not use a parameter file and thus is not handled " +
                                  "by ciao_contrib.runtool. Use `subprocess.run` instead " +
                                  f"(see https://docs.python.org/3/library/subprocess.html) to call {toolname}.")
    return no_parfile

for toolname in no_par_file_tools:
    if toolname not in dir(sys.modules[__name__]):
        setattr(sys.modules[__name__], toolname, make_no_par_file_message(toolname))
        __all__.append(toolname)

__all__.extend(['no_par_file_tools', 'make_no_par_file_message'])

# And this one is special, so list individually.
def download_chandra_obsid(*args, **kwargs):
    '''Dummy function that raises an error when called.

    The error message tells the user to use
    `ciao_contrib.cda.data.download_chandra_obsids`
    instead to download Chandra data.
    '''
    raise NotImplementedError(f"download_chandra_obsid does not use a parameter file and thus is not handled " +
                               "by ciao_contrib.runtool. " +
                               "Use ciao_contrib.cda.data.download_chandra_obsids instead.")

__all__ = tuple(__all__)
