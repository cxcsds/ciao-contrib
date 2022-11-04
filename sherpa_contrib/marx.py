#
#  Copyright (C) 2018, 2019, 2022
#           Massachusetts Institute of Technology
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

"""Create a spectrum file for use in MARX.

Helper routines for creating a spectrum file for use with
`MARX <https://space.mit.edu/cxc/marx/>`_.

Examples
--------

>>> load_pha('src.pi')
>>> notice(0.5, 7)
>>> set_source(xsphabs.gal * xsapec.src)
>>> set_stat('wstat')
>>> fit()
>>> plot_marx_spectrum()
>>> save_marx_spectrum(outfile='marx.dat', clobber=True)

"""

from sherpa.plot import HistogramPlot
from sherpa import plot

from crates_contrib.utils import write_columns

from .chart import _get_chart_spectrum

__all__ = ("get_marx_spectrum",
           "save_marx_spectrum",
           "plot_marx_spectrum")


def get_marx_spectrum(id=None, elow=None, ehigh=None, ewidth=None,
                      norm=None):
    """Return the spectrum in the form needed by MARX.

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
    (energ_hi, flux_bins)
       The energies are in keV and fluxes in photons/cm^2/s/keV.

    Notes
    -----
    The bins are supposed to be continuous and the value of energ_hi
    for one bin is use as the lower boundary of the next bin. MARX
    ignores the first bin the input file since its lower boundary is
    not specified.

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


    Examples
    --------

    >>> load_pha('src.pi')
    >>> set_source(xsphabs.gal * powlaw1d.pl)
    >>> gal.nh = 0.09
    >>> pl.gamma = 1.25
    >>> pl.ampl = 8.432e-5
    >>> (xhi, y) = get_marx_spectrum()

    """

    vals = _get_chart_spectrum(id, elow, ehigh, ewidth, norm)
    return (vals["xhi"], vals["y"] / (vals['xhi'] - vals['xlo']))


def save_marx_spectrum(outfile, clobber=True, verbose=True,
                       id=None, elow=None, ehigh=None, ewidth=None,
                       norm=None):
    """Create a spectrum file in the format used by MARX.

    Parameters
    ----------
    outfile : string
        The name of the file to create. It is no-longer possible
        to use None to get the output displayed to the screen.
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
    The format needed for MARX is two columns - the upper
    energy value along with the spectrum.
    """

    if outfile is None:
        raise ValueError("The outfile argument must be specified")

    (ehi, flux) = get_marx_spectrum(id=id, elow=elow,
                                    ehigh=ehigh, ewidth=ewidth,
                                    norm=norm)
    write_columns(outfile, ehi, flux,
                  format='raw', clobber=clobber)

    if verbose:
        print("Created: {}".format(outfile))


def plot_marx_spectrum(id=None, elow=None, ehigh=None, ewidth=None,
                       norm=None, overplot=False, clearwindow=True):
    """Plots the spectrum as used by MARX.

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
    hplot.y = vals['y'] / (vals['xhi'] - vals['xlo'])
    hplot.xlabel = 'Energy (keV)'
    hplot.title = 'MARX Spectrum: {}'.format(vals['model'])

    # LaTeX support depends on the backend
    if plot.backend.name == 'pylab':
        hplot.ylabel = 'Flux (photon cm$^{-2}$ s$^{-1}$ keV$^{-1}$)'
    else:
        hplot.ylabel = 'Flux (photon cm^-2 s^-1)'

    hplot.plot(overplot=overplot, clearwindow=clearwindow)
