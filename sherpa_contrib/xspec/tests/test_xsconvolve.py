#
#  Copyright (C) 2017
#            Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
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

import numpy as np
from numpy.testing import assert_allclose

from sherpa.data import Data1DInt
from sherpa.models.basic import Box1D, PowLaw1D
from sherpa.astro.xspec import XSpowerlaw
from sherpa.models.parameter import Parameter

from sherpa_contrib.xspec.xsconvolve import XScflux, XSzashift
from sherpa_contrib.xspec.xsmodels import XSConvolutionKernel, \
    XSConvolutionModel


# really should bite the bullet and get pytest working...
counter = {'ran': [], 'success': []}


def setup_data(elo=0.1, ehi=10.0, ebin=0.01):
    """Return a data set.

    Parameters
    ----------
    elo, ehi : number, optional
        The start and end energy of the grid, in keV.
    ebin : number, optional
        The bin width, in keV.

    Returns
    -------
    data : Data1DInt
        The data object. The Y values are not expected to be used,
        so are set to 1.

    """

    if elo >= ehi:
        raise ValueError("elo >= ehi")
    if elo <= 0:
        raise ValueError("elo <= 0")
    if ebin <= 0:
        raise ValueError("ebin <= 0")

    x = np.arange(elo, ehi + ebin, ebin)
    if x.size < 2:
        raise ValueError("elo, ehi, ebin not sensible")

    y = np.ones(x.size - 1)
    return Data1DInt('dummy', x[:-1], x[1:], y)


def _check_pars(label, mdl, parvals):
    """Check that we have the expected parameters.

    Parameters
    ----------
    label : str
        The label to use in the assertions
    mdl
        The model object. It must have a pars attribute.
    parvals : sequence of tuples
        Each entry gives the parameter name, value, frozen flag,
        and units field.
    """

    nexp = len(parvals)
    ngot = len(mdl.pars)
    assert nexp == ngot, '{}: number of parameters'.format(label)

    for i, vals in enumerate(parvals):

        par = mdl.pars[i]
        plbl = '{} param {}: '.format(label, i + 1)
        assert isinstance(par, Parameter), plbl + 'is a parameter'
        assert par.name == vals[0], plbl + 'name'
        assert par.val == vals[1], plbl + 'value'
        assert par.frozen == vals[2], plbl + 'frozen'
        assert par.units == vals[3], plbl + 'units'


def test_cflux_settings():
    """Do the expected things happen when a model is calculated?"""

    counter['ran'].append('test_cflux_settings')

    kern = XScflux('cflux')
    assert isinstance(kern, XSConvolutionKernel), \
        "cflux creates XSConvolutionKernel"

    cfluxpars = [('Emin', 0.5, True, 'keV'),
                 ('Emax', 10.0, True, 'keV'),
                 ('lg10Flux', -12, False, 'cgs')]
    _check_pars('cflux', kern, cfluxpars)

    mdl = kern(PowLaw1D('pl'))
    assert isinstance(mdl, XSConvolutionModel), \
        "cflux(mdl) creates XSConvolutionModel"

    plpars = [('gamma', 1.0, False, ''),
              ('ref', 1.0, True, ''),
              ('ampl', 1.0, False, '')]
    _check_pars('model', mdl, cfluxpars + plpars)

    counter['success'].append('test_cflux_settings')


