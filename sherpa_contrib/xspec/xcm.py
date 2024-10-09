#
#  Copyright (C) 2020, 2023-2024
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

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import importlib
import logging
from typing import Any, Callable, TypedDict

import numpy as np

from sherpa.astro import hc
from sherpa.astro import ui  # type: ignore
from sherpa.astro import xspec  # type: ignore
from sherpa.astro.ui.utils import Session  # type: ignore
from sherpa.models.basic import ArithmeticModel, UserModel  # type: ignore
from sherpa.models.model import RegridWrappedModel  # type: ignore
from sherpa.models.parameter import Parameter, CompositeParameter, ConstantParameter  # type: ignore
# from sherpa.models.regrid import EvaluationSpace1D, ModelDomainRegridder1D  # type: ignore
from sherpa.models.regrid import EvaluationSpace1D  # type: ignore
from sherpa.utils.err import ArgumentErr, DataErr  # type: ignore
from sherpa.utils._utils import rebin  # type: ignore

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


# For code run within a Sherpa session, rather than from the
# convert_xspec_script script, We don't want to use the contrib logger
# as it will not be affected by SherpaVerbosity, so use the sherpa
# one.
#
swarn = logging.getLogger("sherpa").warning


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
        The channel range, as recorded by XSPEC (this need not be the
        channel range depending if the data is grouped or the channel
        values do not start at 1).
    ignore : bool, optional
        If set then we ignore the range.

    See Also
    --------
    ignore

    Notes
    -----
    As of CIAO 4.15, the notice and ignore calls from the UI layer
    report the selected filter. This routine used to call the method
    directly but has switched to calling the UI layer to get the same
    behavior (it is more work but this is not a time-sensitive
    routine).

    """

    d = ui.get_data(spectrum)

    # XSPEC channels and Sherpa group numbers do not always agree.
    # This is fast enough it's not worth storing in a cache.
    #
    mapping = validate_grouping(d)
    if mapping.different:
        swarn("Spectrum %s: the grouping scheme does not match OGIP "
              "standards. The filtering may not exactly match XSPEC.",
              spectrum)

    xlo = XSPECChannel(lo)
    xhi = XSPECChannel(hi)

    # Get the start and end channel values (Sherpa). As I do not
    # understand exactly what XSPEC reports, in particularly for "bad"
    # channels, allow the mapping to be missing. If xlo is missing
    # then we just skip the filter.
    #
    try:
        smin = mapping.xspec[xlo][0].channel
    except KeyError:
        print("MISSING LOW")
        return

    try:
        smax = mapping.xspec[xhi][1].channel
    except KeyError:
        print("MISSING HIGH")
        smax = int(d.channel[-1])

    if d.units == "channel":
        v2(f"Converting group {lo}-{hi} to channels {smin}-{smax} [ignore={ignore}]]")
        ui.notice_id(spectrum, smin, smax)
        return

    elo, ehi = d._get_ebins(group=False)

    if d.units == "energy":
        emin = elo[smin]
        emax = ehi[smax]

        v2(f"Converting group {lo}-{hi} to {emin:.3f}-{emax:.3f} keV [ignore={ignore}]]")
        ui.notice_id(spectrum, emin, emax, ignore=ignore)
        return

    if d.units == "wavelength":
        # In case the response happens to have any non-positive
        # values.
        #
        tiny = np.finfo(np.float32).tiny
        elo = elo.copy()
        ehi = ehi.copy()
        elo[elo <= 0] = tiny
        ehi[ehi <= 0] = tiny

        whi = hc / elo
        wlo = hc / ehi

        wmin = wlo[smin]
        wmax = whi[smax]

        v2(f"Converting group {lo}-{hi} to {wmin:.5f}-{wmax:.5f} A [ignore={ignore}]]")
        ui.notice_id(spectrum, wmin, wmax, ignore=ignore)
        return

    raise ValueError(f"Unexpected analysis setting for spectrum {spectrum}: {d.units}")


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


# For CIAO 4.16 the regrid support doesn't quite work, so work around
# it.
#
class EnergyExtend:
    """Evaluate model on the energies grid and interpolate.

    For CIAO 4.16 the sherpa.models.regrid.ModelDomainRegridder1D
    class doesn't quite work for composite models (particularly
    those that , so this is a way to work around the restriction.
    It is also not generic, as it is designed for PHA data only.

    """

    name: str
    name = "energyextend"

    integrate: bool
    integrate = True

    def __init__(self, espace: EvaluationSpace1D) -> None:

        if espace.is_empty:
            raise ValueError("espace is empty")

        if not espace.is_integrated:
            raise ValueError("espace is not integrated")

        self._evaluation_space = espace
        self.xlo = espace.x_axis.lo
        self.xhi = espace.x_axis.hi

    @property
    def evaluation_space(self):
        return self._evaluation_space

    @property
    def grid(self):
        return self._evaluation_space.grid

    def calc(self, pars, model, xlo, xhi, **kwargs):
        """Use the user-requested grid and rebin onto the output grid"""
        y = model(pars, self.xlo, self.xhi, **kwargs)
        return rebin(y, self.xlo, self.xhi, xlo, xhi)


def extend_model_expression(pha, model, energies):
    """Extend the model so it is evaluated over the given grid.

    The given energies grid is combined with the existing response to
    create a new grid which is used to evaluate the model, and then it
    will be re-binned to remove the excess bins. This allows signal
    from outside the instrument response to be included, for instance
    by downscattering or redshifting data. It is only useful if the
    model expression contains a convolution model.

    Parameters
    ----------
    pha : sherpa.astro.data.DataPHA
        The dataset that contains the response.
    model : sherpa.models.model.Model
        The model to extend. It is expected that it contains a convolution
        component but this is not required.
    energies : sequence of number
        The energy grid to use (n bins are represented by n+1
        elements, with the first n being the left-edge and the last
        element is the right-edge of the last bin). The energies are
        in keV.

    See Also
    --------
    extend_model

    Examples
    --------

    This example does not use an XSPEC convolution model so it is not
    going to actually make use of the extended energy grid when
    evaluating the model:

    >>> pha = get_data()
    >>> model = xsphabs.gal * xspowerlaw.pl
    >>> energies = np.logspace(-3, 3, 500)
    >>> nmodel = extend_model_expression(pha, model, energies)

    """

    # What is the current response grid?
    #
    arf, rmf = pha.get_response()
    if arf is None and rmf is None:
        raise DataErr("norsp", pha.name)

    # The base grid to use is obj.xlo + [obj.xhi[-1]].
    #
    obj = rmf if rmf is not None else arf

    # Check the user grid.
    #
    usergrid = np.asarray(energies)
    if not np.iterable(usergrid):
        raise DataErr("energies must be iterable")

    if usergrid.ndim != 1:
        raise DataErr("energies must be a 1D grid")

    if usergrid.size < 2:
        raise DataErr("energies must have at least 2 elements")

    ediff = np.diff(usergrid)
    if np.any(ediff <= 0):
        raise DataErr("energies must be monotonically increasing")

    # Create the new grid by combining the user-grid with the base
    # grid.
    #
    idxlo, = np.where(usergrid < obj.xlo[0])
    idxhi, = np.where(usergrid > obj.xhi[-1])

    # Combine.
    #
    # TODO: is there a benefit to combine any bins that are too small?
    # In particular the bins around obj.xlo[0] and obj.xhi[-1] may be
    # too small?
    #
    grid = np.concatenate((usergrid[idxlo],
                           obj.xlo, [obj.xhi[-1]],
                           usergrid[idxhi]))

    # Regrid the model.
    #
    eval_space = EvaluationSpace1D(grid[:-1], grid[1:])

    # This doesn't work in CIAO 4.16
    # regridder = ModelDomainRegridder1D(eval_space)
    # return regridder.apply_to(model)

    return RegridWrappedModel(model, EnergyExtend(eval_space))


# No typing rules at the moment as typing NumPy expressions is complex.
#
def extend_model(idval, energies):
    """Extend the model so it is evaluated over the given grid.

    The given energies grid is combined with the existing response to
    create a new grid which is used to evaluate the model, and then it
    will be re-binned to remove the excess bins. This allows signal
    from outside the instrument response to be included, for instance
    by downscattering or redshifting data. It is only useful if the
    associated source model contains a convolution model.

    Parameters
    ----------
    idval : int or str
        The dataset identifier. The dataset must contain a PHA
        dataset, a response, and a source model.
    energies : sequence of number or None
        The energy grid to use (n bins are represented by n+1
        elements, with the first n being the left-edge and the last
        element is the right-edge of the last bin). The energies are
        in keV. If set to None then any existing extension is removed.

    See Also
    --------
    extend_model_expression

    Examples
    --------

    This example does not use an XSPEC convolution model so it is not
    going to actually make use of the extended energy grid when
    evaluating the model:

    >>> load_pha("src.pha")
    >>> set_source(xsphabs.gal * xspowerlaw.pl)
    >>> energies = np.logspace(-3, 3, 500)
    >>> extend_model(1, energies)

    """

    # Check we have a response.
    # TODO: what happens when we have multiple responses?
    #
    pha = ui.get_data(idval)
    if not isinstance(pha, ui.DataPHA):
        raise DataErr(f"Dataset {idval} is not a PHA dataset!")

    # What is the model? Note that we "remove" any previous extension
    # via a not-particularly-pythonic check (I do not want to rely on
    # the presence of the model attribute meaning this is a regridded
    # model, in case some other class also uses the same attribute
    # name).
    #
    orig = ui.get_source(idval)
    if isinstance(orig, RegridWrappedModel):
        orig = orig.model

    if energies is None:
        # Do not bother with checking if the source was regridded.
        ui.set_source(idval, orig)
        return

    nmodel = extend_model_expression(pha, orig, energies)
    ui.set_source(idval, nmodel)


# Explicitly separate the XSPEC and Sherpa "channel" numbering.
# This is a bit excessive.
#
@dataclass(frozen=True)
class Channel:
    """A channel number. It must be an integer and 0 or larger."""

    channel: int

    def __post_init__(self):
        if self.channel < 0:
            raise ValueError(f"channel must be >= 0, not {self.channel}")

        if not float(self.channel).is_integer():
            raise ValueError(f"channel must be an integer, not {self.channel}")


@dataclass(frozen=True)
class XSPECChannel(Channel):
    """The XSPEC channel number.

    XSPEC drops "bad" quality channels and counts in "group" number,
    starting at 1 (if there is no grouping then each "group" maps to a
    single channel).

    """

    def __post_init__(self):
        if self.channel <= 0:
            raise ValueError(f"channel must be > 0, not {self.channel}")

        super().__post_init__()


@dataclass(frozen=True)
class Grouping:
    """Handle XSPEC/Sherpa differences in grouping."""

    xspec: dict[XSPECChannel, tuple[Channel, Channel]]
    """Keys are XSPEC 'channel' numbers, values are Sherpa channels"""

    different: bool
    """Is the XSPEC and Sherpa grouping different?

    This is set if the quality is both 0 and 2 within a group.
    """


def validate_grouping(pha: ui.DataPHA) -> Grouping:
    """Compare XSPEC and Sherpa grouping.

    Map the XSPEC "channel" numbers to the corresponding range of
    Sherpa channels.

    Parameters
    ----------
    pha : DataPHA
        The PHA data.

    Returns
    -------
    grouping : Grouping

    Notes
    -----

    The OGIP standard does not make it clear what happens if the
    quality changes within a group. XSPEC (12.13/14 era) seem to split
    the group if this happens (unlike Sherpa, XSPEC has already
    removed quality=1 or 5 values from the data).

    """

    nelem = pha.size
    if nelem == 0:
        raise ValueError("PHA has no data!")

    if pha.grouping is None:
        grouping = np.ones(nelem, dtype=np.int16)
    else:
        grouping = pha.grouping

    if pha.quality is None:
        quality = np.zeros(nelem, dtype=np.int16)
    else:
        quality = pha.quality

    # Always create the mapping, even when the XSPEC and Sherpa
    # channel values agree. The keys are the XSPEC "channel" value and
    # the values are the range of Sherpa channels that cover this.
    # This does not track any XSPEC "channels" that contain "bad"
    # channels.
    #
    mapping: dict[XSPECChannel, tuple[Channel, Channel]] = {}

    # If any group contains both 0 and 2 values.
    #
    different = False

    # The states for processing a channel are:
    #
    #   "ignore"    if the quality value is 1 or 5
    #   "start"     if grouping is >= 0
    #   "continue"  if grouping is < 0
    #
    # Now, this is made trickier to match XSPEC which seems to create
    # a new group if the quality value changes between 0 and 2 within
    # a group.
    #
    xspec_chan = 0
    start_chan = None
    end_chan = None
    last_qual = None
    for grp, qual, chan in zip(grouping, quality, pha.channel):

        # If this is a "bad" channel then we drop it.
        #
        if qual in [1, 5]:
            continue

        this_chan = Channel(int(chan))

        # This is a new group, so bump the XSPEC channel number and
        # store the previous range (assuming that ranges is not empty,
        # which would indicate this is the first element).
        #
        if grp > 0:

            # Store the previous mapping, if any.
            if end_chan is not None:
                assert start_chan is not None
                assert xspec_chan > 0
                xchan = XSPECChannel(xspec_chan)
                mapping[xchan] = (start_chan, end_chan)

            start_chan = this_chan
            end_chan = this_chan
            last_qual = qual
            xspec_chan += 1
            continue

        # This is a "continue" bin, but we may need to create
        # a new bin if the quality has changed.
        #
        if last_qual is not None and last_qual != qual:
            different = True

            # Since last_qual is set then ranges must not be empty.
            #
            assert xspec_chan > 0
            assert start_chan is not None
            assert end_chan is not None
            xchan = XSPECChannel(xspec_chan)
            mapping[xchan] = (start_chan, end_chan)
            xspec_chan += 1
            last_qual = qual
            start_chan = this_chan
            end_chan = this_chan
            continue

        # Special case for the "first bin has grouping < 0", which
        # should be an error but for now we ignore.
        #
        if start_chan is None:
            start_chan = this_chan

        end_chan = this_chan
        last_qual = qual

    # Copy over the last group.
    #
    if start_chan is None or end_chan is None:
        raise ValueError("No group data found; how is this possible")

    xchan = XSPECChannel(xspec_chan)
    mapping[xchan] = (start_chan, end_chan)

    return Grouping(xspec=mapping, different=different)


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
    params: list[str]
    models: list[str]
    converted: str   # the Python version of the model (likely needs reworking)
    mtype: Term
    erange: tuple[float, float] | None


SimpleToken = str | ArithmeticModel
Expression = list[SimpleToken]


class StateDict(TypedDict):
    nodata: bool
    statistic: str
    subtracted: bool
    nobackgrounds: list[int]
    group: dict[int, list[int]]
    datasets: list[int]
    sourcenum: dict[int, list[int]]
    datanum: dict[int, list[int]]
    exprs: dict[int, dict[int, Expression]]
    allpars: dict[str, Parameter]
    mdefines: list[MDefine]
    extend: EnergyGrid


RangeValue = int | float


class Output:
    """Represent the output text."""

    def __init__(self, explicit: str | None = None) -> None:
        self.imports: list[str] = []
        self.text: list[str] = []
        self.explicit = explicit

    @property
    def answer(self):
        """The output"""
        answer = list(self.imports)
        if answer:
            answer += [""]

        answer += self.text
        return "\n".join(answer) + "\n"

    def add_comment(self, comment: str | None = None) -> None:
        if comment is None:
            self.text.append("#")
            return

        self.text.append(f"# {comment}")

    def add_import(self, text: str) -> None:
        """Record an import line.

        We avoid repititions but only an exact match,
        so adding "from foo import a,b" and
        "from foo import b,a" will duplicate things.
        """

        if text in self.imports:
            return

        self.imports.append(text)

    def add_spacer(self, always: bool = True) -> None:
        """Add an extra line (with some flexibility)"""

        if not always and len(self.text) > 0 and self.text[-1] == '':
            return

        self.text.append('')

    def add_warning(self, msg: str, local: bool = True) -> None:
        """Add a warning message (both now and in the script)"""

        if local:
            v1(f"WARNING: {msg}")

        self.add_import("import logging")
        self.add_expr(f'logging.getLogger("sherpa").warning("{msg}")')

    def add_expr(self, expr: str, expand: bool = False) -> None:
        """Add the expression. 'XX' is used to handle implicit/explicit ui import"""

        if expand:
            if self.explicit is None:
                store = expr.replace('XX', '')
            else:
                store = expr.replace('XX', f'{self.explicit}.')

        else:
            store = expr

        self.text.append(store)

    def symbol(self, name: str) -> str:
        """Do we expand out the symbol?"""

        if self.explicit is None:
            return name

        return f"{self.explicit}.{name}"

    def add_call(self, name: str, *args, expand: bool = True, **kwargs):
        """Represent a function call."""

        if expand:
            sym = self.symbol(name)
        else:
            sym = name

        cstr = f"{sym}("
        arglist = [str(a) for a in args] + \
            [f"{k}={v}" for k, v in kwargs.items()]
        cstr += ", ".join(arglist)
        cstr += ")"
        self.text.append(cstr)


def set_subtract(output: Output,
                 state: StateDict) -> None:
    """Ensure the data is subtracted (as much as we can tell)."""

    if state['nodata'] or state['subtracted'] or not state['statistic'].startswith('chi'):
        return

    for did in state['datasets']:
        if did in state['nobackgrounds']:
            continue

        output.add_import('from sherpa_contrib.xspec import xcm')
        output.add_call('xcm.subtract', did, expand=False)

    output.add_spacer()

    # The assumption is that we don't add data/backgrounds after this is called
    state['subtracted'] = True


def parse_tie(output: Output,
              pars: dict[str, Parameter],
              par: str,
              pline: str) -> None:
    """Parse a tie line.

    The idea is to convert p<integer> or <integer> to the
    correct parameter name. We should support multiple
    substitutions and also <modelname><integer>.

    Parameters
    ----------
    output : Output
        The output state.
    pars : dict
        The parameters for each "label".
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
                token = expand_token(output, pars, par, token)
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
        token = expand_token(output, pars, par, token)
        expr += token

    output.add_call('link', par, expr)


