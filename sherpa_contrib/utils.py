#
#  Copyright (C) 2009, 2010, 2011, 2012, 2014, 2015, 2016, 2019
#            Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.
#

"""Utility routines for Sherpa.

Adjusting model parameters
--------------------------

    renorm()

Weighted instrument maps
------------------------

The following routines are useful for creating, and validating, the
weights file used by mkinstmap when making a weighted instrument map::

    get_instmap_weights()
    save_instmap_weights()
    plot_instmap_weights()
    estimate_weighted_expmap()

See the `Calculating Spectral Weights
<https://cxc.harvard.edu/ciao/threads/spectral_weights/>`_ thread
for more information.

"""

import os

import logging
import time

import numpy as np

from sherpa.astro import ui
from sherpa.astro.utils import _charge_e
import sherpa.utils as su

from sherpa.utils import print_fields
from sherpa.utils.err import ArgumentErr, ParameterErr

from sherpa.data import Data1DInt
from sherpa.astro.data import DataPHA
from sherpa.models.parameter import Parameter
from sherpa.plot import HistogramPlot

import pycrates

__all__ = ["renorm", "get_instmap_weights", "save_instmap_weights",
           "plot_instmap_weights", "estimate_weighted_expmap",
           "InstMapWeights", "InstMapWeights1DInt",
           "InstMapWeightsPHA"
           ]


# Should this use its own logger, derived from the Sherpa one?
logger = logging.getLogger("sherpa")
warn = logger.warn
error = logger.error
info = logger.info
del logger


def _is_boolean(val):
    "Returns True if val is a boolean."
    return isinstance(val, (bool, np.bool_))


