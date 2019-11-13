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

"""Add annotations to a plot using ChIPS.

This is specific to the sherpa_contrib.profiles routines.
"""

import pychips.all as chips


def add_rlabel(x, y, lbl):
    chips.add_label(x, y, lbl,
                    ['coordsys', chips.PLOT_NORM, 'halign', 1])


def add_hline(y):
    chips.add_hline(y)
    # The following is not required, but as we can easily do it in
    # ChIPS do so.
    chips.shuffle_back(chips.chips_line)


def add_subscript(term, subscript):
    return "{}_{}".format(term, subscript)


def add_latex_symbol(symbol):
    return symbol