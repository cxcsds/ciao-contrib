from functools import partial

import numpy as np
from sherpa.optmethods.optfcts import lmdif
from .constants import arcsec_per_pix, wavelength_scale

from ciao_contrib.psf_contrib import PSF

psf = PSF()


def counts_circle_band(evt, pos, waveband, skyconverter, psffrac=0.9):
    """Counts in a circle around pos in a given energy band

    Parameters
    ----------
    evt : crates object
        Open crates object with the event file
    pos : tuple
        (x, y) position in sky coordinates (in degrees) around which to count
    waveband : tuple
        (wave_low, wave_high) in Angstroms
    skyconverter : Chandra2Sky object
        Object that encapsulates the Chandra coordinate conversions for a
        particular event file
    psffrac : float
        Fraction of the PSF to include in the circle.
    """
    en_low = 12398 / np.max(waveband)   # Ang to eV
    en_high = 12398 / np.min(waveband)  # Ang to eV
    # Get position in MSC coordinates
    coo = skyconverter(pos[0], pos[1])
    # Note that this function expects input in keV, thus an extra "/1000" here
    radius = psf.psfSize(
        np.mean([en_low / 1000, en_high / 1000]),
        coo["theta"][0],
        coo["phi"][0],
        psffrac,
    )

    ind = np.hypot(evt.sky.x.values - pos[0], evt.sky.y.values - pos[1]) < radius
    ind = ind & (evt.energy.values > en_low) & (evt.energy.values < en_high)
    return ind.sum() / psffrac

# Estimate of point source contribution to a 1 pixel long part of the grating
# spectrum Sorry Dave: There is no analytic solution to find where the point
# source PSF falls below the threshold (called "maxlevel" here). I need to
# optimize that numerically and the scipy function to numerically find a root
# works by putting in the function that is optimized so I have to write this a
# sa function


def pntsrc_fluxlevel(r, maxlevel, energy, theta, phi, N, arm, cross_disp_pixel):
    """Estimate radius where point source flux drops below maxlevel

    For a given radius, this function estimates how much above or below a certain level
    the flux of a point source will be.
    This flux level is expressed as counts / Ang for a grating extraction.

    The purpose of this function is to be used in a root finder: The roots of this function
    are the locations where the contribution of a point source to a grating spectrum is
    exactly maxlevel and the interface is written to match the requirements of
    the functions in `sherpa.optmethods.optfcts.lmdif`.

    Parameters
    ----------
    r : array
        Array with one element.
        Radius (in pix) from the location of the point source
    maxlevel : float
        cnt / Ang in an extracted grating spectrum
    energy : float
        Energy in keV. Needed because the PSF is energy dependent.
    theta, phi : float
        Source coordinates in Chandra's MSC coordinate system
    N : float or int
        total point source number of counts
    arm : string
        "heg" or "meg" to select the wavelength scale.
    cross_disp_pixel : float
        width of the grating extraction region in the cross-dispersion direction in pixels

    Returns
    -------
    radius : float
        radius [in pixels] at which the contribution of the point source to the
        extracted grating spectrum is less than maxlevel [cnts / Ang]
    radius : float
        (Same as previous, but the Sherpa optimizers to be used with this function
        expect this output format)
    """
    r = r[0]
    dPSFdr = psf.psfFrac(energy, theta, phi, (r + 1) * arcsec_per_pix) - psf.psfFrac(
        energy, theta, phi, r * arcsec_per_pix
    )
    counts_per_pixel = N * dPSFdr / (2 * np.pi * (r + 0.5 ))
    out = counts_per_pixel * cross_disp_pixel / wavelength_scale[arm] - maxlevel
    return out, out


