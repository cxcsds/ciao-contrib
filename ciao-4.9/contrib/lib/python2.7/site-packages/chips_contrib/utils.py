#
#  Copyright (C) 2009, 2010, 2011, 2015
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

"""Utility routines for ChIPS.
"""

import numpy as np

import pychips as chips
import pychips.advanced as chipsadv

from crates_contrib.utils import read_ds9_contours, SimpleCoordTransform

__all__ = (
    "xlabel", "ylabel", "title",
    "xlog", "ylog", "xylog", "xlin", "ylin", "xylin",
    "xlim", "ylim", "xylim",
    "add_ds9_contours")


def xlabel(txt):
    """Change the label of the current X axis to txt.
    Using a value of "" will "hide" or turn-off the
    display. It is equivalent to the ChIPS command:

      set_plot_xlabel(txt)

    """

    chips.set_plot_xlabel(txt)


def ylabel(txt):
    """Change the label of the current Y axis to txt.
    Using a value of "" will "hide" or turn-off the
    display. It is equivalent to the ChIPS command:

      set_plot_ylabel(txt)

    """

    chips.set_plot_ylabel(txt)


def title(txt):
    """Change the title of the current plot to txt.
    Using a value of "" will "hide" or turn-off the
    display. It is equivalent to the ChIPS command:

      set_plot_title(txt)

    """

    chips.set_plot_title(txt)


def xlog():
    """Change the current X axis to display with a
    logarithmic scale. It is equivalent to the ChIPS
    command:

      log_scale(X_AXIS)

    """

    chips.log_scale(chips.X_AXIS)


def ylog():
    """Change the current Y axis to display with a
    logarithmic scale. It is equivalent to the ChIPS
    command:

      log_scale(Y_AXIS)

    """

    chips.log_scale(chips.Y_AXIS)


def xylog():
    """Change the current X and Y axes to display with a
    logarithmic scale. It is equivalent to the ChIPS
    command:

      log_scale()
      log_scale(XY_AXIS)

    """

    chips.log_scale(chips.XY_AXIS)


def xlin():
    """Change the current X axis to display with a
    linear scale. It is equivalent to the ChIPS
    command:

      lin_scale(X_AXIS)

    """

    chips.lin_scale(chips.X_AXIS)


def ylin():
    """Change the current Y axis to display with a
    linear scale. It is equivalent to the ChIPS
    command:

      lin_scale(Y_AXIS)

    """

    chips.lin_scale(chips.Y_AXIS)


def xylin():
    """Change the current X and Y axes to display with a
    linear scale. It is equivalent to the ChIPS
    command:

      lin_scale()
      lin_scale(XY_AXIS)

    """

    chips.lin_scale(chips.XY_AXIS)


def xlim(lo=chips.AUTO, hi=chips.AUTO):
    """Change the current X axis limits to the range
    lo to hi.

    It is equivalent to the ChIPS command:

      limits(X_AXIS, lo, hi)

    """

    chips.limits(chips.X_AXIS, lo, hi)


def ylim(lo=chips.AUTO, hi=chips.AUTO):
    """Change the current Y axis limits to the range
    lo to hi.

    It is equivalent to the ChIPS command:

      limits(Y_AXIS, lo, hi)

    """

    chips.limits(chips.Y_AXIS, lo, hi)


def xylim(lo=chips.AUTO, hi=chips.AUTO):
    """Change the current X and Y axis limits to the range
    lo to hi.

    It is equivalent to the ChIPS command:

      limits(lo, hi, lo, hi)

    Note that this does not allow you to set different
    limits for the X and Y axes; use thelimits command for
    that.
    """

    chips.limits(lo, hi, lo, hi)


def _add_nans(xs):
    """Append all the elements of the input array, which are assumed
    to be numpy arrays, separating them by NaN. The return value is a
    1D numpy array.

    """

    nelem = 0
    for x in xs:
        nelem += x.size

    if nelem == 0:
        return np.ones(0)

    nnan = len(xs) - 1
    nout = nelem + nnan
    out = np.ones(nout)
    s = 0
    nout -= 1
    for x in xs:
        ne = x.size
        out[s:s + ne] = x.copy()
        s += ne
        if s < nout:
            out[s] = np.nan

        s += 1

    return out


def add_ds9_contours(fname,
                     color="green", thickness=1,
                     style="solid", depth=100,
                     stem="ds9con",
                     coords=None, fromsys=None, tosys=None):
    """Add the contours from a DS9 *.con file as a
    ChIPS curve with the options defined by the color, thickness,
    style, depth, and stem arguments (the color, thickness, and
    style arguments map to the line.* curve attributes and the
    symbol.style attribute is set to "none").

    The coords, fromsys, and tosys arguments are used to convert
    the coordinates to a different system: coords is either the
    name of an image or a crate that contains the desired coordinate
    systems, fromsys is the name of the coordinate system used to
    store the contours and tosys the name to convert to. The valid
    values for fromsys and tosys are:

      world, eqpos
      physical, sky
      logical, image

    """

    lopts = {"line.color": color, "line.thickness": thickness,
             "line.style": style, "symbol.style": "none",
             "baddata": "omit",
             "depth": depth, "stem": stem}

    # To simplify use, we treat the contours as a single curve separating each
    # fragment by a NaN which indicates to ChIPS not to draw a segment between
    # the fragments (since we set baddata to 'omit'). Ideally we would use a
    # line here, but we only guarantee handling of NaN/Inf values with curves
    # in ChIPS at present.
    #
    (xall, yall) = read_ds9_contours(fname, coords=coords,
                                     fromsys=fromsys, tosys=tosys)
    xl = _add_nans(xall)
    yl = _add_nans(yall)

    chipsadv.open_undo_buffer()
    try:
        # Do we need to add WCS axes? This is not a complete check but we
        # can not identify WCS axes from normal ones with ChIPS at present
        # so restrict to this check.
        #
        if coords is not None and \
           (tosys is None or tosys.lower() in ["world", "eqpos"]) and \
           chips.info(chips.chips_plot) is None:

            tr = SimpleCoordTransform(coords)
            world = tr.transforms["world"]["transform"]
            chips.add_axis(chips.XY_AXIS, 0,
                           np.nanmax(xl), np.nanmin(xl),
                           np.nanmin(yl), np.nanmin(yl),
                           world)

        chips.add_curve(xl, yl, lopts)

    except:
        chipsadv.discard_undo_buffer()
        raise

    chipsadv.close_undo_buffer()

# End
