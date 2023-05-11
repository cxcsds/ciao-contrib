#
#  Copyright (C) 2020, 2023
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
Convert a XSPEC xcm file into Sherpa.

The intention is to make it possible to convert an XSPEC model
session into Sherpa, but without a guarantee of 100% fidelity.
The idea is that further work may be needed to allow full
analysis in Sherpa.

"""

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import importlib
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from sherpa.astro import ui  # type: ignore
from sherpa.astro.ui.utils import Session  # type: ignore
from sherpa.astro import xspec  # type: ignore
from sherpa.models.basic import ArithmeticModel, UserModel  # type: ignore
from sherpa.models.parameter import Parameter, CompositeParameter, ConstantParameter  # type: ignore
from sherpa.utils.err import ArgumentErr, DataErr  # type: ignore

import sherpa.astro.instrument  # type: ignore
import sherpa.models.parameter  # type: ignore
import sherpa.utils             # type: ignore

import ciao_contrib.logger_wrapper as lw  # type: ignore


__all__ = ("convert", )

lgr = lw.initialize_module_logger(__name__)
v1 = lgr.verbose1
v2 = lgr.verbose2
v3 = lgr.verbose3
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


def notice(spectrum: int, lo: int, hi: int, ignore: bool = False) -> None:
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

        v2(f"Converting group {lo}-{hi} to {elo:.3f}-{ehi:.3f} keV [ignore={ignore}]]")
        d.notice(elo, ehi, ignore=ignore)
        return

    if d.units == 'wavelength':
        whi = d._channel_to_energy(lo)
        wlo = d._channel_to_energy(hi)

        v2(f"Converting group {lo}-{hi} to {wlo:.5f}-{whi:.5f} A [ignore={ignore}]]")
        d.notice(wlo, whi, ignore=ignore)
        return

    if d.units != 'channel':
        raise ValueError(f"Unexpected analysis setting for spectrum {spectrum}: {d.units}")

    # Convert from group number (XSPEC) to channel units
    clo = d._group_to_channel(lo)
    chi = d._group_to_channel(hi)

    v2(f"Converting group {lo}-{hi} to channels {clo}-{chi} [ignore={ignore}]]")
    d.notice(clo, chi, ignore=ignore)


def ignore(spectrum: int, lo: int, hi: int) -> None:
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


def subtract(spectrum: int) -> None:
    """Subtract the background (a no-op if there is no background).

    Parameters
    ----------
    spectrum : int
        Dataset identifier.
    """

    try:
        ui.subtract(spectrum)
    except DataErr:
        v1(f"Dataset {spectrum} has no background data!")


def _mklabel(func: Callable) -> str:
    """Create a 'nice' symbol for the function.

    Is this worth it over just using __name__?

    Parameters
    ----------
    func : function reference

    Returns
    -------
    label : str
        A representation of the function.
    """

    if isinstance(func, np.ufunc):
        return 'np.'

    try:
        lbl = f'{func.__module__}.'
    except AttributeError:
        return ''

    if lbl == 'builtins.':
        return ''

    return lbl


class FunctionParameter(CompositeParameter):
    """Store a function of a single argument.

    We need to only evalate the function when required.
    """

    @staticmethod
    def wrapobj(obj):
        if isinstance(obj, Parameter):
            return obj
        return ConstantParameter(obj)

    def __init__(self, arg, func):

        if not callable(func):
            raise ValueError("func argument is not callable!")

        self.arg = self.wrapobj(arg)
        self.func = func

        # Would like to be able to add the correct import symbol here
        lbl = _mklabel(func)
        lbl += f'{func.__name__}({self.arg.fullname})'
        CompositeParameter.__init__(self, lbl, (self.arg,))

    def eval(self):
        return self.func(self.arg.val)


class Function2Parameter(CompositeParameter):
    """Store a function of two arguments.

    We need to only evalate the function when required.
    """

    @staticmethod
    def wrapobj(obj):
        if isinstance(obj, Parameter):
            return obj
        return ConstantParameter(obj)

    def __init__(self, arg1, arg2, func):

        if not callable(func):
            raise ValueError("func argument is not callable!")

        self.arg1 = self.wrapobj(arg1)
        self.arg2 = self.wrapobj(arg2)
        self.func = func

        # Would like to be able to add the correct import symbol here
        lbl = _mklabel(func)
        lbl += f'{func.__name__}({self.arg1.fullname}, {self.arg2.fullname})'
        CompositeParameter.__init__(self, lbl, (self.arg1, self.arg2))

    def eval(self):
        return self.func(self.arg1.val, self.arg2.val)


def exp(x):
    """exp(x)"""
    return FunctionParameter(x, np.exp)


def sin(x):
    """sin where x is in radians."""
    return FunctionParameter(x, np.sin)


def sind(x):
    """sin where x is in degrees."""
    # could use np.deg2rad but would need to wrap that
    return FunctionParameter(x * np.pi / 180, np.sin)


def cos(x):
    """cos where x is in radians."""
    return FunctionParameter(x, np.cos)


def cosd(x):
    """cos where x is in degrees."""
    # could use np.deg2rad but would need to wrap that
    return FunctionParameter(x * np.pi / 180, np.cos)


def tan(x):
    """tan where x is in radians."""
    return FunctionParameter(x, np.tan)


def tand(x):
    """tan where x is in degrees."""
    # could use np.deg2rad but would need to wrap that
    return FunctionParameter(x * np.pi / 180, np.tan)


def log(x):
    """logarithm base 10"""
    return FunctionParameter(x, np.log10)


def ln(x):
    """natural logarithm"""
    return FunctionParameter(x, np.log)


def sqrt(x):
    """sqrt(x)"""
    return FunctionParameter(x, np.sqrt)


def abs(x):
    """abs(x)"""
    return FunctionParameter(x, np.abs)


def asin(x):
    """arcsin where x is in radians."""
    return FunctionParameter(x, np.arcsin)


def acos(x):
    """arccos where x is in radians."""
    return FunctionParameter(x, np.arccos)


# It's not entirely clear that int maps to floor
def xint(x):
    """floor(x)"""
    return FunctionParameter(x, np.floor)


def xmin(x, y):
    """Return the minimum value"""
    return Function2Parameter(x, y, min)


def xmax(x, y):
    """Return the maximum value"""
    return Function2Parameter(x, y, max)


# Routines used in converting a script.
#
def set_subtract(add_import: Callable[[str], None],
                 add_spacer: Callable[[], None],
                 add: Callable[..., None],
                 state: Dict[str, Any]) -> None:
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


def parse_tie(pars, add_import, add, par, pline) -> None:
    """Parse a tie line.

    The idea is to convert p<integer> or <integer> to the
    correct parameter name. We should support multiple
    substitutions and also <modelname><integer>.

    Parameters
    ----------
    pars : dict
        The parameters for each "label".
    add_import : function reference
        Add an import
    add : function reference
        Add a command to the record
    par : str
        The full parameter name (e.g. foo.xpos) being linked
    pline : str
        The tie line.

    """

    assert pline.startswith('= ')
    line = pline[1:].strip()

    # I have seen the line
    #   '= 1.6392059E + 02*pbg3:2'
    # which I am going to assume is 1.639e+02*pbg3:2, so let's just
    # remove the spaces.
    #
    line = line.translate({32: None})

    # Build up the link expression.
    #
    expr = ''
    token = ''
    exponentiation = False
    while line != '':
        fchar = line[0]

        # The * character can be an exponentiation
        #
        if fchar == '*' and len(line) > 1 and line[1] == '*':
            if exponentiation:
                raise ValueError(f"Unable to parse {pline}")

            exponentiation = True
            continue

        # The +/- characters can be in a numeric expresion
        #
        if fchar in "+-" and token != '' and token[-1].lower() == 'e':
            token += fchar
            line = line[1:]
            continue

        # Have we ended the token?
        #
        if fchar in "()+*/-^":
            if token != '':
                token = expand_token(add_import, pars, par, token)
                expr += token
                token = ''

            if exponentiation or fchar == '^':
                expr += "**"
                exponentiation = False
            else:
                expr += fchar

            line = line[1:]
            continue

        if exponentiation:
            raise ValueError(f"Unable to parse {pline}")

        token += fchar
        line = line[1:]

    if exponentiation:
        raise ValueError(f"Unable to parse {pline}")

    if token != '':
        token = expand_token(add_import, pars, par, token)
        expr += token

    add('link', par, expr)


def expand_token(add_import, pars, pname, token) -> str:
    """Is this a reference to a parameter?

    Ideally we'd add a '.val' to the parameter value when we
    know we are in a function.
    """

    def import_xcm():
        add_import('from sherpa_contrib.xspec import xcm')

    # Hard code the function names. This allows us to replace
    # symbols if needed (such as the degree variants of the
    # trigonometric functions).
    #
    # We assume that the token is used correctly (e.g. that
    # "min" is followed by "(").
    #
    ltoken = token.lower()

    if ltoken == 'mean':
        v1(f"Use of MEAN found in parameter tie for {pname}: please review")
        return 'mean'

    if ltoken in ["exp", "sin", "cos", "tan", "sqrt", "abs",
                  "sind", "cosd", "tand", "asin", "acos",
                  "ln", "log"]:
        import_xcm()
        return f'xcm.{ltoken}'

    if ltoken in ["int", "min", "max"]:
        import_xcm()
        return f'xcm.x{ltoken}'

    # We want to look for
    #   a:b
    #   p<int>
    #   int
    #
    if ':' in token:
        # I don't think this can be anything but a parameter reference
        #
        toks = token.split(':')
        if len(toks) != 2:
            raise ValueError(f"Unsupported parameter tie: '{token}'")

        try:
            plist = pars[toks[0]]
        except KeyError:
            raise ValueError(f"Unrecognized model name {toks[0]} in '{token}'") from None

        try:
            tie = int(toks[1])
        except ValueError:
            raise ValueError(f"Not a parameter number in '{token}'") from None

        try:
            tpar = plist[tie - 1]
        except IndexError:
            raise ValueError(f"Invalid parameter number in '{token}'") from None

        return tpar.fullname

    # See if we can convert the token to an integer (beginnnig with
    # p or not). If we can't we just return the token.
    #
    if token.startswith('p'):
        tie = token[1:]
    else:
        tie = token

    try:
        tie = int(tie)
    except ValueError:
        return token

    # At this point we are sure we have a parameter reference.
    #
    try:
        plist = pars['unnamed']
    except KeyError:
        raise RuntimeError("Internal error accessing parameter names") from None

    try:
        tpar = plist[tie - 1]
    except IndexError:
        raise ValueError(f"Invalid parameter number in '{token}'") from None

    return tpar.fullname


def parse_dataid(token: str) -> Tuple[Optional[int], int]:
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
        itoks = [int(t) for t in toks]
    except ValueError:
        raise ValueError(emsg) from None

    if ntoks == 2:
        return itoks[0], itoks[1]

    return None, itoks[0]


RangeValue = Union[int, float]

def parse_ranges(ranges: str) -> Tuple[str, List[Tuple[Optional[RangeValue], Optional[RangeValue]]]]:
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

    store = {"chantype": "channel"}

    def lconvert(val: str) -> Optional[RangeValue]:
        if '.' in val:
            try:
                out = float(val)
                store["chantype"] = "other"
                return out
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
            end = lconvert(rs[0])
            start = end
            #if len(out) == 0:
            #    start = 1  # is this correct?
            #else:
            #    start = end
        elif len(rs) == 2:
            start = lconvert(rs[0])
            end = lconvert(rs[1])
        else:
            raise ValueError(f"Unexpected range in '{ranges}'")

        out.append((start, end))

    return store["chantype"], out


def parse_notice_range(add_import: Callable[[str], None],
                       add: Callable[..., None],
                       datasets: List[int],
                       command: str,
                       tokens: List[str]) -> None:
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


SimpleToken = Union[str, ArithmeticModel]


class Term(Enum):
    """The "type" of an XSPEC model."""

    ADD = 1
    MUL = 2
    CON = 3


MODEL_TYPES = {t.name: t for t in list(Term)}


@dataclass
class MDefine:
    name: str
    expr: str        # the original expression
    params: List[str]
    models: List[str]
    converted: str   # the Python version of the model (likely needs reworking)
    mtype: Term
    erange: Optional[Tuple[float, float]]


def is_model_convolution(mdl: Union[xspec.XSModel, MDefine]) -> bool:
    """Is this a convolution model"""

    if isinstance(mdl, MDefine):
        return mdl.mtype == Term.CON

    return isinstance(mdl, xspec.XSConvolutionKernel)


def is_model_multiplicative(mdl: Union[xspec.XSModel, MDefine]) -> bool:
    """Is this a multiplicative model"""

    if isinstance(mdl, MDefine):
        return mdl.mtype == Term.MUL

    return isinstance(mdl, xspec.XSMultiplicativeModel)


def is_model_additive(mdl: Union[xspec.XSModel, MDefine]) -> bool:
    """Is this an additive model"""

    if isinstance(mdl, MDefine):
        return mdl.mtype == Term.ADD

    return isinstance(mdl, xspec.XSAdditiveModel)


def create_session(models: Optional[List[str]]) -> Tuple[Session, List[str]]:
    """Create a Sherpa session into which XSPEC models have been loaded.

    Parameters
    ----------
    models : list of str or None
        The models created by convert_xspec_user_model to
        import.

    Returns
    -------
    session, extras : Session, list of str
        The Sherpa session object and the list of any "extra"
        models that have been loaded from the models arguments.

    """

    MODTYPES = (xspec.XSAdditiveModel,
                xspec.XSMultiplicativeModel,
                xspec.XSConvolutionKernel)

    # Create our own session object to make it easy to
    # find out XSPEC models and the correct naming scheme.
    #
    session = Session()
    session._add_model_types(xspec, MODTYPES)

    extras: List[str] = []
    if models is None:
        return session, extras

    # Need to register the XSPEC user models.
    #
    for model in models:
        lmod = importlib.import_module(model)
        session._add_model_types(lmod, MODTYPES)

        for symbol in lmod.__all__:
            cls = getattr(lmod, symbol)
            if issubclass(cls, MODTYPES):
                extras.append(symbol.lower())

    return session, extras


def handle_xspecmodel(session: Session,
                      model: str,
                      cpt: str,
                      madd: Optional[Callable[..., None]] = None) -> Optional[tuple[xspec.XSModel, Term]]:
    """Create a model instance for an XSPEC model.

    Parameters
    ----------
    session : Session
        The session to query/add to.
    model : str
        The model name (e.g. phabs). It should not begin with xs as it's
        the name from the XCM script.
    cpt : str
        The component name for the model.
    madd : callable, optional
        Create the model text (if wanted)

    Notes
    -----

    To support XSPEC user models, which could have arbitrary prefixes,
    we try several options. It may turn out that we need to get the
    user to report the prefix, or to grab it from the module metadata
    (unfortunately we do not store it yet), bit for now just try the
    "obvious" options:

        prefix = xs    - the standard XSPEC models or --prefix xs
        prefix = xsum  - default for convert_xspec_user_script
        prifix =       - User used --prefix

    """

    for prefix in ["xs", "xsum", ""]:
        try:
            v3(f"Looking for XSPEC model '{model}' with prefix '{prefix}'")
            mname = f"{prefix}{model}"
            mdl = session.create_model_component(mname, cpt)
            if madd is not None:
                madd(f"{cpt} = XXcreate_model_component('{mname}', '{cpt}')",
                     expand=True)

            if isinstance(mdl, xspec.XSAdditiveModel):
                mtype = MODEL_TYPES["ADD"]
            elif isinstance(mdl, xspec.XSMultiplicativeModel):
                mtype = MODEL_TYPES["MUL"]
            elif isinstance(mdl, xspec.XSConvolutionKernel):
                mtype = MODEL_TYPES["CON"]
            else:
                raise ValueError(f"Unable to recognize XSPEC model {mname}: {mdl}")

            return mdl, mtype

        except ArgumentErr:
            pass

    return None


def create_source_expression(expr: List[SimpleToken]) -> str:
    "create a readable source expression"

    v3(f"Processing an expression of {len(expr)} terms")
    v3(f"Expression: {expr}")

    def tokenize(t: SimpleToken) -> str:
        if isinstance(t, ArithmeticModel):
            # want the "name", so "gal" in "xsphabs.gal"
            toks = t.name.split(".")
            return toks[-1]

        return t

    cpts = [tokenize(t) for t in expr]
    out = "".join(cpts)
    v3(f" -> {out}")
    return out


def make_component_name(postfix: str, ngroups: int, ctr: int, grp: int) -> str:
    name = f"m{ctr}{postfix}"
    if ngroups > 1:
        name += f"g{grp}"

    return name


def handle_tablemodel(session: Session,
                      expr: str,
                      gname: str,
                      add: Callable[..., None],
                      madd: Callable[..., None]) -> Tuple[xspec.XSTableModel, Term]:
    """Create a tablemodel (it the file can be found)"""

    if expr.startswith("atable{"):
        mtype = MODEL_TYPES["ADD"]
    elif expr.startswith("mtable{"):
        mtype = MODEL_TYPES["MUL"]
    elif expr.startswith("etable{"):
        mtype = MODEL_TYPES["MUL"]
    else:
        raise ValueError(f"Expected a tablemodel, found '{expr}'")

    if not expr.endswith('}'):
        raise ValueError(f"No }} in {expr}")

    v2(f"Handling TABLE model: {expr} for {gname}")
    tbl = expr[7:-1]
    kwargs = {}
    if expr.startswith("etable"):
        kwargs['etable'] = True

    try:
        session.load_xstable_model(gname, tbl, **kwargs)
    except FileNotFoundError:
        raise ValueError(f"Unable to find XSPEC table model: {tbl}") from None

    mdl = session.get_model_component(gname)

    if mdl.etable:
        kwargs = {"etable": True}
    else:
        kwargs = {}

    add("load_xstable_model", f"'{gname}'", f"'{tbl}'",
        expand=True, **kwargs)

    # Not really needed but just in case
    madd(f"{gname} = XXget_model_component('{gname}')",
         expand=True)

    return mdl, mtype


def dummy_model(pars, elo, ehi=None):
    raise NotImplementedError()


def handle_mdefine(session: Session,
                   mdefines: List[MDefine],
                   basename: str,
                   gname: str,
                   add: Callable[..., None]) -> Optional[Tuple[UserModel, Term]]:
    """Is this a mdefine model?

    Note we actually create a model (with a dummy function)
    as it makes downstream processing easier to handle.
    """

    for mdefine in mdefines:
        if mdefine.name != basename:
            continue

        v2(f"Handling MDEFINE model: {basename} for {gname}")

        add("load_user_model", f"model_{basename}", f"'{gname}'",
            expand=True)
        add("add_user_pars", f"'{gname}'", str(mdefine.params),
            expand=True)

        session.load_user_model(dummy_model, gname)
        session.add_user_pars(gname, mdefine.params)
        mdl = session.get_model_component(gname)
        return mdl, mdefine.mtype

    return None


# The return vaue is not typed as this causes mypy no end of problems
# that I don't want to deal with just yet.
#
def convert_model(session: Session,
                  extra_models: List[str],
                  expr: str,
                  postfix: str,
                  groups: List[int],
                  mdefines: List[MDefine],
                  add: Callable[..., None],
                  madd: Callable[..., None]):  # mypy falls over if use -> List[List[SimpleToken]]:
    """Extract the model components.

    Model names go from m1 to mn (when groups is empty) or
    m1g1 to mng1 and then m1g2 to mng<ngrops>.

    Parameters
    ----------
    session : Session
        The Sherpa session used to define/create models.
    extra_models : list of str
        The XSPEC user models to search from.
    expr : str
        The XSPEC model expression.
    postfix : str
        Add to the model + number string.
    groups : list of int
        The groups to create. It must not be empty. We special case a
        single group, as there's no need to add an identifier.
    mdefines : list of MDefine
    add, madd : callable
        Create the output.

    Returns
    -------
    exprs : list of list of tokens
        The model expression for each group (if groups was None then
        for a single group).

    Notes
    -----
    We require the Sherpa XSPEC module here.

    This routine does not take advantage of the knowledge that a
    model "sub expression" ends in an additive model - e.g. m1*m2*m3.
    So, for instance, we would know we don't have to deal with
    closing brackets when processing a multiplcative model.
    """

    v2(f"Processing model expression: {expr}")

    # First tokenize. Note that we assume this is a valid XSPEC
    # expression, so we can make a number of assumptions about the
    # input.
    #
    toks = tokenize_model_expr(session, extra_models, expr,
                               mdefines=mdefines)

    ngroups = len(groups)
    if ngroups == 1:
        # TODO: mypy complains about this as groups: List[int]; this
        # should be redesigned.
        groups = [None]

    # Need an output list for each group
    out: List[List[SimpleToken]] = [[] for g in groups]

    # We need to address differences in the XSPEC and Sherpa
    # model language:
    #
    # - need to add multiplication for cases like "(...)model"
    # - need to handle mdl1(mdl2) for multiplicative models
    # - convert cmdl*amdl[*...] to cmdl(amdl[*...]) for
    #   convolution models
    #
    v2(f"Found {len(toks)} tokens in the model expression")
    v3(f"expression: {toks}")
    in_convolution = False
    fake_bracket = False
    ctr = 1

    # What was the previous model type (add, mul, con)? This is
    # separate to the in_convolution check.
    #
    prev_model_type = None

    for i, tok in enumerate(toks, 1):
        v2(f"  token {i} = '{tok}'")
        v3(f"    bracket={fake_bracket} convolution={in_convolution}")

        if tok == "(":

            # If the previous term was a multiplicative model
            # then add in a * term.
            #
            if prev_model_type is not None and \
               prev_model_type == Term.MUL:
                tok = " * ("

            for outlist in out:
                outlist.append(tok)

            prev_model_type = None
            continue

        if tok == ")":
            if fake_bracket:
                for outlist in out:
                    outlist.append(")")

                fake_bracket = False

            for outlist in out:
                outlist.append(tok)

            in_convolution = False
            prev_model_type = None
            continue

        if tok == "+":
            if fake_bracket:
                for outlist in out:
                    outlist.append(")")

                fake_bracket = False

            for outlist in out:
                outlist.append(" + ")

            in_convolution = False
            prev_model_type = None
            continue

        # We need to worry about cmdl*amdl when cmdl is a convolution
        # model.
        #
        if tok == "*":
            # If the previous term as a convolution model then
            # drop the multiplication.
            #
            if prev_model_type is not None and \
               prev_model_type == Term.CON:
                # At this point we expect to have [..., model, "("]
                # thanks to the fake_bracket handling.
                #
                v3(f"  - found 'cmdl * ..' so dropping * for {outlist[-2].name}")

                # Should we clear prev_model_type?
                # prev_model_type = None
                continue

            for outlist in out:
                outlist.append(" * ")

            prev_model_type = None
            continue

        # This must be a model.
        #
        for i, grp in enumerate(groups, 1):
            outlist = out[i - 1]
            gname = make_component_name(postfix, ngroups, ctr, grp)

            if "{" in tok:
                mdl, mtype = handle_tablemodel(session, tok, gname, add, madd)
            else:
                answer = handle_xspecmodel(session, tok, gname, madd)
                if answer is None:
                    answer = handle_mdefine(session, mdefines, tok, gname, add)
                    if answer is None:
                        raise ValueError(f"Unable to convert {tok} to a model")

                mdl, mtype = answer

            outlist.append(mdl)

            # This is annoying to check as we need to loop over the
            # groups here, so can not change in_convolution or
            # fake_bracket until after the loop.
            #
            if mtype == Term.CON and not in_convolution:
                # Adding a bracket is needed to support con*m1*m2 syntax.
                # This a simple solution which can be improved upon.
                #
                outlist.append("(")

        v3(f" - found model token: {tok} - type: {mtype.name}")

        # Adjust in_convolution / fake_bracket if needed
        #
        if mtype == Term.CON:
            if in_convolution:
                print("WARNING: found a convolution term within a convolution")
            else:
                in_convolution = True
                fake_bracket = True

        prev_model_type = mtype

        # Update the counter for the next model
        ctr += 1

    # If the expression was just 'con*m1*m2' then need to add a
    # trailing bracket.
    #
    if fake_bracket:
        for outlist in out:
            outlist.append(")")

    v2(f"Found {len(out)} expressions")
    for i, eterm in enumerate(out):
        v2(f"Expression: {i + 1}")
        for token in eterm:
            if isinstance(token, ArithmeticModel):
                v2(f"  '{token.name}'")
            else:
                v2(f"  '{token}'")

    return out


FunctionDict = Dict[str, Optional[str]]


UNOP_TOKENS: FunctionDict = {
    "EXP": "np.exp",
    "SIN": "np.sin",
    "SIND": None,
    "COS": "np.cos",
    "COSD": None,
    "TAN": "np.tan",
    "TAND": None,
    "SINH": "np.sinh",
    "SINHD": None,
    "COSH": "np.cosh",
    "COSHD": None,
    "TANH": "np.tanh",
    "TANHD": "np.tanhd",
    "LOG": "np.log10",
    "LN": "np.log",
    "SQRT": "np.sqrt",
    "ABS": "np.abs",
    "INT": None,
    "ASIN": "np.arcsin",
    "ACOS": "np.arccos",
    "ATAN": "np.arctan",
    "ASINH": "np.arcsinh",
    "ACOSH": "np.aarccosh",
    "ATANH": "np.aarctanh",
    "ERF": "sherpa.utils.erf",
    "ERFC": None,
    "GAMMA": "sherpa.utils.gamma",
    "SIGN": None,
    "HEAVISIDE": None,
    "BOXCAR": None,
    "MEAN": "np.mean",
    "DIM": "np.size",  # is this correct?
    "SMIN": "np.min",
    "SMAX": "np.max"
}


BINOP_TOKENS: FunctionDict = {
    "ATAN2": "np.arctan2",  # does this match XSPEC?
    "MAX": None,
    "MIN": None
}


# Add helper functions to handle the UNOP and BINOP models which we
# can not just handle with numpy routines. As we do not actually parse
# the expressions, we can't easily add extra closing brackets to allow
# the <trigonometric>D forms to be inlined.
#
def SIND(x):
    return np.sin(np.deg2rad(x))

def COSD(x):
    return np.cos(np.deg2rad(x))

def TAND(x):
    return np.tan(np.deg2rad(x))

def SINHD(x):
    return np.sinh(np.deg2rad(x))

def COSHD(x):
    return np.cosh(np.deg2rad(x))

def TANHD(x):
    return np.tanh(np.deg2rad(x))

def SIGN(x):
    """-1 if negative, 1 if positive; assume 0 is positive"""
    return -1 + (np.asarray(x) >= 0) * 2

def HEAVISIDE(x):
    """0 if negative, 1 if positive; assume 0 is positive"""
    return (np.asarray(x) >= 0) * 1

def BOXCAR(x):
    """1 if 0 <= x <= 1, 0 elsewhere"""
    xx = np.asarray(x)
    return ((xx >= 0) & (xx <= 1)) * 1

def INT(x):
    """Can we assume everything is an array?"""
    if np.isscalar(x):
        return np.int(x)
    return np.asarray([np.int(xi) for xi in x])

def ERFC(x):
    return 1 - sherpa.utils.erf(x)

def MAX(x, y):
    """Is this a per-element max or are x and y only scalars?"""
    if np.isscalar(x) and np.isscalar(y):
        return np.max([x, y])
    raise RuntimeError("Unclear from documentation what MAX is meant to do here")

def MIN(x, y):
    """Is this a per-element min or are x and y only scalars?"""
    if np.isscalar(x) and np.isscalar(y):
        return np.min([x, y])
    raise RuntimeError("Unclear from documentation what MIN is meant to do here")


def parse_mdefine_expr(session: Session,
                       extra_models: List[str],
                       expr: str,
                       mdefines: List[MDefine]) -> Tuple[str, List[str], List[str]]:
    """Parse the model expression in a MDEFINE line.

    This is incomplete, as all we do is find what appear to be
    the model parameters.

    Parameters
    ----------
    session : Session
        The Sherpa session to use to find models.
    extra_models : list of str
        XSPEC user models created with convert_xspec_user_model.
    expr : str
        The model expression
    mdefines : list of MDefine
        The existing model definitions.

    Returns
    -------
    converted, pars : str, list of str, list of str
        The converted expression, parameter names found in the
        model, and any models used in the expression.

    """

    if not expr:
        raise ValueError("Model expression can not be empty")

    KNOWN_MODELS = [n[2:].upper() for n in session.list_models("xspec")] + \
        [m.upper() for m in extra_models] + \
        [m.name.upper() for m in mdefines]

    pnames: List[str] = []
    models: List[str] = []
    seen: Set[str] = set()
    out: List[str] = []

    def add_current(symbol: str) -> None:
        """Add the current symbol to the output."""

        if not symbol:
            return

        usymbol = symbol.upper()
        if usymbol in ["E", ".E"]:
            # For now we do not support convolution models so just punt here
            out.append(usymbol)
            return

        try:
            answer = UNOP_TOKENS[usymbol]
            if answer is None:
                out.append(f"xcm.{usymbol}")
            else:
                out.append(answer)
            return
        except KeyError:
            pass

        try:
            answer = BINOP_TOKENS[usymbol]
            if answer is None:
                out.append(f"xcm.{usymbol}")
            else:
                out.append(answer)
            return
        except KeyError:
            pass

        if usymbol in KNOWN_MODELS:
            # This is currently unsupported
            out.append(symbol)
            if symbol not in models:
                models.append(symbol)
            return

        # Maybe it's a number
        try:
            float(symbol)
            out.append(symbol)
            return
        except ValueError:
            pass

        # XSPEC allows syntax like "(1+E)normVal" so check if
        # we need to add "*". This is not particularly efficient.
        #
        if out and "".join(out).rstrip()[-1] == ")":
            out.append("*")

        out.append(symbol)

        # Assume it's a parameter name
        #
        if usymbol in seen:
            return

        pnames.append(symbol)
        seen.add(usymbol)

    # This code is not designed for efficiency!
    #
    instack = list(expr)
    current = ""
    while instack:
        c = instack.pop(0)

        # If it's a space, an operator, or bracket we can push the
        # current symbol. The '^' and '*' cases are handled separately.
        #
        if c in " ()+-/,":
            add_current(current)
            out.append(c)
            current = ""
            continue

        if c == "^":
            add_current(current)
            out.append("**")
            current = ""
            continue

        # Is this multiply or exponent? Not really needed just yet.
        #
        if c == "*":
            # A valid MDEFINE expression will not end in * so assume
            # that there is another token to check.
            #
            if instack[0] == "*":
                instack.pop(0)
                c = "**"

            add_current(current)
            out.append(c)
            current = ""
            continue

        current += c

    # There may be a trailing term
    add_current(current)

    converted = "".join(out)
    return converted, pnames, models


def tokenize_model_expr(session: Session,
                        extra_models: List[str],
                        expr: str,
                        mdefines: List[MDefine]) -> List[str]:
    """Parse the model expression.

    This is simpler than parse_mdefine_expr as do not have to
    deal with parameters or functions.

    Parameters
    ----------
    session : Session
        The Sherpa session to use to find models.
    extra_models : list of str
        Any XSPEC user models.
    extra_models : list of str
        XSPEC user models created with convert_xspec_user_model.
    expr : str
        The model expression
    mdefines : list of MDefine
        The existing model definitions.

    Returns
    -------
    tokens : list of terms

    """

    if not expr:
        raise ValueError("Model expression can not be empty")

    KNOWN_MODELS = [n[2:].upper() for n in session.list_models("xspec")] + \
        [m.upper() for m in extra_models] + \
        [m.name.upper() for m in mdefines]

    out: List[str] = []

    def add_current(symbol: str) -> None:
        """Add the current symbol to the output."""

        if not symbol:
            return

        # Check to see if we need to add a "*" symbol. This is assumed to
        # not need to be efficient.
        #
        if out and out[-1] == ")":
            out.append("*")

        usymbol = symbol.upper()

        # Is this a table model? We include the { in case a user has
        # created a local model starting [ame]table.... (it that is
        # possible).
        #
        if usymbol.startswith("ATABLE{") or \
           usymbol.startswith("MTABLE{") or \
           usymbol.startswith("ETABLE{"):
            out.append(symbol)  # no case change because of file names
            return

        if usymbol not in KNOWN_MODELS:
            raise ValueError(f"Unrecognized model '{symbol}' in '{expr}'")

        out.append(symbol.lower())

    # This code is not designed for efficiency!
    #
    # We strip out spaces as we assume there are none that will
    # be relevant (it may be needed for table names?).
    #
    instack = list(expr.translate({32: None}))
    current = ""
    while instack:
        c = instack.pop(0)

        # If it's aan operator or bracket we can push the current
        # symbol. We only have to deal with brackets () and operators
        # + and *. We do not parse the table names here for table
        # models.
        #
        if c in "()+*":
            add_current(current)
            out.append(c)
            current = ""
            continue

        current += c

    # There may be a trailing term
    add_current(current)
    return out


def process_mdefine(session: Session,
                    extra_models: List[str],
                    xline: str,
                    mdefines: List[MDefine]) -> MDefine:
    """Parse a mdefine line.

    Parameters
    ----------
    session : Session
        The Sherpa session.
    extra_models : Session
        XSPEC user models.
    xline : str
        The line to process.
    mdefines : list of MDefine
        The already-processed mdefines (in case the model expression
        makes use of one).

    Returns
    -------
    mdefine : MDefine
        A representation of the model.

    Notes
    -----
    Tries to follow
    https://heasarc.gsfc.nasa.gov/docs/xanadu/xspec/manual/XSmdefine.html

    The returned model may redfine an existing element in mdefines,
    although I'm not sure that's likely in a XCM file.

    """

    # For the moment we require that the line start with 'mdefine '
    xline = xline[7:].strip()

    if not xline:
        raise ValueError(f"No name or expression in '{xline}'")

    # Strip off any options. We assume that : can only exist once,
    # if given (the documentation is unclear)
    #
    toks = xline.split(":")
    if len(toks) > 2:
        raise ValueError(f"Expected only one : in '{xline}'")

    name, expr = toks[0].strip().split(" ", 1)
    expr = expr.strip()

    # For now we do not parse the expression other than to try
    # and grab the parameter names.
    #
    converted, params, models = parse_mdefine_expr(session, extra_models, expr, mdefines)

    mtype = Term.ADD
    erange = None
    if len(toks) == 2:

        stoks = toks[1].strip().split(" ")
        nstoks = len(stoks)
        if nstoks > 3:
            raise ValueError(f"Expected ': <type> <emin> <emax>' in '{xline}'")

        # It looks like can have 1, 2, or 3 values
        #   - 1: type
        #   - 2: emin emax
        #   - 3: type emin emax
        #
        if nstoks != 2:
            mtok = stoks.pop(0).upper()
            try:
                mtype = MODEL_TYPES[mtok]
            except KeyError:
                raise ValueError(f"Unknown model type '{mtok}' in '{xline}'") from None

        if nstoks > 1:
            emin = float(stoks[0])
            emax = float(stoks[1])
            erange = (emin, emax)

    if mtype == Term.ADD:
        params.append("norm")

    return MDefine(name=name,
                   expr=expr,
                   params=params,
                   models=models,
                   converted=converted,
                   mtype=mtype,
                   erange=erange)


def get_pars_from_expr(expr: List[SimpleToken]) -> List[Parameter]:
    """Find all the parameters."""

    out = []
    for t in expr:
        if not isinstance(t, ArithmeticModel):
            continue

        for par in t.pars:
            if par.hidden:
                continue

            out.append(par)

    return out

# The conversion routine. The functionality needs to be split out
# of this.
#
def convert(infile: Any,  # to hard to type this
            models: Optional[List[str]] = None,
            chisq: str = "chi2datavar",
            clean: bool = False,
            explicit: Optional[str] = None) -> str:
    """Convert a XSPEC xcm file into Sherpa commands.

    The XSPEC save command will create an ASCII representation of the
    XSPEC session (perhaps just the models or files).

    Parameters
    ----------
    infile : str or fileio-like
        The file containing the XCM files. It can be a file name or a
        file handle, in which case the read method is used to access
        the data.
    models : List of str or None
        What XSPEC user models should be loaded. Each entry should be
        the module name sent to convert_xspec_user_script (i.e. is the
        name used in the "import name" or "import name.ui" line). For
        the moment it requires that convert_xspec_user_script were
        called with the empty --prefix argument.
    chisq : str, optional
        The Sherpa chi-square statistic to use for "statistic chi".
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
        with open(infile, "r", encoding="utf-8") as fh:
            intext = fh.readlines()

    # TODO: convert the output routines (*add*) to a class.
    #
    out_imports = []
    def add_import(expr):
        """Add the import if we haven't alredy done so"""

        if expr in out_imports:
            return

        out_imports.append(expr)

    out: List[str] = []

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

    # Are there any XSPEC user models to load?
    #
    if models is not None:
        for mexpr in models:
            add_import(f"import {mexpr}.ui")

    if clean:
        add("clean")

    # Store information about datasets, responses, and models.
    #
    state: Dict[str, Any] = {
        'nodata': True,  # set once a data command is found

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

        # The known user-models created by mdefine.
        # At the moment we do not handle them (i.e.
        # create usable usermodels).
        #
        'mdefines': [],
    }

    session, extra_models = create_session(models)

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
        v2(f"[{command}] - {xline}")

        if command == 'bayes':
            v2(f"Skipping: {command}")
            # No need to mention this
            # madd(f"print('skipped \"{xline}\"')")
            continue

        if command == 'systematic':
            v2(f"Skipping: {command}")
            # Only report if not "systematic 0"
            if toks[1] != "0":
                madd(f"print('skipped \"{xline}\"')")

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
            if ntoks != 2:
                raise ValueError(f"Expected 1 argument for {command.upper()}: '{xline}'")

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
                v2("Skipping 'xset delta'")
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
        if command == 'backgrnd':
            if state['subtracted']:
                raise ValueError("XCM file is too complex: calling BACKGRND after METHOD is not supported.")

            if ntoks < 2:
                raise ValueError(f"Missing BACKGRND options: '{xline}'")

            if ntoks > 3:
                raise ValueError(f"Unsupported BACKGRND syntax: '{xline}'")

            if ntoks == 2:
                if toks[1] == 'none':
                    state['nobackgrounds'].append(1)
                else:
                    add('load_background', f"'{toks[1]}'")
                continue

            groupnum, datanum = parse_dataid(toks[1])
            if groupnum is not None:
                raise ValueError(f"Unsupported BACKGRND syntax: '{xline}'")

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

        if command == 'mdefine':
            mdefine = process_mdefine(session, extra_models, xline, state["mdefines"])

            # We may over-write an existing model, but I am not
            # convinced this will result in a usable XCM file if it
            # happens.
            #
            for idx, m in enumerate(state["mdefines"]):
                if m.name != mdefine.name:
                    continue

                # There should only be a single value
                del state["mdefines"][idx]
                break

            state["mdefines"].append(mdefine)

            # We have to define the model function here, as the MODEL
            # command will cause the model function to be converted
            # into a user model.
            #
            madd("")
            madd(f"# mdefine {mdefine.name} {mdefine.expr} : {mdefine.mtype.name}")
            madd(f"# parameters: {', '.join(mdefine.params)}")
            madd(f"def model_{mdefine.name}(pars, elo, ehi):")
            for idx, par in enumerate(mdefine.params):
                madd(f"    {par} = pars[{idx}]")

            madd("    elo = np.asarray(elo)")
            madd("    ehi = np.asarray(ehi)")

            if mdefine.models:
                madd("")
                for model in mdefine.models:

                    # Is this a mdefine/user model or a compiled model?
                    #
                    matches = [md for md in state["mdefines"] if md.name == model]
                    if matches:
                        # assume there's only one match by construction
                        match = matches[0]

                        # We should be able to call the model function
                        # we created directly.
                        #
                        callfunc = f"model_{match.name}"
                        temp_mtype = match.mtype
                    else:
                        answer = handle_xspecmodel(session, model, "temp_cpt")
                        if answer is None:
                            print(f"Unable to find model '{model}' for MDEFINE {mdefine.name}")
                            madd(f"    print('Unable to identify model={model}')")
                            continue

                        temp_cpt = answer[0]
                        # Hopefully the class is available
                        madd(f"    {model}_cpt = {temp_cpt.__class__.__name__}()")
                        callfunc = f"{model}_cpt.calc"
                        temp_mtype = answer[1]

                    madd("")
                    madd(f"    def {model}(*args):")
                    madd("        pars = list(args)")
                    if temp_mtype == Term.ADD:
                        madd("        pars.append(1.0)  # model is additive")
                    madd(f"        out = {callfunc}(pars, elo, ehi)")
                    if temp_mtype == Term.ADD:
                        madd("        out /= de  # model is additive")
                    madd("        return out")
                    madd("")

            # Use the name E to match the XSPEC code
            madd("    E = (elo + ehi) / 2")
            if mdefine.mtype == Term.ADD:
                madd("    de = ehi - elo")
                madd(f"    return norm * ({mdefine.converted}) * de")
            elif mdefine.mtype == Term.MUL:
                madd(f"    return {mdefine.converted}")
            else:
                madd(f"    raise RuntimeError('convolution model to write: {mdefine.expr}')")

            madd("\n")  # want two bare lines
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
            v1(xline)
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

            if len(groups) == 0:
                raise RuntimeError("The script is currently unable to handle the input file")

            exprs = convert_model(session, extra_models, rest, postfix, groups,
                                  state['mdefines'],
                                  add=add, madd=madd)

            assert sourcenum not in state['exprs'], sourcenum
            state['exprs'][sourcenum] = exprs

            # Create the list of all parameters, so we can set up links.
            # Note that we store these with the label, not sourcenumber,
            # since this is how they are referenced.
            #
            assert label not in state['allpars'], label
            state['allpars'][label] = []
            for expr in exprs:
                pars = get_pars_from_expr(expr)
                for par in pars:
                    state['allpars'][label].append(par)

            # Separate the model definition from the parameters
            madd("")
            if state['allpars'][label]:
                madd("# Parameter settings")

            # Process all the parameter values for each data group.
            #
            escape = False  # NEED TO REFACTOR THIS CODE!
            for expr in exprs:
                if escape:
                    break

                pars = get_pars_from_expr(expr)
                for par in pars:
                    if escape:
                        break

                    assert isinstance(par, Parameter)  # for mypy
                    pname = par.fullname
                    pmin = par.min
                    pmax = par.max

                    # Grab the parameter line
                    try:
                        pline = intext.pop(0).strip()
                    except IndexError:
                        v1(f"Unable to find parameter value for {pname} - skipping other parameters")
                        escape = True
                        break

                    # This may only be possible with hand-edited files.
                    if not pline:
                        v1(f"Found a blank line when expecting paramter {pname} - skipping other parameters")
                        excape = True
                        break

                    if pline.startswith('='):
                        parse_tie(state['allpars'], add_import, add, pname, pline)
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

                    pargs = [pname, toks[0]]
                    pkwargs = {}

                    if pmin is None or lmin != pmin:
                        pkwargs['min'] = toks[3]

                    if pmax is None or lmax != pmax:
                        pkwargs['max'] = toks[4]

                    if toks[1].startswith('-'):
                        pkwargs['frozen'] = True

                    add('set_par', *pargs, **pkwargs)

            continue

        v1(f"SKIPPING '{xline}'")
        madd(f"print('WARNING: skipped {xline}')")

    # Warn the user if MDEFINE was used
    #
    if state["mdefines"]:
        v1("Found MDEFINE command: please consult 'ahelp convert_xspec_script'")
        for mdefine in state["mdefines"]:
            if mdefine.mtype == Term.CON:
                status = "convolution models are not currently supported"
            else:
                status = f"check definition of model_{mdefine.name}()"

            v1(f"  - {mdefine.name}  {mdefine.mtype.name} : {status}")

    # We need to create the source models. This is left till here because
    # Sherpa handles "multiple specnums" differently to XSPEC.
    #

    # Technically we could have no model expression, but assume that is unlikely
    madd("")
    madd("# Set up the model expressions")
    madd("#")

    # The easy case:
    #
    exprs = state['exprs']
    nsource = len(state['sourcenum'])
    v3(f"Number of extra sources: {nsource}")
    v3(f"Keys in exprs: {exprs.keys()}")
    if list(exprs.keys()) == []:
        v3("Appear to have no model expression")

    elif nsource == 0:
        if list(exprs.keys()) != [None]:
            raise RuntimeError("Unexpected state when processing the model expressions in the XCM file!")

        # Do we use the same model or separate models?
        #
        if len(exprs[None]) == 1:
            v2("Single source expression for all data sets")
            sexpr = create_source_expression(exprs[None][0])
            for did in state['datasets']:
                add('set_source', did, sexpr)

        else:
            v2("Separate source expressions for the data sets")
            if len(state['datasets']) != len(exprs[None]):
                raise RuntimeError("Unexpected state when handling source models!")

            for did, expr in zip(state['datasets'], exprs[None]):
                sexpr = create_source_expression(expr)
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

            sexpr = create_source_expression(expr)

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

                    sexpr = create_source_expression(xexpr)
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
