#!/usr/bin/env python

"""
Usage:

  ./mk_runtool.py

  Will use the contents of $ASCDS_INSTALL/[bin|param]/ and
  ciao-<version>/contrib/[bin|param]/ to determine what API
  to create (i.e. what tools to support).

  Output is to
  ciao-<version>/contrib/lib/python2.7/site-packages/ciao_contrib/runtool.py

  Note that this file is *not* checked into the repository to
  allow you to check for changes (this could be added once the
  process has been worked through a few times).

Aim:

Create a module which can be imported to allow you to run CIAO tools.
I had originally intended this to be auto-generated when the module
was loaded, but having troubles getting the names to work out right,
so hard-coding it for now.

It requires the following files:

  mk_runtool.header
  mk_runtool.footer

The handling of "redirects" in the minval/maxval ranges is sub-optimal
since we take it apart and then re-create a string, when things could
be handled more sensibly.

"""

import os
import os.path
import re
import subprocess
import sys
import glob


def _find_pathname():
    "Return value includes trailing slash"
    matches = glob.glob("ciao-*.*/")
    nmatches = len(matches)
    if nmatches == 1:
        return matches[0]
    elif nmatches == 0:
        raise IOError("Unable to find ciao-*.*/ subdirectory!")
    else:
        raise IOError("Found {} matches to ciao-*.*/!".format(nmatches))

# A lot of this code should probably go in the 'if __name__' section below!

ciao_head = _find_pathname()

ascds_install = os.getenv("ASCDS_INSTALL")
if ascds_install is None:
    raise IOError("ASCDS_INSTALL environment variable is not set; has CIAO been started?")

ascds_contrib = "{}contrib".format(ciao_head)

for pathname in [ascds_install, ascds_contrib]:
    if not os.path.isdir(pathname):
        raise IOError("Unable to find directory: {}".format(pathname))

module_header = "mk_runtool.header"
module_footer = "mk_runtool.footer"

for filename in [module_header, module_footer]:
    if not os.path.isfile(filename):
        raise IOError("Unable to find the file: {}".format(filename))

# TODO: how best to handle the Python version here?
#
contrib_path = "contrib/lib/python2.7/site-packages/ciao_contrib/"
odir = os.path.join(ciao_head, contrib_path)
if not os.path.isdir(odir):
    raise IOError("Unable to find output directory:\n{}".format(odir))
oname = os.path.join(odir, "runtool.py")

# Identifier information from
# http://docs.python.org/reference/lexical_analysis.html#identifiers
#
# identifier ::=  (letter|"_") (letter | digit | "_")*
# letter     ::=  lowercase | uppercase
# lowercase  ::=  "a"..."z"
# uppercase  ::=  "A"..."Z"
# digit      ::=  "0"..."9"
# Identifiers are unlimited in length. Case is significant.
#
identifier = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")

# From
# https://docs.python.org/3/reference/lexical_analysis.html#keywords
#
language_keywords = [
    "False",      "class",      "finally",    "is",         "return",
    "None",       "continue",   "for",        "lambda",     "try",
    "True",       "def",        "from",       "nonlocal",   "while",
    "and",        "del",        "global",     "not",        "with",
    "as",         "elif",       "if",         "or",         "yield",
    "assert",     "else",       "import",     "pass",
    "break",      "except",     "in",         "raise"]
language_keywords_lower = [k.lower() for k in language_keywords]


