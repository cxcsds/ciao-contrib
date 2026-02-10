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


class SourceNotOnChipException(Exception):
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

    def __call__(self, x, y, energy, logfile='terminal'):
        '''
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
            Frational energy contained in the given region
        '''
        coords = self.skyconverter(x, y)

        # In testing, we found that source can have e.g. chipx=0.4
        # while the OSIP regions are only defined from 1 on.
        # We conclude that that's just due to dither and numerics
        # and should not stop the code.
        # So, we simply reset min and max number here and put in a
        # warning for now.
        chipx_orig = coords['chipx'][0]
        chipy_orig = coords['chipy'][0]
        # Make sure x,y is in range 1..1023
        chipx = max(min(chipx_orig, 1023), 1)
        chipy = max(min(chipy_orig, 1023), 1)
        # Print function for debugging. Can hopefully be removed later:
        if (chipx != chipx_orig) or (chipy != chipy_orig):
            if logfile == 'terminal':
                print('Reset (chipx, chipy) = ({}, {}) such that x and y are in range 1..1023 for source at (x,y)=({},{}).'.format(chipx_orig, chipy_orig, x, y))
            else:
                logfile.write('Reset (chipx, chipy) = ({}, {}) such that x and y are in range 1..1023 for source at (x,y)=({},{}). \n'.format(chipx_orig, chipy_orig, x, y))

        ind = self.osip.get_column('ccd_id').values == coords['chip_id'][0]
        if ind.sum() == 0:
            raise SourceNotOnChipException('Source at ({}, {}) is not on any chip.'.format(x,y))

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
