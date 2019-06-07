#
#  Copyright (C) 2009, 2010, 2015, 2019
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

"""
Routines to calculate the radial profile of a 2D image and fit,
along with the residuals.
"""

#
# Perhaps there should be a routine to calculate the indexes
# for the radial bins, and then one to perform the actual
# "binning"?
#

import sherpa.astro.ui as ui

from sherpa.utils.err import ArgumentErr

import sherpa.astro.data

import numpy as np

from .annotations import add_latex_symbol, add_subscript


__all__ = ("calc_profile", )


def _get_parameter_value(name, val):
    """Return a numeric value given one of:
       a number
       a model parameter (something with a .val field)
       a string nameing a model parameter

    The name field is used in any error message, val is the
    value to decode.

    Raises an ValueError if unable to retrieve a number.

    If val is not a string or without a .val field then we just
    return val. We do not throw an error.
    """

    # Could try isinstance(val, sherpa.models.parameter.Parameter)
    # here instead, but stick with hasattr for now
    #
    if hasattr(val, "val"):
        return val.val
    elif isinstance(val, str):
        try:
            return ui.get_par(val).val
        except ArgumentErr:
            raise ValueError(
                "Name of {0} argument does not appear to be a model parameter: '{1}'".format(name, val)
                )
    else:
        return val


def _find_model(id):
    """Return the model expression for the given dataset id. It tries
    to handle models that have been given via set_full_model or
    set_source/model.

    At the moment we do not return information on whether this
    is a source, model or full_model expression.

    Raises an error if there is no model expression.
    """

    (mdl, is_src) = ui._session._get_model_status(id)
    return mdl


def _find_model_info(model_expr):
    """
    (xpos, ypos, ellip, theta) = _find_model_info (expression)

    Returns the xpos, ypos, ellip, and theta values from the given
    expression (where expression should be the return value from
    get_model or _find_model), otherwise raise an ValueError.
    """

    mname = model_expr.name

    # Find the fields
    #
    xpos = None
    ypos = None
    ellip = None
    theta = None
    for par in model_expr.pars:
        if par.name == "xpos":
            if xpos is not None:
                raise ValueError("Multiple xpos parameters in source expression:\n\t{0}".format(mname))

            xpos = par.val.copy()

        if par.name == "ypos":
            if ypos is not None:
                raise ValueError("Multiple ypos parameters in source expression:\n\t{0}".format(mname))

            ypos = par.val.copy()

        if par.name == "ellip":
            if ellip is not None:
                raise ValueError("Multiple ellip parameters in source expression:\n\t{0}".format(mname))

            ellip = par.val.copy()

        if par.name == "theta":
            if theta is not None:
                raise ValueError("Multiple theta parameters in source expression:\n\t{0}".format(mname))

            theta = par.val.copy()

    return (xpos, ypos, ellip, theta)


def _get_position_from_model(name):
    """Returns the xpos, ypos, ellip, and theta values for the
    given model, where name is either
       a model
       a string nameing a model

    Raises an ValueError if unable to retrieve a number.
    """

    # Could try isinstance(val, sherpa.models.model.Model)
    # here instead, but stick with hasattr for now
    #
    if hasattr(name, "xpos") and hasattr(name, "ypos") and \
       hasattr(name, "ellip") and hasattr(name, "theta"):
        return (name.xpos.val, name.ypos.val, name.ellip.val, name.theta.val)

    if isinstance(name, str):
        if name not in ui.list_model_components():
            raise ValueError(
                "Name of model argument does not appear to be a model: '{0}'".format(name)
                )

        xpos = _get_parameter_value("xpos", "{0}.xpos".format(name))
        ypos = _get_parameter_value("ypos", "{0}.ypos".format(name))
        ellip = _get_parameter_value("xpos", "{0}.ellip".format(name))
        theta = _get_parameter_value("ypos", "{0}.theta".format(name))
        return (xpos, ypos, ellip, theta)

    raise ValueError("Unrecognized argument to _get_position_from_model: '{0}'".format(str(name)))