class InstMapWeights:
    """Store the weights information needed by mkinstmap.

    It is up to the user to ensure that the model evaluates to
    photon/cm^2/s when integrated over a bin and that the bins are in
    keV.

    Attributes
    ----------
    id : int or string
        dataset id
    modelexpr: string
        The textual representation of the source model
    xmid : array of numbers
        The mid-point of each bin
    xlo : array of numbers
        The lower edge of ech bin
    xhi : array of numbers
        The upper edge of each bin
    weight : array of numbers
        The weight value for each bin
    fluxtype : 'photon' or 'erg'
        The instrument map has units of cm^2 count / <fluxtype>

    """

    _valid_fluxtypes = ["erg", "photon"]

    def __str__(self):
        def fmt(key, val):
            return "{0:10} = {1}".format(key, str(val))

        names = ["id", "modelexpr", "xlo", "xhi", "xmid", "weight",
                 "fluxtype"]
        vals = [getattr(self, n) for n in names]
        return print_fields(names, dict(zip(names, vals)))

    def __init__(self, id=None, fluxtype="photon"):
        "If id is None the default id will be used."

        if id is None:
            self.id = ui.get_default_id()
        else:
            self.id = id

        if fluxtype in self._valid_fluxtypes:
            self.fluxtype = fluxtype
        else:
            emsg = "fluxtype set to {} but must be one of: {}".format(
                fluxtype, " ".join(self._valid_fluxtypes))
            raise ValueError(emsg)

        # Set up the xlo/xhi/xmid arrays
        d = ui.get_data(self.id)
        self._calc_bins(d)
        self._apply_mask(d)

        # Important to use get_source and not get_model as we do not
        # want to apply any instrument model to the evaluation.
        #
        # Note that we do not hold onto the model expression object,
        # which is probably not an issue here.
        #
        mdl = ui.get_source(id)
        self.modelexpr = mdl.name

        # We do not use xlo/xhi but the _xlo/_xhi attributes which
        # contain an extra bin, in case of X-Spec models
        #
        src = mdl(self._xlo, self._xhi)[:-1]
        if np.any(src < 0.0):
            emsg = "There are negative values in your source " + \
                "model (id={0})!".format(self.id)
            raise RuntimeError(emsg)
        if np.all(src <= 0.0):
            emsg = "The source model for id={0} ".format(self.id) + \
                "evaluates to 0!"
            raise RuntimeError(emsg)

        # Conversion to a single datatype is a bit excessive here.
        #
        dtype = src.dtype

        if self.fluxtype == "erg":
            norm = _charge_e * np.sum(src * self.xmid)
        else:
            norm = np.sum(src)

        self.weight = src / norm

        self.weight = self.weight.astype(dtype)
        self.xlo = self.xlo.astype(dtype)
        self.xhi = self.xhi.astype(dtype)
        self.xmid = self.xmid.astype(dtype)

    def _calc_bins(self, data):
        "Calculate the bin edges"

        raise NotImplementedError("_calc_bins")

    def _apply_mask(self, data):
        "Apply any mask/filter to the xlo, xhi, xmid attributes"

        # Apply the filter if necessary.
        #
        m = data.mask
        if _is_boolean(m):
            if not m:
                raise RuntimeError("filter excludes all data")
        else:
            self.xlo = self.xlo[m]
            self.xhi = self.xhi[m]

        if len(self.xlo) == 0:
            raise RuntimeError("filter excludes all data")
        if len(self.xlo) == 1:
            raise RuntimeError("Only 1 data point in grid!")

        self.xmid = 0.5 * (self.xlo + self.xhi)

        # Add in an extra point in case dealing with X-Spec models
        # (where the last bin is used to define the bin edges, so
        # the model evaluates to 0 there).
        #
        # Errr, given that we explicitly give the low and high bin
        # edges to the models, I think this is actually unnecessary.
        #
        self._xlo = np.append(self.xlo,
                              [self.xhi[-1]])
        self._xhi = np.append(self.xhi,
                              [self.xhi[-1] + self.xlo[1] +
                               self.xlo[0]])

    def save(self, filename, clobber=True):
        """Save the weights to filename as an ASCII file, that
        can be used as the spectrumfile input for mkinstmap.

        The output file contains a header (comment character is
        '#') containing some metadata, and then two columns
        of data, the mid-point of the bin and the weight
        value for the bin. It is compatible with the CIAO
        ASCII file support (use with ``[opt colname=first]``).

        Parameters
        ----------
        filename : string
            The name of the output file.
        clobber : bool, optional
            Controls whether the output file is overwritten
            if it exists (``True``) or an IOError is raised.
        """

        # Used to use crates, but it does not write out keywords for
        # the TEXT/SIMPLE format, which we now want. So we now
        # manually create the output file.
        #
        # cr = make_table_crate(self.xmid, self.weight,
        #      colnames=["X", "WEIGHT"])
        # key = cr.get_key("CREATOR")
        # key.value = self.__class__.__name__
        # cr.write("{0}[opt kernel=text/simple]".format(filename),
        #          clobber=clobber)

        if not clobber and os.path.exists(filename):
            raise IOError("{} exists and ".format(filename) +
                          "clobber=False")

        elo = self.xlo[0]
        ehi = self.xhi[-1]

        stime = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

        # The column names are written first so that the file can
        # easily be used with CIAO tools (as they assume 'opt
        # colname=first' by default).
        #
        with open(filename, 'w') as fh:
            fh.write('#TEXT/SIMPLE\n')
            fh.write('# X WEIGHT\n')
            fh.write('#\n')
            fh.write("# DATE = {} / ".format(stime))
            fh.write("Date and time of file creation\n")
            fh.write("# MODELEXPR = {}\n".format(self.modelexpr))
            fh.write("# ENERG_LO = {} / ".format(elo))
            fh.write("[keV] Minimum energy\n")
            fh.write("# ENERG_HI = {} / ".format(ehi))
            fh.write("[keV] Maximum energy\n")
            fh.write('#\n')
            for (x, weight) in zip(self.xmid, self.weight):
                # As we expect weight values to be ~ 0.01 to 1
                # and the energy values to also be "nice" then
                # rely on the default formatting rules used by
                # Python.
                fh.write("{} {}\n".format(x, weight))

        info("Created: {}".format(filename))

    def plot(self, overplot=False, clearwindow=True, **kwargs):
        """Plot the weights values.

        Parameters
        ----------
        overplot : bool, optional
            If ``True`` then the data is added to the current plot,
            otherwise a new plot is created.
        clearwindow: bool, optional
            If ``True`` then clear out the current plot area of
            all existing plots. This is not used if ``overplot`` is
            set.
        **kwargs
            Assumed to be plot preferences that override the
            HistogramPlot.histo_plot preferences.

        Notes
        -----
        The data plot preferences are used to control the
        appearance of the plot: at present the following fields
        are used::

            ``xlog``
            ``ylog``
            ``color``

        Examples
        --------

        >>> hplot.plot()

        >>> hplot.plot(ylog=True, color='orange', linestyle='dotted')

        """

        # Create a Sherpa histogram plot. Unlike other plot
        # classes there is no prepare method, which means
        # that we do not have to create a temporary data object,
        # but do have to set the attributes manually.
        #
        # This assumes that it is okay to use a histogram-style
        # plot, since pre CIAO 4.2 there were numeric problems with
        # bin edges that made these plots look ugly, so a "curve"
        # was used.
        #
        # To avoid issues with numeric accuracy (I have seen a
        # case where the variation in the weight values was ~2e-16
        # and matplotlib showed this structure), convert the weights
        # to 32-bit before plotting. This is a lot simpler than
        # dealing with some sort of run-length-encoding scheme to
        # group bins that are "close enough" numerically.
        #
        hplot = HistogramPlot()
        hplot.xlo = self.xlo
        hplot.xhi = self.xhi
        hplot.y = self.weight.astype(np.float32)
        hplot.xlabel = 'Energy (keV)'
        hplot.ylabel = 'Weights'
        hplot.title = 'Weights for {}: '.format(self.id) + \
                      ' {}'.format(self.modelexpr)

        # There is no validation of the preference values.
        #
        # I have removed linestyle from this list since the pylab
        # backend default is 'None', which ends up meaning nothing
        # appears to get drawn. Which is less-than helpful.
        # linecolor also doen't appear to be used, but color is.
        #
        # names = ['xlog', 'ylog', 'linestyle', 'linecolor']
        names = ['xlog', 'ylog', 'color']
        prefs = ui.get_data_plot_prefs()
        for name in names:
            value = prefs.get(name, None)
            if value is not None:
                hplot.histo_prefs[name] = value

        hplot.plot(overplot=overplot, clearwindow=clearwindow, **kwargs)

    def _estimate_expmap(self, *args):
        """Estimate the exposure map given an ARF.

        Although the arguments are listed with parameter names
        below, the function **does not** accept named arguments.
        It uses positional arguments and type checks to determine
        the parameters.

        Parameters
        ----------
        crate
            A TABLECrate, containing ``energ_lo``, ``energ_hi``,
            and ``specresp`` columns.
        filename : string
            The name of an ARF file
        xlo, xhi, y : arrays of numbers
            The arrays taken to be the ``energ_lo``, ``energ_hi``, and
            ``specresp`` columns

        Return
        ------
        expmap : number
            An estimate of the exposure map at the position
            of the source, and has units of cm^2 count / self.fluxtype

        Notes
        -----
        The ARF is linearly interpolated onto the energy grid
        of the dataset and the weighted sum calculated. The
        ARF is assumed to have units of cm^2 count / photon, and
        be defined on a grid given in keV.

        The ``estimate_instmap()`` method should be called in
        preference to this routine.
        """

        nargs = len(args)
        if nargs == 3:
            elo = args[0]
            ehi = args[1]
            specresp = args[2]

            if len(elo) == 1 or len(ehi) == 1 or len(specresp) == 1:
                emsg = "Expected three arrays of the same " + \
                    "length, with more than one element in"
                raise TypeError(emsg)
            if len(elo) != len(ehi) or len(elo) != len(specresp):
                emsg = "Expected three arrays of the same length"
                raise ValueError(emsg)

        elif nargs != 1:
            emsg = "_estimate_expmap() takes 2 or 4 arguments " + \
                "({} given)".format(nargs + 1)
            raise TypeError(emsg)

        else:
            if isinstance(args[0], pycrates.TABLECrate):
                cr = args[0]
            else:
                cr = pycrates.TABLECrate(args[0], mode="r")

            try:
                elo = cr.get_column("ENERG_LO").values.copy()
                ehi = cr.get_column("ENERG_HI").values.copy()
                specresp = cr.get_column("SPECRESP").values.copy()
            except ValueError as e:
                fname = cr.get_filename()
                raise ValueError("Crate {} - {}".format(fname, e))

        # Interpolate using the mid-point of the ARF
        # onto the mid-point of the grid if necessary.
        #
        emid = 0.5 * (elo + ehi)
        if emid.shape == self.xmid.shape and \
                np.all(emid == self.xmid):
            arf = specresp
        else:
            arf = su.interpolate(self.xmid, emid, specresp)
            arf = np.asarray(arf, dtype=self.weight.dtype)
            arf[arf < 0] = 0.0

        return np.sum(self.weight * arf)

    def estimate_expmap(self, *args):
        """Estimate the exposure map given an ARF.

        Although the arguments are listed with parameter names
        below, the function **does not** accept named arguments.
        It uses positional arguments and type checks to determine
        the parameters.

        Parameters
        ----------
        crate
            A TABLECrate, containing ``energ_lo``, ``energ_hi``,
            and ``specresp`` columns.
        filename : string
            The name of an ARF file
        xlo, xhi, y : arrays of numbers
            The arrays taken to be the ``energ_lo``, ``energ_hi``, and
            ``specresp`` columns

        Return
        ------
        expmap : number
            An estimate of the exposure map at the position
            of the source, and has units of cm^2 count / self.fluxtype

        Notes
        -----
        The ARF is linearly interpolated onto the energy grid
        of the dataset and the weighted sum calculated. The
        ARF is assumed to have units of cm^2 count / photon, and
        be defined on a grid given in keV.
        """

        nargs = len(args)
        if nargs != 1 and nargs != 3:
            emsg = "estimate_expmap() takes 2 or 4 " + \
                "arguments ({0} given)".format(nargs + 1)
            raise TypeError(emsg)
        return self._estimate_expmap(*args)