def expand_token(output: Output,
                 pars: dict[str, Parameter],
                 pname: str,
                 token: str) -> str:
    """Is this a reference to a parameter?

    Ideally we'd add a '.val' to the parameter value when we
    know we are in a function.
    """

    def import_xcm():
        output.add_import('from sherpa_contrib.xspec import xcm')

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

    # See if we can convert the token to an integer (beginning with
    # p or not). If we can't we just return the token.
    #
    if token.startswith('p'):
        tieval = token[1:]
    else:
        tieval = token

    try:
        tie = int(tieval)
    except ValueError:
        return token

    # At this point we are sure we have a parameter reference.
    #
    try:
        plist = pars['unnamed']
    except KeyError:
        raise RuntimeError(f"Internal error accessing parameter names: pars={pars}") from None

    try:
        tpar = plist[tie - 1]
    except IndexError:
        raise ValueError(f"Invalid parameter number in '{token}'") from None

    return tpar.fullname


def parse_dataid(token: str) -> tuple[int | None, int]:
    """Convert '[<data group #>:] <spectrum #>' to values.

    This is used for both the DATA command, and the ARF/RESPONSE
    commands, which have subtly-different meanings but the syntax is
    the same. It is not used for MODEL as the second element is a
    string in that case.

    Parameters
    ----------
    token : str

    Returns
    -------
    othernum, datanum : None or int, int

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


def parse_ranges(ranges: str) -> tuple[str, list[tuple[RangeValue | None,
                                                       RangeValue | None]]]:
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

    def lconvert(val: str) -> RangeValue | None:
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


def parse_data(output : Output,
               state: Session,
               toks: list[str]) -> None:
    """Parse the DATA line

    https://heasarc.gsfc.nasa.gov/docs/xanadu/xspec/manual/XSdata.html

    """

    state['nodata'] = False

    ntoks = len(toks)
    if ntoks == 1:
        assert len(state['datasets']) == 0
        groupnum = 1
        datanum = 1
        args = [f"'{toks[0]}'"]
    else:
        igroupnum, datanum = parse_dataid(toks[0])
        if igroupnum is None:
            groupnum = 1
        else:
            groupnum = igroupnum

        args = [str(datanum), f"'{toks[1]}'"]

    state['group'][groupnum].append(datanum)
    state['datasets'].append(datanum)
    output.add_call('load_pha', *args, use_errors=True)


def parse_backgrnd(output: Output,
                   state: StateDict,
                   xline: str,
                   toks: list[str]) -> None:
    """Parse the BACKGRND line

    https://heasarc.gsfc.nasa.gov/docs/xanadu/xspec/manual/XSbackgrnd.html

    """

    ntoks = len(toks)
    if ntoks == 1:
        if toks[0] == 'none':
            state['nobackgrounds'].append(1)
        else:
            output.add_call('load_bkg', f"'{toks[0]}'")

        return

    groupnum, datanum = parse_dataid(toks[0])
    if groupnum is not None:
        raise ValueError(f"Unsupported BACKGRND syntax: '{xline}'")

    if toks[1] == 'none':
        state['nobackgrounds'].append(datanum)
    else:
        output.add_call('load_bkg', str(datanum), f"'{toks[1]}'")


def parse_response(output: Output,
                   state: StateDict,
                   command: str,
                   toks: list[str]) -> None:
    """Parse a arf or response line

    From

    https://heasarc.gsfc.nasa.gov/docs/xanadu/xspec/manual/XSarf.html
    https://heasarc.gsfc.nasa.gov/docs/xanadu/xspec/manual/XSresponse.html

    Syntax:  arf       [<filespec>...]
    Syntax:  response  [<filespec>...]
             response  [<source num>:]<spectrum num> none

    where <filespec> ::= [[<source num>:]<spectrum num>] <file name>...,
    """

    if command == 'arf':
        xcommand = 'load_arf'
    elif command == 'response':
        xcommand = 'load_rmf'
    else:
        raise NotImplementedError(f"Internal error: command={command}")

    ntoks = len(toks)
    if ntoks == 1:
        output.add_call(xcommand, f"'{toks[0]}'")
        return

    sourcenum, datanum = parse_dataid(toks[0])

    if sourcenum is not None and sourcenum != 1:
        # TODO: Shouldn't we always record these?
        state['sourcenum'][sourcenum].append(datanum)
        state['datanum'][datanum].append(sourcenum)

        output.add_call(xcommand, datanum, f"'{toks[1]}'", resp_id=str(sourcenum))

    else:
        output.add_call(xcommand, datanum, f"'{toks[1]}'")



def parse_notice_range(output: Output,
                       datasets: list[int],
                       command: str,
                       tokens: list[str]) -> None:
    """Handle the notice range.

    Parameters
    ----------
    output : Output
        The output state
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
                output.add_call(f'{command}_id', ds, lo, hi)

            return

        # We have to use our own "notice" command to handle group numbering.
        #
        for d in ds:
            for lo, hi in ranges:
                output.add_import('from sherpa_contrib.xspec import xcm')
                output.add_call(f"xcm.{command}", d, lo, hi, expand=False)


