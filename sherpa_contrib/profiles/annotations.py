#
#  Copyright (C) 2019
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

"""Support adding lannotations to plots

The radial profile plots add extra annotations compared to the normal Sherpa
plots, which means we need some backend-specific code to support this.

"""

import importlib
import logging
import sys

from functools import wraps

from sherpa import plot

warning = logging.getLogger(__name__).warning

backend = None
try:
    pkg = 'sherpa_contrib.profiles'
    modname = '.annotations_{}'.format(plot.backend.name)
    importlib.import_module(modname, package=pkg)
    backend = sys.modules['{}{}'.format(pkg, modname)]
except AttributeError:
    warning('Unable to find plotting library used by Sherpa')
except ImportError:
    warning('No support for annotations with the ' +
            '{} backend'.format(plot.backend.name))

del pkg
del modname


def ignore_attribute_error(func):
    """A decorator that ignores any AttributeError raised by the code.

    The assumption is that the AttribteError can only come from
    the backend not having the correct symbol, or backend is None,
    but the decorator does not enforce this.
    """

    @wraps(func)
    def newfunc(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError:
            return None

    return newfunc


@ignore_attribute_error
def add_rlabel(x, y, lbl):
    """Add right-justified text to the current plot.

    Parameters
    ----------
    x, y : float
        The location for the label, in "plot normalized" coordinates
        (0,0 is the bottom left of the current plot area and 1,1 is the
        top right). The label is right-justified, so x refers to the end
        of the label text.
    lbl : str
        The label to plot (this includes any special syntax or codes
        to identify latex support or color change or whatever the
        backend supports).
    """

    backend.add_rlabel(x, y, lbl)


@ignore_attribute_error
def add_hline(y):
    """Add a horizontal line.

    Parameters
    ----------
    y : float
        The location for the line, in data coordinates. It covers the
        full plot.
    """

    backend.add_hline(y)


@ignore_attribute_error
def add_subscript(term, subscript):
    """Add a subscript to the term.

    This is intended to support LaTeX-like (or other) control codes.

    Parameters
    ----------
    term, subscript: str

    Returns
    -------
    label: str
    """

    return backend.add_subscript(term, subscript)


@ignore_attribute_error
def add_latex_symbol(symbol):
    r"""Add a LaTeX symbol.

    Parameters
    ----------
    symbol: str
        Examples include r'\epsilon' and r'\Sigma'.

    Returns
    -------
    label: str
    """

    return backend.add_latex_symbol(symbol)