class InstMapWeights1DInt(InstMapWeights):
    "Instrument map weights for Data1DInt datasets"

    def _calc_bins(self, data):
        "Get the xlo/xhi bin values"

        self.xlo = data.xlo

        # Handle a case when dataspace1d in CIAO 4.1.2 can produce
        # different length bins. If this has happened then we know
        # that d.mask will be True since ignore/notice will
        # fail to work on such a dataset. We do not take advantage of
        # this knowledge since it doesn't really help.
        #
        nlo = len(data.xlo)
        nhi = len(data.xhi)
        if nlo == nhi:
            self.xhi = data.xhi

        elif nhi == nlo + 1:
            self.xhi = data.xhi[:-1]

        else:
            emsg = "Internal error: need to handle .xlo/xhi " + \
                "lengths of {0} and {1}!".format(nlo, nhi)
            raise RuntimeError(emsg)


class InstMapWeightsPHA(InstMapWeights):
    "Instrument map weights for DataPHA datasets"

    def _calc_bins(self, data):
        "Get the xlo/xhi bin values"

        (self.xlo, self.xhi) = data._get_ebins()

    def estimate_expmap(self, *args):
        """Estimate the exposure map given an ARF.

        If no argumenhts are supplied then the ARF of the Sherpa
        dataset associated with this obhect is used (``self.id``).

        Although the arguments are listed with parameter names
        below, the function **does not** accept named arguments.
        It uses positional arguments and type checks to determine
        the parameters.

        Parameters
        ----------
        crate
            A TABLECrate, containing ``energ_lo``, ``energ_hi``,
            and ``specresp`` columns.
        filename : string
            The name of an ARF file
        xlo, xhi, y : arrays of numbers
            The arrays taken to be the ``energ_lo``, ``energ_hi``, and
            ``specresp`` columns

        Return
        ------
        expmap : number
            An estimate of the exposure map at the position
            of the source, and has units of cm^2 count / self.fluxtype

        Notes
        -----
        The ARF is linearly interpolated onto the energy grid
        of the dataset and the weighted sum calculated. The
        ARF is assumed to have units of cm^2 count / photon, and
        be defined on a grid given in keV.
        """

        nargs = len(args)
        if nargs == 0:
            darf = ui.get_arf(self.id)
            return self._estimate_expmap(darf.energ_lo,
                                         darf.energ_hi,
                                         darf.specresp)
        else:
            return self._estimate_expmap(*args)