def _test_cflux_calc(mdl, slope, ampl):
    """Test the CFLUX convolution model calculation.

    This is a test of the convolution interface, as the results of
    the convolution can be easily checked.

    Parameters
    ----------
    mdl
        The unconvolved model. It is assumed to be a power law (so
        either a XSpowerlaw or PowLaw1D instance).
    slope, ampl : number
        The slope (gamma or PhoIndex) and amplitude
        (ampl or norm) of the power law.

    See Also
    --------
    test_cflux_calc_sherpa, test_cflux_calc_xspec

    """

    d = setup_data()

    kern = XScflux('cflux')

    mdl_unconvolved = mdl
    mdl_convolved = kern(mdl)

    # As it's just a power law can evaluate analytically
    #
    pterm = 1.0 - slope
    emin = d.xlo[0]
    emax = d.xhi[-1]
    counts_expected = ampl * (emax**pterm - emin**pterm) / \
        pterm

    # Could evaluate the model directly, but check that it's working
    # with the Sherpa setup. It is not clear that going through
    # the eval_model method really buys us much testing since the
    # main check we would really want to do is with the DataPHA
    # class, but that requires a lot of set up; the idea is that
    # the interface is abstract enough that going through
    # Data1DInt's eval_model API is sufficient.
    #
    y_unconvolved = d.eval_model(mdl_unconvolved)
    nbins_unconvolved = y_unconvolved.size
    assert nbins_unconvolved == d.xlo.size, \
        'unconvolved model has correct # bins'

    counts_unconvolved = y_unconvolved.sum()

    # This is mainly a sanity check of everything, as it is not
    # directly related to the convolution model. The counts_expected
    # term is > 0.01 with the chosen settings, so 1e-15
    # is a hand-wavy term to say "essentially zero". It may need
    # tweaking depending on platform/setup.
    #
    assert np.abs(counts_expected - counts_unconvolved) < 1e-15, \
        'can integrate a power law'

    # How to verify the convolution model? Well, one way is to
    # give it a flux, get the model values, and then check that
    # these values are very close to the expected values for
    # that flux.
    #
    kern.emin = 0.5
    kern.emax = 7.0

    desired_flux = 3.2e-14
    kern.lg10flux = np.log10(desired_flux)

    y_convolved = d.eval_model(mdl_convolved)
    nbins_convolved = y_convolved.size
    assert nbins_convolved == d.xlo.size, \
        'convolved model has correct # bins'

    # The model evaluated by mdl_convolved should have a
    # log_10(flux), over the kern.Emin to kern.Emax energy range,
    # of kern.lg10Flux, when the flux is in erg/cm^2/s (assuming
    # the model it is convolving has units of photon/cm^2/s).
    #
    # d.xlo and d.xhi are in keV, so need to convert them to
    # erg.
    #
    # Use 1 keV = 1.60218e-9 erg for the conversion, which limits
    # the accuracy (in part because I don't know how this compares
    # to the value that XSPEC uses, which could depend on the
    # version of XSPEC).
    #
    econv = 1.60218e-9
    emid = econv * (d.xlo + d.xhi) / 2.0

    y_signal = emid * y_convolved

    # Do not bother with trying to correct for any partially-filled
    # bins at the end of this range (there shouldn't be any).
    #
    idx = np.where((d.xlo >= kern.emin.val) &
                   (d.xhi <= kern.emax.val))
    flux = y_signal[idx].sum()

    # Initial tests had desired_flux = 3.2e-14 and the difference
    # ~ 1.6e-16. This has been used to determine the tolerance.
    # Note that 2e-16/3.2e-14 ~ 0.006 ie ~ 0.6%
    #
    assert np.abs(flux - desired_flux) < 2e-16, \
        'flux is not as expected'

    # The cflux model should handle any change in the model amplitude
    # (I believe; as there's no one definition of what the model
    # amplitude means in XSPEC). So, increasing the amplitude - assumed
    # to the last parameter of the input model - should result in
    # the same flux values. The unconvolved model is checked to make
    # sure it does scale (as a sanity check).
    #
    rescale = 1000.0
    mdl.pars[-1].val *= rescale
    y_unconvolved_rescaled = d.eval_model(mdl_unconvolved)
    y_convolved_rescaled = d.eval_model(mdl_convolved)

    assert_allclose(y_unconvolved, y_unconvolved_rescaled / rescale,
                    atol=0, rtol=1e-7)
    assert_allclose(y_convolved, y_convolved_rescaled,
                    atol=0, rtol=1e-7)