def _process_profile_details(id, xpos, ypos, ellip, theta, model):
    """
    (xpos, ypos, ellip, theta) = _process_profile_details(xpos, ypos,
                                                          ellip, theta, model)

    Find the center and ellipticity/PA to use.
    We use the individual values in preference to the
    given model, in preference to guessing from the
    model expression.
    """

    assert model is not None, "_process_profile_details sent model=None"

    if xpos is not None:
        xpos = _get_parameter_value("xpos", xpos)
    if ypos is not None:
        ypos = _get_parameter_value("ypos", ypos)

    if ellip is not None:
        ellip = _get_parameter_value("ellip", ellip)
    if theta is not None:
        theta = _get_parameter_value("theta", theta)

    # If we are missing some data then we need to extract the missing
    # values from the model expression.
    #
    if None in [xpos, ypos, ellip, theta]:

        (xpos2, ypos2, ellip2, theta2) = _find_model_info(model)

        if xpos is None:
            xpos = xpos2
        if ypos is None:
            ypos = ypos2
        if ellip is None:
            ellip = ellip2
        if theta is None:
            theta = theta2

        mname = model.name
        if xpos is None:
            raise ValueError("Unable to find the xpos value in the expression:\n\t{0}".format(mname))

        if ypos is None:
            raise ValueError("Unable to find the ypos value in the expression:\n\t{0}".format(mname))

        if ellip is None:
            ellip = 0.0

        if theta is None:
            theta = 0.0

    return (xpos, ypos, ellip, theta)


def _calc_pixel_size(x, y):
    """
    Return the pixel size of the data. If the pixels are not
    square then use the smaller of the two sides. Also returns
    the area.

    We assume the x and y arrays are ordered as the
    get_data().x0/x1 arrays are ordered.
    """

    nx = y[np.where(y == y[0])].size
    ny = x[np.where(x == x[0])].size

    dx = (x[-1] - x[0]) / (nx - 1.0)
    dy = (y[-1] - y[0]) / (ny - 1.0)
    area = dx * dy

    if dx > dy:
        return (dy, area)
    else:
        return (dx, area)


def _normalize_pixel_orig(x, dx, flag):
    """
    Given a value (x) and a pixel size (dx), determine
    the edge of the pixel that contains this value. If
    flag is False then we want the lower-edge of the
    pixel, otherwise the upper-edge.

    We assume that x >= 0.
    """

    xp = int(x * 1.0 / dx)
    if flag:
        return dx * (xp + 1.0)
    else:
        return dx * xp * 1.0


def _normalize_pixel(x, dx, flag):
    """
    Given a value (x) and a pixel size (dx), determine
    the edge of the pixel that contains this value. If
    flag is False then we want the lower-edge of the
    pixel, otherwise the upper-edge.

    We assume that x >= 0.
    """

    assert x >= 0, "invalid x argument: x={0}".format(x)

    # This is a very-hacky way to try and avoid some rounding issues
    #
    if dx < 1.0:
        norm = 10 ** np.ceil(abs(np.log10(dx)))
    else:
        norm = 1.0

    x1 = x * norm
    dx1 = dx * norm
    xp = int(x1 / dx1)

    if flag:
        return dx * (xp + 1.0)
    else:
        return dx * xp * 1.0


def _process_rstep_array(rstep, rmin, rmax):
    """
    Convert an rstep array, in the form
        [delta1, r1, delta2, r2, ..., deltan]
    into
        [(rmin, ra, deltaa), ..., (rq,rmax,deltaq)]
    removing all elements outside the range rmin to rmax

    """

    assert len(rstep) % 2 == 1, \
        "rstep array does not contain an odd number of elements"

    # Copy the rstep array
    r = rstep[:]

    # Convert into a set of (r1,r2,delta) triples
    # and filter by the user's rmin/rmax values.
    # This is an ugly, but simple-ish way
    #
    istart = 1
    while True:
        if istart >= len(r):
            break
        if r[istart] > rmin:
            break
        istart += 2

    iend = istart
    while True:
        if iend == len(r):
            iend = len(r) - 1
            break
        if r[iend] >= rmax:
            r[iend] = rmax
            break
        iend += 2

    r = r[istart - 1:iend + 1]

    # Ugh, need to deal with python containers or numpy arrays
    # which makes statements like
    #      rvals = ([rmin] + r + [rmax])[0::2]
    # dangerous. So convert to numpy and do the concatenation
    # there.
    #
    rvals = np.concatenate(([rmin], r, [rmax]))[0::2]
    return [x for x in zip(rvals[:-1], rvals[1:], r[0::2])]