def get_instmap_weights(id=None, fluxtype="photon"):
    """Returns the weights information for use by mkinstmap.

    Parameters
    ----------
    id : int or string
        If id is None then the default Sherpa id is used. This
        dataset must have a grid and source model defined.
    fluxtype : 'photon' or 'erg'
        The units of the instrument map are
        cm^2 count / ``fluxtype``.

    Return
    ------
    weights
        A weights object. When ``fluxtype="photon"`` the
        weights will sum to 1.

    See Also
    --------
    estimate_weighted_expmap
    plot_instmap_weights
    save_instmap_weights

    Notes
    -----
    An error will be thrown if the model evaluates to
    a negative value, or there is no flux.

    This is intended for use with a dataset "faked" using::

        dataspace1d(elow, ehigh, estep)
        set_source(...)

    although there is an attempt to support DataPHA objects
    (either for spectra that have been loaded in or "faked"
    using ``dataspace1d``, specifying the data type explicitly).
    """

    if id is None:
        id = ui.get_default_id()

    # Since sherpa.astro.data.DataPHA is a subclass of
    # sherpa.data.Data1DInt we need to check for it first.
    #
    d = ui.get_data(id)
    if isinstance(d, DataPHA):
        return InstMapWeightsPHA(id, fluxtype=fluxtype)
    elif isinstance(d, Data1DInt):
        return InstMapWeights1DInt(id, fluxtype=fluxtype)
    else:
        emsg = "Unable to calculate weights from a dataset " + \
            "of type {0}.{1}".format(d.__class__.__module__,
                                     d.__class__.__name__)
        raise RuntimeError(emsg)


