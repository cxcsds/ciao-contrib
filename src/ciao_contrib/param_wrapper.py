
# Python35Support

#
#  Copyright (C) 2010, 2011, 2015
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

"""Utility routines for using the parameter module; as with the
other ciao_contrib.*_wrapper modules it is mainly intended for internal
use and so the API is not guaranteed to be stable.

"""

import os

import ciao_contrib.logger_wrapper as lw
import paramio as pio

logger = lw.initialize_module_logger("param_wrapper")
v5 = logger.verbose5

__all__ = ("open_param_file",)


def show_pfiles():
    """Returns a string listing the directories in the
    PFILES environment variable.

    """

    try:
        pf = os.environ["PFILES"]
    except KeyError:
        raise IOError("The PFILES environment variable is not set!")

    types = pf.split(";")
    if len(types) != 2:
        raise IOError("Expected one ; in\nPFILES={0}".format(pf))

    out = types[0].split(":") + types[1].split(":")
    return " ".join(out)


def open_param_file(argv, toolname=None):
    """Given a command line, parse it and return
    information useful for using it. We attempt to match the
    behavior of tools as much as possible, including support for
    use of @@foo.par. It is not guaranteed to be a complete
    match.

    If toolname is given then use this for the toolname (assuming
    no @@xxx is used), otherwise use the basename of argv[0]
    as the name of the tool).

    The return value is a dictionary with the following keys:

      fp    - the paramio handle for the parameter file (which is
              open and needs to be closed by the user)

      progname - the program name
      parname  - the name of the parameter file (may not match progname)
      mode     - the mode used to open the parameter file

    """

    if argv is None or argv == []:
        raise ValueError("argv argument is None or empty")

    args = argv[:]
    if toolname is None:
        progname = os.path.basename(args[0])
    else:
        progname = toolname

    # Undocumented features for setting debugging on this library.
    # This is intended for internal testing only.
    #
    #  --paramdebug      sets verbosity of this module's logger to 5
    #  --tracebackdebug  turns on traceback in error reporting by lw.handle_ciao_error
    #
    if "--paramdebug" in args:
        logger.verbose = 5
        args.remove("--paramdebug")

    args = lw.preprocess_arglist(args)

    v5("Tool name = {0}".format(progname))

    # In CIAO 4.2 the paramio module does not provide useful error
    # messages, so add in some simple heuristics to let the user what
    # (probably) went wrong. For more useful error messages we would have
    # to parse the parameter file and then look at the input arguments
    # to guess what happened, but leave that for now.
    #
    if len(args) > 1 and args[1].startswith("@@"):
        parname = args[1][2:]
        v5("using re-directed parameter file '@@{0}'".format(parname))

    else:
        parname = progname

    v5("Checking we can find the parameter file: {0}".format(parname))
    try:
        # we do not care what the return value is
        pio.paramgetpath(parname)
    except:
        if progname == parname:
            emsg = "Unable to open parameter file for {0}. Looked in:\n{1}".format(progname, show_pfiles())
        else:
            emsg = "Unable to open parameter file for {0} using {1}".format(progname, parname)

        raise IOError(emsg)

    # mode= "rwL"
    mode= "rw"
    v5("Calling paramopen for {0} with mode={1} args={2}".format(progname, mode, args))
    try:
        fp = pio.paramopen(None, mode, args)

    except Exception:
        raise IOError("There was a problem with the command-line parameter settings.")

    return {"progname": progname, "parname": parname, "fp": fp, "mode": mode}
