#!/usr/bin/env python

"""
Usage:

  ./mk_runtool.py

  Will use the contents of

      $ASCDS_INSTALL/[bin|param]/ and
      [bin|param]/

  to determine what API to create (i.e. what tools to support).
  To support running with the conda environment, we allow files
  in $ASCDS_INSTALL to be "over-written" by those in the current
  working directory (since conda removes the distinction between
  ASCDS_INSTALL and ASCDS_CONTRIB, installing all scripts into the
  same directory).

  Output is to

      ciao_contrib/runtool.py

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


MODULE_HEADER = "mk_runtool.header"
MODULE_FOOTER = "mk_runtool.footer"


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
# Updated for Python 3.12
language_keywords = [
    "False",      "await",      "else",       "import",     "pass",
    "None",       "break",      "except",     "in",         "raise",
    "True",       "class",      "finally",    "is",         "return",
    "and",        "continue",   "for",        "lambda",     "try",
    "as",         "def",        "from",       "nonlocal",   "while",
    "assert",     "del",        "global",     "not",        "with",
    "async",      "elif",       "if",         "or",         "yield"]
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
                    raise IOError(f"Expected a comma after a quote, found {c} in [{txt}], tool={toolname}")

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
            print(f"DBG: len toks = {nt}")
            print(f"DBG:     toks = {toks}")
            raise IOError(f"Unable to process parameter line '{txt}' for {toolname}")

        elif nt < 7:
            toks.extend(["" for i in range(nt, 7)])

        self.name = toks[0]
        self.type = toks[1]
        self.python_type = self.python_type_map[self.type]
        self.mode = toks[2]
        self.value = toks[3]
        self.minval = toks[4]
        self.maxval = toks[5]
        self.info = toks[6].strip()

        # Use a case-insensitive check
        if self.name.lower() in language_keywords_lower:
            print(f"WARNING: [{self.toolname}] parameter name clashes with Python reserved word:\n  {txt}")

        # This is just a warning as the ParameterInfo object does the
        # remapping.
        # NOTE that for CIAO 4.4 development we skip these parameters
        # since dmtabfilt has parameters with names like "3", and I need
        # to think about how to handle.
        #
        if re.match(identifier, self.name) is None:
            nname = self.name.replace("-", "_")
            if re.match(identifier, nname) is None:
                print(f"WARNING: [{self.toolname}] parameter name is not a valid Python identifier and does not transform '-' -> '_': {txt}")
                self.skip = True
                return  # will this work?

            else:
                print(f"Note: converting {self.name} -> {nname}")

        if "INDEF" in self.info:
            self.info = self.info.replace("INDEF", "None")

        # Not 100% sure what to do with these, so make sure they
        # are noted as a reminder.
        #
        if "INDEF" in [self.minval, self.maxval]:
            print(f"Note: minval/maxval is INDEF in\n  {txt}")

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
        return f"{self.__class__.__name__}('{self.toolname}', '{self.input_line}')"

    def __str__(self):
        return self.input_line

    def describe(self, sep):
        """Return a string of a tuple describing this parameter
        in the format needed by the ParameterInfo object.

        The sep argument is the spacing to use before the text
        """

        args = f'"{self.name}","{self.type}","{self.info}",'
        if self.value is None or str(self.value) == "":
            # not sure about this
            args += "None"

        elif self.type in "sf" or self.value == "INDEF" or \
                str(self.value).startswith(")"):
            args += f"'{self.value}'"
        else:
            args += f"{self.value}"

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
                minval = f'"{self.minval}"'
            else:
                minval = self.minval

            if self.maxval == "INDEF" or self.is_maxval_redirect:
                maxval = f'"{self.maxval}"'
            else:
                maxval = self.maxval

            args += f",{minval},{maxval}"

        else:
            ptype = "ParValue"

        return f"{sep}{ptype}({args})"


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
    pname = os.path.join(dirname, f"{toolname}.par")
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
    out = f"parinfo['{toolname}'] = {{\n"
    out += f"\t'istool': {istool},\n"

    rpars = [p.describe("") for p in req_params]
    out += "\t'req': [{}],\n".format(",".join(rpars))

    opars = [p.describe("") for p in opt_params]
    out += "\t'opt': [{}],\n".format(",".join(opars))
    out += "\t}\n"
    out += "\n"
    return out.replace("\t", "    ")


def add_output(funcinfo, parname):
    """Store information on the tool for later use.

    It is assumed that the "installed" version is processed
    before the developmetn version, so the latter will "win out"
    when both are present.
    """

    dirname, toolname = os.path.split(parname)
    if dirname == '':
        raise ValueError(f"Unexpected: dirname='' in parname={parname}")
    if toolname == '' or not toolname.endswith('.par'):
        raise ValueError(f"Unexpected: toolname={toolname} in parname={parname}")

    toolname = toolname[:-4]

    # This could be just a warning, or quietly ignored, but leave as
    # an error for now as it should not happen. Actually, now it
    # can happen (with the conda build), so silently over-write.
    #
    """
    if toolname in funcinfo:
        raise ValueError(f"The tool {toolname} has already been added!")
    """

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


def doit():

    ascds_install = os.getenv("ASCDS_INSTALL")
    if ascds_install is None:
        raise IOError("ASCDS_INSTALL environment variable is not set; " +
                      "has CIAO been started?")

    # Assume to be run from the top level of the directory structure
    ascds_contrib = os.getcwd()

    for pathname in [ascds_install, ascds_contrib]:
        if not os.path.isdir(pathname):
            raise IOError(f"Unable to find directory: {pathname}")

    for filename in [MODULE_HEADER, MODULE_FOOTER]:
        if not os.path.isfile(filename):
            raise IOError(f"Unable to find the file: {filename}")

    contrib_path = "ciao_contrib/"
    odir = os.path.join(ascds_contrib, contrib_path)
    if not os.path.isdir(odir):
        raise IOError(f"Unable to find output directory:\n{odir}")
    oname = os.path.join(odir, "runtool.py")

    print(f"Input directores:\n  {ascds_install}\n  {ascds_contrib}\n")

    with open(oname, "w") as ofh:
        print_module_section(ofh, MODULE_HEADER)
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

        print_module_section(ofh, MODULE_FOOTER)

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

    if rval == b'':
        print("The module has not changed.")
    else:
        print("*** The runtool module has changed!")
        print("*** Review the differences with:")
        print("*** {}".format(" ".join(gitargs)))
        print("***")


if __name__ == "__main__":

    if len(sys.argv) != 1:
        sys.stderr.write(f"Usage: python {sys.argv[0]}\n")
        sys.exit(1)

    doit()