def save_instmap_weights(*args, **kwargs):
    """Save a weights file in a format usable by mkinstmap.

    This routine does not have a typical Python interface, in that
    up to three arguments are positional, although they can be
    explicitly named. When used positionally, the following
    orders are allowed::

        filename
        id, filename
        filename, clobber
        id, filename, clobber

    Parameters
    ----------
    id : int, string, or None
        The Sherpa dataset to use. If ``None`` then the default
        dataset is used.
    filename : string
        The name of the file to create.
    fluxtype : 'photon' or 'erg'
        The units of the instrument map are
        cm^2 count / ``fluxtype``. The default is ``photon``.
    clobber : bool, optional
        If the output file already exists, should it be deleted
        (``True``) or an IOError raised? The default is ``True``.

    See Also
    --------
    estimate_weighted_expmap
    get_instmap_weights
    plot_instmap_weights

    Notes
    -----
    The output file contains a header (comment character is '#')
    containing some metadata, and then two columns of data, the
    mid-point of the bin and the weight value for the bin. It is
    compatible with the CIAO ASCII file support (use with ``[opt
    colname=first]``).

    Examples
    --------

    Save the weights to the file wgt.dat, and will error out if it
    already exists. The weights are written out so as to create an
    instrument map with units of cm^2 count / erg.

    >>> dataspace1d(0.5, 7.0, 0.1)
    >>> set_source(xsphabs.gal * xspowerlaw.pl)
    >>> gal.nh = 0.12
    >>> pl.phoindex = 1.7
    >>> save_instmap_weights("wgt.dat", fluxtype="erg", clobber=False)

    """

    fname = "save_instmap_weights"
    nargs = len(args)
    if nargs == 0:
        emsg = "{}() takes at least 1 argument ".format(fname) + \
            "(0 given)"
        raise TypeError(emsg)

    if nargs > 3:
        emsg = "{}() takes at most 3 arguments ".format(fname) + \
            "({} given)".format(nargs)
        raise TypeError(emsg)

    # The default values
    user = {"id": ui.get_default_id(),
            "filename": None,
            "clobber": True,
            "fluxtype": "photon"}
    argnames = user.keys()

    if nargs == 1:
        user["filename"] = args[0]

    elif nargs == 3:
        user["id"] = args[0]
        user["filename"] = args[1]
        user["clobber"] = args[2]

    elif _is_boolean(args[1]):
        user["filename"] = args[0]
        user["clobber"] = args[1]

    elif isinstance(args[1], int):
        # This was needed in CIAO 4.2 and earlier since S-Lang would
        # end up using integers for boolean values. Left in in CIAO
        # 4.3 in case there is any old code or documentation relying
        # on this. Note that Python treats non-zero integers as True
        # so this is perhaps not needed (and slightly harmful, as
        # clobber=2 will not map to True).
        #
        user["filename"] = args[0]
        user["clobber"] = args[1] == 1

    else:
        user["id"] = args[0]
        user["filename"] = args[1]

    for (n, v) in kwargs.items():
        if n not in argnames:
            emsg = "{}() got an unexpected ".format(fname) + \
                "keyword argument '{}'".format(n)
            raise TypeError(emsg)
        user[n] = v

    wgts = get_instmap_weights(user["id"], fluxtype=user["fluxtype"])
    wgts.save(user["filename"], clobber=user["clobber"])