def add_mdefine_model(output: Output,
                      state: StateDict,
                      session: Session,
                      mdefine: MDefine
                      ) -> None:
    """Set up the MDEFINE model"""

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
    output.add_spacer()
    output.add_comment(f"mdefine {mdefine.name} {mdefine.expr} : {mdefine.mtype.name}")
    output.add_comment(f"parameters: {', '.join(mdefine.params)}")
    output.add_expr(f"def model_{mdefine.name}(pars, elo, ehi):")
    for idx, par in enumerate(mdefine.params):
        output.add_expr(f"    {par} = pars[{idx}]")

    output.add_expr("    elo = np.asarray(elo)")
    output.add_expr("    ehi = np.asarray(ehi)")

    if mdefine.models:
        output.add_expr("")
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
                answer = handle_xspecmodel(session, model, "temp_cpt", output=None)
                if answer is None:
                    print(f"Unable to find model '{model}' for MDEFINE {mdefine.name}")
                    output.add_expr(f"    print('Unable to identify model={model}')")
                    continue

                temp_cpt = answer[0]
                # Hopefully the class is available
                output.add_expr(f"    {model}_cpt = {temp_cpt.__class__.__name__}()")
                callfunc = f"{model}_cpt.calc"
                temp_mtype = answer[1]

            output.add_expr("")
            output.add_expr(f"    def {model}(*args):")
            output.add_expr("        pars = list(args)")
            if temp_mtype == Term.ADD:
                output.add_expr("        pars.append(1.0)  # model is additive")
            output.add_expr(f"        out = {callfunc}(pars, elo, ehi)")
            if temp_mtype == Term.ADD:
                output.add_expr("        out /= de  # model is additive")
            output.add_expr("        return out")
            output.add_expr("")

    # Use the name E to match the XSPEC code
    output.add_expr("    E = (elo + ehi) / 2")
    if mdefine.mtype == Term.ADD:
        output.add_expr("    de = ehi - elo")
        output.add_expr(f"    return norm * ({mdefine.converted}) * de")
    elif mdefine.mtype == Term.MUL:
        output.add_expr(f"    return {mdefine.converted}")
    else:
        output.add_expr(f"    raise RuntimeError('convolution model to write: {mdefine.expr}')")

    # want two bare lines
    output.add_spacer()
    output.add_spacer()