def test_cflux_calc_xspec():
    """Test the CFLUX convolution model calculations (XSPEC model)

    This is a test of the convolution interface, as the results of
    the convolution can be easily checked. The model being convolved
    is an XSPEC model.

    See Also
    --------
    test_cflux_calc_sherpa

    """

    counter['ran'].append('test_cflux_calc_xspec')

    mdl = XSpowerlaw('xspec')
    mdl.phoindex = 1.7
    mdl.norm = 0.025
    _test_cflux_calc(mdl, mdl.phoindex.val, mdl.norm.val)

    counter['success'].append('test_cflux_calc_xspec')


def test_cflux_calc_sherpa():
    """Test the CFLUX convolution model calculations (sherpa model)

    This is a test of the convolution interface, as the results of
    the convolution can be easily checked. The model being convolved
    is a Sherpa model.

    See Also
    --------
    test_cflux_calc_xspec

    """

    counter['ran'].append('test_cflux_calc_sherpa')

    mdl = PowLaw1D('sherpa')
    mdl.gamma = 1.7
    mdl.ampl = 0.025
    _test_cflux_calc(mdl, mdl.gamma.val, mdl.ampl.val)

    counter['success'].append('test_cflux_calc_sherpa')


def test_cflux_nbins():
    """Check that the number of bins created by cflux is correct.

    The test_cflux_calc_xxx routines do include a test of the number
    of bins, but that is just for a Data1DInt dataset, so the model
    only ever gets called with explicit lo and hi edges. This test
    calls the model directly to check both 1 and 2 argument variants.

    Notes
    -----
    There's no check of a non-contiguous grid.
    """

    counter['ran'].append('test_cflux_nbins')

    spl = PowLaw1D('sherpa')
    xpl = XSpowerlaw('xspec')

    spl.gamma = 0.7
    xpl.phoindex = 0.7

    egrid = np.arange(0.1, 2, 0.01)
    elo = egrid[:-1]
    ehi = egrid[1:]

    nbins = elo.size

    def check_bins(lbl, mdl):
        y1 = mdl(egrid)
        y2 = mdl(elo, ehi)

        assert y1.size == nbins + 1, '{}: egrid'.format(lbl)
        assert y2.size == nbins, '{}: elo/ehi'.format(lbl)

    # verify assumptions
    #
    check_bins('Sherpa model', spl)
    check_bins('XSPEC model', xpl)

    # Now try the convolved versions
    #
    cflux = XScflux("conv")
    check_bins('Convolved Sherpa', cflux(spl))
    check_bins('Convolved XSPEC', cflux(xpl))

    counter['success'].append('test_cflux_nbins')


def test_calc_xspec_regrid():
    """Test the CFLUX convolution model calculations (XSPEC model)

    Can we regrid the model and get a similar result to the
    direct version? This uses zashift but with 0 redshift.

    See Also
    --------
    test_calc_sherpa_regrid

    """

    counter['ran'].append('test_calc_xspec_regrid')

    mdl = XSpowerlaw('xspec')
    mdl.phoindex = 1.7
    mdl.norm = 0.025

    # rather than use the 'cflux' convolution model, try
    # the redshift model but with 0 redshift.
    #
    kern = XSzashift('zshift')
    kern.redshift = 0
    mdl_convolved = kern(mdl)

    d = setup_data(elo=0.2, ehi=5, ebin=0.01)

    dr = np.arange(0.1, 7, 0.005)
    mdl_regrid = mdl_convolved.regrid(dr[:-1], dr[1:])

    yconvolved = d.eval_model(mdl_convolved)
    yregrid = d.eval_model(mdl_regrid)

    # Do a per-pixel comparison (this will automatically catch any
    # difference in the output sizes).
    #
    ydiff = np.abs(yconvolved - yregrid)
    mdiff = ydiff.max()
    rdiff = ydiff / yconvolved

    # in testing see the max difference being ~ 3e-17
    assert mdiff < 1e-15, \
        'can rebin an XSPEC powerlaw: max diff={}'.format(mdiff)

    counter['success'].append('test_calc_xspec_regrid')