def plot_instmap_weights(id=None, fluxtype="photon",
                         overplot=False, clearwindow=True, **kwargs):
    """Plot the weights values.

    Parameters
    ----------
    id : int, string, or None
        The Sherpa dataset to use. If ``None`` then the default
        dataset is used.
    fluxtype : 'photon' or 'erg'
        The units of the instrument map are
        cm^2 count / ``fluxtype``. The default is ``photon``.
    overplot : bool, optional
        If ``True`` then the data is added to the current plot,
        otherwise a new plot is created.
    clearwindow: bool, optional
        If ``True`` then clear out the current plot area of all
        existing plots. This is not used if ``overplot`` is set.
    **kwargs
        Override the histogram plot preferences

    See Also
    --------
    estimate_weighted_expmap
    get_instmap_weights
    save_instmap_weights

    Notes
    -----
    The data plot preferences are used to control the
    appearance of the plot: at present the following fields
    are used::

        ``xlog``
        ``ylog``
        ``color``

    Examples
    --------

    Show the weights for an absorbed powerlaw.

    >>> dataspace1d(0.5, 7.0, 0.1)
    >>> set_source(xsphabs.gal * xspowerlaw.pl)
    >>> gal.nh = 0.12
    >>> pl.phoindex = 1.7
    >>> plot_instmap_weights()

    Change the model to an absorbed APEC model and overplot it.

    >>> set_source(gal * xsapec.gal)
    >>> gal.kt = 1.2
    >>> plot_instmap_weights(overplot=True)

    Compare the weights when using the photon and erg weighting
    schemes (the normalization is significantly different).

    >>> plot_instmap_weights()
    >>> plot_instmap_weights(fluxtype='erg')

    Plot the weights with a log scale on the y axis, and then overplot
    the weights using erg weighting and drawn with a dotted line:

    >>> plot_instmap_weights(ylog=True)
    >>> plot_instmap_weights(fluxtype='erg', overplot=True, linestyle='dotted')

    """

    if id is None:
        id = ui.get_default_id()

    wgts = get_instmap_weights(id, fluxtype=fluxtype)
    wgts.plot(overplot=overplot, clearwindow=clearwindow, **kwargs)


