#
#  Copyright (C) 2010, 2011, 2012, 2013, 2014, 2015, 2021
#  Smithsonian Astrophysical Observatory
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
A simple set of routines to try and provide a consistent user
interface for script use of the Python logging framework.

This is primarily an internal interface for use by the CIAO
contributed scripts, and so there is no guarantee that any interface
is stable.

The logging class has changed in the December 2010/CIAO 4.3 release;
it now tries to map the CIAO verbose levels onto the standard logging
hierarchy rather than insert a new system within the hierarchy.

"""

# Standard logging levels are
#
# CRITICAL = 50
# FATAL = 50
# ERROR = 40
# WARN = 30
# WARNING = 30
# INFO = 20
# DEBUG = 10
# NOTSET = 0
#
# and CIAO tools use a scale of 0 to 5 inclusive (integers)
# with 0 being essentially no information and 5 the most.
#
# The semantics aren't quite the same, but how about mapping
#
#   verbose   logging
#   ------------------
#   0         ERROR
#   1         INFO
#   2         17
#   3         15
#   4         12
#   5         DEBUG
#

import sys
import logging
import traceback

# The module versions are not exported
#
__all__ = ("initialize_logger",
           "get_logger",
           "set_verbosity",
           "get_verbosity",
           "make_verbose_level",
           "handle_ciao_errors",
           "set_handle_ciao_errors_debug",
           "get_handle_ciao_errors_debug",
           "preprocess_arglist"
           )


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# The logging numerical hierarchy is opposite
# to verbose settings, so we supply conversion
# routines.
#
# The conversions are lossy, since we can not
# guarantee that the logging levels match the
# default values.
#

_verbose_mapping = [
    (0, logging.ERROR),
    (1, logging.INFO),
    (2, 17),
    (3, 15),
    (4, 12),
    (5, logging.DEBUG)
    ]

VNOTSET = -1


def _lvl_to_v(lvl):
    if lvl == logging.NOTSET:
        return VNOTSET
    else:
        for (v, l) in _verbose_mapping:
            if l <= lvl:
                return v

        return _verbose_mapping[-1][0]


def _v_to_lvl(v):
    if v == VNOTSET:
        return logging.NOTSET
    else:
        for (vv, l) in _verbose_mapping:
            if vv == v:
                return l

        raise ValueError(f"Unrecognized verbose level: {v}")

V0 = _v_to_lvl(0)
V1 = _v_to_lvl(1)
V2 = _v_to_lvl(2)
V3 = _v_to_lvl(3)
V4 = _v_to_lvl(4)
V5 = _v_to_lvl(5)


def _check_verbose(verbose):
    """Raises a ValueError if verbose is
    invalid."""
    if verbose == VNOTSET or (verbose >= 0 and verbose <= 5):
        return
    else:
        raise ValueError(f"verbose must be 0-5 (inclusive) or {VNOTSET}, sent {verbose}")


# From
#   http://www.gossamer-threads.com/lists/python/python/691906
#   http://docs.python.org/library/logging.html
#
# we subclass from object to allow the use of property attributes; I
# am not convinced that it is actually sensible but let us see how it
# goes.
#
class CIAOLogger(logging.getLoggerClass(), object):
    """Create a logging class that uses the CIAO tool
    verbose hierarchy, where the verbose levels are
    the integers 0 to 5 inclusive, and you get more
    output as the level increases. A level of 0 is
    is considered to be no output, 1 is minimal
    output and higher levels provide more debugging
    information.

    All we do is transform the CIAO verbose levels
    onto the standard logging hieararchy/values
    system and provide some accessors.

    A verbose value of -1 indicates that it is
    not set (logging.NOTSET is 0, so can not use this).
    """

    def __init__(self, name, verbose=-1, level=None):
        """Create a CIAO logger, which uses the CIAO verbose
        level, which is an integer (0 to 5) where
        higher means more information.

        A verbose value of -1 means 'not set'.
        """

        _check_verbose(verbose)
        level = _v_to_lvl(verbose)
        logging.Logger.__init__(self, name, level=level)

    @property
    def verbose(self):
        "Returns the verbose level of this logger (or the closest value)"
        return _lvl_to_v(self.level)

    @verbose.setter
    def verbose(self, verbose):
        "Sets the verbose level of this logger (0 to 5)"
        _check_verbose(verbose)
        self.level = _v_to_lvl(verbose)

    def getEffectiveVerbose(self):
        "Get the effective verbose level for this logger (or the closest value)."

        lvl = self.getEffectiveLevel()
        if lvl == logging.NOTSET:
            return VNOTSET

        else:
            return _lvl_to_v(lvl)

    def verbose0(self, msg):
        "Log the message if the verbose level is 0 or higher"
        self.log(V0, msg)

    def verbose1(self, msg):
        "Log the message if the verbose level is 1 or higher"
        self.log(V1, msg)

    def verbose2(self, msg):
        "Log the message if the verbose level is 2 or higher"
        self.log(V2, msg)

    def verbose3(self, msg):
        "Log the message if the verbose level is 3 or higher"
        self.log(V3, msg)

    def verbose4(self, msg):
        "Log the message if the verbose level is 4 or higher"
        self.log(V4, msg)

    def verbose5(self, msg):
        "Log the message if the verbose level is 5 or higher"
        self.log(V5, msg)

logging.setLoggerClass(CIAOLogger)

# Ensure we have a "top-level" cxc.ciao logger
# which does nothing. We do not add it to cxc.ciao.contrib
# to make it easier to turn on logging for all contrib
# packages. We make sure that the cxc logger has a
# verbose setting (otherwise a check for the verbose
# level of a child could lead up to the RootLogger,
# which has no verbose level)
#
lhead = "cxc.ciao.contrib"
mhead = "cxc.ciao.contrib.module"
logging.getLogger("cxc.ciao").addHandler(NullHandler())
logging.getLogger("cxc").verbose = 0


def get_logger(lgr):
    """If lgr is a logging object (or at least something with a
    log attribute), return it. Otherwise return the logger
    with the name cxc.ciao.contrib.<lgr>.

    """

    if hasattr(lgr, "log"):
        logger = lgr
    else:
        logger = logging.getLogger(f"{lhead}.{lgr}")

    return logger


def get_module_logger(lgr):
    """If lgr is a logging object (or at least something with a
    log attribute), return it. Otherwise return the logger
    with the name cxc.ciao.contrib.module.<lgr>.

    """

    if hasattr(lgr, "log"):
        logger = lgr
    else:
        logger = logging.getLogger(f"{mhead}.{lgr}")

    return logger


# def add_handler_if_needed(name):
#    """Adds a standard handler to the given
#    level of the hierarchy as long as it, and its
#    parents, do not have a handler that isn't
#    the NullHandler.
#
#    name must be the 'fully-qualified' logger
#    name - e.g. 'cxc.ciao.contrib'
#
#    """
#
#    logger = logging.getLogger(name)
#
#    while name != "":
#        if not all([isinstance(h,NullHandler) for h in logging.getLogger(name).handlers]):
#            return
#        name = ".".join(name.split(".")[:-1])
#
#    hdlr = logging.StreamHandler()
#    #hdlr.setFormatter(logging.Formatter("%(message)s"))
#    logger.addHandler(hdlr)
#    return logger

