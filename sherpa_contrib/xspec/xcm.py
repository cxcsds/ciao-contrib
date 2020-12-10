#
#  Copyright (C) 2020  Smithsonian Astrophysical Observatory
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
Convert a XSPEC xcm file into Sherpa.

The intention is to make it possible to convert an XSPEC model
session into Sherpa, but without a guarantee of 100% fidelity.
The idea is that further work may be needed to allow full
analysis in Sherpa.

"""

import logging

from collections import defaultdict

from sherpa.astro import ui
from sherpa.astro.ui.utils import Session
from sherpa.astro import xspec
from sherpa.utils.err import ArgumentErr, DataErr

import sherpa.astro.instrument


__all__ = ("convert", )

lgr = logging.getLogger(__name__)
dbg = lgr.debug
del lgr


# Helper classes and functions that can be used by the converted
# script.
#
class Response1D(sherpa.astro.instrument.Response1D):
    """Allow the response id to be set.

    Notes
    -----
    This functionality should probably be moved to Sherpa: see [1]_

    References
    ----------

    .. [1] https://github.com/sherpa/sherpa/issues/1025

    """

    def __init__(self, pha, resp_id):
        self.resp_id = resp_id
        super().__init__(pha)

    def __call__(self, model):
        pha = self.pha
        arf, rmf = pha.get_response(self.resp_id)

        # Automatically add exposure time to source model
        if pha.exposure is not None:
            model = pha.exposure * model
        elif arf is not None and arf.exposure is not None:
            model = arf.exposure * model

        if arf is not None and rmf is not None:
            return sherpa.astro.instrument.RSPModelPHA(arf, rmf, pha, model)

        if arf is not None:
            return sherpa.astro.instrument.ARFModelPHA(arf, pha, model)

        if rmf is not None:
            return sherpa.astro.instrument.RMFModelPHA(rmf, pha, model)

        raise DataErr('norsp', pha.name)


def notice(spectrum, lo, hi, ignore=False):
    """Apply XSPEC channel numbering to notice or ignore a range.

    Parameters
    ----------
    spectrum : int
        The dataset identified.
    lo, hi: int
        The channel range, as recorded by XSPEC (this is the group
        number for Sherpa).
    ignore : bool, optional
        If set then we ignore the range.

    See Also
    --------
    ignore

    """

    d = ui.get_data(spectrum)

    # The naming of these routines is a bit odd since sometimes
    # channel means group and sometimes it means channel.
    #
    if d.units == 'energy':
        elo = d._channel_to_energy(lo)
        ehi = d._channel_to_energy(hi)

        dbg(f"Converting group {lo}-{hi} to {elo:.3f}-{ehi:.3f} keV [ignore={ignore}]]")
        d.notice(elo, ehi, ignore=ignore)
        return

    if d.units == 'wavelength':
        whi = d._channel_to_energy(lo)
        wlo = d._channel_to_energy(hi)

        dbg(f"Converting group {lo}-{hi} to {wlo:.5f}-{whi:.5f} A [ignore={ignore}]]")
        d.notice(wlo, whi, ignore=ignore)
        return

    if d.units != 'channel':
        raise ValueError(f"Unexpected analysis setting for spectrum {spectrum}: {d.units}")

    # Convert from group number (XSPEC) to channel units
    clo = d._group_to_channel(lo)
    chi = d._group_to_channel(hi)

    dbg(f"Converting group {lo}-{hi} to channels {clo}-{chi} [ignore={ignore}]]")
    d.notice(clo, chi, ignore=ignore)


def ignore(spectrum, lo, hi):
    """Apply XSPEC channel numbering to ignore a range.

    Parameters
    ----------
    spectrum : int
        The dataset identified.
    lo, hi: int
        The channel range, as recorded by XSPEC (this is the group
        number for Sherpa).

    See Also
    --------
    notice

    """

    notice(spectrum, lo, hi, ignore=True)


def subtract(spectrum):
    """Subtract the background (a no-op if there is no background).

    Parameters
    ----------
    spectrum : int
        Dataset identifier.
    """

    try:
        ui.subtract(spectrum)
    except DataErr:
        print(f"Dataset {spectrum} has no background data!")


# Routines used in converting a script.
#
def set_subtract(add_import, add_spacer, add, state):
    """Ensure the data is subtracted (as much as we can tell)."""

    if state['nodata'] or state['subtracted'] or not state['statistic'].startswith('chi'):
        return

    for did in state['datasets']:
        if did in state['nobackgrounds']:
            continue

        add_import('from sherpa_contrib.xspec import xcm')
        add('xcm.subtract', did, expand=False)

    add_spacer()

    # The assumption is that we don't add data/backgrounds after this is called
    state['subtracted'] = True


def parse_tie(pline):
    """Parse a tie line.

    Supported formats include:
      - '= n' or '= pn'
      - '= number*n' or '= number*pn' (ditto for +-/)
      - '= label:n'
      - '= number*label:n' (ditto for +-/)

    Parameters
    ----------
    pline : str
        The tie line.

    Returns
    -------
    label, ctr, prefix : str, int, str
         The label used to identify the parameter settings
         ('unnamed' or the label value), the parameter
         number (1 based), and any prefix (the 'number*'
         segment).

    """

    assert pline.startswith('= ')
    line = pline[1:].strip()

    # I have seen the line
    #   '= 1.6392059E + 02*pbg3:2'
    # which I am going to assume is 1.639e+02*pbg3:2, so let's just
    # remove the spaces.
    #
    line = line.translate({32: None})

    # Perhaps it would be better to parse the term backwards,
    # to extract just the [a:]b syntax
    #
    # What values can be included here?
    #
    mul = line.find('*')
    div = line.find('/')
    add = line.find('+')
    sub = line.find('-')
    idx = max(mul, div, add, sub)
    if idx > -1:
        prefix = line[:idx + 1]
        line = line[idx + 1:]
    else:
        prefix = ''

    if ':' in line:
        toks = line.split(':')
        if len(toks) != 2:
            raise ValueError(f"Unsupported parameter tie: '{pline}'")

        tlabel = toks[0]
        tie = toks[1]
    else:
        tlabel = 'unnamed'
        tie = line

    # I don't know what the rule is with the parameter
    # number, I assume that "23" and "p23" have the
    # same meaning.
    #
    if tie.startswith('p'):
        tie = tie[1:]

    try:
        tie = int(tie)
    except ValueError:
        raise ValueError(f"Unsupported parameter tie: '{pline}'") from None

    return tlabel, tie, prefix


def parse_dataid(token):
    """Convert '[<data group #>:] <spectrum #>' to values.

    Parameters
    ----------
    token : str

    Returns
    -------
    groupnum, datanum : None or int, int
    """

    emsg = f"Unsupported data identifier: '{token}'"
    toks = token.split(':')
    ntoks = len(toks)
    if ntoks > 2:
        raise ValueError(emsg)

    try:
        toks = [int(t) for t in toks]
    except ValueError:
        raise ValueError(emsg)

    if ntoks == 2:
        return toks[0], toks[1]

    return None, toks[0]


def parse_ranges(ranges):
    """Convert a-b,... to a set of ranges.

    Parameters
    ----------
    ranges : str
        The range specification

    Returns
    -------
    chantype, ranges : str, list of (lo,hi)
        The channel type is "channel" or "other" and the tuples
        indicate the ranges, with None standing in for no-limit.

    Notes
    -----
    Sherpa and XSPEC have a different concept of channel, so we may need
    to actually read in the PHA file (actually, the responses) to
    validate this.
    """

    chantype = "channel"

    def convert(val):
        global chantype
        if '.' in val:
            chantype = "other"
            try:
                return float(val)
            except ValueError:
                raise ValueError(f"Expected **, integer, or float: sent '{val}'") from None

        if val == '**':
            return None

        try:
            return int(val)
        except ValueError:
            raise ValueError(f"Expected **, integer, or float: sent '{val}'") from None

    out = []
    for r in ranges.split(','):
        rs = r.split('-')
        if len(rs) == 1:
            end = rs
            start = 1
        elif len(rs) == 2:
            start = rs[0]
            end = rs[1]
        else:
            raise ValueError(f"Unexpected range in '{ranges}'")

        out.append((convert(start), convert(end)))

    return chantype, out


def parse_notice_range(add_import, add, datasets, command, tokens):
    """Handle the notice range.

    Parameters
    ----------
    add_import : function reference
        Used to add an import command
    add : function reference
        Used to add the commands to the store.
    datasets : list of int
        The loaded datasets.
    command : {'notice', 'ignore'}
        The command for these settings.
    tokens : list of str
        It is assumed that each token represents a set of datasets.

    """

    # The selected datasets
    ds = [1]

    for token in tokens:
        vals = token.split(':')
        nvals = len(vals)
        if nvals > 2:
            raise ValueError(f"Unsupported {command.upper()} range: '{token}'")

        if nvals == 2:
            if vals[0] == '**':
                ds = datasets
            else:
                try:
                    v = [int(v) for v in vals[0].split('-')]
                except TypeError:
                    raise ValueError(f"Expected integer[-integer] but sent '{vals[0]}'") from None

                if len(v) == 1:
                    ds = v
                elif len(v) == 2:
                    ds = list(range(v[0], v[1] + 1))
                else:
                    raise ValueError(f"Unrecognized spectrum range '{vals[0]}' in '{token}'")

        chantype, ranges = parse_ranges(vals[-1])

        if chantype == 'other':
            for lo, hi in ranges:
                add(f'{command}_id', ds, lo, hi)

            return

        # We have to use our own "notice" command to handle group numbering.
        #
        for d in ds:
            for lo, hi in ranges:
                add_import('from sherpa_contrib.xspec import xcm')
                add(f"xcm.{command}", d, lo, hi, expand=False)


def convert_model(expr, postfix, groups, names):
    """Extract the model components.

    Model names go from m1 to mn (when groups is empty) or
    m1g1 to mng1 and then m1g2 to mng<ngrops>.

    Parameters
    ----------
    expr : str
        The XSPEC model expression.
    postfix : str
        Add to the model + number string.
    groups : list of int
        The groups to create. It must not be empty. We special case a
        single group, as there's no need to add an identifier.
    names : set of str
        The names we have created (will be updated). This is just
        for testing.

    Returns
    -------
    exprs : list of lists
        The model expression for each group (if groups was None then
        for a single group). Each list contains a pair of
        (str, None) or ((str, str), Model), where for the Model
        case the two names are the model type and the instance name.

    Notes
    -----
    We require the Sherpa XSPEC module here.

    """

    assert len(groups) > 0

    # Create our own session object to make it easy to
    # find out XSPEC models and the correct naming scheme.
    #
    session = Session()
    session._add_model_types(xspec,
                             (xspec.XSAdditiveModel,
                              xspec.XSMultiplicativeModel,
                              xspec.XSConvolutionKernel))


    # Let's remove the spaces
    dbg(f"Processing model expression: {expr}")
    expr = expr.translate({32: None})

    if len(groups) == 1:
        groups = [None]
        def mkname(ctr, grp):
            n = f"m{ctr}{postfix}"
            assert n not in names
            names.add(n)
            return n

    else:
        def mkname(ctr, grp):
            n = f"m{ctr}{postfix}g{grp}"
            assert n not in names
            names.add(n)
            return n

    out = [[] for _ in groups]

    def add_term(start, end, ctr, storage):
        """storage tracks the convolution state."""

        # It's not ideal we need this
        if start == end:
            return ctr

        name = f"xs{expr[start:end]}"
        dbg(f"Identified model expression '{name}'")

        for i, grp in enumerate(groups, 1):
            try:
                mdl = session.create_model_component(name, mkname(ctr, grp))
            except ArgumentErr:
                raise ValueError(f"Unrecognized XSPEC model '{name[2:]}' in {expr}") from None

            out[i - 1].append((mdl.name.split('.'), mdl))

            # This only needs to be checked for the first group.
            #
            if i == 1:
                if isinstance(mdl, xspec.XSConvolutionKernel):
                    if storage['convolution'] is not None:
                        print("Convolution found within a convolution expession. This is not handled correctly.")
                    else:
                        storage['convolution'] = storage['depth']
                        storage['lastterm'] = 'convolution'
                        out[i - 1].append(("(", None))

                elif isinstance(mdl, xspec.XSMultiplicativeModel):
                    storage['lastterm'] = 'multiplicative'

                elif isinstance(mdl, xspec.XSAdditiveModel):
                    storage['lastterm'] = 'additive'

                else:
                    raise RuntimeError(f"Unrecognized XSPEC model: {mdl.__class__}")

        return ctr + 1

    def add_sep(sep):
        for i, grp in enumerate(groups, 1):
            out[i - 1].append((sep, None))

    def check_end_convolution(storage):
        if storage['convolution'] is None:
            return

        if storage['convolution'] > storage['depth']:
            return

        if storage['convolution'] == storage['depth']:
            add_sep(")")
        elif storage['convolution'] > storage['depth']:
            print("WARNING: convolution model may not be handled correctly.")

        storage['convolution'] = None

    def in_convolution(storage):
        return storage['convolution'] is not None \
            and storage['convolution'] == storage['depth']

    maxchar = len(expr) - 1
    start = 0
    end = 0
    mnum = 1
    storage = {'convolution': None, 'depth': 0, 'lastterm': None}
    for end, char in enumerate(expr):

        # Not completely sure of the supported language.
        #
        if char not in "*+-/()":
            continue

        if char == "(":
            if end == 0:
                add_sep('(')
            else:
                mnum = add_term(start, end, mnum, storage)
                # We want to leave ( alone for convolution models.
                # This is a bit messy.
                #
                if expr[end - 1] in "+*-/":
                    add_sep(" (")
                elif storage['lastterm'] == 'convolution':
                    add_sep("(")
                else:
                    add_sep(" * (")

            start = end + 1
            storage['depth'] += 1
            continue

        if char == ")":
            mnum = add_term(start, end, mnum, storage)

            # Check to see whether we can close out the convolution.
            #
            check_end_convolution(storage)

            if end == maxchar:
                add_sep(")")
            elif expr[end + 1] in "+*-/":
                add_sep(") ")
            else:
                add_sep(") * ")

            start = end + 1
            storage['depth'] -= 1
            continue

        mnum = add_term(start, end, mnum, storage)

        # conv*a1+a2 is conv(s1) + a2
        if char == '+':
            check_end_convolution(storage)

        # If we had conv*mdl then we want to drop the *
        # but conv*m1*a1 is conv(m1*a1)
        #
        if not(char == '*' and in_convolution(storage) and out[0][-1][1] is None and out[0][-1][0] == "("):
            # Add space characters to separate out the expression,
            # even if start==end.
            #
            add_sep(f" {char} ")

        start = end + 1

    # Last name, which is not always present.
    #
    if start < end:
        add_term(start, None, mnum, storage)

    # I'm not sure whether this should only be done if start < end.
    # I am concerned we may have a case where this is needed.
    #
    check_end_convolution(storage)

    if storage['convolution'] is not None:
        print("WARNING: convolution model may not be handled correctly.")

    if storage['depth'] != 0:
        print("WARNING: unexpected issues handling brackets in the model")

    return out


# The conversion routine. The functionality needs to be split out
# of this.
#
def convert(infile, chisq="chi2datavar", clean=False, explicit=None):
    """Convert a XSPEC xcm file into Sherpa commands.

    The XSPEC save command will create an ASCII representation of the
    XSPEC session (perhaps just the models or files).

    Parameters
    ----------
    infile : str or fileio-like
        The file containing the XCM files. It can be a file name or a
        file handle, in which case the read method is used to access
        the data.
    chisq : str, optional
        The Sherpa chi-square statistic to use for "statistic chi".
        Unfortunately 'chi2xspecvar' is known to not match XSPEC
        in CIAO 4.13.
    clean : bool, optional
        Should the commands start with a call to clean()? This should
        only be used when the XCM file loads in data.
    explicit : str or None, optional
        If None then all Sherpa symbols are assumed to have been
        imported from sherpa.astro.ui, otherwise it is the name given
        to the module.

    Returns
    -------
    commands : list of str
        The Sherpa commands to try and re-create the XSPEC session. It
        will not match everything, as the two systems do not have the
        same exact capabilities.

    """

    try:
        intext = infile.readlines()
    except AttributeError:
        intext = open(infile, 'r').readlines()

    # TODO: convert the output routines (*add*) to a class.
    #
    out_imports = []
    def add_import(expr):
        """Add the import if we haven't alredy done so"""

        if expr in out_imports:
            return

        out_imports.append(expr)

    out = []

    def add_spacer(always=True):
        if not always and len(out) > 0 and out[-1] == '':
            return

        out.append('')

    def madd(expr, expand=False):
        if expand:
            if explicit is None:
                expr = expr.replace('XX', '')
            else:
                expr = expr.replace('XX', f'{explicit}.')

        out.append(expr)

    if explicit is None:
        def sym(name):
            """Expand the symbol name"""
            return name

    else:
        def sym(name):
            """Expand the symbol name"""
            return f"{explicit}.{name}"

    def add(name, *args, expand=True, **kwargs):
        if expand:
            name = sym(name)

        cstr = f"{name}("

        arglist = [str(a) for a in args] + \
            [f"{k}={v}" for k, v in kwargs.items()]
        cstr += ", ".join(arglist)

        cstr += ")"
        out.append(cstr)

    # START
    #
    if explicit is None:
        add_import("from sherpa.astro.ui import *")
    else:
        add_import(f"import sherpa.astro.ui as {explicit}")

    if clean:
        add("clean")

    # Store information about datasets, responses, and models.
    #
    state = {'nodata': True,  # set once a data command is found

             'statistic': 'chi',
             'subtracted': False,
             'nobackgrounds': [], # contains dataset with no background

             # I still don't have a good grasp on the internal structures
             # used by XSPEC, so I have both 'group' and 'sourcenum'.
             #
             'group': defaultdict(list),
             'datasets': [],

             # Map of those datasets with extra sourcenum values,
             # and then the map of what sourcenum values are
             # associated with each dataset.
             #
             'sourcenum': defaultdict(list),
             'datanum': defaultdict(list),
             'exprs': {},
             'allpars': {},
             'names': set()
    }

    # Processing is just a hard-coded set of rules.
    #
    while len(intext) > 0:
        xline = intext.pop(0).strip()
        if xline == '' or xline.startswith('#'):
            # Is there a comment character in XCM files?
            continue

        toks = xline.split()
        ntoks = len(toks)
        command = toks[0].lower()
        dbg(f"[{command}] - {xline}")

        if command in ['bayes', 'systematic']:
            dbg(f"Skipping")
            continue

        if command == 'method':
            # Assume we have method after data so a nice place to put a spacer
            add_spacer(always=False)

            meth = toks[1].lower()
            if meth == 'leven':
                add('set_method', "'levmar'")
            elif meth == 'simplex':
                add('set_method', "'simplex'")
            else:
                add('print', f"'WARNING: there is no equivalent to METHOD {meth}'")

            continue

        if command == 'statistic':
            if ntoks == 1:
                raise ValueError(f"Missing STATISTIC option: '{xline}'")

            stat = toks[1].lower()
            if stat == 'chi':
                add('set_stat', f"'{chisq}'")
            elif stat.startswith('cstat'):
                add('print', "'WARNING: Have chosen cstat but wstat statistic may be better'")
                add('set_stat', "'cstat'")
            else:
                add('print', f"'WARNING: there is no equivalent to STATISTIC {stat}'")

            state['statistic'] = stat
            continue

        if command in ['abund', 'xsect']:
            if ntoks == 1:
                raise ValueError(f"Missing {command.upper()} option: '{xline}'")

            add(f'set_xs{command}', f"'{toks[1]}'")
            continue

        if command == 'cosmo':
            if ntoks != 4:
                raise ValueError(f"Expected 3 arguments for COSMO: '{xline}'")

            add('set_xscosmo', *toks[1:])
            continue

        if command == 'xset':
            # May need to handle values with spaces in
            if ntoks != 3:
                raise ValueError(f"Expected 2 arguments for XSET: '{xline}'")

            # We skip the delta setting
            if toks[1] == 'delta':
                dbg("Skipping 'xset delta'")
                continue

            # At the moment force this to a string value. This may
            # not be sensible.
            add('set_xsxset', f"'{toks[1]}'", f"'{toks[2]}'")
            continue

        # We do not support all data options, such as
        #    - setting a value to none
        #    - setting multiple files in a single command
        #    - using {...} to apply multiple components
        #
        if command == 'data':
            if state['subtracted']:
                raise ValueError("XCM file is too complex: calling DATA after METHOD is not supported.")

            if ntoks < 2:
                raise ValueError(f"Missing DATA options: '{xline}'")

            if ntoks > 3:
                raise ValueError(f"Unsupported DATA syntax: '{xline}'")

            state['nodata'] = False

            if ntoks == 2:
                assert len(state['datasets']) == 0
                add('load_pha', f"'{toks[1]}'", use_errors=True)
                state['datasets'].append(1)
                continue

            groupnum, datanum = parse_dataid(toks[1])
            if groupnum is None:
                groupnum = 1

            state['group'][groupnum].append(datanum)
            state['datasets'].append(datanum)
            add('load_pha', datanum, f"'{toks[2]}'", use_errors=True)
            continue

        # similar to data but
        #  - error out if a group number is given
        #  - handle the none setting
        #
        # Let's just assume the source already exists.
        #
        if command == 'background':
            if state['subtracted']:
                raise ValueError("XCM file is too complex: calling BACKGROUND after METHOD is not supported.")

            if ntoks < 2:
                raise ValueError(f"Missing BACKGROUND options: '{xline}'")

            if ntoks > 3:
                raise ValueError(f"Unsupported BACKGROUND syntax: '{xline}'")

            if ntoks == 2:
                if toks[1] == 'none':
                    state['nobackgrounds'].append(1)
                else:
                    add('load_background', f"'{toks[1]}'")
                continue

            groupnum, datanum = parse_dataid(toks[1])
            if groupnum is not None:
                raise ValueError(f"Unsupported BACKGROUND syntax: '{xline}'")

            if toks[2] == 'none':
                state['nobackgrounds'].append(datanum)
            else:
                add('load_background', f"'{toks[2]}'")
            continue

        # We do not support all response options, such as
        #    - setting a value to none
        #    - setting multiple files in a single command
        #    - using {...} to apply a component
        #    - automatically loading multiple responses from a file
        #
        # I think we can use load_rmf to load a RSP file.
        #
        if command in ['arf', 'response']:
            if ntoks < 2:
                raise ValueError(f"Missing {command.upper()} options: '{xline}'")

            if ntoks > 3:
                raise ValueError(f"Unsupported {command.upper()} syntax: '{xline}'")

            if command == 'arf':
                command = 'load_arf'
            elif command == 'response':
                command = 'load_rmf'
            else:
                raise NotImplementedError(f"Internal error: command={command}")

            if ntoks == 2:
                add(command, f"'{toks[1]}'")
                continue

            sourcenum, datanum = parse_dataid(toks[1])

            kwargs = {}
            if sourcenum is not None and sourcenum != 1:
                kwargs['resp_id'] = sourcenum
                state['sourcenum'][sourcenum].append(datanum)
                state['datanum'][datanum].append(sourcenum)

            add(command, datanum, f"'{toks[2]}'", **kwargs)
            continue

        if command in ['ignore', 'notice']:
            if ntoks == 1:
                raise ValueError(f"Missing {command.upper()} option: '{xline}'")

            parse_notice_range(add_import, add, state['datasets'], command, toks[1:])
            continue

        if command == 'model':
            # Need some place to set up subtract calls, so pick here
            #
            add_spacer(always=False)

            set_subtract(add_import, add_spacer, add, state)

            # Now, the XCM file may not contain any data statements,
            # so if so we assume a single dataset only. This is done
            # after the set_subtract call.
            #
            if state['nodata']:
                state['datasets'] = [1]
                state['group'][1] = [1]

            # I find it useful to point out the models being processed
            #
            print(xline)
            madd(f"# {xline}")

            if ntoks == 1:
                raise ValueError(f"Missing MODEL option: '{xline}'")

            # do we have a sourcenumber?
            #
            rest = xline[5:]
            tok = rest.split()[0]
            if ':' in tok:

                toks = tok.split(':')
                emsg = f"Unable to parse spectrum number of MODEL: '{xline}'"
                if len(toks) != 2:
                    raise ValueError(emsg)

                try:
                    sourcenum = int(toks[0])
                except ValueError:
                    raise ValueError(emsg) from None

                label = toks[1]
                rest = rest.strip()[len(tok) + 1:]

            else:
                sourcenum = None
                label = None

            # If there's no spectrum number then we want an expression
            # for each group. It there is a spectrum number then
            # we only want those spectra with a response for that
            # spectrum number.
            #
            # I really shouldn't use the term "groups" here as it
            # muddies the water.
            #
            if label is None:
                label = "unnamed"
                postfix = ''
                groups = sorted(list(state['group'].keys()))
            else:
                postfix = f"s{sourcenum}"
                groups = sorted(state['sourcenum'][sourcenum])

            exprs = convert_model(rest, postfix, groups, state['names'])

            assert len(groups) > 0
            assert sourcenum not in state['exprs'], sourcenum
            state['exprs'][sourcenum] = exprs

            # We create the model components here, but do not create the
            # full source model until the end of the script, since
            # we may need to handle multiple source "spectra".
            #
            for expr in exprs:
                for cpt in expr:
                    if cpt[1] is None:
                        continue

                    mtype, mname = cpt[0]
                    madd(f"{mname} = XXcreate_model_component('{mtype}', '{mname}')",
                         expand=True)

            # Create the list of all parameters, so we can set up links.
            # Note that we store these with the label, not sourcenumber,
            # since this is how they are referenced.
            #
            assert label not in state['allpars'], label
            state['allpars'][label] = []
            for expr in exprs:
                for mdl in [t[1] for t in expr if t[1] is not None]:
                    for par in mdl.pars:
                        if par.hidden:
                            continue

                        state['allpars'][label].append(par)

            # Process all the parameter values for each data group.
            #
            for expr in exprs:
                for mdl in [t[1] for t in expr if t[1] is not None]:

                    for par in mdl.pars:
                        if par.hidden:
                            continue

                        # Grab the parameter line
                        pline = intext.pop(0).strip()

                        if pline.startswith('='):
                            tlabel, tienum, tprefix = parse_tie(pline)
                            try:
                                tpar = state['allpars'][tlabel][tienum - 1]
                            except IndexError:
                                raise ValueError(f"Invalid tie in '{pline}'") from None

                            add('link', f"{par.fullname}", f"{tprefix}{tpar.fullname}")
                            continue

                        toks = pline.split()
                        if len(toks) != 6:
                            raise ValueError(f"Unexpected parameter line '{pline}'")

                        # We always set the parameter value, but only change the
                        # limits if they are different. We only look at the "soft"
                        # limits.
                        #
                        lmin = float(toks[3])
                        lmax = float(toks[4])

                        args = [par.fullname, toks[0]]
                        kwargs = {}

                        if lmin != par.min:
                            kwargs['min'] = toks[3]

                        if lmax != par.max:
                            kwargs['max'] = toks[4]

                        if toks[1].startswith('-'):
                            kwargs['frozen'] = True

                        add('set_par', *args, **kwargs)

            continue

        print(f"SKIPPING '{xline}'")

    # We need to create the source models. This is left till here because
    # Sherpa handles "multiple specnums" differently to XSPEC.
    #

    def conv(t):
        if t[1] is None:
            return t[0]

        return t[0][1]

    # Technically we could have no model expression, but assume that is unlikely
    madd("")
    madd("# Set up the model expressions")
    madd("#")

    # The easy case:
    #
    exprs = state['exprs']
    if len(state['sourcenum']) == 0:
        if list(exprs.keys()) != [None]:
            raise RuntimeError("Unexpected state when processing the model expressions in the XCM file!")

        if len(exprs[None]) != 1:
            raise RuntimeError("Unexpected state when processing the model expressions in the XCM file!")

        assert len(exprs[None]) == 1
        cpts = [conv(t) for t in exprs[None][0]]
        sexpr = "".join(cpts)
        for did in state['datasets']:
            add('set_source', did, sexpr)

    else:
        # What "specnums" do we have to deal with?
        #   'unnamed' + <numbers>
        #
        # We need to check each dataset to see what specnums we care about.
        #
        if len(exprs[None]) != len(state['datasets']):
            # I am not convinced this is a requirement
            raise RuntimeError("Unexpected state when handling multiple sourcenum components!")

        # Response1D only seems to use the default response id.
        #
        add_import('from sherpa.astro.instrument import Response1D')

        for did, expr in zip(state['datasets'], exprs[None]):

            madd(f"# source model for dataset {did}")

            try:
                snums = state['datanum'][did]
            except KeyError:
                # I should probably add a mapping to unnamed when we have the
                # first data or model command.
                #
                snums = []

            cpts = [conv(t) for t in expr]
            sexpr = "".join(cpts)

            if snums == []:
                # Easy
                add('set_source', did, sexpr)
                continue

            madd(f"d = get_data({did})")
            madd(f"m = {sexpr}")
            madd("fmdl = Response1D(d)(m)")

            # Identifying the source expression is more-awkward than it needs
            # to be!
            #
            for snum in snums:

                xs = state['sourcenum'][snum]
                if len(exprs[snum]) != len(xs):
                    raise RuntimeError("Unexpected state when handling multiple sourcenum components!")

                found = False
                for xid, xexpr in zip(xs, exprs[snum]):
                    if xid != did:
                        continue

                    cpts = [conv(t) for t in xexpr]
                    sexpr = "".join(cpts)
                    found = True

                    add_import('from sherpa_contrib.xspec import xcm')
                    madd(f"m = {sexpr}")
                    madd(f"fmdl += xcm.Response1D(d, {snum})(m)")
                    break

                if not found:
                    raise RuntimeError(f"Unable to find expression for sourcenum={snum} with dataset {did}")

            add('set_full_model', did, 'fmdl')
            madd("")

    return "\n".join(out_imports + [""] + out) + "\n"