def _calc_bins(rmin, rmax, rstep):
    """
    Returns an array of bin values for
    rmin to rmax, with a step size of rstep
    (a scalar).

    The last element of the bins is guaranteed
    to be >= rmax.
    """

    # should convert from S-Lang code into using np.arange
    # but not convinced I have the exact same behaviour
    #
    # bins = np.range(rmin, rmax, rstep)

    nbins = int(np.ceil((rmax - rmin) * 1.0 / rstep))
    assert nbins > 0, \
        "Error calculating the number of bins: rmin={0} rmax={1} rstep={2}".format(rmin, rmax, rstep)

    bins = np.arange(0, nbins + 1, 1) * rstep + rmin

    # Try and deal with potential rounding errors. The choice of
    # rstep/1e5 as the tolerance is rather arbitrary
    #
    delta = np.abs(bins[-2] - rmax)
    if delta < 1.0e-5 * rstep:
        bins = bins[:-1]

    assert len(bins) > 1, "Error calculating bins: bins={0}".format(bins)
    return bins


def _calc_bin_edges(rmin, rmax, rstep):
    """
    (lo, hi) = _calc_bin_edges (rmin, rmax, rstep)

    Return the min and max values of each radial bin
    for bins spanning rmin to rmax with a step size of
    rstep.

    Note that max(hi) >= rmax, so that we do not
    force the last bin to fit into rmax. Perhaps we
    should.

    rstep can be an array, in which case it is taken to be
      [delta1, r1, delta2, r2, ..., delta(n-1), r(n-1), deltan]
    so that
      delta = delta1 for r <~ r1
              delta2 for r1 <~ r <~ r2
              ...
              delta(n-1) for r(n-2) <~ r <~ r(n-1)
              deltan for r >~ r(n-1)

    The approximate values are included since we can guarantee that
    the bin edges will match up with the rn values.

    I should probably change this so that the input is an
    array of (rmin,rmax,step) values for all cases.
    """

    # We assume that rstep is correct
    if hasattr(rstep, "__iter__"):

        bins_lo = None
        bins_hi = None
        rlast = None
        for (r1, r2, rs) in rstep:

            if bins_lo is None:
                bins = _calc_bins(r1, r2, rs)
                bins_lo = bins[:-1]
                bins_hi = bins[1:]
            else:
                bins = _calc_bins(rlast, r2, rs)
                bins_lo = np.append(bins_lo, bins[:-1])
                bins_hi = np.append(bins_hi, bins[1:])

            rlast = bins_hi[-1]

    else:
        bins = _calc_bins(rmin, rmax, rstep)
        bins_lo = bins[:-1]
        bins_hi = bins[1:]

    return (bins_lo, bins_hi)


def _process_bin_limits(rmin, rmax, drmin, drmax):
    "Want radial range to use?"

    if rmin is None:
        rmin = drmin
    elif rmin < 0.0:
        raise ValueError("rmin must be >= 0.0, sent {0}".format(rmin))
    elif rmin > drmax:
        raise ValueError("The maximum radius of the data is {0} which is <= rmin ({1})".format(drmax, rmin))

    if rmax is None:
        rmax = drmax
    elif rmax <= rmin:
        raise ValueError("rmax must be > rmin, have rmin={0} rmax={1}".format(rmin, rmax))

    return (rmin, rmax)


def _process_bin_step(rstep, rmin, rmax):
    "Want step size(s) to use?"

    if rstep is None:
        raise ValueError("At present rstep can not be left at None")

    elif hasattr(rstep, "__iter__"):
        # May not be the best check
        if len(rstep) % 2 == 0:
            raise ValueError("rstep must contain an odd number of elements, but sent {0}".format(len(rstep)))

        if False in [rs > 0 for rs in rstep]:
            raise ValueError("rstep elements must all be > 0")

        rstep = _process_rstep_array(rstep, rmin, rmax)

    elif rstep <= 0.0:
        raise ValueError("rstep must be > 0.0, sent {0}".format(rstep))

    elif rstep >= (rmax - rmin):
        raise ValueError("The radial range (rmin={0} rmax={1}) is <= rstep ({2})".format(rmin, rmax, rstep))

    return rstep


