#
# Copyright (C) 2010-2012, 2013, 2014, 2015, 2016
#           Smithsonian Astrophysical Observatory
#
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

"""
Wrapper around asect solution files.
"""

import numpy as np

import pycrates as pcr

import ciao_contrib.logger_wrapper as lw

import ciao_contrib._tools.fileio as fileio

# __all__ = ("",)

lgr = lw.initialize_module_logger('_tools.aspsol')
v3 = lgr.verbose3


class AspectSolution(object):
    """Represent the aspect solution for an observation. It can consist
    of 1 or more aspect solution files. This class deals with sorting
    the files in time order.

    After creation, the idea is that you use the .name field for
    any tool that needs the aspect solution (e.g. asphist.infile or
    skyfov.aspect), and nbins for the number of bins to use in
    a call to asphist.

    If there are multiple files then the .name field will be a
    comma-separated list of files. The assumption here is that
    the length of this string will not be large enough to need
    a stack file.
    """

    def __init__(self, asolfiles, tmpdir="/tmp"):

        nasol = len(asolfiles)
        if nasol == 0:
            raise ValueError("asolfiles must contain at least one entry.")

        elif nasol == 1:
            self.name = asolfiles[0]
            self._files = asolfiles

        else:
            v3("Time-sorting aspect solutions.")
            self._files = fileio.sort_mjd(asolfiles)
            v3("Time sorted orded: {}".format(self._files))

            self.name = ",".join(self._files)

    # See https://icxc.harvard.edu/pipe/ascds_help/2009/0651.html
    def nbins(self, roll=600.0, xy=0.5):
        """Return the number of aspect bins to use (the max_bin parameter
        of asphist), given the set of aspect files.

        The roll and xy parameters correspond to the asphist.res_roll and
        asphist.res_xy parameter values (and are in arcsec).
        They used to be read from the asphist parameter file
        but have now been converted to default parameter values.

        Users should check that these defaults are still valid with
        new CIAO releases (in case this code doesn't get updated).
        """

        ralim = (None, None)
        declim = (None, None)
        rolllim = (None, None)

        def get_minmax(cr, colname, orange):
            "Work out min/max from column + input values"

            omin, omax = orange

            vals = pcr.get_colvals(cr, colname)
            vmin = vals.min()
            vmax = vals.max()

            if omin is None:
                nmin = vmin
            else:
                nmin = min(vmin, omin)

            if omax is None:
                nmax = vmax
            else:
                nmax = min(vmax, omax)

            return (nmin, nmax)

        # the min/max check could be done within __init__
        for aspfile in self._files:
            asol = pcr.read_file(aspfile)
            ralim = get_minmax(asol, "ra", ralim)
            declim = get_minmax(asol, "dec", declim)
            rollim = get_minmax(asol, "roll", rolllim)

        n_ra = (ralim[1] - ralim[0]) * 3600.0 / xy
        n_dec = (declim[1] - declim[0]) * 3600.0 / xy
        n_roll = (rollim[1] - rollim[0]) * 3600.0 / roll

        nbins = np.ceil(n_ra * n_dec * n_roll).astype(np.int)
        if nbins <= 10000:
            return 10000

        else:
            # would base 2 be better than base 10 here?
            # l = np.ceil(np.log10(nbins)).astype(np.int)
            # return 10 ** l
            l = np.ceil(np.log2(nbins)).astype(np.int)
            return 2 ** l
