#
# Copyright (C) 2018, 2020, 2023
# Smithsonian Astrophysical Observatory
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

'An IMAGECrate that knows which pixels are valid'

from pycrates import IMAGECrate
import numpy as np


class MaskedIMAGECrate(IMAGECrate):
    """
    This class extends the basic IMAGECrate by adding a 'valid'
    method.

    The valid method takes the 0-based image index and sees if
    the pixel is valid, where valid means:

     - pixel is not a special IEEE value, eg NaN or +/- INF
     - pixel is not an integer NULL value, eg -999 (if set)
     - pixel is inside the data subspace, ie region filter
    """

    def __init__(self, filename, mode="r"):
        super().__init__(filename, mode)

        if 2 != len(self.get_image().values.shape):
            raise NotImplementedError("Only 2D images are supported")

        self._pix = self.get_image().values
        self.__make_valid_mask()

    def __check_finite(self):
        """Check for NaN|Inf

        """
        badidx = np.where(~(np.isfinite(self._pix)))
        self._mask[badidx[0]] = 0

    def __check_null(self):
        """Check for integer NULL values """
        nullval = self.get_image().get_nullval()
        if nullval is None:  # is None, not == None (nor 0)
            return
        nullidx = np.where(self._pix == nullval)
        self._mask[nullidx[0]] = 0

    def __check_subspace(self):
        """Check to see if pixels are in subspace
        """
        _a = [x.lower() for x in self.get_axisnames()]
        if 'sky' in _a:
            sky = 'sky'
        elif 'pos' in _a:
            sky = 'pos'
        else:
            #  warning()
            return

        xform = self.get_axis(sky).get_transform()
        subspace = self.get_subspace_data(1, sky)

        xcol = 'x'
        ycol = 'y'

        def get_col_range(col_name):
            'Get column range'
            col_range = self.get_subspace_data(1, col_name)
            if col_range:
                my_range = (col_range.range_min, col_range.range_max)
            else:
                my_range = None
            return my_range

        def check_col_range(col_range, col_val):
            'Check if val is in ranges'
            if col_range is None or len(col_range) == 0:
                return True

            for low, hi in zip(*col_range):
                if low <= col_val < hi:
                    return True
            return False

        xrange_vals = get_col_range(xcol)
        yrange_vals = get_col_range(ycol)

        # We need to check regInside using physical coords. Compute 'em all.
        ylen, xlen = self._pix.shape

        # TODO: is there is numpy meshgrid or somesort to do this
        ivals = [x+1.0 for x in range(xlen)]   # +1 -> image coords
        jvals = [y+1.0 for y in range(ylen)]
        ivals = np.array(ivals*ylen)  # why using lists instead of np.arrays
        jvals = np.repeat(jvals, xlen)
        ijvals = list(zip(ivals, jvals))
        # Due to memory leaks/etc, best to send all i, j in at once.
        xyvals = xform.apply(ijvals)

        # Crates still uses the old region module :(
        import region as old
        for ij, xy in zip(ijvals, xyvals):
            i = int(ij[0])-1
            j = int(ij[1])-1
            x = xy[0]
            y = xy[1]

            if not check_col_range(xrange_vals, x):
                self._mask[j][i] = 0
                continue

            if not check_col_range(yrange_vals, y):
                self._mask[j][i] = 0
                continue

            if subspace.region and not old.regInsideRegion(subspace.region, x, y):
                self._mask[j][i] = 0
                continue

            self._mask[j][i] = 1

    def __make_valid_mask(self):
        """
        Apply all the filters to create the mask array
        """
        self._mask = np.ones_like(self._pix)  # Assume everything is good
        self.__check_finite()
        self.__check_null()
        self.__check_subspace()

    def valid(self, i, j):
        """
        Is pixel at 0-based indices i, j valid?
        """
        return self._mask[j][i] == 1