def _get_bin_edges(rmin, rmax, rstep, drmin, drmax):
    """
    (lo, hi) = _get_bin_edges (rmin, rmax, rstep, drmin, drmax)

    Return the min and max values of each radial bin
    given the users rmin/rmax/rstep inputs and the min/max
    radii for the data (drmin/drmax), which are assumed to have been
    normalized to the pixel size (but needn't be).

    rstep can be None, a scalar, or an array of values of the form
      [delta_1, r_1, ..., delta_(n-1), r_(n-1), delta_n]

    (ie an odd-number of elements) which means to use a step size of
      delta_1 for r <~ r_1,
      delta_2 for r_1 <~ r <~ e_2,
      delta_n for r >~ r_(n-1)

    """

    (r1, r2) = _process_bin_limits(rmin, rmax, drmin, drmax)
    dr = _process_bin_step(rstep, r1, r2)
    return _calc_bin_edges(r1, r2, dr)


def _calculate_distances2(data, xpos, ypos, ellip=None, theta=None):
    """
    Returns dr2.

    dr2 is the square of the distance of each pixel from the given position
    (xpos, ypos). If ellip and theta are not None then they are used to create
    elliptical "distances".
    """

    # Calculate the separation of each pixel from the center.
    # Based on the description from 'ahelp beta2d'
    #
    dx = data.x0 - xpos
    dy = data.x1 - ypos

    if ellip is None or theta is None:
        dr2 = dx * dx + dy * dy
    else:
        ct = np.cos(theta)
        st = np.sin(theta)
        x_new = dx * ct + dy * st
        y_new = -dx * st + dy * ct
        efact = (1.0 - ellip) * (1.0 - ellip)
        dr2 = (x_new * x_new * efact + y_new * y_new) / efact

    return dr2


def _calc_error(n):
    """Return the error on n counts using Gehrel's approximation.

    We assume that n >= 0.
    """
    return (1.0 + np.sqrt(n + 0.75))


def _apply_grouping(prof, grouping, last=False):
    """Apply the user's grouping scheme to the data.

    If last=True then the last bin is included, whether it meets
    the criterion or not. When False, the returned arrays are
    guaranteed to all meet the criterion.

    If no bins match then an ValueError is thrown.

    Bin values are expected to be >= 0.

    The input dictionary can contain keys other than
      data, area, rlo, rhi, model, resid
    but the output content of these keys is not guaranteed to
    be in any way useful.
    """

    (gtype, gval) = grouping
    if gtype == "counts":
        def comparison_fn(s):
            return s >= gval
    elif gtype == "snr":
        def comparison_fn(s):
            return (s / _calc_error(s)) >= gval
    else:
        raise ValueError("Unrecognized grouping type '{0}' (value={1})".format(gtype, gval))

    data = prof["data"]

    out = {}
    for k in prof:
        out[k] = np.zeros_like(prof[k])

    sum_names = ["data", "area"]
    if "model" in out:
        sum_names.extend(["model", "resid"])

    group_idx = 0
    for i in range(data.size):

        ingrp = True
        for n in sum_names:
            out[n][group_idx] += prof[n][i]
        out["rhi"][group_idx] = prof["rhi"][i]

        if comparison_fn(out["data"][group_idx]):
            ingrp = False
            group_idx += 1
            if i < (data.size - 1):
                out["rlo"][group_idx] = prof["rlo"][i + 1]

    if last and ingrp:
        valid_size = group_idx + 1
    else:
        valid_size = group_idx

    if valid_size == 0:
        raise ValueError("Unable to find any radial profile data within the min/max limits after grouping.")

    for k in out:
        out[k] = np.resize(out[k], valid_size)

    return out


