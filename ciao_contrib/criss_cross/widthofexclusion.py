from functools import partial

import numpy as np
from sherpa.optmethods.optfcts import lmdif

from ciao_contrib.psf_contrib import PSF, psfSize

psf = PSF()

# Currently, we only do HETG/ACIS,
# so I hardcode the default min_tg_d number here
min_tg_d = -2.39  # arcsec
max_tg_d = 2.39   # arcsec
acis_pix_size = 0.4920  # arcsec / pixel
cross_disp_width = (max_tg_d - min_tg_d) / acis_pix_size  # pixel

wavelength_scale = {1: 0.0055595,  # HEG Ang / ACIS pixel
                    2: 0.0111200,  # MEG Ang / ACIS pixel
                   }


def counts_circle_band(evt, x, y, waveband, skyconverter, psffrac=0.9):
    en_low = 12398 / np.max(waveband)   # Ang to eV
    en_high = 12398 / np.min(waveband)  # Ang to eV
    # Get position in MSC coordinates
    coo = skyconverter(x, y)
    # Note that this function expects input in keV, thus an extra "/1000" here
    radius = psfSize(np.mean([en_low / 1000, en_high / 1000]),
                     coo['theta'][0], coo['phi'][0], psffrac)

    ind = np.sqrt((evt.sky.x.values - x)**2 + (evt.sky.y.values - y)**2) < radius
    ind = ind & (evt.energy.values > en_low) & (evt.energy.values < en_high)
    return ind.sum() / psffrac

# Estimate of point source contribution to a 1 pixel long part of the grating
# spectrum Sorry Dave: There is no analytic solution to find where the point
# source PSF falls below the threshold (called "maxlevel" here). I need to
# optimize that numerically and the scipy function to numerically find a root
# works by putting in the function that is optimized so I have to write this a
# sa function


def pntsrc_fluxlevel(r, maxlevel, energy, theta, phi, N, wavelength_scale):
    '''Estimate radius where point source flux drops below maxlevel

    For a given radius, this function estimates how much above or below a certain level
    the flux of a point source will be.
    This flux level is expressed as counts / Ang for a grating extraction.

    The purpose of this function is to be used in a root finder: The roots of this function
    are the locations where the contribution of a point source to a grating spectrum is
    exactly maxlevel and the interface is written to match the requirements of
    the functiions in `sherpa.optmethods.optfcts.lmdif`.

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
    wavelength_scale : float
        Ang / pixel fo the given grating arm

    Returns
    -------
    radius : float
        radius [in pixels] at which the contribution of the point source to the
        extracted grating spectrum is less than maxlevel [cnts / Ang]
    radius : float
        (Same as previous, but the Sherpa optimizers to be used with this function
        expect this output format)
    '''
    r = r[0]
    dPSFdr = (psf.psfFrac(energy, theta, phi, (r + 1)  * acis_pix_size) -
              psf.psfFrac(energy, theta, phi, r  * acis_pix_size))
    counts_per_pixel = N * dPSFdr / (2 * np.pi * (r + 0.5 ))
    out = counts_per_pixel * cross_disp_width / wavelength_scale - maxlevel
    return out, out


def pnt_src_masking_region(evt, osip, skyconverter, x_0order, y_0order,
                           x_pnt, y_pnt, dg, wavelength, tg_part, factor=.1, logfile='terminal'):
    '''Masking a grating spectrum due to point source contamination

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
    x_0order, y_0order : float
        coordinates (in pixels) of the 0 order position of the source that
        causes the grating spectrum
    x_pnt, y_pnt : float
        coordinates (in pixels) of the point source that contaminates the
        grating arm
    dg : float
        distance (in pixels) from the contaminating point source to the grating
        spectrum
    wavelength : float
        wavelength (in Ang) on the grating arm
    tg_part : int
        1 for an HEG arm, 2 for an MEG arm
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
    '''
    energyband = osip(x_pnt, y_pnt, 12398 / wavelength, logfile)
    waveband = (12398 / energyband[1], 12398 / energyband[0])
    pnt_src_counts = counts_circle_band(evt, x_pnt, y_pnt, waveband, skyconverter)
    if pnt_src_counts < 1:
        # No counts in point source in the band in question, so no need to mask
        # anything.  I just return an interval with size 0 for now, but I think
        # it would be better to have some other mechanism, e.g. return nan or
        # NONE
        return 9999.0, 9999.0
    grt_counts_0 = counts_circle_band(evt, x_0order, y_0order,
                                      waveband, skyconverter)
    if grt_counts_0 == 0:
        if logfile == 'terminal':
            print('Estimating zero grating counts from 0th order for source at {},{}'.format(x_pnt, y_pnt))
        else:
            logfile.write('Estimating zero grating counts from 0th order for source at {},{} \n'.format(x_pnt, y_pnt))
        return 0.8 * waveband[0], 1.2 * waveband[1]

    # The following line does not do anything right now, but I have it here to
    # mark the position where we need to change the code if we want to take the
    # difference in arfs into account
    grt_counts = grt_counts_0

    pnt_src_maxlevel = grt_counts * factor
    coo = skyconverter(x_pnt, y_pnt)
    if pntsrc_fluxlevel([0.], pnt_src_maxlevel, 12.4 / wavelength,
                        coo['theta'][0], coo['phi'][0],
                        pnt_src_counts, wavelength_scale[tg_part])[0] < 0:
        # Point source is so weak that it never contributes more than allowed
        # Nothing needs to be masked.  I just return a interval with size 0 for
        # now, but I think it would be better to have some other mechanism,
        # e.g. return nan or NONE
        return 9998.0, 9998.0

    function = partial(pntsrc_fluxlevel,
                   maxlevel=pnt_src_maxlevel,
                   energy=12.4 / wavelength,
                   theta=coo['theta'][0],
                   phi=coo['phi'][0],
                   N=pnt_src_counts,
                   wavelength_scale=wavelength_scale[tg_part])
    out = lmdif(function, (5.0,), (0.,), (1000,))
    if not out[0]:
        raise Exception(f'Failed to find PSF radius with flux level {pnt_src_maxlevel}: {out[3]}')

    if dg >= out[1][0]:
        # Source is relatively weak and so far away from grating arm
        # that we don't have to mask anything
        return 9997.0, 9997.0
    else:
        d_g = np.sqrt(out[1][0]**2 - dg**2)  # all in units of pixels
        d_lambda = d_g * wavelength_scale[tg_part]
        return max(0, wavelength - d_lambda), wavelength + d_lambda
