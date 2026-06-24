# Copyright (C) 2025-2026 MIT
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

import numpy as np

import caldb4
from pycrates import read_file
from coords.chandra import sky_to_chandra
from coords.chandra import cel_to_chandra


__all__ = ['Sky2Chandra',
           'Cel2chandra',
           'OSIP',
           'CALDBException']


class Sky2Chandra:
    '''Convert Chandra physical coordinates to other coordinate systems.

    This class is a simple wrapper around the function `sky_to_chandra` from
    the `coords.chandra` package. When an object of this class is created,
    it reads the header of a fits file to get the WCS information and saves
    that. The object can then be called to perform coordinate transformations
    without reading the header again.

    Parameters
    ----------
    evt : string
        location (path and filename) to an event file. The WCS information is
        read from the header of that file.
    '''
    def __init__(self, evt):
        cr = read_file(evt)
        self.keywords = {n: cr.get_key_value(n) for n in cr.get_keynames()}

    def __call__(self, x, y):
        '''
        Parameters
        ----------
        x, y : float
            X, Y position in physical pixels
        '''
        return sky_to_chandra(self.keywords, x, y)

class Cel2Chandra:
    '''Convert Celestial coordinates to other coordinate systems.

    This class is a simple wrapper around the function `cel_to_chandra` from
    the `coords.chandra` package. When an object of this class is created,
    it reads the header of a fits file to get the WCS information and saves
    that. The object can then be called to perform coordinate transformations
    without reading the header again.

    Parameters
    ----------
    evt : string
        location (path and filename) to an event file. The WCS information is
        read from the header of that file.
    '''
    def __init__(self, evt):
        cr = read_file(evt)
        self.keywords = {n: cr.get_key_value(n) for n in cr.get_keynames()}

    def __call__(self, x, y):
        '''
        Parameters
        ----------
        x, y : float
            X, Y position in physical pixels
        '''
        return cel_to_chandra(self.keywords, x, y)

class CALDBException(Exception):
    pass


class OSIP:
    def __init__(self, evt):
        cr = read_file(evt)
        cdb = caldb4.Caldb("", "", "OSIP", evt)
        cdb.CTI_APP = cr.get_key_value('CTI_APP')
        cdb.CTI_CORR = cr.get_key_value('CTI_CORR')
        cdb.start = cr.get_key_value('TSTART')
        cdb.stop = cr.get_key_value('TSTOP')
        osipfiles = cdb.search
        if cdb.errmsg is not None:
            raise CALDBException('Looking for OSIP file based on header keywords in {} return: {}'.format(evt, cdb.errmsg))
        if len(osipfiles) == 0:
            raise CALDBException('Looking for OSIP file based on header keywords in {} returns no match.'.format(evt))
        cdb.close
        self.osip = read_file(osipfiles[0][:-3] + '[AXAF_OSIP]')
        self.skyconverter = Sky2Chandra(evt)

    def __call__(self, x, y, energy):
        """
        Parameters
        ----------
        x, y : float
            Chandra physical coordinates
        energy : float
            energy in eV

        Returns
        -------
        ener_lo, ener_hi : float
            Lower and upper bound for OSIP region
        fracresp : float
            Fractional energy contained in the given region
        """
        coords = self.skyconverter(x, y)
        chipx = coords["chipx"][0]
        chipy = coords["chipy"][0]

        # If the point is not on a chip, the converter returns
        # the coordinate system for the closest chip, but with pixel numbers outside
        # the range 1..1023. We allow a little wider area to account for rounding
        # errors and dither and return the OSIP at the chip edge in that case.
        if not (-10 < chipx < 1034) or not (-10 < chipy < 1034):
            return np.nan, np.nan, np.nan
        chipx = np.clip(1, int(chipx), 1023)
        chipy = np.clip(1, int(chipy), 1023)

        ind = self.osip.get_column("ccd_id").values == coords["chip_id"][0]
        ind = ind & (self.osip.get_column('chipx_min').values <= int(chipx))
        ind = ind & (self.osip.get_column('chipx_max').values >= int(chipx))
        ind = ind & (self.osip.get_column('chipy_min').values <= int(chipy))
        ind = ind & (self.osip.get_column('chipy_max').values >= int(chipy))

        if ind.sum() != 1:
            raise ValueError('No unique OSIP value found for given position in {}'.format(self.osip.get_filename()))

        n = self.osip.get_column('npoints').values[ind][0]
        energ = np.squeeze(self.osip.get_column('energy').values[ind, :n])
        energ_lo = np.squeeze(self.osip.get_column('energ_lo').values[ind, :n])
        energ_hi = np.squeeze(self.osip.get_column('energ_hi').values[ind, :n])
        fracresp = np.squeeze(self.osip.get_column('fracresp').values[ind, :n])
        return np.interp(energy, energ, energ_lo), \
            np.interp(energy, energ, energ_hi), \
            np.interp(energy, energ, fracresp)