def _calc_radial_profile(data, model, dr2, bins_lo, bins_hi, pixarea,
                         grouptype=None):
    """Returns a structure containing the data need to plot up the radial profiles.
    model may be None.
    If grouptype is not None then it should be a tuple
        (method name, parameter value)
    where the supported values are given in calc_profile

    We assume that there has been no background subtraction
    """

    # We use the mask array from the data object to filter all
    # the data.
    #
    # QUS: what happens if the original data file contains masked pixels -
    # is this included in the mask? It definitely isn't for integer images
    # with NULL keyword values or with a CIAO data subspace region filter.
    # We add in a isfinite check to modify the data.mask file as a precaution
    # but it's not ideal.
    #
    zdata = data.y * 1.0
    # good_idx = data.mask
    good_idx = data.mask & np.isfinite(data.y)

    if model is None:
        dr2 = dr2[good_idx]
        zdata = zdata[good_idx]

    else:

        dr2 = dr2[good_idx]
        zdata = zdata[good_idx]
        zmodel = (model.y * 1.0).flatten()[good_idx]

    good_idx = None

    rlo2 = bins_lo * bins_lo
    rhi2 = bins_hi * bins_hi

    nbins = bins_lo.size
    hist_data = np.zeros(nbins)
    hist_area = np.zeros(nbins)
    flag = np.zeros(nbins, dtype=bool)
    if model is not None:
        hist_model = np.zeros(nbins)

    # Could try argsort on dr2 to sort the array, then
    # instead of a where(dr2>=lo & dr2<hi) statement
    # we could loop through the sorted array.
    # It is not clear that it would be faster, and
    # it would definitely be more complex.
    #
    for i in range(0, nbins, 1):

        # Find the pixels that are within this annulus
        idx, = np.where((dr2 >= rlo2[i]) & (dr2 < rhi2[i]))
        npix = idx.size

        if npix != 0:
            zs = np.sum(zdata[idx])

            hist_data[i] = zs * 1.0
            hist_area[i] = npix * pixarea
            flag[i] = True

            if model is not None:
                hist_model[i] = np.sum(zmodel[idx]) * 1.0

    # Remove bins for which there are no valid pixels. Note that we do this
    # before grouping (although the order doesn't actually matter to the end
    # result at present)
    #
    idx, = np.where(flag)
    if idx.size == 0:
        raise ValueError("Unable to find any radial profile data within the min/max limits.")

    # For now return a dictionary
    #
    out = {}
    out["rlo"] = bins_lo[idx]
    out["rhi"] = bins_hi[idx]
    out["data"] = hist_data[idx]
    out["area"] = hist_area[idx]

    if model is not None:
        out["model"] = hist_model[idx]
        out["resid"] = out["data"] - out["model"]

    # Apply grouping, if necessary
    #
    if grouptype is not None:
        out = _apply_grouping(out, grouptype)

    # Use the Gehrels approximation, but perhaps should just
    # use Gaussian errors. Or allow a routine to be specified
    # so that users can use whatever they want.
    #
    out["err"] = _calc_error(out["data"])
    if model is not None:
        out["delchi"] = out["resid"] / out["err"]

    # normalize by the area
    #
    for n in ["data", "err", "model"]:
        if n in out:
            out[n] /= out["area"]

    return out


def _set_subscript(term, subscript, symval):
    """Return a string showing the subscripted value setting.

    Parameters
    ----------
    term, subscript: str
        The value being subscripted and the subscript (assumed to need
        no LaTeX for either).
    symval : val
        The symbol value: something that can be converted to a string.

    Returns
    -------
    label : str
        Returns 'symname = symval' in a form suitable for the plotting
        backend (where symname is term + subscript).
    """

    return '{} = {}'.format(add_subscript(term, subscript), symval)


def _set_symbol(symname, symval):
    """Return a string showing the symbol setting.

    Parameters
    ----------
    symname: str
        The symbol name (e.g. '\theta')
    symval : val
        The symbol value: something that can be converted to a string.

    Returns
    -------
    label : str
        Returns 'symname = symval' in a form suitable for the plotting
        backend.
    """

    return '{} = {}'.format(add_latex_symbol(symname), symval)


