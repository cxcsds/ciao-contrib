#
# Copyright (C) 2009, 2010, 2015, 2016, 2019
#           Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

"""Create a spectrum file for use in ChART2.

Helper routines for creating a spectrum file for use with
`ChART version 2 <http://cxc.harvard.edu/ciao/PSFs/chart2/>`_.

Examples
--------

>>> load_pha('src.pi')
>>> notice(0.5, 7)
>>> set_source(xsphabs.gal * xsapec.src)
>>> set_stat('wstat')
>>> fit()
>>> plot_chart_spectrum()
>>> save_chart_spectrum(outfile='chart.dat', clobber=True)

"""

import sherpa.astro.ui as s

from sherpa.plot import HistogramPlot, backend
from sherpa.utils.err import IdentifierErr, ArgumentErr

import numpy as np

from crates_contrib.utils import write_columns

__all__ = ("get_chart_spectrum",
           "save_chart_spectrum",
           "plot_chart_spectrum")


def _get_chart_spectrum(id=None, elow=None, ehigh=None, ewidth=None,
                        norm=None):
    """Helper routine for *_chart_spectrum."""

    # What source expression are we using?
    # get_model/source will throw an IdentifierErr if the expression
    # is not defined; we do not, at present catch/re-throw this
    #
    if id is None:
        id = s.get_default_id()

    mdl = s.get_source(id)

    # What energy grid to use?  Since we do not want to restrict users
    # to only using PHA datasets (i.e. if I just want to create
    # something simple) then we have to look for a range of errors
    # from get_arf
    #
    if elow is None or ehigh is None or ewidth is None:
        try:
            arf = s.get_arf(id)
        except (IdentifierErr, ArgumentErr):
            # a) PHA dataset, no ARF
            # b) Assume this means the dataset is not derived from the
            #    PHA class
            arf = None

        if arf is None:
            emsg = "No ARF found for dataset {} ".format(repr(id)) + \
                "so unable to create energy grid"
            raise TypeError(emsg)

        if elow is None:
            elow = arf.energ_lo[0]
        if ehigh is None:
            ehigh = arf.energ_hi[-1]
        if ewidth is None:
            # Assume constant grid spacing in the ARF
            de = arf.energ_hi[-1] - arf.energ_lo[0]
            nelem = np.size(arf.energ_lo)
            ewidth = de * 1.0 / nelem

    if elow >= ehigh:
        emsg = "elow is >= ehigh: " + \
            "elow={}  ehigh={}".format(elow, ehigh)
        raise TypeError(emsg)
    if ewidth <= 0.0:
        raise TypeError("ewidth is <= 0.0: ewidth={0}".format(ewidth))

    # The following is wasteful if we have an ARF and the user
    # supplies no elow, ehigh, or ewidth arguments.
    #
    # Should I check that nbins is a sensible number (e.g. >= 2)?
    #
    nbins = 1 + np.rint((ehigh - elow) / ewidth)
    erange = elow + ewidth * np.arange(nbins)
    elo = erange[:-1]
    ehi = erange[1:]

    flux = mdl(elo, ehi)
    emid = 0.5 * (ehi + elo)

    # do we want to renormalize?
    if norm is not None:
        flux *= norm
    return {"x": emid, "xlo": elo, "xhi": ehi,
            "y": flux, "id": id, "model": mdl.name}


def get_chart_spectrum(id=None, elow=None, ehigh=None, ewidth=None,
                       norm=None):
    """Return the spectrum in the form needed by ChART2.

    Parameters
    ----------
    id : int or string or None
        If id is None then the default Sherpa id is used. This
        dataset must have a grid and source model defined.
    elow, ehigh, ewidth : number or None
        Only used if all three are given, otherwise the grid
        of the data set is used. The elo value gives the start
        of the grid (the left edge of the first bin) and ehi
        is the end of the grid (the right edge of the last bin),
        and ewidth the bin width, all in keV.
    norm : number or None
        Multiply the flux values by this value, if set.

    Returns
    -------
    (energy_lo, energ_hi, flux_bins)
       The energies are in keV and fluxes in photons/cm^2/s.
       This has changed from ChART version 1, which used
       the mid point rather than low and high edges.

    Notes
    -----
    It is possible for the start or end bin to exceed the
    desired energy limit. For example, if::

        elow=2
        ehigh=2.5
        ewidth=0.2

    then the bins will be 2-2.2, 2.2-2.4, 2.4-2.6. The error
    introduced by this is assumed to be significantly smaller than
    other errors in the calculation (such as how well the source
    spectrum is actually known).

    The source model is assumed to be defined on an energy grid,
    with units of keV, and evaluate to photon/cm**2/s per bin.
    This is true of the XSpec models and 1D Sherpa models.

    At present there is no restriction on the energy grid, which
    needs to lie between 0.2 and 10 keV for ChART2.

    Examples
    --------

    >>> load_pha('src.pi')
    >>> set_source(xsphabs.gal * powlaw1d.pl)
    >>> gal.nh = 0.09
    >>> pl.gamma = 1.25
    >>> pl.ampl = 8.432e-5
    >>> (xlo, xhi, y) = get_chart_spectrum()

    """

    vals = _get_chart_spectrum(id, elow, ehigh, ewidth, norm)
    return (vals["xlo"], vals["xhi"], vals["y"])