def parse_model(output: Output,
                state: StateDict,
                session: Session,
                extra_models: list[str],
                xline: str) -> dict[int, Expression]:
    """Handle the model line

    Can we assume that if the model has no dataset/label then it's
    used for all datasets, otherwise we have separate models, or
    is that too simple? Too simple, as I have an example with

    model  gaussian + gaussian + constant*constant(apec + (apec + apec + powerlaw)wabs + apec*wabs)
    model  2:pbg1 powerlaw
    model  3:pbg2 powerlaw
    model  4:pbg3 powerlaw

    From https://heasarc.gsfc.nasa.gov/docs/xanadu/xspec/manual/XSmodel.html

    Syntax: model[<source num>:<name>] [<delimiter>] <component1> <delimiter><component2><delimiter>...<componentN> [<delimiter>]

    """

    # Need some place to set up subtract calls, so pick here
    #
    output.add_spacer(always=False)

    set_subtract(output, state)

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
    output.add_comment(xline)

    # Do we have a group or source number? At the moment the code is unclear
    # about the labelling for the two concepts.
    #
    rest = xline[5:]
    tok = rest.split()[0]
    ilabel: str | None = None
    if ':' in tok:

        toks = tok.split(':')
        emsg = f"Unable to parse spectrum number of MODEL: '{xline}'"
        if len(toks) != 2:
            raise ValueError(emsg)

        try:
            sourcenum = int(toks[0])
        except ValueError:
            raise ValueError(emsg) from None

        # It looks like this is allowed, but maybe not going to happen
        # in a XCM file created by XSPEC.
        #
        ilabel = toks[1].strip()
        if not ilabel:
            ilabel = None

        rest = rest.strip()[len(tok) + 1:]

    else:
        sourcenum = 0
        ilabel = None

    # If there's no spectrum number then we want an expression
    # for each group. It there is a spectrum number then
    # we only want those spectra with a response for that
    # spectrum number.
    #
    # I really shouldn't use the term "groups" here as it
    # muddies the water.
    #
    if ilabel is None:
        label = "unnamed"
        postfix = ''
        groups = sorted(list(state['group'].keys()))
    else:
        label = ilabel

        # at this point sourcenum is expected to be > 0
        postfix = f"s{sourcenum}"
        groups = sorted(state['sourcenum'][sourcenum])

    if len(groups) == 0:
        raise RuntimeError("The script is currently unable to handle the input file")

    exprs = convert_model(output, session, extra_models,
                          rest, postfix, groups,
                          state['mdefines'])

    assert sourcenum not in state['exprs'], sourcenum
    state['exprs'][sourcenum] = exprs

    # Create the list of all parameters, so we can set up links.
    # Note that we store these with the label, not sourcenumber,
    # since this is how they are referenced.
    #
    assert label not in state['allpars'], label
    state['allpars'][label] = []
    for expr in exprs.values():
        pars = get_pars_from_expr(expr)
        for par in pars:
            state['allpars'][label].append(par)

    output.add_spacer()

    # Separate the model definition from the parameters.  We could
    # wait to add this until we fnid any parameter definition.
    #
    if state['allpars'][label]:
        output.add_comment("Parameter settings")

    return exprs