def initialize_module_logger(name):
    """Create a logger for the module with an id of name.

    Returns the logger. Unlike initialize_logger, no handler
    is set up.

    """

    return get_module_logger(name)


def initialize_logger(name, verbose=0, out=sys.stdout):
    """Create a logger with the name cxc.ciao.contrib.<name>.

    If there is no handler already set up, then add one
    (to cxc.ciao.contrib) that logs all
    messages with a format of just the message (i.e. just
    '%(message)s').

    The name can include "." characters.

    Returns an instance of the logger. Use the verbose0()
    ... verbose5() methods to display a message if the verbosity
    of the logger is >= 0 ... 5.

    The verbose field is used to set or get the verbosity
    level of the logger. This routine sets the level to
    the given verbose value (-1 means not set).

    The out option controls where the messages are logged to.
    The default value is sys.stdout.

    Note: if a handler already exists for this logger
    then none is added.

    """

    plogger = logging.getLogger(lhead)

    if plogger.handlers == []:
        hdlr = logging.StreamHandler(stream=out)
        # hdlr.setFormatter(logging.Formatter("%(message)s"))
        plogger.addHandler(hdlr)

    logger = get_logger(name)
    set_verbosity(verbose)
    return logger


def get_verbosity():
    """Returns the verbosity of the contrib logging
    level cxc.ciao.contrib. This is the level in the hierarchy
    which "general users" should use for logging.

    It does not check the hierarchy for whether 'parent'
    or 'child' elements have a different verbosity.
    """

    return logging.getLogger(lhead).verbose


def get_effective_verbosity():
    """Returns the effective verbosity of the contrib logging
    level cxc.ciao.contrib. This is the level in the hierarchy
    which "general users" should use for logging.
    """

    return logging.getLogger(lhead).getEffectiveVerbose()


def set_verbosity(verbose=1):
    """Sets the verbosity of the contrib logging
    level cxc.ciao.contrib. This is the level in the hierarchy
    which "general users" should use for logging.

    It does not check the hierarchy for whether 'parent'
    or 'child' elements have a different verbosity and
    so should also be changed.

    A value of -1 means "unset".
    """

    _check_verbose(verbose)
    logging.getLogger(lhead).verbose = verbose


def get_module_verbosity():
    """Returns the verbosity of the contrib logging
    level cxc.ciao.contrib.module. This is the level in the hierarchy
    which can be used to turn on/off logging of the modules.

    It does not check the hierarchy for whether 'parent'
    or 'child' elements have a different verbosity.
    """

    return logging.getLogger(mhead).verbose