def save_chart_spectrum(outfile, clobber=True, verbose=True,
                        format='text',
                        id=None, elow=None, ehigh=None, ewidth=None,
                        norm=None):
    """Create a spectrum file in the format used by ChART2.

    Parameters
    ----------
    outfile : string
        The name of the file to create. It is no-longer possible
        to use None to get the output displayed to the screen.
    format : 'text' or 'fits'
        Use ASCII format ('text') or FITS format ('fits').
    clobber : bool, optional
        If the output file already exists, should it be deleted
        (``True``) or an IOError raised? The default is ``True``.
    verbose : bool, optional
        Should a message be displayed indicating that the file
        has been created? This is only used when outfile is not
        ``None``.
    id : int or string or None
        If id is None then the default Sherpa id is used. This
        dataset must have a grid and source model defined.
    elow, ehigh, ewidth : number or None
        Only used if all three are given, otherwise the grid
        of the data set is used. The elo value gives the start
        of the grid (the left edge of the first bin) and ehi
        is the end of the grid (the right edge of the last bin),
        and ewidth the bin width, all in keV.
    norm : number or None
        Multiply the flux values by this value, if set.

    Notes
    -----
    The format needed for ChART2 is three columns - low and
    high energy values along with the spectrum - and can be in
    any Data-Model supported format (so both ASCII and FITS).
    This is different to version 1, which required a 2 column
    ASCII file.
    """

    if outfile is None:
        raise ValueError("The outfile argument must be specified")

    # For now restrict to just these two forms (write_columns supports
    # a few more).
    if format not in ['text', 'fits']:
        raise ValueError("The format argument must be 'text' or " +
                         "'fits', not '{}'".format(format))

    # Chart2 uses
    #  - 3 columns (energ_lo, energ_hi, spectrum)
    #  - can accept ascii or FITS format
    #
    (elo, ehi, flux) = get_chart_spectrum(id=id, elow=elow,
                                          ehigh=ehigh, ewidth=ewidth,
                                          norm=norm)
    colnames = ['elo', 'ehi', 'spectrum']
    write_columns(outfile, elo, ehi, flux, colnames=colnames,
                  format=format, clobber=clobber)

    if verbose:
        print("Created: {}".format(outfile))


def plot_chart_spectrum(id=None, elow=None, ehigh=None, ewidth=None,
                        norm=None, overplot=False, clearwindow=True):
    """Plots the spectrum as used by ChART2.

    Parameters
    ----------
    id : int or string or None
        If id is None then the default Sherpa id is used. This
        dataset must have a grid and source model defined.
    elow, ehigh, ewidth : number or None
        Only used if all three are given, otherwise the grid
        of the data set is used. The elo value gives the start
        of the grid (the left edge of the first bin) and ehi
        is the end of the grid (the right edge of the last bin),
        and ewidth the bin width, all in keV.
    norm : number or None
        Multiply the flux values by this value, if set.
    overplot : bool, optional
        If ``True`` then the data is added to the current plot,
        otherwise a new plot is created.
    clearwindow: bool, optional
        If ``True`` then clear out the current plot area of all
        existing plots. This is not used if ``overplot`` is set.

    Notes
    -----
    A histogram plot is now used, instead of the curve plot
    used for ChART version 1.

    Labels used to be added to the top-left and -right corners to
    indicate the model and dataset identifier. The plot title
    now contains the model name and the dataset identifier has been
    removed.
    """

    vals = _get_chart_spectrum(id=id, elow=elow,
                               ehigh=ehigh, ewidth=ewidth,
                               norm=norm)

    # In sherpa_contrib.utils.plot_instmap_weights it was found useful
    # to convert the Y values to float32 from float64 to avoid
    # precision issues confusing the plot (i.e. showing structure that
    # isn't meaningful to the user). Is this going to be needed
    # here too?
    #
    hplot = HistogramPlot()
    hplot.xlo = vals['xlo']
    hplot.xhi = vals['xhi']
    hplot.y = vals['y']  # .astype(np.float32)
    hplot.xlabel = 'Energy (keV)'
    hplot.title = 'ChaRT Spectrum: {}'.format(vals['model'])

    # LaTeX support depends on the backend
    if backend.name == 'pylab':
        hplot.ylabel = 'Flux (photon cm$^{-2}$ s$^{-1}$)'
    elif backend.name == 'chips':
        hplot.ylabel = 'Flux (photon cm^{-2} s^{-1})'
    else:
        hplot.ylabel = 'Flux (photon cm^-2 s^-1)'

    hplot.plot(overplot=overplot, clearwindow=clearwindow)
