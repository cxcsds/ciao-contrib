#
#  Copyright (C) 2009, 2010, 2015, 2016, 2019
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

"Simple utility routines for CIAO analysis"

import numpy as np

from sherpa.utils import print_fields

__all__ = ["simple_stats", "simple_hist",
           "SimpleStats", "SimpleHistogram"]


class SimpleStats:
    "Calculate simple statistic information for an array"

    def __init__(self, array):

        # Ensure we have a numpy array
        array = np.asarray(array)

        self.npts = array.size
        self.min = array.min()
        self.max = array.max()
        self.total = array.sum()
        self.mean = np.mean(array)
        self.median = np.median(array)
        self.stddev = np.std(array)

    def __str__(self):

        names = ["npts", "min", "max", "total", "mean", "median", "stddev"]
        vals = [getattr(self, n) for n in names]
        return print_fields(names, dict(zip(names, vals)))


class SimpleHistogram:
    "Calculate a 1D histogram for an array"

    def __init__(self, array, nbins=10, min=None, max=None, step=None):
        """Create a histogram of the values in array. The bins are
        determined from the min and max arguments; if they are None
        then the corresponding limit from the data is used. min refers
        to the lower edge of the first bin and max the upper edge of
        the last bin.

        If step is not None then it is used as the bin width, and the
        upper limit is modified if (max-min)/step is not an integer.
        If step is None then the number of bins used is taken from
        the nbins parameter.

        This routine only allows equally-spaced bins to be created,
        and ignores all values outside the range min <= x <= max.

        Note that all but the last bin is half open - i.e. they cover
        the range

          x_i <= x < x_i+1

        but the last bin covers

          x_i <= x <= x_i+1

        """

        # Ensure we have a numpy array
        array = np.asarray(array)

        if min is None:
            min = array.min()
        if max is None:
            max = array.max()

        if max <= min:
            raise ValueError("Maximum value ({0}) is <= minimum ({1})".format(max, min))

        if step is None:
            if nbins < 1:
                raise ValueError("nbins must be > 0, sent {0}".format(nbins))
        else:
            if step <= 0:
                raise ValueError("step, if not None, must be > 0, sent {0}".format(step))

            nb = (max - min) / step
            if nb != int(nb):
                nbins = int(nb) + 1
            else:
                nbins = int(nb)
            max = min + nbins * step

        (y, bins) = np.histogram(array, range=(min, max), bins=nbins)

        self.xlow = bins[:-1]
        self.xhigh = bins[1:]
        self.y = y

    def __str__(self):

        names = ["xlow", "xhigh", "y"]
        vals = [getattr(self, n) for n in names]
        return print_fields(names, dict(zip(names, vals)))


def simple_stats(array):
    """Return a set of simple statistical values for the input array."""

    return SimpleStats(array)


def simple_hist(array, nbins=10, min=None, max=None, step=None):
    """Calculates a one-dimensional histogram of the numerical
    data in array.

    The bins are determined from the min and max arguments; if they
    are None then the corresponding limit from the data is used. min
    refers to the lower edge of the first bin and max the upper edge
    of the last bin.

    If step is not None then it is used as the bin width, and the
    upper limit is modified if (max-min)/step is not an integer.  If
    step is None then the number of bins used is taken from the nbins
    parameter.

    This routine only allows equally-spaced bins to be created, and
    ignores all values outside the range min <= x <= max.

    Note that all but the last bin is half open - i.e. they cover the
    range

      x_i <= x < x_i+1

    but the last bin covers

      x_i <= x <= x_i+1

    """

    return SimpleHistogram(array, nbins=nbins, min=min, max=max, step=step)