class Param:
    """A parameter from a tool, as parsed from an input line.

    The constructor will throw an IOError if there was a problem
    parsing the line.
    """

    python_type_map = {
        "s": "string",
        "f": "filename (string)",
        "i": "integer",
        "r": "number",
        "b": "bool"}

    def __init__(self, toolname, txt):
        "Parse a parameter line (txt) for the given tool."

        self.toolname = toolname
        self.input_line = txt

        # Can not just split on "," since the default value may contain
        # commas - e.g. stdlev1 of acis_process_events
        #
        # At present assume no need to handle \ for protecting string
        # characters.
        #
        toks = [""]
        in_string = False
        expect_comma = False
        for c in txt:

            if expect_comma:
                if c == ",":
                    expect_comma = False
                else:
                    raise IOError("Expected a comma after a quote, found {} in [{}], tool={}".format(c, txt, toolname))

            # Assume that only " is used for start/end of a string
            if c == '"':
                if in_string:
                    in_string = False
                    expect_comma = True
                else:
                    in_string = True
                continue

            if c == "," and not in_string:
                toks.append("")
                continue

            toks[-1] += c

        nt = len(toks)
        if nt < 4:
            print("DBG: len toks = {}".format(nt))
            print("DBG:     toks = {}".format(toks))
            raise IOError("Unable to process parameter line '{}' for {}".format(txt, toolname))

        elif nt < 7:
            toks.extend(["" for i in range(nt, 7)])

        self.name   = toks[0]
        self.type   = toks[1]
        self.python_type = self.python_type_map[self.type]
        self.mode   = toks[2]
        self.value  = toks[3]
        self.minval = toks[4]
        self.maxval = toks[5]
        self.info   = toks[6].strip()

        # Use a case-insensitive check
        if self.name.lower() in language_keywords_lower:
            print("WARNING: parameter name clashes with Python reserved word:\n  {}".format(txt))

        # This is just a warning as the ParameterInfo object does the
        # remapping.
        # NOTE that for CIAO 4.4 development we skip these parameters
        # since dmtabfilt has parameters with names like "3", and I need
        # to think about how to handle.
        #
        if re.match(identifier, self.name) is None:
            nname = self.name.replace("-", "_")
            if re.match(identifier, nname) is None:
                print("WARNING: parameter name is not a valid Python identifier and does not transform '-' -> '_': {}".format(txt))
                self.skip = True
                return  # will this work?

            else:
                print("Note: converting {} -> {}".format(self.name, nname))

        if "INDEF" in self.info:
            self.info = self.info.replace("INDEF", "None")

        # Not 100% sure what to do with these, so make sure they
        # are noted as a reminder.
        #
        if "INDEF" in [self.minval, self.maxval]:
            print("Note: minval/maxval is INDEF in\n  {}".format(txt))

        # We hide the complexity of the mode (e.g. values of
        # h or hl or l) and just make this binary distinction
        #
        self.required = self.mode == "a"

        if self.minval == "" or self.type == "b":
            self.minval = None
        if self.maxval == "" or self.type == "b":
            self.maxval = None

        if self.minval is not None and \
           (("|" in self.minval) or (self.type in "sf")):
            self.opts = self.minval.split("|")
            self.minval = None
            self.set = True
        else:
            self.set = False
            self.opts = None

        self.is_minval_redirect = (self.minval is not None) and \
            self.minval.startswith(")")
        self.is_maxval_redirect = (self.maxval is not None) and \
            self.maxval.startswith(")")

        if self.type == "b" and self.value != "" and \
           not self.value.startswith(")"):
            self.value = self.value == "yes"

        elif self.type in "ir" and self.value == "INDEF":
            self.value = None

        elif self.type in "sf" and self.value == "":
            # not 100% convinced about this
            self.value = None

        # Should this parameter be skipped?
        #
        self.skip = (self.name == "mode") or \
            (self.opts is not None and len(self.opts) == 1)
        if self.skip and self.required:
            raise IOError("Found a required parameter that is to be skipped!")

    def __repr__(self):
        return "{}('{}', '{}')".format(self.__class__.__name__,
                                       self.toolname, self.input_line)

    def __str__(self):
        return self.input_line

    def describe(self, sep):
        """Return a string of a tuple describing this parameter
        in the format needed by the ParameterInfo object.

        The sep argument is the spacing to use before the text
        """

        args = '"{}","{}","{}",'.format(self.name, self.type,
                                        self.info)
        if self.value is None or str(self.value) == "":
            # not sure about this
            args += "None"

        elif self.type in "sf" or self.value == "INDEF" or \
                str(self.value).startswith(")"):
            args += "'{}'".format(self.value)
        else:
            args += "{}".format(self.value)

        if self.set:
            ptype = "ParSet"
            if self.type in "sf":
                args += ",[{}]".format(",".join(['"{}"'.format(o)
                                                 for o in self.opts]))
            else:
                # assume no INDEF in the list of options here
                args += ",[{}]".format(",".join(["{}".format(o)
                                                 for o in self.opts]))

        elif (self.minval is not None) or (self.maxval is not None):
            ptype = "ParRange"
            if self.minval == "INDEF" or self.is_minval_redirect:
                minval = '"{}"'.format(self.minval)
            else:
                minval = self.minval

            if self.maxval == "INDEF" or self.is_maxval_redirect:
                maxval = '"{}"'.format(self.maxval)
            else:
                maxval = self.maxval

            args += ",{},{}".format(minval, maxval)

        else:
            ptype = "ParValue"

        return "{}{}({})".format(sep, ptype, args)


def get_param_list(dirname, toolname):
    """Return a tuple of required and parameter values,
    where each entry is a list (which can be empty).
    Each list entry is a dictionary containing information
    on that parameter.
    """

    # Unfortunately the Python paramio module does not provide
    # all of the functionality of the S-Lang version (e.g.
    # plist_names) so we have to parse the parameter file
    #
    pname = os.path.join(dirname, "{}.par".format(toolname))
    with open(pname, "r") as pf:
        req_params = []
        opt_params = []
        for l in pf.readlines():
            l = l.strip()
            if len(l) == 0 or l.startswith("#"):
                continue

            p = Param(toolname, l)
            if p.skip:
                continue

            if p.required:
                req_params.append(p)
            else:
                opt_params.append(p)

    return (req_params, opt_params)


