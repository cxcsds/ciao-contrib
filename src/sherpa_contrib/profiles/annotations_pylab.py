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

"""Add annotations to a plot using matplotlib.

This is specific to the sherpa_contrib.profiles routines, and is a
remnant of when we supported both matplotlib and chips in CIAO.
"""

from matplotlib import pyplot as plt


def add_rlabel(x, y, lbl):
    ax = plt.gca()
    plt.text(x, y, lbl, horizontalalignment='right', transform=ax.transAxes)


def add_hline(y):
    ax = plt.gca()

    # Try to match the axes; is there a better way to do this?
    lw = 1.0
    lc = 'k'

    try:
        spine = ax.spines['left']
        lw = spine.get_linewidth()
        lc = spine.get_edgecolor()
    except (KeyError, AttributeError):
        pass

    ax.axhline(y, linewidth=lw, color=lc)


def add_subscript(term, subscript):
    return "{}$_{}$".format(term, subscript)


def add_latex_symbol(symbol):
    return '${}$'.format(symbol)