def calc_profile(model_image_fn,
                 id=None,
                 rmin=None, rmax=None, rstep=None, rlo=None, rhi=None,
                 model=None, xpos=None, ypos=None, ellip=None, theta=None,
                 grouptype=None
                 ):
    """Calculate the data needed to create the desired radial or
    elliptical profile.

    model_image_fn should be None or one of get_source_image or
    get_model_image, depending on whether you want the source or model image to
    be used for calculating properties.

    If grouptype is not None then it should be a tuple
        (method name, parameter value)
    where the supported values are
        ("counts", minimum-counts-per-bin)
        ("snr", minimum-snr-per-bin)

    """

    # Throw an error if input is invalid.
    #
    if id is None:
        id = ui.get_default_id()

    data = ui.get_data(id)
    if not isinstance(data, sherpa.astro.data.DataIMG):
        raise TypeError("data set {0} does not contain 2-D data".format(id))

    # Access model information
    #
    if model is None:
        model = _find_model(id)

    # What profile parameters do we use?
    #
    (xpos, ypos, ellip, theta) = _process_profile_details(id, xpos, ypos,
                                                          ellip, theta, model)
    ellipflag = ellip > 0.0

    # Calculate the separation of each pixel from the center
    #
    if ellipflag:
        dr2 = _calculate_distances2(data, xpos, ypos, ellip=ellip, theta=theta)
    else:
        dr2 = _calculate_distances2(data, xpos, ypos)

    # Filter out "bad" points, but only for the evaluation of min/max.
    # - this could be doine in _calculate_distances2 as it would save some
    #   time, but would need to make sure the filtering was done the
    #   same as with the data/models
    #
    mask = data.mask
    if isinstance(mask, (bool, np.bool_)):
        if mask:
            dr2mask = dr2
        else:
            raise ValueError("All data appears to have been filtered out for dataset id={0}".format(id))

    else:
        if not np.any(mask):
            raise ValueError("All data appears to have been filtered out for dataset id={0}".format(id))

        dr2mask = dr2[mask]

    drmin = np.sqrt(dr2mask.min())
    drmax = np.sqrt(dr2mask.max())
    dr2mask = None

    (pixsize, pixarea) = _calc_pixel_size(data.x0, data.x1)
    drmin = _normalize_pixel(drmin, pixsize, False)
    drmax = _normalize_pixel(drmax, pixsize, True)

    # Calculate the binning (before grouping)
    #
    if rlo is not None:
        if (np.diff(rlo) <= 0).any():
            raise ValueError("rlo array must be in ascending order")
        if rhi is None:
            bins_lo = np.asarray(rlo[:-1])
            bins_hi = np.asarray(rlo[1:])
        else:
            if len(rlo) != len(rhi):
                raise ValueError(
                    "rlo and rhi arrays must have the same length: rlo has {0} and rhi has {1} elements".format(len(rlo), len(rhi))
                    )

            if not (np.diff(rhi) > 0).all():
                raise ValueError("rhi array must be in ascending order")

            bins_lo = np.asarray(rlo)
            bins_hi = np.asarray(rhi)
            if ((bins_hi - bins_lo) <= 0).any():
                raise ValueError("Have a rhi element <= the corresponding rlo element")
    else:
        if rstep is None:
            rstep = pixsize

        (bins_lo, bins_hi) = _get_bin_edges(rmin, rmax, rstep, drmin, drmax)

    if model_image_fn is None:
        mdata = None
    else:
        mdata = model_image_fn(id)

    rprof = _calc_radial_profile(data, mdata, dr2, bins_lo, bins_hi,
                                 pixarea, grouptype=grouptype)

    # Mixing presentational and data concerns here, which is not ideal
    #
    rprof["coord"] = ui.get_coord(id)
    rprof["id"] = id
    rprof["datafile"] = data.name

    if ellipflag:
        rprof["xlabel"] = "Major axis ({0} pixel)".format(rprof["coord"])
    else:
        rprof["xlabel"] = "Radius ({0} pixel)".format(rprof["coord"])

    rprof["xpos"] = xpos
    rprof["ypos"] = ypos
    rprof["labels"] = [_set_subscript('x', '0', xpos),
                       _set_subscript('y', '0', ypos)]

    if ellipflag:
        rprof["ellip"] = ellip
        rprof["theta"] = theta
        rprof['labels'].extend([_set_symbol(r'\epsilon', ellip),
                                _set_symbol(r'\theta', theta)])

    return rprof