def create_output(dirname, toolname, istool=True):
    """Return Python code for the given tool.

    Parameters
    ----------
    dirname : str
        The name of the directory containing <toolname>.par.
    toolname : str
        The name of the tool/parameter file.
    istool : bool
        True if the par file belongs to a tool; False if there
        is no tool for the .par file (e.g. the 'lut' par file).

    Returns
    -------
    pycode : str
        The Pyton code for this tool.

    """

    (req_params, opt_params) = get_param_list(dirname, toolname)

    # create the parameter object
    out  = "parinfo['{}'] = {{\n".format(toolname)
    out += "\t'istool': {},\n".format(istool)

    rpars = [p.describe("") for p in req_params]
    out += "\t'req': [{}],\n".format(",".join(rpars))

    opars = [p.describe("") for p in opt_params]
    out += "\t'opt': [{}],\n".format(",".join(opars))
    out += "\t}\n"
    out += "\n"
    return out.replace("\t", "    ")


def add_output(funcinfo, parname):
    """Store information on the tool for later use."""

    dirname, toolname = os.path.split(parname)
    if dirname is '':
        raise ValueError("Unexpected: dirname='' in parname={}".format(parname))
    if toolname is '' or not toolname.endswith('.par'):
        raise ValueError("Unexpected: toolname={} in parname={}".format(toolname, parname))

    toolname = toolname[:-4]

    # This could be just a warning, or quietly ignored, but leave as
    # an error for now as it should not happen.
    #
    if toolname in funcinfo:
        raise ValueError("The tool {} has already been added!".format(toolname))

    epath = os.path.normpath(os.path.join(dirname, '../bin'))

    # skip the .py files - why is this? Probably because, at the
    # moment (CIAO 4.9), the .py files in the bin/ directory
    # are not ones we want to expose directly to the user.
    #
    # An alternative check would be to see if the script has
    # an ahelp file, but that also has its issues (e.g.
    # can we guarantee that the file name matches, either because
    # the name is just different or multiple tools have the
    # same ahelp file), although they are probably theoretical.
    #
    fname = os.path.join(epath, toolname)
    if os.path.isfile(fname + ".py"):
        return

    istool = os.path.isfile(fname)
    funcinfo[toolname] = (dirname, toolname, istool)


def print_module_section(ofh, filename):
    "Add contents of filename to ofh"

    with open(filename, "r") as f:
        for l in f.readlines():
            ofh.write(l)

    ofh.flush()


def add_par_files(parinfo, dirname, pardir='param'):
    """Update parinfo with .par files in dirname.

    Parameters
    ----------
    parinfo : dict
        A dictionary, where the key is the tool name and
        the value is (dirname, toolname, istool) where
        istool is a flag that is True if there is an 'executable'
        file for the param file (actually, any file) otherwise it
        is False (e.g. for par files like 'lut').
    dirname : str or None
        The name of the directory containing a pardir directory,
        in which to look. If None this step is skipped.
    pardir : str, optional
        The name of the directory within dirname in which to
        look for .par files.

    """

    if dirname is None:
        return

    pdir = os.path.join(dirname, pardir)
    search = os.path.join(pdir, "*.par")
    for fname in glob.glob(search):
        add_output(parinfo, fname)


if __name__ == "__main__":

    print("Input directores:\n  {}\n  {}\n".format(ascds_install,
                                                   ascds_contrib))

    with open(oname, "w") as ofh:
        print_module_section(ofh, module_header)
        tools = {}

        add_par_files(tools, ascds_install)
        add_par_files(tools, ascds_contrib)

        # sort the array so that we have a more consistent output to
        # make it easier to spot changes
        #
        toolnames = list(tools.keys())
        toolnames.sort()
        for tname in toolnames:
            (dirname, toolname, istool) = tools[tname]
            ofh.write(create_output(dirname, toolname, istool=istool))
            ofh.write("\n")
            ofh.flush()

        print_module_section(ofh, module_footer)

    print("")
    print("Created: {}".format(oname))
    print("")

    # Has it changed?
    #
    gitargs = ['git', 'diff', oname]
    try:
        rval = subprocess.check_output(gitargs)
    except subprocess.CalledProcessError as se:
        print("---")
        print("--- unable to run:")
        print("--- {}".format(" ".join(gitargs)))
        print("---")
        print(str(se))
        print("---")
        sys.exit(1)

    if rval == '':
        print("The module has not changed.")
    else:
        print("*** The runtool module has changed!")
        print("*** Review the differences with:")
        print("*** {}".format(" ".join(gitargs)))
        print("***")