def parse_possible_parameters(output: Output,
                              state: StateDict,
                              intext: list[str],
                              exprs: dict[int, Expression]) -> None:
    """Do we have any parameter lines to deconstruct?

    This mutates the intext argument
    """

    # Process all the parameter values for each data group.
    # Is the ordering correct here?
    #
    escape = False  # NEED TO REFACTOR THIS CODE!
    for expr in exprs.values():
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
                escape = True
                break

            if pline.startswith('='):
                parse_tie(output, state['allpars'], pname, pline)
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

            KWargs = TypedDict('KWargs', {"min": str, "max": str, "frozen": bool}, total=False)
            pkwargs: KWargs = {}

            if pmin is None or lmin != pmin:
                pkwargs['min'] = toks[3]

            if pmax is None or lmax != pmax:
                pkwargs['max'] = toks[4]

            if toks[1].startswith('-'):
                pkwargs['frozen'] = True

            output.add_call('set_par', *pargs, **pkwargs)


def is_model_convolution(mdl: xspec.XSModel | MDefine
                         ) -> bool:
    """Is this a convolution model"""

    if isinstance(mdl, MDefine):
        return mdl.mtype == Term.CON

    return isinstance(mdl, xspec.XSConvolutionKernel)


def is_model_multiplicative(mdl: xspec.XSModel | MDefine
                            ) -> bool:
    """Is this a multiplicative model"""

    if isinstance(mdl, MDefine):
        return mdl.mtype == Term.MUL

    return isinstance(mdl, xspec.XSMultiplicativeModel)


def is_model_additive(mdl: xspec.XSModel | MDefine
                      ) -> bool:
    """Is this an additive model"""

    if isinstance(mdl, MDefine):
        return mdl.mtype == Term.ADD

    return isinstance(mdl, xspec.XSAdditiveModel)