def test_calc_sherpa_regrid():
    """Test the CFLUX convolution model calculations (Sherpa model)

    Can we redshift a sherpa model and get the expected
    result, with a regrid applied? In this case a feature
    is added outside the default energy range, but in the
    regridded range, to check things are working.

    See Also
    --------
    test_calc_xspec_regrid

    """

    counter['ran'].append('test_calc_sherpa_regrid')

    mdl = Box1D('box')
    mdl.xlow = 4
    mdl.xhi = 12
    # why is the box amplitude restricted like this?
    mdl.ampl.max = 2
    mdl.ampl = 2

    kern = XSzashift('zshift')
    kern.redshift = 1.0
    mdl_convolved = kern(mdl)

    d = setup_data(elo=0.1, ehi=10, ebin=0.01)
    dr = setup_data(elo=0.1, ehi=13, ebin=0.005)

    mdl_regrid = mdl_convolved.regrid(dr.xlo, dr.xhi)

    yconvolved = d.eval_model(mdl_convolved)
    yregrid = d.eval_model(mdl_regrid)

    # We expect values < 2 keV to be 0
    #   yconvolved:  > 2 keV to < 5 keV to be 0.02 (ampl / bin width)
    #   yregrid:     > 2 keV to < 6 keV to be 0.02
    # above this to be 0, with some fun at the edges.
    #

    ehi = d.xhi

    idx = np.where(ehi < 2)
    ymax = np.abs(yconvolved[idx]).max()
    assert ymax == 0.0, 'yconvolved < 2 keV: max={}'.format(ymax)

    idx = np.where((ehi >= 2) & (ehi < 5))
    ymax = np.abs(yconvolved[idx] - 0.02).max()
    assert ymax < 1e-14, 'yconvolved: 2-5 keV max={}'.format(ymax)

    idx = np.where(ehi >= 5)
    ymax = np.abs(yconvolved[idx]).max()
    assert ymax == 0.0, 'yconvolved: > 5 keV max={}'.format(ymax)


    # expect last bin to be ~ 0 but preceeding ones to be zero
    idx = np.where(ehi < 2)
    ymax = np.abs(yregrid[idx][:-1]).max()
    assert ymax == 0, 'yregrid < 2 keV: max={}'.format(ymax)

    ymax = np.abs(yregrid[idx])[-1]
    assert ymax < 1e-14, 'yregrid < 2 keV: max={}'.format(ymax)

    idx = np.where((ehi >= 2) & (ehi < 6))
    ymax = np.abs(yregrid[idx] - 0.02).max()
    assert ymax < 2e-14, 'yregrid: 2-6 keV {}'.format(ymax)

    # expect first bin to be ~ 0 but following ones to be zero
    idx = np.where(ehi >= 6)
    ymax = np.abs(yregrid[idx])[0]
    assert ymax < 2e-14, 'yregrid: > 6 keV max={}'.format(ymax)

    ymax = np.abs(yregrid[idx][1:]).max()
    assert ymax == 0.0, 'yregrid: > 6 keV max={}'.format(ymax)

    counter['success'].append('test_calc_sherpa_regrid')


if __name__ == "__main__":

    import sys

    test_cflux_settings()
    test_cflux_calc_xspec()
    test_cflux_calc_sherpa()
    test_cflux_nbins()
    test_calc_xspec_regrid()
    test_calc_sherpa_regrid()

    # This is all a bit silly since if a test fails it is obvious
    # with the current set up; this is just to check I have
    # changed counter correctly in the tests.
    #
    ran = set(counter['ran'])
    success = set(counter['success'])
    failed = False
    if len(ran) != 6:
        sys.stderr.write("ERROR: did not run 5 tests!\n")
        failed = True

    if success != ran:
        sys.stderr.write("ERROR: at least one test failed\n")
        failed = True

    if failed:
        sys.exit(1)
