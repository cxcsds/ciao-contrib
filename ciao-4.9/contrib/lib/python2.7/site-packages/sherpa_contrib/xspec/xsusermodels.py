#
# Copyright (C) 2012, 2013, 2014, 2015, 2016
#           Smithsonian Astrophysical Observatory
#
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.
#

# Note:
#  Some of the code is based on the code in
#    src/pkg/sherpa/sherpa/sherpa/include/sherpa/astro/xspec_extension.hh
#  eg xspecmodelfct
#
# Ideally this would just use the same wrapper code as the Sherpa
# XSPEC module, but this is not possible as of CIAO 4.8
#

"""
Support for binding XSPEC user models to Python for use in
Sherpa. The models are assumed to have been created by the
convert_xspec_user_model script, but this module can also be
used with other models that follow the same interface.

This interface has seen limited testing, so please check the
documentation and then the CXC HelpDesk -
http://cxc.harvard.edu/helpdesk/ - if you have problems.

Note that the convolution interface has seen very limited testing,
so please take care when using it!

"""

import numpy as np

import sherpa.astro.xspec as xspec
import sherpa.models as models
import sherpa.utils as utils

from .xsmodels import XSConvolutionKernel

# c_ang * h_kev, so that E_kev = _hc / E_angstrom
_hc = 2.99792458e+18 * 6.6260693e-27 / 1.60217653e-9

__all__ = (
    'XSUserModel', 'XSAdditiveUserModel', 'XSMultiplicativeUserModel',
    'XSConvolutionUserKernel'
)


# In CIAO 4.8 the XSPEC interface was re-written and uses the same
# idea as used here for missing bins (although the algorithm is
# different).
#
def _find_missing_bins(xlo, xhi):
    """Return the indexes of bins for which xlo[i+1] != xhi[i], where
    xlo and xhi are assumed to be doubles, and the comparison uses the
    np.isclose algorithm with rtol=0 and atol=np.finfo(xlo.dtype).eps.

    There is no attempt to handle invalid numbers, e.g. NaN or Inf
    values in the input arrays.

    Parameters
    ----------
    xlo, xhi: array_like
        The bin edges. The arrays are assumed to be 1D, have the same
        length, be monotonic, and do not contain overlapping bins.

    Returns
    -------
    idx : array_like or None
        If there are no missing bins, None is returned, otherwise
        an array of integers
    """

    idx, = np.where(
        np.logical_not(
            np.isclose(xlo[1:], xhi[:-1],
                       rtol=0,
                       atol=np.finfo(xlo.dtype).eps
                       )
        )
    )

    # Should [] or None be returned?
    if len(idx) == 0:
        return None
    else:
        return idx


def _calc_ranges(nelem, midx):
    """For an array of nelem points - where nelem is the size of the
    elo/ehi arrays - and an array of "missing" bins or None - the
    output of _find_missing_bins, return an array listing the ranges
    to fill the output. Each element is

      (ia, ib)   - fill in with the elo bins
                   elo[ia] .. elo[ib]
      (ia, None) - fill in with ehi[ia]

    At present the return value is guaranteed to start with (ia,ib)
    and end with (ia,None).
    """

    nout = nelem - 1

    if midx is None:
        return [(0, nout), (nout, None)]

    out = []
    last = 0
    for i in midx:
        out.append((last, i))
        out.append((i, None))
        last = i + 1

    # TODO: may need to check here as should it be < nelem-1?
    if i < nelem:
        out.append((last, nout))

    out.append((nout, None))
    return out


def _remap_energy_grid(elo, ehi):
    """Return the XSPEC energy grid for use by XSPEC, given the
    input elo/ehi grid.

    elo and ehi are assumed to be 1D, contain the same number of
    elements, to have the same data type, to not have overlapping
    bins, and be in ascending order.

    The return is the pair

      (evals, idxs)

    where idxs is an array of bins in ebins that are to be excluded
    from the result (they indicate that bins had to be added to create
    a contiguous grid of evals), or None if there are none.

    evals has the type of elo.
    """

    # ideally this would be done for all bins
    assert elo[0] < ehi[0], "elo > ehi"
    assert elo[0] < elo[1], "elo not ascending"
    assert ehi[0] < ehi[1], "ehi not ascending"

    nbins = len(elo)
    midx = _find_missing_bins(elo, ehi)
    nout = nbins + 1
    if midx is not None:
        nout += len(midx)

    out = np.zeros(nout, dtype=elo.dtype)

    # Assume that calc_ranges always starts
    # with a (ia,ib!=None) pair, even if ia == ib.
    #
    step = 0
    oidx = []
    for (ia, ib) in _calc_ranges(nbins, midx):
        if ib is None:
            out[ia + step] = ehi[ia]
            oidx.append(ia + step)
        else:
            out[ia + step:ib + step + 1] = elo[ia:ib + 1]
            step += 1

    # drop the last bin from the "oidx" array as it's the last bin
    if len(oidx) < 2:
        return (out, None)
    else:
        return (out, oidx[:-1])


def _remove_extra_bins(ys, midx):
    """Return the array of bins with the "extra" bins, added by
    remap_energy_grid, removed.

    If midx is empty or None then the return value is the same as the
    input array, otherwise it's a copy (to ensure that it is
    contiguous in memory).

    The array ys must be a floating-point numpy array.
    """

    if midx is None or len(midx) == 0:
        return ys

    mask = np.zeros(ys.size, dtype=np.bool)
    mask[midx] = True
    return np.ma.masked_where(mask, ys, copy=True).compressed()


