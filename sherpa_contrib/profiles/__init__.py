#
#  Copyright (C) 2009, 2010, 2015, 2016, 2018, 2019
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
Routines to plot the radial profile of a 2D image and fit,
along with the residuals.

The routines are:

  prof_data()
  prof_model()
  prof_source()
  prof_resid()
  prof_delchi()
  prof_fit()
  prof_fit_resid()
  prof_fit_delchi()

  get_data_prof_prefs()
  get_model_prof_prefs()
  get_source_prof_prefs()
  get_resid_prof_prefs()
  get_delchi_prof_prefs()

  get_data_prof()
  get_model_prof()
  get_source_prof()
  get_resid_prof()
  get_delchi_prof()
  get_fit_prof()

The aim is to provide an interface similar to the plot_data()
family of routines in Sherpa for 1D data sets. The interface is,
however, more complicated since we need to provide information on
how to create the profiles (e.g. the center, ellipticity, bin
sizes).
"""

from __future__ import absolute_import

from sherpa.astro import ui

import sherpa.utils as utils
import sherpa.plot as plot

from sherpa.plot import Histogram, FitPlot, JointPlot
from sherpa.astro.plot import ModelHistogram

import numpy as np

from . import calculate as c

from . import annotations


__all__ = (
    # Classes
    #
    "RadialProfile", "ResidRadialProfile", "ModelRadialProfile",
    #
    # Data accessors
    #
    "get_data_prof",
    "get_model_prof", "get_source_prof",
    "get_resid_prof", "get_delchi_prof", "get_fit_prof",
    # "get_prof_fit_resid_plot", "get_prof_fit_delchi_plot",
    #
    "get_data_prof_prefs",
    "get_model_prof_prefs", "get_source_prof_prefs",
    "get_resid_prof_prefs", "get_delchi_prof_prefs",
    #
    # Plot routines
    #
    "prof_data", "prof_model", "prof_source",
    "prof_resid", "prof_delchi",
    "prof_fit", "prof_fit_resid", "prof_fit_delchi"
)


# Set up plot defaults: the *_defaults routines are not expected
# to be called externally.
#
# Apparently the xxx.get_yyy_defaults() routines already return
# a copy of the structure so no need to here.
#
def get_data_prof_defaults():
    d = plot.backend.get_histo_defaults()

    d['yerrorbars'] = True

    # Try to support backend-specific settings
    #
    if plot.backend.name == 'pylab':
        newopts = [('marker', 'o'),
                   ('markerfacecolor', 'none'),
                   ('markersize', 4),
                   ('linestyle', '')]

    for n, v in newopts:
        d[n] = v

    # d['xlog'] = True
    # d['ylog'] = True
    return d


def get_model_prof_defaults():
    d = plot.backend.get_model_histo_defaults()
    return d


def get_resid_prof_defaults():
    d = plot.backend.get_resid_plot_defaults()

    # are these needed/are more needed?
    d.pop('xerrorbars', True)
    d.pop('ratioline', True)

    if plot.backend.name == 'pylab':
        d['markerfacecolor'] = 'none'

    return d


# Looks like need to create a class to handle histograms with Y error
# bars
#
class RadialProfile(Histogram):
    "Create radial profiles of 2D data"

    histo_prefs = get_data_prof_defaults()

    def __init__(self):
        self.xlo = None
        self.xhi = None
        self.y = None
        self.yerr = None
        self.xlabel = None
        self.ylabel = None
        self.labels = None
        self.title = "Radial Profile"
        Histogram.__init__(self)

    def __str__(self):
        # Be safe and ensure the old print options are restored (e.g.
        # in-case a user hits control-c)
        #
        oldopts = np.get_printoptions()
        np.set_printoptions(precision=4, threshold=6)

        try:
            xlo = self.xlo
            if self.xlo is not None:
                xlo = np.array2string(self.xlo)

            xhi = self.xhi
            if self.xhi is not None:
                xhi = np.array2string(self.xhi)

            y = self.y
            if self.y is not None:
                y = np.array2string(self.y)

            yerr = self.yerr
            if self.yerr is not None:
                yerr = np.array2string(self.yerr)

            out = ('xlo    = {}\n' +
                   'xhi    = {}\n' +
                   'y      = {}\n' +
                   'yerr   = {}\n' +
                   'xlabel = {}\n' +
                   'ylabel = {}\n' +
                   'labels = {}\n' +
                   'title  = {}\n' +
                   'histo_prefs = {}').format(
                       xlo,
                       xhi,
                       y,
                       yerr,
                       self.xlabel,
                       self.ylabel,
                       self.labels,
                       self.title,
                       self.histo_prefs)
        finally:
            np.set_printoptions(**oldopts)

        return out

    def prepare(self, xlo, xhi, y, yerr, title, xlabel, ylabel, labels=None):
        self.xlo = xlo
        self.xhi = xhi
        self.y = y
        self.yerr = yerr
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.labels = labels

    def plot(self, overplot=False, clearwindow=True):
        #
        # Note the hack to work around the lack of support for
        # xaxis preferences in the Histogram class, and xerrorbars
        # (in case sub-classed profiles use it, such as
        # the residual plots)
        #
        store = self.histo_prefs.copy()
        try:
            self.histo_prefs.pop("xaxis", True)
            self.histo_prefs.pop("ratioline", True)
            self.histo_prefs.pop("xerrorbars", True)
            Histogram.plot(self, self.xlo, self.xhi, self.y,
                           yerr=self.yerr, title=self.title,
                           xlabel=self.xlabel, ylabel=self.ylabel,
                           overplot=overplot, clearwindow=clearwindow)
        finally:
            self.histo_prefs = store

        if not overplot:
            if store.get("xaxis", False):
                annotations.add_hline(0)

            if self.labels is not None:
                x0 = 0.95
                y0 = 0.92
                dy = 0.05
                for l in self.labels:
                    annotations.add_rlabel(x0, y0, l)
                    y0 -= dy


# Hmmm, do we want to bother with X error bars?
# If so need to plot using a curve rather than histogram
#
class ResidRadialProfile(RadialProfile):
    "Create radial profiles of 2D data (residuals about the fit)"

    histo_prefs = get_resid_prof_defaults()

    def __init__(self):
        RadialProfile.__init__(self)
        self.title = "Radial Profile of Residuals"


class ModelRadialProfile(ModelHistogram):
    "Radial profiles of models"

    histo_prefs = get_model_prof_defaults()

    def __init__(self):
        self.labels = None
        ModelHistogram.__init__(self)
        self.title = "Radial Profile of Model"

    def prepare(self, xlo, xhi, y, title, xlabel, ylabel, labels=None):
        self.xlo = xlo
        self.xhi = xhi
        self.y = y
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.labels = labels

    def plot(self, overplot=False, clearwindow=True):
        ModelHistogram.plot(self, overplot=overplot, clearwindow=clearwindow)
        if not overplot and self.labels is not None:
            x0 = 0.95
            y0 = 0.92
            dy = 0.05
            for l in self.labels:
                annotations.add_rlabel(x0, y0, l)
                y0 -= dy


# Global storage
#
# Perhaps I should store the output of calc_profile()
# so that I can re-use it for the different plots (although
# would then have to extend for calculating both the model
# and source profiles). This way
#   prof_data(...)
#   prof_model(...)
# would be faster. It would have to be done using the recalc
# (or replot) flag which may be a bit confusing since it would
# be different to how it works with plot_data etc.
#
_prof_data_plot = RadialProfile()
_prof_model_plot = ModelRadialProfile()
_prof_source_plot = ModelRadialProfile()
_prof_resid_plot = ResidRadialProfile()
_prof_delchi_plot = ResidRadialProfile()
_prof_fit_plot = FitPlot()
_prof_fit_resid_plot = {
    "jointplot": JointPlot(),
    "fitplot": _prof_fit_plot,
    "residplot": _prof_resid_plot
}
_prof_fit_delchi_plot = {
    "jointplot": JointPlot(),
    "fitplot": _prof_fit_plot,
    "residplot": _prof_delchi_plot
}


def _process_grouping(counts, snr):
    """Convert the user's grouping choices into the parameter
    to send to calc_profile."""

    if counts is not None:
        return ("counts", counts)
    elif snr is not None:
        return ("snr", snr)
    else:
        return None


def _prepare_prof_data_plot(id=None, model=None,
                            rmin=None, rmax=None, rstep=None,
                            rlo=None, rhi=None,
                            xpos=None, ypos=None, ellip=None, theta=None,
                            group_counts=None, group_snr=None,
                            label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(None, id=id, rmin=rmin, rmax=rmax, rstep=rstep,
                           rlo=rlo, rhi=rhi, model=model,
                           xpos=xpos, ypos=ypos, ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    ylabel = "Counts per {0} pixel".format(rprof["coord"])
    _prof_data_plot.prepare(rprof["rlo"], rprof["rhi"],
                            rprof["data"], rprof["err"],
                            title=rprof["datafile"],
                            xlabel=rprof["xlabel"],
                            ylabel=ylabel,
                            labels=labels)


def _prepare_prof_model_plot(id=None, model=None,
                             rmin=None, rmax=None, rstep=None,
                             rlo=None, rhi=None,
                             xpos=None, ypos=None, ellip=None, theta=None,
                             group_counts=None, group_snr=None,
                             label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_model_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    ylabel = "Counts per {0} pixel".format(rprof["coord"])
    _prof_model_plot.prepare(rprof["rlo"], rprof["rhi"], rprof["model"],
                             title="Model of {0}".format(rprof["datafile"]),
                             xlabel=rprof["xlabel"],
                             ylabel=ylabel,
                             labels=labels)


def _prepare_prof_source_plot(id=None, model=None,
                              rmin=None, rmax=None, rstep=None,
                              rlo=None, rhi=None,
                              xpos=None, ypos=None, ellip=None, theta=None,
                              group_counts=None, group_snr=None,
                              label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_source_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    title = "Source Model of {0}".format(rprof["datafile"])
    ylabel = "Flux per {0} pixel".format(rprof["coord"])
    _prof_source_plot.prepare(rprof["rlo"], rprof["rhi"], rprof["model"],
                              title=title,
                              xlabel=rprof["xlabel"],
                              ylabel=ylabel,
                              labels=labels)


def _prepare_prof_resid_plot(id=None, model=None,
                             rmin=None, rmax=None, rstep=None,
                             rlo=None, rhi=None,
                             xpos=None, ypos=None, ellip=None, theta=None,
                             group_counts=None, group_snr=None,
                             label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_model_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    title = "Residuals of {0} - Model".format(rprof["datafile"])
    _prof_resid_plot.prepare(rprof["rlo"], rprof["rhi"],
                             rprof["resid"], rprof["err"] * rprof["area"],
                             title=title,
                             xlabel=rprof["xlabel"],
                             ylabel="Residual (counts)",
                             labels=labels)


def _prepare_prof_delchi_plot(id=None, model=None,
                              rmin=None, rmax=None, rstep=None,
                              rlo=None, rhi=None,
                              xpos=None, ypos=None, ellip=None, theta=None,
                              group_counts=None, group_snr=None,
                              label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_model_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    title = 'Sigma Residuals of {} - Model'.format(rprof["datafile"])
    sigma = annotations.add_latex_symbol(r'\sigma')
    _prof_delchi_plot.prepare(rprof["rlo"], rprof["rhi"],
                              rprof["delchi"], np.ones(rprof["delchi"].size),
                              title=title,
                              xlabel=rprof["xlabel"],
                              ylabel='Residual ({})'.format(sigma),
                              labels=labels)


def _prepare_prof_fit_plot(id=None, model=None,
                           rmin=None, rmax=None, rstep=None,
                           rlo=None, rhi=None,
                           xpos=None, ypos=None, ellip=None, theta=None,
                           group_counts=None, group_snr=None,
                           label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_model_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    dataplot = _prof_data_plot
    modelplot = _prof_model_plot

    dataplot.prepare(rprof["rlo"], rprof["rhi"], rprof["data"], rprof["err"],
                     title=rprof["datafile"],
                     xlabel=rprof["xlabel"],
                     ylabel="Counts per {0} pixel".format(rprof["coord"]),
                     labels=labels)

    modelplot.prepare(rprof["rlo"], rprof["rhi"], rprof["model"],
                      title=rprof["datafile"],
                      xlabel=rprof["xlabel"],
                      ylabel="Counts per {0} pixel".format(rprof["coord"]))
    _prof_fit_plot.prepare(dataplot, modelplot)


def _prepare_prof_fit_resid_plot(id=None, model=None,
                                 rmin=None, rmax=None, rstep=None,
                                 rlo=None, rhi=None,
                                 xpos=None, ypos=None, ellip=None, theta=None,
                                 group_counts=None, group_snr=None,
                                 label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_model_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    fp = _prof_fit_resid_plot["fitplot"]
    rp = _prof_fit_resid_plot["residplot"]
    # jp = _prof_fit_resid_plot["jointplot"]  # TODO: should this be used?

    dataplot = _prof_data_plot
    modelplot = _prof_model_plot

    dataplot.prepare(rprof["rlo"], rprof["rhi"], rprof["data"], rprof["err"],
                     title=rprof["datafile"],
                     xlabel=rprof["xlabel"],
                     ylabel="Counts per {0} pixel".format(rprof["coord"]),
                     labels=labels)
    modelplot.prepare(rprof["rlo"], rprof["rhi"], rprof["model"],
                      title=rprof["datafile"],
                      xlabel=rprof["xlabel"],
                      ylabel="Counts per {0} pixel".format(rprof["coord"]))

    fp.prepare(dataplot, modelplot)
    rp.prepare(rprof["rlo"], rprof["rhi"],
               rprof["resid"], rprof["err"] * rprof["area"],
               title=rprof["datafile"],
               xlabel=rprof["xlabel"],
               ylabel="Residual (counts)")


def _prepare_prof_fit_delchi_plot(id=None, model=None,
                                  rmin=None, rmax=None, rstep=None,
                                  rlo=None, rhi=None,
                                  xpos=None, ypos=None, ellip=None, theta=None,
                                  group_counts=None, group_snr=None,
                                  label=True):

    grouptype = _process_grouping(group_counts, group_snr)
    rprof = c.calc_profile(ui.get_model_image, id=id, rmin=rmin, rmax=rmax,
                           rstep=rstep, rlo=rlo, rhi=rhi,
                           model=model, xpos=xpos, ypos=ypos,
                           ellip=ellip, theta=theta,
                           grouptype=grouptype)

    if label:
        labels = rprof["labels"]
    else:
        labels = None

    fp = _prof_fit_delchi_plot["fitplot"]
    rp = _prof_fit_delchi_plot["residplot"]
    # jp = _prof_fit_delchi_plot["jointplot"]

    dataplot = _prof_data_plot
    modelplot = _prof_model_plot

    dataplot.prepare(rprof["rlo"], rprof["rhi"], rprof["data"], rprof["err"],
                     title=rprof["datafile"],
                     xlabel=rprof["xlabel"],
                     ylabel="Counts per {0} pixel".format(rprof["coord"]),
                     labels=labels)
    modelplot.prepare(rprof["rlo"], rprof["rhi"], rprof["model"],
                      title=rprof["datafile"],
                      xlabel=rprof["xlabel"],
                      ylabel="Counts per {0} pixel".format(rprof["coord"]))

    fp.prepare(dataplot, modelplot)

    sigma = annotations.add_latex_symbol(r'\sigma')
    rp.prepare(rprof["rlo"], rprof["rhi"],
               rprof["delchi"], np.ones(rprof["delchi"].size),
               title=rprof["datafile"],
               xlabel=rprof["xlabel"],
               ylabel='Residual ({})'.format(sigma))


#
# High Level UI Functions
#

#
# Data access routines
#
def get_data_prof(id=None, model=None,
                  rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                  xpos=None, ypos=None, ellip=None, theta=None,
                  group_counts=None, group_snr=None,
                  **kwargs):
    """Return the data used by prof_data.

    See prof_data for a description of the arguments.

    Returns
    -------
    data : a `sherpa_contrib.profiles.RadialProfile` instance
       An object representing the data used to create the plot by
       `prof_data`.

    """
    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_data_plot(id=id, rmin=rmin, rmax=rmax, rstep=rstep,
                                rlo=rlo, rhi=rhi, model=model,
                                xpos=xpos, ypos=ypos, ellip=ellip, theta=theta,
                                group_counts=group_counts, group_snr=group_snr)
    return _prof_data_plot


def get_model_prof(id=None, model=None,
                   rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                   xpos=None, ypos=None, ellip=None, theta=None,
                   group_counts=None, group_snr=None,
                   **kwargs):
    """Return the data used by prof_model.

    See prof_data for a description of the arguments.

    Returns
    -------
    data : a `sherpa_contrib.profiles.ModelRadialProfile` instance
       An object representing the data used to create the plot by
       `prof_model`.

    """
    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_model_plot(id=id, rmin=rmin, rmax=rmax,
                                 rstep=rstep, rlo=rlo, rhi=rhi,
                                 model=model, xpos=xpos, ypos=ypos,
                                 ellip=ellip, theta=theta,
                                 group_counts=group_counts,
                                 group_snr=group_snr)
    return _prof_model_plot


def get_source_prof(id=None, model=None,
                    rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                    xpos=None, ypos=None, ellip=None, theta=None,
                    group_counts=None, group_snr=None,
                    **kwargs):
    """Return the data used by prof_source.

    See prof_data for a description of the arguments.

    Returns
    -------
    data : a `sherpa_contrib.profiles.ModelRadialProfile` instance
       An object representing the data used to create the plot by
       `prof_source`.

    """
    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_source_plot(id=id, rmin=rmin, rmax=rmax,
                                  rstep=rstep, rlo=rlo, rhi=rhi,
                                  model=model, xpos=xpos, ypos=ypos,
                                  ellip=ellip, theta=theta,
                                  group_counts=group_counts,
                                  group_snr=group_snr)
    return _prof_source_plot


def get_resid_prof(id=None, model=None,
                   rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                   xpos=None, ypos=None, ellip=None, theta=None,
                   group_counts=None, group_snr=None,
                   **kwargs):
    """Return the data used by prof_resid.

    See prof_data for a description of the arguments.

    Returns
    -------
    data : a `sherpa_contrib.profiles.ResidRadialProfile` instance
       An object representing the data used to create the plot by
       `prof_resid`.

    """
    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_resid_plot(id=id, rmin=rmin, rmax=rmax, rstep=rstep,
                                 rlo=rlo, rhi=rhi,
                                 model=model, xpos=xpos, ypos=ypos,
                                 ellip=ellip, theta=theta,
                                 group_counts=group_counts,
                                 group_snr=group_snr)
    return _prof_resid_plot


def get_delchi_prof(id=None, model=None,
                    rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                    xpos=None, ypos=None, ellip=None, theta=None,
                    group_counts=None, group_snr=None,
                    **kwargs):
    """Return the data used by prof_delchi.

    See prof_data for a description of the arguments.

    Returns
    -------
    data : a `sherpa_contrib.profiles.ResidRadialProfile` instance
       An object representing the data used to create the plot by
       `prof_delchi`.

    """
    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_delchi_plot(id=id, rmin=rmin, rmax=rmax,
                                  rstep=rstep, rlo=rlo, rhi=rhi,
                                  model=model, xpos=xpos, ypos=ypos,
                                  ellip=ellip, theta=theta,
                                  group_counts=group_counts,
                                  group_snr=group_snr)
    return _prof_delchi_plot


def get_fit_prof(id=None, model=None,
                 rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                 xpos=None, ypos=None, ellip=None, theta=None,
                 group_counts=None, group_snr=None,
                 **kwargs):
    """Return the data used by prof_fit.

    See prof_data for a description of the arguments.

    Returns
    -------
    data : a `sherpa.plot.FitPlot` instance
       An object representing the data used to create the plot by
       `prof_fit`.

    """
    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_fit_plot(id=id, rmin=rmin, rmax=rmax,
                               rstep=rstep, rlo=rlo, rhi=rhi,
                               model=model, xpos=xpos, ypos=ypos,
                               ellip=ellip, theta=theta,
                               group_counts=group_counts, group_snr=group_snr)
    return _prof_fit_plot


#
# Plot routines
#
def prof_data(id=None, model=None,
              rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
              xpos=None, ypos=None, ellip=None, theta=None,
              group_counts=None, group_snr=None,
              label=True,
              **kwargs):

    """Plot up the profile of the imaging data.

    id is the data set id to use (if None then use the default id).

    The initial binning used is governed by the rstep, rmin, rmax, rlo,
    and rhi parameters, as described below. After binning, the data
    may be grouped if the group_counts or group_snr arguments are set.

    The choice of binning is determined by:

      - rlo and rhi are given then these are used as the left and
        right edges of each bin (the values should be sequences or
        numpy arrays)
      - rlo is given but rhi is None, where rlo is a sequence or numpy
        array uses the rlo values as the left edges of the bins. In this
        case the last element defines the upper edge of the last bin
      - otherwise the binning is from rmin to rmax with a step size
        of rstep (where rmin gives the lower edge of the bin and
        the last bin will contain rmax but its uppter edge may exceed
        rmax). If rmin, rmax, or rstep are None then the values are
        taken from the data; rmin and rmax are set to the minimum and
        maximum separations and rstep is set to the pixel size. Note
        that, as described below, rstep can be a scalar or array
        or sequence.

    The units of rlo, rhi, rmin, rmax, and rstep are those of the
    coordinate system selected for the given dataset.

    If rlo is None then rstep is the width of the bins for the profile;
    it can be a scalar, in which case a single value is used for all
    bins, or it can be an array or list of value of the format

      [delta1, r1, delta2, r2, delta3, r3, ..., deltan, rn, deltam]

    which means to use a spacing of

      delta1 for       r <~ r1
      delta2 for r1 <~ r <~ r2
      delta3 for r2 <~ r <~ r3
      ...
      deltan for r(n-1) <~ r <~ rn
      deltam for r >~ rn

    The bins are filtered to lie within rmin and rmax. Note that the
    limits are "approximate" since the final bin of a section is
    not forced to end at the rmax value for that section.

    With
      rmin=0, rmax=30, rstep=[0.5, 2, 1, 10, 2, 20, 5]
    we would use
      rstep=0.5 for  0 <= r < 2
            1        2 <= r < 10
            2       10 <= r < 20
            5       20 <= r < 30

    With
      rmin=2.5, rmax=22, rstep=[0.5, 2, 1, 10, 2, 20, 5]
    the radial bins would be
      2.5-3.5, 3.5-4.5, 4.5-5.5, ..., 9.5-10.5,
      10.5-12.5, 12.5-14.5, 14.5-16.5, 16.5-18.5, 18.5-20.5,
      20.5-22.5

    The bins can be grouped to ensure a minimum number of counts or a
    minimum signal-to-noise ratio per bin:

      - group_counts is not None then this value is used to give the
        minimum number of counts per bin
      - otherwise if group_snr is not None then this value is used to
        give the minimum signal-to-noise ratio per bin, where the errors
        on a bin are currently calculated using the Gehrel's approximation
        error = 1 + sqrt(N+0.75) and no background subtraction is
        assumed to have taken place, so the signal to noise of a bin of
        with counts c is c/(1+sqrt(c+0.75))

    When grouping, the last bin shown is guaranteed to pass the grouping
    constraint. So for instance
      prof_data(rmin=5,rmax=100,group_snr=10)
    may stop before a radius of 100 if the signal to noise ratio is too
    low at these radii.

    The profile is defined in one of several ways:

      a) if the argument name is given then use this value - so if the
         user calls the routine with one or more of

           xpos=..., ypos=..., ellip=..., theta=...

         then the value is taken from this. The values can be one of:
           actual numeric values, parameters of a model, or the names
           of model parameters
         so that the following are all valid
           xpos=4023.45
           xpos=clus.xpos.val
           xpos=clus.xpos
           xpos="clus.xpos"

      b) if the individual argument value is None but the model argument is
         set then the value is taken from the corresponding parameter of the
         model. So if xpos=None and model=clus then the x position will be
         taken from clus.xpos
         The model argument accepts the name of the model as a string or
         as the actual component itself, so both the following are valid

           model=clus
           model="clus"

      c) if value has not been set then the source expression is searched to
         find a valid component. This will fail if there are either no or
         multiple model components with xpos, ypos, ellipm and theta
         parameters in the expression.

    If the model has non-zero ellipticity but you want to use circular annuli,
    set ellip to 0 - e.g.

      plot_data(model=src, ellip=0)

    will use the xpos and ypos parameters from the component called "src"
    but override the ellip value.

    If label is True then the values for the profile center - and,
    if ellipticity is not 0, the ellipticity and theta values - will be
    added to the top-right corner of the plot.

    If overplot is True then the plot is added to the current plot,
    otherwise a new plot is created. If recalc is set to False then the
    values used from the last time the data was plotted will be used,
    otherwise the profile is re-calculated.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_data_plot(id=id, rmin=rmin, rmax=rmax,
                                rstep=rstep, rlo=rlo, rhi=rhi,
                                model=model, xpos=xpos, ypos=ypos,
                                ellip=ellip, theta=theta,
                                group_counts=group_counts,
                                group_snr=group_snr,
                                label=label)

    try:
        plot.begin()
        _prof_data_plot.plot(**kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_model(id=None, model=None,
               rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
               xpos=None, ypos=None, ellip=None, theta=None,
               group_counts=None, group_snr=None,
               label=True,
               **kwargs):
    """
    Plot up the profile of the model (i.e. the source as measured
    by the detector).

    See prof_data() for information on the arguments.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_model_plot(id=id, rmin=rmin, rmax=rmax,
                                 rstep=rstep, rlo=rlo, rhi=rhi,
                                 model=model, xpos=xpos, ypos=ypos,
                                 ellip=ellip, theta=theta,
                                 group_counts=group_counts,
                                 group_snr=group_snr,
                                 label=label)

    try:
        plot.begin()
        _prof_model_plot.plot(**kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_source(id=None, model=None,
                rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                xpos=None, ypos=None, ellip=None, theta=None,
                group_counts=None, group_snr=None,
                label=True,
                **kwargs):
    """
    Plot up the profile of the source (i.e. the source before
    passing through the telescope/detector system).

    See prof_data() for information on the arguments.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_source_plot(id=id, rmin=rmin, rmax=rmax,
                                  rstep=rstep, rlo=rlo, rhi=rhi,
                                  model=model, xpos=xpos, ypos=ypos,
                                  ellip=ellip, theta=theta,
                                  group_counts=group_counts,
                                  group_snr=group_snr,
                                  label=label)

    try:
        plot.begin()
        _prof_source_plot.plot(**kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_resid(id=None, model=None,
               rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
               xpos=None, ypos=None, ellip=None, theta=None,
               group_counts=None, group_snr=None,
               label=True,
               **kwargs):
    """
    Plot up the profile of the residuals to the fit: note that the residuals
    are not normalized by the pixel size.

    See prof_data() for information on the arguments.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_resid_plot(id=id, rmin=rmin, rmax=rmax,
                                 rstep=rstep, rlo=rlo, rhi=rhi,
                                 model=model, xpos=xpos, ypos=ypos,
                                 ellip=ellip, theta=theta,
                                 group_counts=group_counts,
                                 group_snr=group_snr,
                                 label=label)

    try:
        plot.begin()
        _prof_resid_plot.plot(**kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_delchi(id=None, model=None,
                rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                xpos=None, ypos=None, ellip=None, theta=None,
                group_counts=None, group_snr=None,
                label=True,
                **kwargs):
    """
    Plot up the profile of the residuals to the fit, where the residuals are
    expressed in units of the error on the bin.

    See prof_data() for information on the arguments.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_delchi_plot(id=id, rmin=rmin, rmax=rmax,
                                  rstep=rstep, rlo=rlo, rhi=rhi,
                                  model=model, xpos=xpos, ypos=ypos,
                                  ellip=ellip, theta=theta,
                                  group_counts=group_counts,
                                  group_snr=group_snr,
                                  label=label)

    try:
        plot.begin()
        _prof_delchi_plot.plot(**kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_fit(id=None, model=None,
             rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
             xpos=None, ypos=None, ellip=None, theta=None,
             group_counts=None, group_snr=None,
             label=True,
             **kwargs):
    """
    Plot up the profile of the fit: this is a combination of prof_data()
    and prof_model().

    See prof_data() for information on the arguments.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_fit_plot(id=id, rmin=rmin, rmax=rmax,
                               rstep=rstep, rlo=rlo, rhi=rhi,
                               model=model, xpos=xpos, ypos=ypos,
                               ellip=ellip, theta=theta,
                               group_counts=group_counts,
                               group_snr=group_snr,
                               label=label)

    try:
        plot.begin()
        _prof_fit_plot.plot(**kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_fit_resid(id=None, model=None,
                   rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                   xpos=None, ypos=None, ellip=None, theta=None,
                   group_counts=None, group_snr=None,
                   label=True,
                   **kwargs):
    """
    Plot up the profile of the fit and underneath display the residuals
    to the fit: this is a combination of prof_fit() and prof_resid().

    See prof_data() for information on the arguments. If label is True
    then the labels will be added to the top plot (fit) only.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_fit_resid_plot(id=id, rmin=rmin, rmax=rmax,
                                     rstep=rstep, rlo=rlo, rhi=rhi,
                                     model=model, xpos=xpos, ypos=ypos,
                                     ellip=ellip, theta=theta,
                                     group_counts=group_counts,
                                     group_snr=group_snr,
                                     label=label)

    jp = _prof_fit_resid_plot["jointplot"]
    fp = _prof_fit_resid_plot["fitplot"]
    rp = _prof_fit_resid_plot["residplot"]

    try:
        plot.begin()
        jp.reset()
        jp.plottop(fp, **kwargs)
        jp.plotbot(rp, **kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


def prof_fit_delchi(id=None, model=None,
                    rstep=None, rmin=None, rmax=None, rlo=None, rhi=None,
                    xpos=None, ypos=None, ellip=None, theta=None,
                    group_counts=None, group_snr=None,
                    label=True,
                    **kwargs):
    """
    Plot up the profile of the fit and underneath display the residuals
    to the fit: this is a combination of prof_fit() and prof_delchi().

    See prof_data() for information on the arguments. If label is True
    then the labels will be added to the top plot (fit) only.
    """

    if utils.bool_cast(kwargs.pop('recalc', True)):
        _prepare_prof_fit_delchi_plot(id=id, rmin=rmin, rmax=rmax,
                                      rstep=rstep, rlo=rlo, rhi=rhi,
                                      model=model, xpos=xpos, ypos=ypos,
                                      ellip=ellip, theta=theta,
                                      group_counts=group_counts,
                                      group_snr=group_snr,
                                      label=label)

    jp = _prof_fit_delchi_plot["jointplot"]
    fp = _prof_fit_delchi_plot["fitplot"]
    rp = _prof_fit_delchi_plot["residplot"]

    try:
        plot.begin()
        jp.reset()
        jp.plottop(fp, **kwargs)
        jp.plotbot(rp, **kwargs)
    except Exception:
        plot.exceptions()
        raise
    else:
        plot.end()


# Plot preferences
#
def get_data_prof_prefs():
    """Return the preferences for prof_data.

    Returns
    -------
    prefs : dict
       Changing the values of this dictionary will change any new
       data plots. This dictionary will be empty if no plot
       backend is available.

    See Also
    --------
    prof_data, prof_fit, prof_fit_resid, prof_fit_delchi

    Notes
    -----
    The meaning of the fields depend on the chosen plot backend.
    A value of ``None`` means to use the default value for that
    attribute, unless indicated otherwise.

    """
    return _prof_data_plot.histo_prefs


def get_resid_prof_prefs():
    """Return the preferences for prof_resid.

    Returns
    -------
    prefs : dict
       Changing the values of this dictionary will change any new
       residual plots. This dictionary will be empty if no plot
       backend is available.

    See Also
    --------
    prof_resid, prof_fit_resid

    Notes
    -----
    The meaning of the fields depend on the chosen plot backend.
    A value of ``None`` means to use the default value for that
    attribute, unless indicated otherwise.

    """
    return _prof_resid_plot.histo_prefs


def get_delchi_prof_prefs():
    """Return the preferences for prof_delchi.

    Returns
    -------
    prefs : dict
       Changing the values of this dictionary will change any new
       delchi plots. This dictionary will be empty if no plot
       backend is available.

    See Also
    --------
    prof_delchi, prof_fit_delchi

    Notes
    -----
    The meaning of the fields depend on the chosen plot backend.
    A value of ``None`` means to use the default value for that
    attribute, unless indicated otherwise.

    """
    return _prof_delchi_plot.histo_prefs


def get_model_prof_prefs():
    """Return the preferences for prof_model.

    Returns
    -------
    prefs : dict
       Changing the values of this dictionary will change any new
       model plots. This dictionary will be empty if no plot
       backend is available.

    See Also
    --------
    prof_model, prof_fit, prof_fit_resid, prof_fit_delchi

    Notes
    -----
    The meaning of the fields depend on the chosen plot backend.
    A value of ``None`` means to use the default value for that
    attribute, unless indicated otherwise.

    """
    return _prof_model_plot.histo_prefs


def get_source_prof_prefs():
    """Return the preferences for prof_source.

    Returns
    -------
    prefs : dict
       Changing the values of this dictionary will change any new
       source plots. This dictionary will be empty if no plot
       backend is available.

    See Also
    --------
    prof_source

    Notes
    -----
    The meaning of the fields depend on the chosen plot backend.
    A value of ``None`` means to use the default value for that
    attribute, unless indicated otherwise.

    """
    return _prof_source_plot.histo_prefs