def create_session(models: list[str] | None) -> tuple[Session, list[str]]:
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

    extras: list[str] = []
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
                      output: Output | None
                      ) -> tuple[xspec.XSModel, Term] | None:
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
    output : Output or None
        The output object, if output is wanted,

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
            if output is not None:
                output.add_expr(f"{cpt} = XXcreate_model_component('{mname}', '{cpt}')",
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


def create_source_expression(expr: Expression) -> str:
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


def handle_tablemodel(output: Output,
                      session: Session,
                      expr: str,
                      gname: str) -> tuple[xspec.XSTableModel, Term]:
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

    output.add_call("load_xstable_model", f"'{gname}'", f"'{tbl}'",
                    expand=True, **kwargs)

    # Not really needed but just in case
    output.add_expr(f"{gname} = XXget_model_component('{gname}')",
                    expand=True)

    return mdl, mtype


def dummy_model(pars, elo, ehi=None):
    raise NotImplementedError()


def handle_mdefine(output: Output,
                   session: Session,
                   mdefines: list[MDefine],
                   basename: str,
                   gname: str
                   ) -> tuple[UserModel, Term] | None:
    """Is this a mdefine model?

    Note we actually create a model (with a dummy function)
    as it makes downstream processing easier to handle.
    """

    for mdefine in mdefines:
        if mdefine.name != basename:
            continue

        v2(f"Handling MDEFINE model: {basename} for {gname}")

        output.add_call("load_user_model", f"model_{basename}", f"'{gname}'",
                        expand=True)
        output.add_call("add_user_pars", f"'{gname}'", str(mdefine.params),
                        expand=True)

        session.load_user_model(dummy_model, gname)
        session.add_user_pars(gname, mdefine.params)
        mdl = session.get_model_component(gname)
        return mdl, mdefine.mtype

    return None


def convert_model(output : Output,
                  session: Session,
                  extra_models: list[str],
                  expr: str,
                  postfix: str,
                  groups: list[int],
                  mdefines: list[MDefine]) -> dict[int, Expression]:
    """Extract the model components.

    Model names go from m1 to mn (when groups is empty) or
    m1g1 to mng1 and then m1g2 to mng<ngrops>.

    Parameters
    ----------
    output : Output
        The output object
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

    Returns
    -------
    exprs : list of list of tokens
        The model expression for each group (if len(groups) == 1 then
        for a single un-named group).

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

    # Need an output list for each group
    out: dict[int, Expression] = {g: [] for g in groups}

    def add_token(tkn):
        for outlist in out.values():
            outlist.append(tkn)

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
        v3(f"    bracket={fake_bracket} convolution={in_convolution} prev_model_type={prev_model_type}")

        if tok == "(":

            # If the previous term was a multiplicative model
            # then add in a * term.
            #
            if prev_model_type is not None and \
               prev_model_type == Term.MUL:
                tok = " * ("

            elif i > 1 and toks[i - 2] == ")":
                # Special case "(phabs)(apec)". I am concerned this
                # could cause problems elsewhere, in particular with
                # the fake_bracket rule, so let's see.
                #
                tok = " * ("

            add_token(tok)
            prev_model_type = None
            continue

        if tok == ")":
            if fake_bracket:
                add_token(")")
                fake_bracket = False

            add_token(tok)
            in_convolution = False
            prev_model_type = None
            continue

        if tok == "+":
            if fake_bracket:
                add_token(")")
                fake_bracket = False

            add_token(" + ")
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
                v3("  - found 'cmdl * ..' so dropping '*' token")

                # Should we clear prev_model_type?
                # prev_model_type = None
                continue

            add_token(" * ")
            prev_model_type = None
            continue

        # This must be a model.
        #
        for grp, outlist in out.items():
            gname = make_component_name(postfix, ngroups, ctr, grp)

            if "{" in tok:
                mdl, mtype = handle_tablemodel(output, session, tok, gname)
            else:
                answer = handle_xspecmodel(session, tok, gname, output=output)
                if answer is None:
                    answer = handle_mdefine(output, session, mdefines, tok, gname)
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
        add_token(")")

    v2(f"Found {len(out)} expressions")
    for grp, eterm in out.items():
        v2(f"Expression: {grp}  #tokens={len(eterm)}")
        for j, token in enumerate(eterm, 1):
            if isinstance(token, ArithmeticModel):
                v2(f"  {j:2d} '{token.name}'")
            else:
                v2(f"  {j:2d} '{token}'")

    return out


FunctionDict = dict[str, str | None]


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
                       extra_models: list[str],
                       expr: str,
                       mdefines: list[MDefine]) -> tuple[str, list[str], list[str]]:
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

    pnames: list[str] = []
    models: list[str] = []
    seen: set[str] = set()
    out: list[str] = []

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
                        extra_models: list[str],
                        expr: str,
                        mdefines: list[MDefine]) -> list[str]:
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

    out: list[str] = []

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
            raise ValueError(f"Unrecognized model '{symbol}' in '{expr.strip()}'")

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
                    extra_models: list[str],
                    xline: str,
                    mdefines: list[MDefine]) -> MDefine:
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


def get_pars_from_expr(expr: Expression) -> list[Parameter]:
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


def create_model_expressions(output: Output,
                             state: StateDict) -> None:

    # We need to create the source models. This is left till here because
    # Sherpa handles "multiple specnums" differently to XSPEC.
    #
    # Technically we could have no model expression, but assume that is unlikely
    output.add_spacer()
    output.add_comment("Set up the model expressions")
    output.add_comment()

    # The easy case:
    #
    exprs = state['exprs']
    nsource = len(state['sourcenum'])
    v2(f"Number of extra sources: {nsource}")
    v2(f"Keys in exprs: {exprs.keys()}")
    if not list(exprs.keys()):
        v3("Appear to have no model expression")
        return

    # In current testing we require exprs[0] to exist. Is this always true?
    if 0 not in exprs.keys():
        output.add_spacer()
        output.add_expr("print('Unexpected state when processing models')")
        print(f"UNEXPECTED: no expression for default model {list(exprs.keys())}")
        return

    exprs0 = exprs[0]

    has_egrid = False
    extend = state["extend"]
    if isinstance(extend, (ExternalGrid, ManualGrid)):
        extend.add_grid(output)
        has_egrid = True

    if nsource == 0:
        if list(exprs.keys()) != [0]:
            output.add_spacer()
            output.add_expr("print('Unexpected state when processing models')")
            print(f"UNEXPECTED: expected [0] but found {list(exprs.keys())}")
            return

        # Do we use the same model or separate models?
        #
        if len(exprs0) == 1:
            v2("Single source expression for all data sets")
            # What is the identifier used here?
            v3(f"  - identifier = {list(exprs0.keys())}")
            evals = list(exprs0.values())
            sexpr = create_source_expression(evals[0])
            for did in state['datasets']:
                output.add_call('set_source', did, sexpr)
                if has_egrid:
                    output.add_call('xcm.extend_model', did, 'egrid',
                                    expand=False)

            return

        v2("Separate source expressions for the data sets")
        if len(state['datasets']) != len(exprs0):
            output.add_spacer()
            output.add_expr("print('Unexpected state when processing models')")
            print(f"UNEXPECTED: expected {len(state['datasets'])} items but found {len(exprs0)}")
            return

        for did in state['datasets']:
            expr = exprs0[did]
            sexpr = create_source_expression(expr)
            output.add_call('set_source', did, sexpr)
            if has_egrid:
                output.add_call('xcm.extend_model', did, 'egrid',
                                expand=False)

        return

    # What "specnums" do we have to deal with?
    #   'unnamed' + <numbers>
    #
    # We need to check each dataset to see what specnums we care about.
    #
    if len(exprs0) != len(state['datasets']):
        # I am not convinced this is a requirement
        output.add_spacer()
        output.add_expr("print('Unexpected state when processing models')")
        print(f"UNEXPECTED: expected {len(state['datasets'])} items but found {len(exprs0)}")
        return

    # Response1D only seems to use the default response id.
    #
    output.add_import('from sherpa.astro.instrument import Response1D')

    for did in state['datasets']:
        expr = exprs0[did]  # This should hold
        output.add_comment(f"source model for dataset {did}")

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
            output.add_call('set_source', did, sexpr)
            if has_egrid:
                output.add_call('xcm.extend_model', did, 'egrid',
                                expand=False)
            continue

        output.add_expr(f"d = get_data({did})")
        output.add_expr(f"m = {sexpr}")
        if has_egrid:
            output.add_expr("m = xcm.extend_model_expression(d, m, egrid)")

        output.add_expr("fmdl = Response1D(d)(m)")

        # Hopefully this is correct. It's a lot simpler than it used
        # to be, at least.
        #
        for snum in snums:
            try:
                xexpr = exprs[snum][did]
                sexpr = create_source_expression(xexpr)

                output.add_import('from sherpa_contrib.xspec import xcm')
                output.add_expr(f"m = {sexpr}")
                if has_egrid:
                    output.add_expr("m = xcm.extend_model_expression(d, m, egrid)")

                output.add_expr(f"fmdl += xcm.Response1D(d, {snum})(m)")
                break
            except KeyError:
                pass

            output.add_spacer()
            emsg = f"Unable to find model for sourcenum={snum} and dataset {did}"
            output.add_expr(f"print('{emsg}')")
            print(f"UNEXPECTED: {emsg}")
            return

        output.add_call('set_full_model', did, 'fmdl')
        output.add_spacer()


class EnergyGrid:
    """Represent an energy grid"""


class NoGrid(EnergyGrid):
    """Hey, no grid"""


class ResetGrid(EnergyGrid):
    """Remove the grid."""


class ExternalGrid(EnergyGrid):
    """Grid read from a file"""

    def __init__(self, filename, grid):
        self.filename = filename
        self.grid = grid

    def add_grid(self, output: Output) -> None:
        """Create the egrid variable"""

        output.add_import("from numpy import array")

        # We are going to need this, so may as well imort it now
        output.add_import('from sherpa_contrib.xspec import xcm')

        output.add_comment(f"grid read from {self.filename}")
        output.add_expr(f"egrid = {repr(self.grid)}")


class ManualGrid(EnergyGrid):
    """User has designed the grid from linear/logarithmic sub-grids"""

    def __init__(self, ranges: list[tuple[str, float, float, int]]) -> None:
        self.ranges = ranges

    def add_grid(self, output: Output) -> None:
        """Create the egrid variable"""

        nr = len(self.ranges)
        v3(f"Found user grid of {nr} range(s)")
        for rval in self.ranges:
            v3(f" - {rval}")

        # We are going to need this, so may as well imort it now
        output.add_import('from sherpa_contrib.xspec import xcm')

        def display(idx):
            ftype, lo, hi, nbins = self.ranges[idx]
            if ftype == "log":
                lo = np.log10(lo)
                hi = np.log10(hi)

            return f"np.{ftype}space({lo}, {hi}, {nbins})"

        if nr == 1:
            output.add_expr(f"egrid = {display(0)}")
            return

        # When combining the ranges we need to drop the first element
        # of all-but-the-first range (as it is identical to the last
        # element of the previous range).
        #
        output.add_expr(f"egrids = [{display(0)}]")
        for idx in range(1, nr):
            output.add_expr(f"egrids.append({display(idx)}[1:])")

        output.add_expr("egrid = np.concatenate(egrids)")


def process_energies_grid(toks: list[str]) -> EnergyGrid:
    """What is the required grid?

    From https://heasarc.gsfc.nasa.gov/xanadu/xspec/manual/XSenergies.html

    Syntax:
        energies  <range specifier>[<additional range specifiers>...]
        energies  <input ascii file>
        energies  extend <extension specifier>
        energies  reset

    where the first <range specifier> ::= <low E><high E><nBins>log|lin
    <additional range specifiers> ::= <high E><nBins>log|lin
    <extension specifier> ::= low|high <energy><nBins>log|lin

    """

    if len(toks) == 0:
        raise RuntimeError("No arguments to ENERGIES command")

    if len(toks) == 1:
        # Either a file name or reset
        if toks[0].lower() == "reset":
            return ResetGrid()

        infile = toks[0]
        vals = []
        with open(infile, "r", encoding="utf-8") as fh:
            for origl in fh.readlines():
                l = origl.strip()
                if l == "" or l.startswith("#"):
                    continue

                idx = l.find("#")
                if idx > -1:
                    l = l[:idx].strip()

                try:
                    vals.append(float(l))
                except ValueError as ve:
                    raise RuntimeError(f"Unable to convert file '{infile}'\nline: {origl}") from ve

        if len(vals) == 0:
            raise RuntimeError("No grid specification found in '{infile}'")

        return ExternalGrid(infile, vals)

    if toks[0].lower() == "extend":
        raise NotImplementedError("EXTEND option for ENERGIES is not supported")

    def_lo = 0.1
    def_hi = 10
    def_nbins = 1000
    def_mode = "lin"

    # We need to deal with a mix of commas and spacing to parse the
    # expression. My guess is that there are cases where this fails,
    # in particular if a user only uses a subset of commas and
    # multiple ranges, like ",,100 1e4," (assuming this is valid).
    #
    store = {"lo": def_lo, "hi": def_hi, "nbins": def_nbins, "mode": def_mode}
    state = "lo"
    next_state = {"lo": "hi", "hi": "nbins", "nbins": "mode", "mode": "hi"}

    ranges: list[tuple[str, float, float, int]] = []

    cstr = " ".join(toks)
    v3(f"Resolving energy grid '{cstr}'")

    # Add an extra space to cstr so that we process the last token in
    # this loop and do not need to add a case after the loop has
    # finished.
    #
    cur = ""
    for c in cstr + " ":
        if c not in " ,":
            cur += c
            continue

        v3(f" - found token [{cur}] for state={state}")

        # We have a token (it can be empty).
        #
        if cur != "":
            if state == "mode":
                if cur not in ["log", "lin"]:
                    raise RuntimeError(f"Expected 'log' or 'lin' but found '{cur}'")

                store[state] = cur
            elif state == "nbins":
                store[state] = int(cur)
            else:
                store[state] = float(cur)

        # Have we come to the end of a range?
        #
        if state == "mode":
            # mypy doesn't like the type-conversion going on here as
            # it thinks the values all have type 'object'.
            #
            ranges.append((store["mode"],
                           store["lo"],
                           store["hi"],
                           store["nbins"]))  # type: ignore

            store["lo"] = store["hi"]
            store["hi"] = None

        # Move to next state
        #
        state = next_state[state]
        cur = ""

    return ManualGrid(ranges)


# The conversion routine. The functionality needs to be split out
# of this.
#
def convert(infile: Any,  # to hard to type this
            models: list[str] | None = None,
            chisq: str = "chi2datavar",
            clean: bool = False,
            explicit: str | None = None) -> str:
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

    out = Output(explicit)

    # START
    #
    # This isn't always needed but let's make it available anyway, to
    # simplify the code.
    #
    out.add_import("import numpy as np")

    if explicit is None:
        out.add_import("from sherpa.astro.ui import *")
    else:
        out.add_import(f"import sherpa.astro.ui as {explicit}")

    # Are there any XSPEC user models to load?
    #
    if models is not None:
        for mexpr in models:
            out.add_import(f"import {mexpr}.ui")

    if clean:
        out.add_call("clean")

    # Store information about datasets, responses, and models.
    #
    state: StateDict = {
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

        # What energy grid extensions are required?
        'extend': NoGrid()
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
            # out.add_expr(f"print('skipped \"{xline}\"')")
            continue

        if command == 'systematic':
            v2(f"Skipping: {command}")
            # Only report if not "systematic 0"
            if toks[1] != "0":
                out.add_expr(f"print('skipped \"{xline}\"')")

            continue

        if command == 'method':
            # Assume we have method after data so a nice place to put a spacer
            out.add_spacer(always=False)

            meth = toks[1].lower()
            if meth == 'leven':
                methname = "levmar"
            elif meth == 'simplex':
                methname = "simplex"
            else:
                out.add_warning(f"there is no equivalent to METHOD {meth}")
                continue

            out.add_call('set_method', f"'{methname}'")
            continue

        if command == 'statistic':
            if ntoks == 1:
                raise ValueError(f"Missing STATISTIC option: '{xline}'")

            stat = toks[1].lower()
            if stat == 'chi':
                statname = chisq
            elif stat.startswith('cstat'):
                out.add_warning('Have chosen cstat but wstat statistic may be better', local=False)
                statname = "cstat"
            else:
                out.add_warning(f"there is no equivalent to STATISTIC {stat}")
                statname = chisq

            out.add_call('set_stat', f"'{statname}'")
            state['statistic'] = stat
            continue

        if command in ['abund', 'xsect']:
            if ntoks != 2:
                raise ValueError(f"Expected 1 argument for {command.upper()}: '{xline}'")

            out.add_call(f'set_xs{command}', f"'{toks[1]}'")
            continue

        if command == 'cosmo':
            if ntoks != 4:
                raise ValueError(f"Expected 3 arguments for COSMO: '{xline}'")

            out.add_call('set_xscosmo', *toks[1:])
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
            out.add_call('set_xsxset', f"'{toks[1]}'", f"'{toks[2]}'")
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

            parse_data(out, state, toks[1:])
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

            parse_backgrnd(out, state, xline, toks[1:])
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

            parse_response(out, state, command, toks[1:])
            continue

        if command in ['ignore', 'notice']:
            if ntoks == 1:
                raise ValueError(f"Missing {command.upper()} option: '{xline}'")

            parse_notice_range(out, state['datasets'], command, toks[1:])
            continue

        if command == 'mdefine':
            mdefine = process_mdefine(session, extra_models, xline, state["mdefines"])
            add_mdefine_model(out, state, session, mdefine)
            continue

        if command == 'model':
            if ntoks == 1:
                raise ValueError(f"Missing MODEL option: '{xline}'")

            exprs = parse_model(out, state, session, extra_models,
                                xline)
            parse_possible_parameters(out, state, intext, exprs)
            continue

        if command == 'energies':
            # Store the energy grid so it can be applied later.
            # We do no processing here.
            #
            if ntoks == 1:
                raise ValueError(f"Missing ENERGIES option: '{xline}'")

            if not isinstance(state["extend"], NoGrid):
                out.add_warning("Multiple ENERGIES statements found; only last one will be used")
                v1("Found multiple ENERGIES statements; only last one will be used")

            state["extend"] = process_energies_grid(toks[1:])
            continue

        v1(f"SKIPPING '{xline}'")
        out.add_warning(f'skipped {xline}', local=False)

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

    create_model_expressions(out, state)
    return out.answer
