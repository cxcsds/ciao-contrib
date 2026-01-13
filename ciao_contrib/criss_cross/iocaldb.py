import numpy as np

import psf
import caldb4
from pycrates import read_file
from coords.chandra import sky_to_chandra


__all__ = ['PSF', 'psfFrac', 'psfSize',
           'Sky2Chandra',
           'OSIP',
           'CALDBException']


class PSF():
    """The psf module is used to calculate an estimate of the size of the Chandra
    PSF at a given off-axis position and energy, or the enclosed fraction of
    energy at a given off-axis position and extraction radius. This module
    (called ``psf_contrib``) extends the CIAO psf module with an
    object-oriented user interface.

    What does 'size of the PSF' mean?

    For this module, the size of the PSF refers to the radius of a circular
    region that encloses a given fraction of the counts from a point
    source. The values are calculated by interpolating the values from the REEF
    file found in the CALDB. It is therefore an approximation to the true PSF.
    """
    def __init__(self, pdata=None):
        if pdata is None:
            cdb = caldb4.Caldb(telescope="CHANDRA", product="REEF")
            # Need check here that search returns values?
            reef = cdb.search[0][:-3]
            cdb.close
            pdata = psf.psfInit(reef)
        self.pdata = pdata

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        psf.psfClose(self.pdata)

    def psfFrac(self, energy_keV, theta_arcmin, phi_deg, size_arcsec):
        """Return approximated enclosed count fraction of a PSF

        Parameters
        ----------
        energy : float
            Energy in keV
        theta : float
            off-axis angle in arcmin
            (see the MSC coordinate system described in "ahelp coords")
        phi : float
            angle in degrees
            (see the MSC coordinate system described in "ahelp coords")
        size : float
            radius in arcsec

        Returns
        -------
        eef : float
            enclosed count fraction
        """
        return psf.psfFrac(self.pdata, energy_keV, theta_arcmin,
                           phi_deg, size_arcsec)

    def psfSize(self, energy_keV, theta_arcmin, phi_deg, ecf):
        """Return approximated enclosed count fraction of a PSF

        Parameters
        ----------
        energy : float
            Energy in keV
        theta : float
            off-axis angle in arcmin
            (see the MSC coordinate system described in "ahelp coords")
        phi : float
            angle in degrees
            (see the MSC coordinate system described in "ahelp coords")

        Returns
        -------
        size : float
            radius in arcsec
        eef : float
            enclosed count fraction
        """
        return psf.psfSize(self.pdata, energy_keV,
                           theta_arcmin, phi_deg, ecf)


def psfFrac(energy, theta, phi, size):
    """Return approximated enclosed count fraction of a PSF

    Parameters
    ----------
    energy : float
        Energy in keV
    theta : float
        off-axis angle in arcmin
        (see the MSC coordinate system described in "ahelp coords")
    phi : float
        angle in degrees
        (see the MSC coordinate system described in "ahelp coords")
    size : float
        radius in arcsec

    Returns
    -------
    eef : float
        enclosed count fraction
    """
    with PSF() as _psf:
        return _psf.psfFrac(energy, theta, phi, size)


def psfSize(energy_keV, theta_arcmin, phi_deg, ecf):
    """Return approximated enclosed count fraction of a PSF

    Parameters
    ----------
    energy : float
        Energy in keV
    theta : float
        off-axis angle in arcmin
        (see the MSC coordinate system described in "ahelp coords")
    phi : float
        angle in degrees
        (see the MSC coordinate system described in "ahelp coords")

    Returns
    -------
    size : float
        radius in arcsec
    eef : float
        enclosed count fraction
    """
    with PSF() as _psf:
        return _psf.psfSize(energy_keV, theta_arcmin, phi_deg, ecf)


class Sky2Chandra:
    '''Convert Chandra physical coordinates to other coordinate systems.

    This class is a wimple wrapper around the function `sky_to_chandra` from
    the `coords.chandra` package. When an object of this class is created,
    it reads the header of a fits file to get the WCS information and saves
    that. The object can then be called to perform coordiante transformations
    without reading the header again.

    Parameters
    ----------
    evt : string
        location (path and filename) to an event files. The WCS information is
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
            X, Y position in phyical pixels
        '''
        return sky_to_chandra(self.keywords, x, y)


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
            raise CALDBException('Looking for OSIP file based on header kerywords in {} return: {}'.format(evt, cdb.errmsg))
        if len(osipfiles) == 0:
            raise CALDBException('Looking for OSIP file based on header kerywords in {} returns no match.'.format(evt))
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