def pnt_src_masking_region(
    evt,
    osip,
    skyconverter,
    src,
    contaminator,
    dg,
    wavelength,
    arm,
    cross_disp_pixel,
    factor=0.1,
    logfile="terminal",
):
    """Masking a grating spectrum due to point source contamination

    Parameters
    ----------
    evt : crates object
        Open crates object with the event file
    osip : OSIP object
        Object that encapsulates the OSIP information for a particular event
        file
    skyconverter: Chandra2Sky Object
        Object that encapsulates the Chandra coordinate conversions for a
        particular event file
    src : tuple
        coordinates (in pixels) of the 0 order position of the source that
        causes the grating spectrum
    contaminator : tuple
        coordinates (in pixels) of the point source that contaminates the
        grating arm
    dg : float
        distance (in pixels) from the contaminating point source to the grating
        spectrum
    wavelength : float
        wavelength (in Ang) on the grating arm
    arm : string
        "heg" or "meg" to select the grating arm
    cross_disp_pixel : float
        width of the grating extraction region in the cross-dispersion direction in pixels
    factor : float
        Acceptable contamination level by point source to grating spectrum,
        e.g. 0.1 means that for any bin in the grating spectrum < 10% of the
        counts are contributed by the point source.  Note that this is not an
        exact calculation, but more an estimate good to factors of a few, so
        choose a conservative factor here!

    Returns
    -------
    d_lambda_min, d_lambda_max : float
        Wavelength interval around "wavelength" (in Ang) that needs to be
        masked out due to point source contamination.  If no masking is needed,
        the function returns (9999.0, 9999.0) or (9998.0, 9998.0) or (9997.0, 9997.0)
        depending on the reason why no masking is needed.
        If a location is not on a chip, (np.nan, np.nan) is returned.
    """
    energyband = osip(contaminator[0], contaminator[1], 12398 / wavelength)
    if np.isnan(energyband[0]):
        return np.nan, np.nan
    waveband = (12398 / energyband[1], 12398 / energyband[0])
    pnt_src_counts = counts_circle_band(evt, contaminator, waveband, skyconverter)
    if pnt_src_counts < 1:
        # No counts in point source in the band in question, so no need to mask
        # anything.  I just return an interval with size 0 for now, but I think
        # it would be better to have some other mechanism, e.g. return nan or
        # NONE
        return 9999.0, 9999.0
    grt_counts_0 = counts_circle_band(evt, src, waveband, skyconverter)
    if grt_counts_0 == 0:
        text = f"Estimating zero grating counts from 0th order for source at {contaminator[0]},{contaminator[1]}"
        if logfile == 'terminal':
            print(text)
        else:
            logfile.write(text + "\n")
        return 0.8 * waveband[0], 1.2 * waveband[1]

    # The following line does not do anything right now, but I have it here to
    # mark the position where we need to change the code if we want to take the
    # difference in arfs into account
    grt_counts = grt_counts_0

    pnt_src_maxlevel = grt_counts * factor
    coo = skyconverter(contaminator[0], contaminator[1])
    if (
        pntsrc_fluxlevel(
            [0.0],
            pnt_src_maxlevel,
            12.4 / wavelength,
            coo["theta"][0],
            coo["phi"][0],
            pnt_src_counts,
            arm,
            cross_disp_pixel,
        )[0]
        < 0
    ):
        # Point source is so weak that it never contributes more than allowed
        # Nothing needs to be masked.  I just return a interval with size 0 for
        # now, but I think it would be better to have some other mechanism,
        # e.g. return nan or NONE
        return 9998.0, 9998.0

    function = partial(
        pntsrc_fluxlevel,
        maxlevel=pnt_src_maxlevel,
        energy=12.4 / wavelength,
        theta=coo["theta"][0],
        phi=coo["phi"][0],
        N=pnt_src_counts,
        arm=arm,
        cross_disp_pixel=cross_disp_pixel,
    )
    out = lmdif(function, (5.0,), (0.,), (1000,))
    if not out[0]:
        raise Exception(f'Failed to find PSF radius with flux level {pnt_src_maxlevel}: {out[3]}')

    if dg >= out[1][0]:
        # Source is relatively weak and so far away from grating arm
        # that we don't have to mask anything
        return 9997.0, 9997.0
    else:
        d_g = np.sqrt(out[1][0]**2 - dg**2)  # all in units of pixels
        d_lambda = d_g * wavelength_scale[arm]
        return max(0, wavelength - d_lambda), wavelength + d_lambda