def estimate_weighted_expmap(id=None, arf=None, elo=None, ehi=None,
                             specresp=None, fluxtype="photon",
                             par=None, pvals=None):
    """Estimate the weighted exposure map value for an ARF.

    Parameters
    ----------
    id : int, string, or None
        The Sherpa dataset to use. If ``None`` then the default
        dataset is used.
    arf : string, TABLECrate, or None
        The ARF to use. It must contain the following columns:
        ``energ_lo``, ``energ_hi``, and ``specresp``.
    elo, ehi, specresp : array of numbers or None
        The ARF, where the bin edges are in KeV and the response is
        in cm^2. These are only checked if arf is None, in which
        case all three must be given and have the same size
        (one dimensional).
    fluxtype : 'photon' or 'erg'
        The units of the exposure map are
        cm^2 count / ``fluxtype``. The default is ``photon``.
    par : Sherpa parameter object or None
        If not given then the exposure map is calculated at the
        current parameter settings. If given, it is the Sherpa
        parameter to loop over, using pvals (which must be set).
    pvals : array of numbers or None
        If par is set, calcualte the exposure map at the current
        parameter settings whilst setting the par parameter to
        each of the values in pvals. The parameter value is reset
        to its original value when the routine exits.

    Return
    ------
    expmap : scalar or array of numbers
        When par is None then a scalar, otherwise an array the same
        size as pvals.

    See Also
    --------
    get_instmap_weights
    plot_instmap_weights
    save_instmap_weights

    Notes
    -----
    The ARF is interpolated onto the energy grid of the dataspace.

    Examples
    --------

    Calculate the exposure map over the range gamma = 0.1 to 5,
    with 0.1 step increments, for an absorbed power-law model and
    with the ARF in the file "arf.fits".

    >>> dataspace1d(0.3, 8.0, 0.1)
    >>> set_source(xsphabs.gal * powlaw1d.pl)
    >>> gal.nh = 0.087
    >>> pl.gamma = 1.2
    >>> gvals = np.arange(0.5,5,0.1)
    >>> evals = estimate_weighted_expmap(arf="arf.fits", par=pl.gamma,
                                         pvals=gvals)

    """

    # Usage errors. We can not catch them all before doing actual
    # work.
    #
    if arf is None and \
       (elo is not None or ehi is not None or specresp is not None):
        # we only worry about elo/ehi/specresp if arf is NOT given
        if elo is None or ehi is None or specresp is None:
            emsg = "Missing one or more of elo, ehi, and specresp."
            raise TypeError(emsg)

    if id is None:
        id = ui.get_default_id()

    if par is not None or pvals is not None:

        if par is None or pvals is None:
            emsg = "Either both par and pvals are set or they " + \
                "are both None."
            raise TypeError(emsg)

        if not isinstance(par, Parameter):
            emsg = "par argument must be a Sherpa model parameter."
            raise TypeError(emsg)

        if not hasattr(pvals, "__iter__"):
            emsg = "pvals argument must be an iterable (array/list)."
            raise TypeError(emsg)

        smdl = ui.get_source(id)
        if par not in smdl.pars:
            emsg = "par argument is not a parameter of the " + \
                "source model"
            raise TypeError(emsg)

    wgts = get_instmap_weights(id, fluxtype=fluxtype)
    if isinstance(wgts, InstMapWeights1DInt) and arf is None and \
            elo is None:
        emsg = "The arf parameter or the elo,ehi,specresp " + \
            "parameters must be given."
        raise TypeError(emsg)

    if arf is None:
        if elo is None:
            args = []
        else:
            args = [elo, ehi, specresp]
    else:
        args = [arf]

    if par is None:
        return wgts.estimate_expmap(*args)

    else:
        # Ugh: we have to create an object for each evaluation, which
        # is rather wasteful.
        #
        orig = par.val
        out = []
        try:
            for pval in pvals:
                par.val = pval
                wgts = get_instmap_weights(id, fluxtype=fluxtype)
                out.append(wgts.estimate_expmap(*args))

        finally:
            par.val = orig

        return np.asarray(out)