def get_module_effective_verbosity():
    """Returns the effective verbosity of the contrib logging
    level cxc.ciao.contrib.module. This is the level in the hierarchy
    which can be used to turn on/off logging of the modules.
    """

    return logging.getLogger(mhead).getEffectiveVerbose()


def set_module_verbosity(verbose=1):
    """Sets the verbosity of the contrib logging
    level cxc.ciao.contrib.module. This is the level in the hierarchy
    which can be used to turn on/off logging of the modules.

    It does not check the hierarchy for whether 'parent'
    or 'child' elements have a different verbosity and
    so should also be changed.

    A value of -1 means "unset".
    """

    _check_verbose(verbose)
    logging.getLogger(mhead).verbose = verbose


def make_verbose_level(progname, verbose):
    """Returns a routine which will log a message
    if the verbosity is >= verbose.

    Example:

       v1 = make_verbose_level(progname, 1)
       v1("This is a verbose=1 message")

    """

    if verbose == VNOTSET:
        raise ValueError(f"verbose must be 0-5, not {verbose}")
    else:
        _check_verbose(verbose)

    vname = f"verbose{verbose}"
    return getattr(get_logger(progname), vname)


# Not sure this is the ideal location for this as it involves parameter
# handling, but do not want it in param_wrapper as it doesn't involve
# paramio, but does involve set_handle_ciao_errors_debug
#

def preprocess_arglist(args):
    """Given an argument list, strip out any CIAO-script-specific
    options, process these options, and return the cleaned argument
    list.

    Options supported:
      --debug             - short form for --tracebackdebug
      --tracebackdebug    - if used then tracebacks are turned on for
                            errors, to make debugging easier

    """

    out = args[:]
    flag = None
    for arg in ["--tracebackdebug", "--debug"]:
        if arg in out:
            flag = True
            out.remove(arg)

    if flag:
        set_handle_ciao_errors_debug(True)

    return out


# Not sure this is the ideal location for this decorator
#

__handle_ciao_errors_debug = False


def set_handle_ciao_errors_debug(flag=False):
    """Should the handle_ciao_errors decorator hide the traceback
    (flag=False) or not (flag=True).
    """

    global __handle_ciao_errors_debug
    __handle_ciao_errors_debug = flag


def get_handle_ciao_errors_debug():
    """Returns the value of the flag that controls whether
    the handle_ciao_errors decorator hide the traceback or not.

    Also see set_handle_ciao_errors_debug().
    """

    return __handle_ciao_errors_debug


def _handle_traceback():
    "Display the traceback if requested to do so."

    if __handle_ciao_errors_debug:
        sys.stderr.write("\n\n##### Traceback:\n\n")
        traceback.print_exc()


def handle_ciao_errors(toolname, version=None):
    """A decorator to convert any errors raised by the routine into a
    CIAO tool-like message, and then call sys.exit(1).

    It catches Exception and KeyboardInterrupt. Should it handle
    other exceptions too?

    The output is of the form (for Exceptions)

      # <toolname> (version): ERROR <message>
      # <toolname>: ERROR <message>

    depending on whether version is set or None. If <message> starts
    with "ERROR" (case insensitive) then 'ERROR' is not prepended to
    the string.

    For keyboard interrupts you get

      # <toolname> (version): Keyboard interrupt (control-c)
      # <toolname>: Keyboard interrupt (control-c)

    A traceback will be included *after* this message if the
    set_handle_ciao_errors_debug() routine has previously been called
    with a True argument. The default is for the traceback to be
    hidden.

    """

    def decorator(fn):
        def new_fn(*args, **kw):

            try:
                return fn(*args, **kw)

            except Exception as se:
                if version is None:
                    label = toolname
                else:
                    label = f"{toolname} ({version})"

                emsg = str(se)
                if emsg.upper().startswith("ERROR"):
                    emsg = emsg[5:]
                    if len(emsg) == 0:
                        emsg = "ERROR"
                    else:
                        # this is a bit OTT and assumes that errors are
                        # 8-bit, not UTF-8
                        fchar = ord(emsg[0].upper())
                        if fchar >= ord('A') and fchar <= ord('Z'):
                            emsg = str(se)
                        else:
                            emsg = "ERROR" + emsg
                else:
                    emsg = "ERROR " + emsg

                sys.stderr.write(f"# {label}: {emsg}\n")
                _handle_traceback()
                sys.exit(1)

            except KeyboardInterrupt:
                if version is None:
                    label = toolname
                else:
                    label = f"{toolname} ({version})"

                sys.stderr.write(f"\n# {label}: Keyboard interrupt (control-c)\n")
                _handle_traceback()
                sys.exit(1)

        new_fn.__doc__ = fn.__doc__
        new_fn.__name__ = fn.__name__
        new_fn.__dict__ = fn.__dict__
        new_fn.__module__ = fn.__module__
        return new_fn

    return decorator