def _calc_xspec_grid(mname, args):
    """Given the arguments for a model, return the single, contiguous
    array required to evalute the model - in the form used by XSPEC -
    along with a flag indicating if the input was a single grid or
    separate elo/ehi arrays (the flag is True if elo and ehi were
    given) and the bins to exclude from the result (if any needed
    to be added, or None if none were added).
    """

    nargs = len(args)
    if nargs == 1:
        ear = np.asarray(args[0])
        if ear[0] > ear[-1]:
            ear = _hc / ear

        return (ear, False, None)

    elif nargs == 2:
        (xlo, xhi) = args
        xlo = np.asarray(xlo)
        xhi = np.asarray(xhi)

        # As we have low and high edges we need to deal
        # with the fact that there may be missing bins.
        # Both the low and high grids are converted
        # to keV from Angstrom if required; note that this
        # is wasteful, since only one element of the xhi
        # array really needs to be converted, but this
        # approach makes remap_energy_grid easier to
        # write.
        #
        if xlo[0] > xlo[-1]:
            (ear, eidx) = _remap_energy_grid(_hc / xhi, _hc / xlo)
        else:
            (ear, eidx) = _remap_energy_grid(xlo, xhi)

        return (ear, True, eidx)

    else:
        raise ValueError("Expected 2 or 3 arguments when evaluating {}, sent {}".format(mname, nargs + 1))


class XSUserModel(xspec.XSModel):
    """Indicates that the model is a compiled XSPEC user model. It
    deals with the different calling conventions created by the f2py
    approach to building the user models from the hand-crafted
    Python/C++ interface used in Sherpa:

    f2py creates an interface like

        output = func(egrid, pars)

    where egrid must be in keV whereas the XSPEC models in Sherpa
    itself are called with

        output = func(pars, egrid)
        output = func(pars, elo, ehi)

    and egrid or elo/ehi can be in keV or Angstroms.

    """

    @models.modelCacher1d
    def calc(self, *args, **kwargs):
        "Evaluate the model"
        pars = args[0]
        (ear, has_elo_ehi, extrabins) = _calc_xspec_grid(self.name,
                                                         args[1:])

        # The f2py interface is set up to not be sent
        # parameters if npars = 0.
        if len(pars) == 0:
            out = self._calc(ear)
        else:
            out = self._calc(ear, pars)

        if extrabins is not None:
            out = _remove_extra_bins(out, extrabins)

        if has_elo_ehi:
            return out
        else:
            return np.append(out, 0)


class XSAdditiveUserModel(XSUserModel):
    """Additive XSPEC user models that have been created using f2py.
    """

    def guess(self, dep, *args, **kwargs):
        if hasattr(self, 'norm'):
            norm = utils.guess_amplitude(dep, *args)
            utils.param_apply_limits(norm, self.norm, **kwargs)

    @models.modelCacher1d
    def calc(self, *args, **kwargs):
        "Evaluate the model"

        # Strip off the last parameter, as it is the
        # normalization parameter, call the model, then
        # apply the parameter to the return value.
        #
        pars = args[0]
        return pars[-1] * XSUserModel.calc(self, pars[:-1], *args[1:],
                                           **kwargs)


class XSMultiplicativeUserModel(XSUserModel):
    """Multiplicative XSPEC user models that have been
    created using f2py.
    """

    pass


# TODO: need to updaye to take advantage of the updates to handle
# XSPEC convolution models in CIAO 4.8 (or, rather, to use the
# same interface)
#
class XSConvolutionUserKernel(XSConvolutionKernel):
    """Support for XSPEC convolution user models, extending the
    support for the built-in versions since the interface is
    slightly different, due to how the user models are wrapped.
    """

    # Do not use this since it doesn't seem useful to introduce
    # a XSConvolutionUserModel class.
    #
    # def __call__(self, model):
    #     return XSConvolutionUserModel(model, self)

    def calc(self, pars, rhs, *args, **kwargs):
        """Convolve the model.

        Note that this method is not cached by
        sherpa.models.modelCacher1d at present.
        """

        npars = len(self.pars)
        lpars = pars[:npars]
        rpars = pars[npars:]

        (ear, has_elo_ehi, extrabins) = _calc_xspec_grid(self.name, args)

        # TODO: is it worth sending in ear rather than args to rhs()?
        fluxes = np.asarray(rhs(rpars, *args, **kwargs))
        if not has_elo_ehi:
            fluxes = fluxes[:-1]

        if npars == 0:
            out = self._calc(ear, fluxes)
        else:
            out = self._calc(ear, lpars, fluxes)

        if extrabins is not None:
            out = _remove_extra_bins(out, extrabins)

        # does the return value depend on the input type?
        if has_elo_ehi:
            return out
        else:
            return np.append(out, 0)

# Do we need the following, which is - at present - just a label that
# indicates this is from a user model rather than a built-in XSPEC model?
#
# class XSConvolutionUserModel(XSConvolutionModel):
#     """The XSConvolutionUserKernel instance creates these models for
#     use by Sherpa. Users should not be creating instances of this
#     class.
#
#     At present this is a wrapper around the XSPEC convolution model
#     just to indicate that this is a user-model component.
#     """
#
#     pass