# Note that the current guess methods are not ideal, in particular
# those for XSPEC models. See
# https://github.com/sherpa/sherpa/issues/104
#
def renorm(id=None, cpt=None, bkg_id=None, names=None,
           limscale=1000.0):
    """Change the normalization of a model to match the data.

    The idea is to change the normalization to be a better match to
    the data, so that the search can be quicker. It can be considered
    to be like the `guess` command, but for the normalization. It
    is *only* intended to change the normalization to a value near
    the correct one; it *should not* be used for any sort of
    calculation without first doing a fit. It is also only going to
    give reasonable results for models where the predicted data of a
    model is linearly related to the normalization.

    Parameters
    ----------
    id : None, int, or str
       The data set identifier to use. A value of ``None`` uses the
       default identifier.
    cpt
       If not ``None``, the model component to use. When ``None``, the
       full source expression for the data set is used. There is no
       check that the ``id`` argument matches the component (i.e. that
       the component is included in the source model for the data set)
    bkg_id : None, int
       If not None then change the normalization of the model to the
       given background dataset.
    names : None or array of str
       The parameter names that should be changed (a case-insensitive
       comparison is made, and the name does not include the model
       name). If ``None`` then the default set of
       ``['ampl', 'norm']`` is used.
    limscale : float
       The min and max range of the normalization is set to the
       calculated value divided and multiplied by ``limscale``.
       These limits will be modified to match the hard limits of the
       parameter if they exceed them.

    See Also
    --------
    guess, ignore, notice, set_par

    Notes
    -----
    The normalization is computed so that the predicted model counts
    matches the observed counts for the currently-noticed data range,
    as long as parameter names match the ``names`` argument (or
    ['ampl', 'norm'] if that is ``None``) and the parameter is not
    frozen.

    If no matches are found, then no changes are made. Otherwise, a
    scale factor is created by summing up the data counts and dividing
    this by the model sum over the currently-noticed range. This scale
    factor is divided by the number of matching parameters, and then
    the parameter values are multiplied by this value. If a model
    contains multiple parameters matching the contents of the
    ``names`` argument then each one will be changed by this routine.

    It is not intended for use with source expressions
    created with `set_full_model`, and may not work well with
    image models that use a PSF (one set with `set_psf`).

    Examples
    --------

    Adjust the normalization of the gal component before fitting.

    >>> load_pha('src.pi')
    >>> subtract()
    >>> notice(0.5, 7)
    >>> set_source(xsphabs.galabs * xsapec.gal)
    >>> renorm()

    Change the normalization of a 2D model using the 'src' dataset.
    Only the ``src`` component is changed since the default value for
    the ``names`` parameter - that is ['ampl', 'norm'] - does not
    match the normalization parameter of the `const2d` model.

    >>> load_image('src', 'img.fits')
    >>> set_source('src', gauss2d.src + const2d.bgnd)
    >>> renorm('src')

    The names parameter is set so that both components are adjusted,
    and each component is assumed to contribute half the signal.

    >>> load_image(12, 'img.fits')
    >>> notice2d_id(12, 'srcfit.reg')
    >>> set_source(12, gauss2d.src12 + const2d.bgnd12)
    >>> renorm(12, names=['ampl', 'c0'])

    Change the minimum and maximum values of the normalization
    parameter to be the calculated value divided by and multiplied by
    1e4 respectively (these changes are made to the soft limits).

    >>> renorm(limscale=1e4)

    """

    if names is None:
        matches = ['ampl', 'norm']
    elif names == []:
        raise ArgumentErr('bad', 'names argument', '[]')
    else:
        matches = [n.lower() for n in names]

    if bkg_id is None:
        d = ui.get_data(id=id)
        m = ui.get_model(id=id)
    else:
        d = ui.get_bkg(id=id, bkg_id=id)
        m = ui.get_bkg_model(id=id, bkg_id=bkg_id)

    if cpt is not None:
        # In this case the get_[bkg_]model call is not needed above,
        # but leave in as it at least ensures there's a model defined
        # for the data set.
        m = cpt

    pars = [p for p in m.pars if p.name.lower() in matches and
            not p.frozen]
    npars = len(pars)
    if npars == 0:
        wmsg = "no thawed parameters found matching: {}".format(
            ", ".join(matches))
        warn(wmsg)
        return

    yd = d.get_dep(filter=True).sum()
    ym = d.eval_model_to_fit(m).sum()

    # argh; these are numpy floats, and they do not throw a
    # ZeroDivisionError, rather you get a RuntimeWarning message.
    # So explicitly convert to Python float.
    #
    try:
        scale = float(yd) / float(ym) / npars
    except ZeroDivisionError:
        error("model sum evaluated to 0; no re-scaling attempted")
        return

    for p in pars:
        newval = p.val * scale
        newmin = newval / limscale
        newmax = newval * limscale

        # Could do the limit/range checks and then call set_par,
        # but only do so if there's a problem.
        #
        try:
            ui.set_par(p, val=newval, min=newmin, max=newmax)

        except ParameterErr:
            # The following is not guaranteed to catch all cases;
            # e.g if the new value is outside the hard limits.
            #
            minflag = newmin < p.hard_min
            maxflag = newmax > p.hard_max
            if minflag:
                newmin = p.hard_min
            if maxflag:
                newmax = p.hard_max

            ui.set_par(p, val=newval, min=newmin, max=newmax)

            # provide informational message after changing the
            # parameter
            if minflag and maxflag:
                reason = "to hard min and max limits"
            elif minflag:
                reason = "to the hard minimum limit"
            elif maxflag:
                reason = "to the hard maximum limit"
            else:
                # this should be impossible
                reason = "for an unknown reason"

            info("Parameter {} is restricted ".format(p.fullname) +
                 reason)

# End
