#
#  Copyright (C) 2020
#            Smithsonian Astrophysical Observatory, MIT
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
"""The psf module is used to calculate an estimate of the size of the Chandra
PSF at a given off-axis position and energy, or the enclosed fraction of energy
at a given off-axis position and extraction radius. This module (called
``psf_contrib``) extends the CIAO psf module with an object-oriented user
interface.

What does 'size of the PSF' mean?

For this module, the size of the PSF refers to the radius of a circular region
that encloses a given fraction of the counts from a point source. The values
are calculated by interpolating the values from the REEF file found in the
CALDB. It is therefore an approximation to the true PSF.
"""
import contextlib

import psf
import caldb4


__all__ = ['PSF', 'psfFrac', 'psfSize']


class PSF(contextlib.AbstractContextManager):
    def __init__(self, pdata=None):
        if pdata is None:
            cdb = caldb4.Caldb(telescope="CHANDRA", product="REEF")
            reef = cdb.search[0][:-3]
            pdata = psf.psfInit(reef)
        self.pdata = pdata

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        psf.psfClose(self.pdata)

    def psfFrac(self, energy_keV, theta_arcmin, phi_deg, size_arcsec):
        return psf.psfFrac(self.pdata, energy_keV, theta_arcmin,
                           phi_deg, size_arcsec)

    def psfSize(self, energy_keV, theta_arcmin, phi_deg, ecf):
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
