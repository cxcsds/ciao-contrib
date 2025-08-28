#
#  Copyright (C) 2008, 2009, 2010, 2011, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2023, 2025
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

"""
Script:
  lightcurves.py

Aim:
  Provide simple light-curve cleaning routines aimed at removing
  flares from Chandra light curves, in particular background light curves.

  This is a combination of code based on the lc_clean routine from
  Maxim Markevitch (see http://hea-www.harvard.edu/~maxim/axaf/acisbg/)
  and a simple sigma-clipped algorithm

Threads:
  https://cxc.harvard.edu/ciao/threads/acisbackground/
  https://cxc.harvard.edu/ciao/threads/filter_ltcrv/

"""

from itertools import groupby
from operator import itemgetter
import tempfile

import numpy as np

import pycrates as pcr

from ciao_contrib.runtool import dmcopy, dmgti

import os, matplotlib
if "DISPLAY" in os.environ and os.environ["DISPLAY"] != "":
    matplotlib.interactive(True)
    matplotlib.rcParams["toolbar"] = "None"
else:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

# NOTE: the lc_sigma_uclip algorithm is not ready for release
# __all__ = ("lc_sigma_clip", "lc_sigma_uclip", "lc_clean")
__all__ = ("lc_sigma_clip", "lc_clean")

__revision = "16 May 2023"


def _write_gti_text(outfile, tstart, tend):
    """Create a GTI file, in TEXT/DTF format, using the
    tstart/tend values, and then does a dmcopy on it
    to convert it to FITS format (to avoid some issues that
    were found in trying to use a TEXT/DTF format GTI file
    to filter an event file; these may have been fixed by
    now).
    """

    # Could use a crate to avoid having to create the output
    # manually, but it is not clear to me how this can be done
    # (since crates does not, as of CIAO 4.4, propagate
    # subspace information), so do it manually. This should
    # be fixed in more-recent CIAO versions, so need to
    # review to see if can remove this step.
    #
    # (ofd, tname) = tempfile.mkstemp(text=True)
    tfile = tempfile.NamedTemporaryFile(suffix=".gti", mode='w+')
    tname = tfile.name

    tfile.write("#TEXT/DTF\n")

    def card(name, value, comment=None, unit=None):
        "Add the record card to the file"
        tfile.write(f"{name:<8s}= ")

        # following checks not ideal but sufficient for now
        if isinstance(value, str):
            sfmt = '"{}"'
            svalue = value
        elif isinstance(value, bool):
            sfmt = "{:20s}"
            if value:
                svalue = "T"
            else:
                svalue = "F"
        elif isinstance(value, int):
            sfmt = "{:20d}"
            svalue = value
        else:
            # assume a float
            sfmt = "{:20.13e}"
            svalue = value

        tfile.write(sfmt.format(svalue))
        if comment is None and unit is None:
            tfile.write("\n")
            return

        tfile.write(" /")
        if unit is not None:
            tfile.write(f" [{unit}]")
        if comment is not None:
            tfile.write(" " + comment)
        tfile.write("\n")

    card("XTENSION", "TABLE")
    card("HDUNAME", "FILTER")
    card("EXTNAME", "FILTER")
    card("TFIELDS", 1)
    card("HDUCLASS", "ASC")
    card("HDUCLAS1", "FILTER")
    card("ORIGIN", "ASC", comment="Source of FITS file")
    card("CREATOR", f"lightcurves - {__revision}",
         comment="tool that created this output")
    card("CONTENT", "GTI", comment="Data product identification")
    card("TTYPE1", "TIME", comment="Time column")
    card("TFORM1", "1D", comment="data format of field.")
    card("TUNIT1", "s", comment="physical unit of field.")
    card("DSTYP1", "TIME", comment="DM Keyword: Descriptor name.")
    card("DSVAL1", "TABLE", unit="s")
    card("DSFORM1", "D", comment="DM Keyword: Descriptor datatype.")
    card("DSUNIT1", "s", comment="DM Keyword: Descriptor unit.")
    card("DSREF1", ":GTI")
    tfile.write("END\n\n\n")

    card("XTENSION", "TABLE")
    card("HDUNAME", "GTI")
    card("EXTNAME", "GTI")
    card("TFIELDS", 2)
    card("TTYPE1", "START")
    card("TFORM1", "1D", comment="data format of field.")
    card("TUNIT1", "s", comment="physical unit of field.")
    card("TTYPE2", "STOP")
    card("TFORM2", "1D", comment="data format of field.")
    card("TUNIT2", "s", comment="physical unit of field.")
    card("CONTENT", "GTI", comment="Data product identification")
    card("HDUCLASS", "OGIP")
    card("HDUCLAS1", "GTI")
    card("HDUCLAS2", "STANDARD")
    card("ORIGIN", "ASC", comment="Source of FITS file")
    card("CREATOR", f"lightcurves - {__revision}",
         comment="tool that created this output")
    card("DSTYP1", "TIME", comment="DM Keyword: Descriptor name.")
    card("DSVAL1", "TABLE", unit="s")
    card("DSFORM1", "D", comment="DM Keyword: Descriptor datatype.")
    card("DSUNIT1", "s", comment="DM Keyword: Descriptor unit.")
    card("DSREF1", ":GTI")
    tfile.write("END\n\n")

    for (tlo, thi) in zip(tstart, tend):
        tfile.write(f"{tlo:19.13e} {thi:19.13e}\n")

    tfile.flush()

    # Convert to FITS format and clean up.
    #
    dmcopy.punlearn()
    dmcopy(tname, outfile, clobber=True)
    # os.unlink(tname)


# We stick pretty-much everything in a class which is a
# fairly-poor design
#
class LightCurve:
    """Store data from a lightcurve and provide
    methods to manipulate and display the data"""

    def __init__(self, filename, verbose=1):
        self.filename = filename
        self.verbose = verbose
        self.__read_data()

        # The storage is rather redundant here (e.g. filter and clean_gti
        # are the same) but was originally written to support easy comparison
        # to the S-Lang version. This could be cleaned up, but is a low
        # priority until it turns out to be a problem.
        #
        self.clean_filter = None
        self.clean_gti = None
        self.clean_bti = None
        self.clean_min_rate = None
        self.clean_max_rate = None
        self.clean_mean_rate = None

        self.method = None
        self.userlimit = None

    def report(self, msg):
        """Display the message if verbose is not 0."""
        if self.verbose == 0:
            return

        print(msg)

    def __read_data(self):
        """
        Reads in the data from the filename and performs simple validation.

        We should use TIMEUNIT and TIMEPIXR to handle non-standard cases,
        but ignore for now.
        """

        cr = pcr.read_file(self.filename)

        if cr.column_exists("count_rate"):
            self.ratename = "count_rate"
        elif cr.column_exists("rate"):
            self.ratename = "rate"
        else:
            raise IOError(f"No count_rate or rate column in file '{self.filename}'")

        self.time = cr.get_column("time").values.copy()
        if self.time.size < 1:
            raise IOError(f"No data read in from the lightcurve '{self.filename}'")
        elif self.time.size < 2:
            raise IOError(f"Only 1 time bin found in the lightcurve '{self.filename}'")

        self.report(f"Total number of bins in lightcurve   = {self.time.size:d}")

        self.rate = cr.get_column(self.ratename).values.copy()

        if cr.column_exists("exposure"):
            self.exposure = cr.get_column("exposure").values.copy()
            self.bin_width = self.exposure.max()

            # We do not make use of this filter, so commenting out for now
            # filter = self.exposure <= 0.0

            if self.verbose > 0:
                nsmall = sum((self.exposure < self.bin_width) &
                             (self.exposure > 0.0))
                n0 = sum(self.exposure <= 0.0)
                print(f"Max length of one bin                = {self.bin_width:g} s")
                print(f"Num. bins with a smaller exp. time   = {nsmall:d}")
                print(f"Num. bins with exp. time = 0         = {n0:d}")

        else:
            self.exposure = None
            self.bin_width = None

        if cr.column_exists("time_min") and cr.column_exists("time_max"):
            self.time_min = cr.get_column("time_min").values.copy()
            self.time_max = cr.get_column("time_max").values.copy()
            self.time_offset = self.time_min[0]
        else:
            self.time_min = None
            self.time_max = None
            self.time_offset = self.time[0]

        self.labels = {}
        self.add_label(cr, "OBJECT")
        self.add_label(cr, "OBS_ID")
        self.add_label(cr, "EXPOSURE", protect=False)
        self.add_label(cr, "DTCOR", protect=False)
        self.add_label(cr, "ONTIME", protect=False)
        self.add_label(cr, "TIMEDEL", protect=False)

        self.filter = self.rate > 0.0
        if any(self.filter) is False:
            raise IOError(f"No rows with a count rate > 0 ({self.filename})")

        # Is there a better way to do this?
        self.gti = self.filter
        self.bti = np.logical_not(self.filter)

        if self.verbose > 0 and any(self.bti):
            print(f"Number of bins with a rate of 0 ct/s = {self.bti.sum()}\n")

        self.mean_rate_original = self.rate.mean()
        self.mean_rate_filtered = self.rate[self.gti].mean()

    def add_label(self, crate, name, protect=True):
        """If there is a keyword of the given name in the crate, add
        it to the store. If the keyword does not exist do
        nothing.

        The protect argument is now ignored.
        """

        # crate.get_key_value returns None on a missing lookup,
        # pycrates.get_keyval raises a LookupError when the key is
        # not found.
        #
        val = crate.get_key_value(name)
        if val is None:
            return

        self.labels[name] = val

    def time_to_offset(self, t):
        """Convert the time(s) in t, assumed to be in seconds, to an
        offset in kiloseconds
        """
        return (t - self.time_offset) / 1.0e3

    def calculate_valid_time_bins(self, minlength=1):
        """Returns (tstart, tend, exposure, flag) for those time bins that pass
        the filter (so calculate_filter() must have already been called).
        flag is True if all intervals pass the minlength filter (i.e. if using
        minlength has no affect here). exposure is the exposure length of
        each interval (if the input light curve had an EXPOSURE column),
        otherwise None.

        The minlength parameter gives the minimum number of consecutive
        bins that must pass the filter to still remain valid (i.e. if
        changed from 1 it acts as an additional filter).
        """

        if self.clean_min_rate is None:
            raise ValueError("calculate_filter() must be run before calculate_valid_time_bins()")

        # Loop through the time bins and ensure that each set of
        # selected times contains >= minlength bins
        #
        if self.time_min is None:
            xlo = self.time
        else:
            xlo = self.time_min
        if self.time_max is None:
            xhi = self.time
        else:
            xhi = self.time_max

        # A simplified version of run-length encoding to calculate
        # those bins that pass both the count rate limit and the
        # minlength test.
        #
        # We add 0's onto the start and end of the filter to simplify
        # handling the start and end bins.
        #
        filter = np.concatenate(([0], self.clean_filter * 1, [0]))
        x = np.diff(filter)
        pstart, = np.where(x == 1)
        pend, = np.where(x == -1)

        if pstart.size != pend.size:
            raise ValueError(f"Internal error: pstart/end lengths are {pstart.size} and {pend.size}!")

        # Filter out those intervals that do not contain minlength
        # elements.
        #
        pnum = pend - pstart
        lcheck = pnum >= minlength
        if not np.any(lcheck):
            raise ValueError(f"Error: there are no periods which pass the minlength ({minlength}) check!")

        i, = np.where(lcheck)
        pend -= 1
        xlo = xlo[pstart[i]]
        xhi = xhi[pend[i]]

        if self.exposure is None:
            exposure = None
        else:
            exposure = np.asarray([self.exposure[pstart[j]:pend[j] + 1].sum()
                                   for j in i])

        return (xlo, xhi, exposure, np.all(lcheck))

    # Should be able to clean up this mess somewhat
    #
    def report_userlimit_using_times(self, tlo=None, thi=None,
                                     exposure=None, minlength=1):
        """Display, to the screen, the valid times as time filters along with
        the corresponding exposure times. At the end indicate the amount of
        valid exposure time that has been retained, although this is only
        approximate as it depends on the GTI intervals in the input file
        as well."""

        if self.verbose < 1:
            return

        if (tlo is None) != (thi is None):
            raise ValueError("tlo and thi must either both be None or both be arrays")

        if tlo is None:
            (tlo, thi, exposure, tflag) = \
                self.calculate_valid_time_bins(minlength)

        ctr = np.arange(tlo.size) + 1
        if exposure is None:

            exposure = (thi - tlo) / 1.0e3

            # There is no guarantee that the exposure time of this bin is
            # the same as (thi-tlo), but we include the DTCOR factor just
            # in case
            #
            if 'DTCOR' in self.labels:
                exposure *= self.labels["DTCOR"]
        else:

            # Assume that the exposure values include any DTCOR factor,
            # and are in seconds
            exposure /= 1.0e3

        # ustr    = ["  ((time >= {:f}) && (time < {:f})) ; {:.2f} ksec, bin {}".format(s,e,d,c) for c,s,e,d in zip(ctr,tlo,thi,exposure)]
        ustr = [f"  ((time >= {str(s)}) && (time < {str(e)})) ; {d:.2f} ksec, bin {c}"
                for c, s, e, d in zip(ctr, tlo, thi, exposure)]

        n = len(tlo)
        if n == 1:
            print(ustr[0])
        else:
            print("\n".join(ustr))
        print("")
        if 'EXPOSURE' in self.labels:
            print("  Exposure time of lightcurve = {:.2f} ks".format(self.labels["EXPOSURE"] / 1000.0))
        print(f"  Filtered exposure time      = {exposure.sum():.2f} ks")
        if 'DTCOR' in self.labels:
            print(f"  DTCOR value                 = {self.labels['DTCOR']:g}")

    def create_userlimit_using_rates(self, minlim, maxlim):
        """Sets the userlimit field for the rate column to
        lie between minlim and maxlim."""

        self.userlimit = f"({self.ratename}>{str(minlim)} && {self.ratename}<{str(maxlim)})"
        self.report(f"GTI limits calculated using a count-rate filter:\n  {self.userlimit}\n")
        self.report("The corresponding times are:")
        self.report_userlimit_using_times(minlength=1)

    # As moving towards writing out the GTI file manually for this case the
    # semantics of this routine no longer matches the name, in that we end
    # up storing the lo/hi values for use by _write_gti_text
    #
    def create_userlimit_using_times(self, lo, hi, exposure=None, minlength=1):
        "Sets the userlimit field for time values between lo and hi."

        # Hmm, should we just go for full accuracy? Not really worth it for
        # most cases
        # ulimits = ["((time>={})&&(time<{}))".format(repr(a), repr(b)) for a,b in zip(lo,hi)]
        ulimits = [f"((time>={a:f})&&(time<{b:f}))"
                   for a, b in zip(lo, hi)]
        n = len(lo)
        if n == 1:
            self.userlimit = ulimits[0]
        else:
            self.userlimit = "({})".format("||".join(ulimits))

        # HACK: save the lo/hi/exposure values for use by _write_gti_text
        self.userlimit_bins = (lo, hi, exposure)

        self.report("GTI limits calculated using a time filter:")
        self.report_userlimit_using_times(tlo=lo, thi=hi,
                                          exposure=exposure,
                                          minlength=minlength)

    def _add_plot_labels(self):
        """Add filename/object/obsid labels to the current plot,
        and make sure the borders are not displayed for this plot
        Ensure these labels are at a lower depth than the main
        plot items.
        """

        trans = plt.gcf().transFigure
        plt.text(0.015, 0.035, self.filename.split("/")[-1],
                 fontsize=8, horizontalalignment="left",
                 verticalalignment="top",
                 transform=trans)
        plt.text(0.985, 0.035, self.method, fontsize=8,
                 horizontalalignment="right", verticalalignment="top",
                 transform=trans)

        if 'OBJECT' in self.labels:
            plt.text(0.015, 0.965, self.labels["OBJECT"],
                     fontsize=8, horizontalalignment="left",
                     verticalalignment="bottom",
                     transform=trans)

        if 'OBS_ID' in self.labels:
            plt.text(0.985, 0.965, "obsid={}".format(self.labels["OBS_ID"]),
                     fontsize=8, horizontalalignment="right",
                     verticalalignment="bottom",
                     transform=trans)

    def plot(self, rateaxis="y", gcol="lime", erase=True):
        """Plot up the light curves.

        The rateaxis argument determines whether the rate is drawn on
        the Y axis or X axis ("y" or "x" respectively). The gcol
        argument is the color to use to draw the "good" points.

        The erase argument is no-longer used.
        """

        if self.clean_gti is None:
            raise ValueError("calculate_filter() must be run before plot()")

        gti = self.clean_gti
        bti = self.clean_bti

        # What data are we plotting?
        #
        t = self.time_to_offset(self.time)
        x1g = t[gti]
        y1g = self.rate[gti]

        if any(bti):
            x1b = t[bti]
            y1b = self.rate[bti]
        else:
            x1b, y1b = None, None

        # We need to calculate the binning for the histograms, so we
        # pick a bin size that is the minimum of 0.01 and (rmax-rmin)/5.0
        # where rmax/min are the max/min count rates of the filtered data.
        # As we have now had reports of this causing a problem - admittedly
        # only for problematic data sets - then we now include a rather
        # arbitrary limit on the number of bins.
        #
        rmin = self.clean_min_rate
        rmax = self.clean_max_rate
        rwidth = min(0.01, (rmax - rmin) / 5.0)

        # Not bothered if number of bins is off by 1 here
        dmin = self.rate.min()
        dmax = self.rate.max()
        nbins = (dmax - dmin) / rwidth
        if nbins > 1000:
            print(f"Warning: Default bin width of {rwidth:g} count/s is too small as it produces")
            print(f"         {nbins} bins.")
            rwidth = (dmax - dmin) / 1000.0
            print(f"         Replacing with a width of {rwidth:g} count/s")
            print("         This may indicate that the lightcurve contains strong flares that")
            print("         require manual filtering.\n")

        ledges = np.arange(dmin, dmax, rwidth)
        ledges = np.append(ledges, ledges[-1] + rwidth)

        (y2a, _) = np.histogram(self.rate, bins=ledges)
        xlo2a = ledges[:-1]
        xhi2a = ledges[1:]

        (y2g, _) = np.histogram(y1g, bins=ledges)
        xlo2g = xlo2a
        xhi2g = xhi2a

        # Filter out zero-rate bins as they are a visual distraction
        #
        i, = np.where(y2a > 0)
        xlo2a = xlo2a[i]
        xhi2a = xhi2a[i]
        y2a = y2a[i]

        i, = np.where(y2g > 0)
        xlo2g = xlo2g[i]
        xhi2g = xhi2g[i]
        y2g = y2g[i]

        # Set up the plot labels
        #
        title = r"mean rate={0:g} {1}".format(self.clean_mean_rate,
                                              r"$\mathrm{s}^{-1}$")
        ratelabel = r"Count Rate $\left[\mathrm{s}^{-1}\right]$"

        # Create the plot
        #
        # setup figure

        if rateaxis == "y":
            # from matplotlib import tight_layout # deprecated in Matplotlib 3.5, breaking in 3.6
            #
            # fig, axs = plt.subplots(2, 1, tight_layout=False)
            # hpad = tight_layout.get_tight_layout_figure(fig,
            #                                             axs,
            #                                             tight_layout.get_subplotspec_list(axs),
            #                                             tight_layout.get_renderer(fig))["hspace"]
            # fig.subplots_adjust(hspace=2*hpad)

            fig, axs = plt.subplots(2, 1, squeeze=True)
            
            hpad = axs[0].get_position().y0 - axs[1].get_position().y1
            fig.subplots_adjust(hspace=6*hpad)
            
        else:
            fig, axs = plt.subplots(2, 1, sharex=True)
            fig.subplots_adjust(hspace=0)

        try:
            # setup subplots and figure labels
            self._add_plot_labels()

            fig.align_ylabels(axs[:])

            axs[0].minorticks_on()
            axs[1].minorticks_on()
            axs[0].tick_params(axis="both", direction="in", which="both",
                               bottom=True, top=True, left=True, right=True)
            axs[1].tick_params(axis="both", direction="in", which="both",
                               bottom=True, top=True, left=True, right=True)

            # plot 1: lightcurve
            #
            # The "bad" set of points are added first, if they
            # exist, so that they are drawn behind the "good" points
            #

            axs[0].set_title(title, fontsize=12)

            plotopts = {"linestyle": "none", "fillstyle": "full"}

            if any(bti):
                if rateaxis == "y":
                    x = x1b
                    y = y1b
                else:
                    x = y1b
                    y = x1b

                plotopts["gid"] = "bad"  # id = "bad"
                plotopts["color"] = "blue"
                plotopts["marker"] = "s"  # symbol.style = "square"
                plotopts["markersize"] = 3.5  # symbol.size = 2

                axs[0].plot(x, y, **plotopts)

            if rateaxis == "y":
                x = x1g
                y = y1g
            else:
                x = y1g
                y = x1g

            plotopts["gid"] = "good"  # id = "good"
            plotopts["marker"] = "o"  # symbol.style = "circle"
            plotopts["markersize"] = 6  # symbol.size = 4
            plotopts["color"] = gcol

            axs[0].plot(x, y, **plotopts)

            if rateaxis == "y":
                axs[0].axhline(y=self.clean_mean_rate, linestyle="dotted")
                axs[0].set_ylabel(ratelabel, fontsize=10)
                axs[0].set_xlabel(r"$\Delta$ Time [ks]", fontsize=10)

            else:
                axs[0].axvline(x=self.clean_mean_rate, linestyle="dotted")
                axs[0].tick_params(labelbottom=False)
                axs[0].set_ylabel(r"$\Delta$ Time [ks]", fontsize=10)

            # plot 2: histogram
            #
            if any(bti):
                # find consecutive indices
                # - first group up consecutive value
                dx2a = xhi2a - xlo2a  # get binsize
                x2a_test = [round(n) for n in xhi2a / dx2a]
                # integer of the bin for grouping ID

                groups = [list(map(itemgetter(1), g))
                          for k, g in groupby(enumerate(x2a_test),
                                              lambda z: z[0] - z[1])]

                grp_a_ind = []

                # open list of indicies
                for g in groups:
                    if len(g) == 1:
                        ind = x2a_test.index(g[0])
                        grp_a_ind.append(ind)

                    else:
                        ind_min = x2a_test.index(min(g))
                        ind_max = x2a_test.index(max(g))
                        grp_a_ind.append((ind_min, ind_max))

                for ind in grp_a_ind:
                    if type(ind) == int:
                        xa_lo = np.array([xlo2a[ind]])
                        xa_hi = np.array([xhi2a[ind]])
                        ya = np.array([y2a[ind]])

                    else:
                        xa_lo = np.array(xlo2a[min(ind):max(ind) + 1])
                        xa_hi = np.array(xhi2a[min(ind):max(ind) + 1])
                        ya = np.array(y2a[min(ind):max(ind) + 1])

                    # 'concatenates' are to add line drop at histogram edges
                    xa = np.append(xa_lo, xa_hi[-1])
                    xa = np.concatenate(([xa_lo[0]], xa))
                    ya = np.append(ya, 0)
                    ya = np.concatenate(([0], ya))

                    # plot entire histogram as step function
                    axs[1].step(x=xa, y=ya, where="post",
                                label="everything", linewidth=1.25,
                                color="blue")

            # try to plot up histogram of good data points
            # - find consecutive indices
            # - first group up consecutive value
            dx2g = xhi2g - xlo2g  # binsize
            x2g_test = [round(n) for n in xhi2g / dx2g]

            groups = [list(map(itemgetter(1), g))
                      for k, g in groupby(enumerate(x2g_test),
                                          lambda z: z[0] - z[1])]

            grp_g_ind = []

            # open list of indicies
            for g in groups:
                if len(g) == 1:
                    ind = x2g_test.index(g[0])
                    grp_g_ind.append(ind)

                else:
                    ind_min = x2g_test.index(min(g))
                    ind_max = x2g_test.index(max(g))
                    grp_g_ind.append((ind_min, ind_max))

            for ind in grp_g_ind:
                if type(ind) == int:
                    xg_lo = np.array([xlo2g[ind]])
                    xg_hi = np.array([xhi2g[ind]])
                    yg = np.array([y2g[ind]])

                else:
                    xg_lo = np.array(xlo2g[min(ind):max(ind) + 1])
                    xg_hi = np.array(xhi2g[min(ind):max(ind) + 1])
                    yg = np.array(y2g[min(ind):max(ind) + 1])

                # 'concatenates' are to add line drop at histogram edges
                xg = np.append(xg_lo, xg_hi[-1])
                xg = np.concatenate(([xg_lo[0]], xg))
                yg = np.append(yg, 0)
                yg = np.concatenate(([0], yg))

                # plot entire histogram as step function
                axs[1].step(x=xg, y=yg, where="post", label="good",
                            linewidth=1.25, color=gcol)

            axs[1].axvline(x=self.clean_mean_rate, linestyle="dotted")

            axs[1].set_xlim(auto=True)
            axs[1].set_ylim(bottom=0, auto=True)

            if rateaxis == "x":
                y_minor_ticks = axs[1].yaxis.get_minorticklocs()
                dytick = y_minor_ticks[1] - y_minor_ticks[0]
                axs[1].set_ylim(bottom=0, top=y_minor_ticks[-1] + 2.5 * dytick)

            axs[1].set_ylabel("Number", fontsize=10)
            axs[1].set_xlabel(ratelabel, fontsize=10)

        except Exception:
            plt.close()
            raise

        return axs

    def plot_gti_limits(self, mplaxs, gtiname, rateaxis="y",
                        pattern="crisscross", pcol="red"):
        "Plot up the GTI limits from the GTI block of gtiname on the rate plot"

        if pattern == "none":
            return

        cr = pcr.read_file(f"{gtiname}[gti]")

        try:
            xr = mplaxs[0].get_xlim()
            yr = mplaxs[0].get_ylim()

            startvals = self.time_to_offset(pcr.copy_colvals(cr, "start"))
            stopvals = self.time_to_offset(pcr.copy_colvals(cr, "stop"))

            edges = []

            if rateaxis == "y":
                start = np.append(startvals, xr[1])
                end = np.append(xr[0], stopvals)

                y_minor_ticks = mplaxs[0].yaxis.get_minorticklocs()
                dytick = y_minor_ticks[1] - y_minor_ticks[0]
                yrs = [yr[0] - dytick, yr[1] + dytick]

                mplaxs[0].set_ylim(bottom=min(yrs),
                                   top=max(yrs))

            else:
                start = np.append(startvals, yr[1])
                end = np.append(yr[0], stopvals)

                x_minor_ticks = mplaxs[0].xaxis.get_minorticklocs()
                dxtick = x_minor_ticks[1] - x_minor_ticks[0]
                xrs = [xr[0] - dxtick, xr[1] + dxtick]

                mplaxs[0].set_xlim(left=min(x_minor_ticks),
                                   right=max(x_minor_ticks))

            lines = mplaxs[0].lines
            zorder = max([line.get_zorder() for line in lines]) + 1

            for key in mplaxs[0].spines.keys():
                mplaxs[0].spines[key].zorder = zorder + 1

            ropts = {}

#        The choices for this parameter are: nofill, solid, updiagonal,
#        downdiagonal, horizontal, vertical, crisscross, grid, polkadot
#
#        No longer support: brick, zigzag, hexagon, wave

            ropts["alpha"] = 0.85
            ropts["facecolor"] = pcol
            ropts["zorder"] = zorder

            ropts["facecolor"] = "none"
            ropts["edgecolor"] = pcol

            if pattern.lower() == "solid":
                ropts["hatch"] = "none"
                ropts["facecolor"] = pcol
                ropts["zorder"] = 0

            elif pattern.lower() == "nofill":
                ropts["hatch"] = ""
                ropts["alpha"] = 0.5

            elif pattern.lower() == "updiagonal":
                ropts["hatch"] = "///"

            elif pattern.lower() == "downdiagonal":
                ropts["hatch"] = "\\\\\\"

            elif pattern.lower() == "horizontal":
                ropts["hatch"] = "---"

            elif pattern.lower() == "vertical":
                ropts["hatch"] = "|||"

            elif pattern.lower() == "crisscross":
                ropts["hatch"] = "xxx"

            elif pattern.lower() == "grid":
                ropts["hatch"] = "+++"

            elif pattern.lower() == "polkadot":
                ropts["hatch"] = "..."

            # add regions blocking the bad intervals
            for s, e in zip(start, end):
                if rateaxis == "y":
                    if pattern.lower() == "nofill":
                        # edge's linestyle and linewidth need to precede all other options
                        # to be recognized, due to bug in matplotlib >1.5.x;
                        # dictionary order is randomized.  From Python 3.6 onwards,
                        # the standard dict type maintains insertion order by default.
                        mplaxs[0].fill_betweenx(y=yrs, x1=s, x2=e,
                                                linestyle="dashed",
                                                linewidth=1, **ropts)

                    else:
                        ropts["linewidth"] = matplotlib.rcParams["hatch.linewidth"] = 0.25

                        mplaxs[0].fill_betweenx(y=yrs, x1=s, x2=e, **ropts)

                    edges.extend([s, e])

                else:
                    if pattern.lower() == "nofill":
                        mplaxs[0].fill_between(x=xrs, y1=s, y2=e,
                                               linestyle="dashed",
                                               linewidth=1, **ropts)
                    else:
                        ropts["linewidth"] = matplotlib.rcParams["hatch.linewidth"] = 0.25

                        mplaxs[0].fill_between(x=xrs, y1=s, y2=e, **ropts)

                    edges.extend([s, e])

            if rateaxis == "y":
                mplaxs[0].set_xlim(left=min(edges), right=max(edges))
            else:
                mplaxs[0].set_ylim(bottom=min(edges), top=max(edges))

        except Exception:
            # Why do we need this again?
            raise ValueError("Failed to highlight 'bad' time intervals in plotted lightcurve.")

    def create_gti_file(self, outfile):
        """Create a GTI file called outfile based on those time periods
        from infile that match the given filter (which is a string of
        the form accepted by the userlimit parameter of dmgti
        """

        if self.userlimit is None:
            raise ValueError("calculate_gti_filter() must be run before create_gti_file()")

        self.report("\nCreating GTI file")

        # Do we write out the GTI manually?
        if hasattr(self, "userlimit_bins"):
            _write_gti_text(outfile, self.userlimit_bins[0],
                            self.userlimit_bins[1])
        else:
            dmgti.punlearn()
            dmgti(self.filename, outfile, self.userlimit, clobber=True,
                  verbose=self.verbose)

        self.report(f"Created: {outfile}")


class CleanLightCurve(LightCurve):
    "Light curve filtering using the same method as the ACIS background files"

    def __init__(self, filename, verbose=1):
        LightCurve.__init__(self, filename, verbose=verbose)
        if self.exposure is None:
            raise IOError(f"The lightcurve '{filename}' does not contain an EXPOSURE column!")

        self.method = "lc_clean"

    def check_valid(self, minfrac):
        """Ensure that the fraction of good bins is >= minfrac (excluding
        the 0-rate bins from the calculation). Throws a ValueError if
        the condition is not met."""

        nrows = self.filter.sum()
        ngood = self.clean_filter.sum()
        frac = (ngood + 0.0) / nrows
        if frac < minfrac:
            raise ValueError("Fraction of bins that are good ({:g}, {} of {}) is below limit of {:g}!".format(frac, ngood, nrows, minfrac))

    def calculate_filter(self, mean=None, clip=3.0, sigma=None, scale=1.2):
        "Filter the light curve."

        # Do we need to calculate an initial mean level?
        #
        if mean is None:

            # The sigma is calculated assuming "poisson" statistics for the
            # mean value, so we have sqrt (mean-rate * bin-width) and then
            # we want to convert it back to a rate, to give
            # sqrt (mean-rate / bin-width)
            #
            omean = self.rate[self.filter].mean()
            osigma = np.sqrt(omean / self.bin_width)
            minval = omean - clip * osigma
            maxval = omean + clip * osigma

            gti, = np.where((self.rate > minval) & (self.rate < maxval))
            if gti.size == 0:
                raise ValueError("Unable to calculate an initial GTI mean rate level via sigma clipping; the unclipped count rate is {0:g} +/- {1:g} ct/s".format(omean,clip*osigma))
            mean = self.rate[gti].mean()

            self.report(f"Calculated an initial mean (sigma-clipped) rate of {mean:g} ct/s")

        else:
            self.report(f"Using a fixed mean rate of {mean:g} ct/s")

        # Calculate the limits based on the mean value and sigma/scale clipping
        #
        if sigma is None:
            self.clean_min_rate = mean / scale
            self.clean_max_rate = mean * scale
            self.report(f"Lightcurve limits use a scale factor of {scale:g} about this mean")

        else:
            # divide by the bin width so we can assume sigma=sqrt(signal)
            #
            sigval = np.sqrt(mean / self.bin_width)
            self.clean_min_rate = mean - sigma * sigval
            self.clean_max_rate = mean + sigma * sigval
            self.report(f"Lightcurve limits clipped using {sigma:g} sigma's about this mean")

        self.report(f"Filtering lightcurve between rates of {self.clean_min_rate:g} and {self.clean_max_rate:g} ct/s")

        self.clean_filter = (self.rate > self.clean_min_rate) & \
                            (self.rate < self.clean_max_rate)
        ngood = self.clean_filter.sum()
        if ngood == 0:
            raise ValueError("Error: no bins match rate={:g} to {:g} (data range is {:g} to {:g})".format(self.clean_min_rate, self.clean_max_rate,
                                                                                                          self.rate[self.filter].min(), self.rate.max()))

        self.report(f"Number of good time bins = {ngood}")

        self.clean_gti = self.clean_filter
        self.clean_bti = np.logical_not(self.clean_gti)

        self.clean_mean_rate = self.rate[self.clean_gti].mean()
        self.report(f"Rate filter:  {str(self.clean_min_rate)} <= {self.ratename} < {str(self.clean_max_rate)}")
        self.report(f"Mean level of filtered lightcurve = {str(self.clean_mean_rate)} ct/s\n")

    def calculate_gti_filter(self):
        "Calculate the GTI filter limit (the userlimit string for dmgti)"

        if self.clean_min_rate is None:
            raise ValueError("calculate_filter() must be run before calculate_gti_filter()")

        self.create_userlimit_using_rates(self.clean_min_rate,
                                          self.clean_max_rate)


class SigmaClipBaseLightCurve(LightCurve):
    """Provide an iterative sigma-clipping filter for a lightcurve. This
    is intended to be sub-classed and should not be created."""

    def __init__(self, filename, verbose=1):
        """The sub-class should set the self.method field after
        calling this method."""
        LightCurve.__init__(self, filename, verbose=verbose)

    def _clip_data(self, sigmas, sigma=3.0):
        """Return True/False for each points: True indicates that
        the point should be clipped. The input is the offset of
        each point in sigmas.
        """

        raise NotImplementedError(f"The _clip_data method has not been sub-classed by {self.__class__}")

    def calculate_filter(self, sigma=3.0, minlength=3):
        "Filter the light curve."

        f = self.filter.copy()
        while True:

            # gp gives the "good points" in this iteration
            (gp,) = np.where(f)
            if gp.size == 0:
                raise ValueError("Error: no bins pass the filter")
            rate = self.rate[gp]
            mean = rate.mean()
            stdev = rate.std()

            min_rate = mean - sigma * stdev
            max_rate = mean + sigma * stdev

            sigmas = (self.rate - mean) / stdev
            flags = self._clip_data(sigmas, sigma=sigma)
            (i,) = np.where(flags & f)
            if i.size == 0:
                break

            f[i] = False

        # Need to improve storage
        #
        self.clean_filter = f
        self.clean_gti = f
        self.clean_bti = np.logical_not(f)
        self.clean_min_rate = min_rate
        self.clean_max_rate = max_rate
        self.clean_mean_rate = self.rate[self.clean_gti].mean()

        self.report(f"Rate filter:  {str(self.clean_min_rate)} <= {self.ratename} < {str(self.clean_max_rate)}")
        self.report(f"Mean level of filtered lightcurve = {str(self.clean_mean_rate)} ct/s\n")

    def calculate_gti_filter(self, minlength=3):
        "Caculate the GTI filter limit (the userlimit string for dmgti)"

        if self.clean_min_rate is None:
            raise ValueError("calculate_filter() must be run before calculate_gti_filter()")

        # If minlength is 1 then we can just the count-rate limits directly.
        # Otherwise we check to see whether the minlength constraint actually
        # makes a difference to the count-rate limit, only using the explicit
        # time ranges if it does
        #
        if minlength == 1:
            self.create_userlimit_using_rates(self.clean_min_rate,
                                              self.clean_max_rate)
        else:
            (tlo, thi, tdur, tflag) = \
                self.calculate_valid_time_bins(minlength=minlength)
            if tflag:
                self.create_userlimit_using_rates(self.clean_min_rate,
                                                  self.clean_max_rate)
            else:
                self.create_userlimit_using_times(tlo, thi, exposure=tdur,
                                                  minlength=minlength)


class SigmaClipLightCurve(SigmaClipBaseLightCurve):
    "Provide an iterative sigma-clipping filter for a lightcurve"

    def __init__(self, filename, verbose=1):
        SigmaClipBaseLightCurve.__init__(self, filename, verbose=verbose)
        self.method = "lc_sigma_clip"

    def _clip_data(self, sigmas, sigma=3.0):
        return (np.abs(sigmas) > sigma)


class SigmaUpperClipLightCurve(SigmaClipBaseLightCurve):
    """Provide an iterative sigma-clipping filter for a lightcurve.

    Unlike SigmaClipLightCurve this only removes points which are
    a given sigma *above* the mean; it ignores those points below
    the mean. This should be better for Chandra-esque light curves
    where there are periods of increased signal you want to remove,
    but very few - if any - periods of lower-than-average signal.

    *** THIS HAS NOT BEEN TESTED ON MANY DATASETS AND IS PROVIDED
    *** AS AN EXPERIMENTAL FEATURE. ITS BEHAVIOR MAY CHANGE AT ANY TIME.
    """

    def __init__(self, filename, verbose=1):
        SigmaClipBaseLightCurve.__init__(self, filename, verbose=verbose)
        self.method = "lc_sigma_uclip"

    def _clip_data(self, sigmas, sigma=3.0):
        return (sigmas > sigma)


# Public access to the filtering
#

def lc_clean(filename, outfile=None, mean=None, clip=3.0, sigma=None,
             scale=1.2, minfrac=0.1,
             plot=True, rateaxis="y", pattern="solid", gcol="lime",
             pcol="red", erase=True,
             verbose=1):
    """
    Calculate good times for a light curve using the same filtering as
    was used to calculate the ACIS blank-sky backgropund files.

    The filename argument must be a table containing TIME, COUNT_RATE (or
    RATE), and EXPOSURE columns.

    If outfile is set then a GTI file will be created representing these
    times.

    If mean is None then the mean count rate is calculted from data, using
    a single sigma clip (the clip pararameter gives the number of
    standard deviations to retain) of the data. The standard deviation is
    calculated as sqrt(mean rate/bin width).

    The mean value is then used to clip the light curve: if sigma is None
    then the limits are mean/scale to min*scale, otherwise they are
    mean - sigma*stdev to mean + sigma*stdev (stdev is again calculated
    from the mean value).

    The minfrac parameter gives the minimum fraction of the lightcurve
    bins that must pass the count-rate filter (after ignoring the zero
    count-rate bins).

    If plot is True then plots of the light curve and histograms of the
    values will be displayed. The rateaxis option determines whether the
    topl plot is drawn as count-rate on the y axis and time on the x axis
    (rateaxis='y') or the other way around (rateaxis='x'). The gcol
    parameter gives the color to use to draw points/histograms of the
    points that are considered good by the iterative clipping (ignoring
    the minlength filter).

    The erase argument is no-longer used.

    If outfile is given and plot is True then the time intervals excluded
    by the calculated GTI file are drawn on the plot as filled regions,
    using the pattern and color determined by the pattern and pcol options
    (setting pattern to 'none' stops this display).

    The verbose parameter can be set to 0, 1, 2, 3, 4, or 5 - although
    the main difference is 0 (none) and not-zero (the only place verbose
    is relevant beyond this is when calling dmgti).

    """

    # Check the arguments
    #
    if clip <= 0.0:
        raise ValueError(f"clip argument must be > 0, not {clip:g}")

    if sigma is None:
        if scale < 1.0:
            raise ValueError(f"scale argument must be >= 1.0, not {scale:g}")
    elif sigma <= 0.0:
        raise ValueError(f"sigma argument must be None or > 0, not {sigma:g}")

    if verbose not in [0, 1, 2, 3, 4, 5]:
        raise ValueError(f"verbose argument must be 0 to 5 (integer), not {verbose}")

    if rateaxis not in ["x", "y"]:
        raise ValueError(f"rateaxis argument must be 'x' or 'y', not '{rateaxis}'")

    # Let the user know what arguments are being used
    #
    if verbose > 0:
        print("Parameters used to clean the lightcurve are:")
        print(f"  script version = {__revision}")
        print(f"  mean           = {mean}")
        print(f"  clip           = {clip:g}")
        if sigma is None:
            print(f"  scale          = {scale:g}")
        else:
            print(f"  sigma          = {sigma:g}")
        print(f"  minfrac        = {minfrac:g}")
        if outfile is not None:
            print(f"  outfile        = {outfile}")
        print(f"  plot           = {plot}")
        if plot:
            print(f"  rateaxis       = {rateaxis}")
            print(f"  color          = {gcol}")
            if outfile is not None:
                print(f"  pattern        = {pattern}")
                if pattern != "none":
                    print(f"  pattern color  = {pcol}")
        print("")

    lc = CleanLightCurve(filename, verbose=verbose)
    lc.calculate_filter(mean=mean, clip=clip, sigma=sigma, scale=scale)

    if plot:
        axs = lc.plot(rateaxis=rateaxis, gcol=gcol, erase=erase)

    # Check that we have enough data points
    #
    lc.check_valid(minfrac)

    # Calculate the GTI file if required. We calculate the limits
    # whether the file is to be created or not so as to get
    # screen output
    #
    lc.calculate_gti_filter()

    if outfile is not None:
        lc.create_gti_file(outfile)

        if plot:
            try:
                lc.plot_gti_limits(axs, outfile, rateaxis=rateaxis,
                                   pattern=pattern, pcol=pcol)
            except ValueError:
                pass


def _lc_sigma_clip(obj, lbl, filename, outfile=None, sigma=3.0,
                   minlength=3, plot=True,
                   rateaxis="y", pattern="solid", gcol="lime",
                   pcol="red", erase=True,
                   verbose=1):
    """
    This is the return used by lc_sigma_clip and lc_sigma_uclip. See
    those routines for help.

    The obj argument is the class to use - SigmaClipLightCurve or
    SigmaUpperClipLightCurve. lbl is used in the screen output for the
    clipping line, and is expected to be "symmetric" or "upper".
    """

    # Check the arguments
    #
    if sigma <= 0.0:
        raise ValueError(f"sigma argument must be > 0, not {sigma:g}")

    minlength = int(minlength)  # deflare sends in a float rather than an int
    if minlength < 1:
        raise ValueError(f"minlength argument must be >= 1, not {minlength:d}")

    if verbose not in [0, 1, 2, 3, 4, 5]:
        raise ValueError(f"verbose argument must be 0 to 5 (integer), not {verbose}")

    if rateaxis not in ["x", "y"]:
        raise ValueError(f"rateaxis argument must be 'x' or 'y', not '{rateaxis}'")

    # Let the user know what arguments are being used
    #
    if verbose > 0:
        print("Parameters used to clean the lightcurve are:")
        print(f"  script version = {__revision}")
        print(f"  clipping       = {lbl}")
        print(f"  sigma          = {sigma:g}")
        print(f"  minlength      = {minlength:d}")
        if outfile is not None:
            print(f"  outfile        = {outfile}")
        print(f"  plot           = {plot}")
        print(f"  rateaxis       = {rateaxis}")
        print(f"  color          = {gcol}")
        if outfile is not None:
            print(f"  pattern        = {pattern}")
            if pattern != "none":
                print(f"  pattern color  = {pcol}")
        print("")

    lc = obj(filename, verbose=verbose)
    lc.calculate_filter(sigma=sigma, minlength=minlength)

    if plot:
        axs = lc.plot(rateaxis=rateaxis, gcol=gcol, erase=erase)

    # Calculate the GTI file if required. We calculate the limits
    # whether the file is to be created or not so as to get
    # screen output
    #
    lc.calculate_gti_filter(minlength=minlength)
    if outfile is not None:
        lc.create_gti_file(outfile)

        if plot:
            try:
                lc.plot_gti_limits(axs, outfile, rateaxis=rateaxis,
                                   pattern=pattern, pcol=pcol)
            except ValueError:
                pass


def lc_sigma_clip(filename, outfile=None, sigma=3.0, minlength=3, plot=True,
                  rateaxis="y", pattern="solid", gcol="lime",
                  pcol="red", erase=True,
                  verbose=1):
    """Calculate good times for a light curve by performing an iterative
    sigma-clip on the count rate column of filename, where points are
    rejected whether they are larger or smaller than the mean.

    The sigma parameter determines which points are to be rejected at
    each iteration (reject if they are more than sigma times the
    standard deviation away from the mean).

    The minlength parameter determines the minimum number of consecutive
    time bins that must all pass the rate filter for the period to be
    considered 'good'. This parameter is not used within the
    sigma-clipping iteration. If minlength=1 then a filter on the count
    rate is determined instead.

    If plot is True then plots of the light curve and histograms of the
    values will be displayed. The rateaxis option determines whether the
    topl plot is drawn as count-rate on the y axis and time on the x axis
    (rateaxis='y') or the other way around (rateaxis='x'). The gcol
    parameter gives the color to use to draw points/histograms of the
    points that are considered good by the iterative clipping (ignoring
    the minlength filter).

    The erase argument is no-longer used.

    If outfile is given and plot is True then the time intervals excluded
    by the calculated GTI file are drawn on the plot as filled regions,
    using the pattern and color determined by the pattern and pcol options
    (setting pattern to 'none' stops this display).

    The verbose parameter can be set to 0, 1, 2, 3, 4, or 5 - although
    the main difference is 0 (none) and not-zero (the only place verbose
    is relevant beyond this is when calling dmgti).

    """

    _lc_sigma_clip(SigmaClipLightCurve, "symmetric",
                   filename, outfile=outfile, sigma=sigma,
                   minlength=minlength, plot=plot,
                   rateaxis=rateaxis, pattern=pattern, gcol=gcol,
                   pcol=pcol, erase=erase,
                   verbose=verbose)


def lc_sigma_uclip(filename, outfile=None, sigma=3.0, minlength=3, plot=True,
                   rateaxis="y", pattern="solid", gcol="lime",
                   pcol="red", erase=True,
                   verbose=1):
    """Calculate good times for a light curve by performing an iterative
    sigma-clip on the count rate column of filename, where only
    those points that are greater than the mean are rejected.
    Use lc_sigma_clip() for symmetric clipping.

    *** THIS HAS NOT BEEN TESTED ON MANY DATASETS AND IS PROVIDED
    *** AS AN EXPERIMENTAL FEATURE. ITS BEHAVIOR MAY CHANGE AT ANY TIME.

    If outfile is set then a GTI file will be created representing
    these times.

    The sigma parameter determines which points are to be rejected at
    each iteration: reject if they are more than sigma times the
    standard deviation away from the mean, and only reject those points
    that are greater than the mean.

    The minlength parameter determines the minimum number of consecutive
    time bins that must all pass the rate filter for the period to be
    considered 'good'. This parameter is not used within the
    sigma-clipping iteration. If minlength=1 then a filter on the count
    rate is determined instead.

    If plot is True then plots of the light curve and histograms of the
    values will be displayed. The rateaxis option determines whether the
    topl plot is drawn as count-rate on the y axis and time on the x axis
    (rateaxis='y') or the other way around (rateaxis='x'). The gcol
    parameter gives the color to use to draw points/histograms of the
    points that are considered good by the iterative clipping (ignoring
    the minlength filter).

    The erase argument is no-longer used.

    If outfile is given and plot is True then the time intervals excluded
    by the calculated GTI file are drawn on the plot as filled regions,
    using the pattern and color determined by the pattern and pcol options
    (setting pattern to 'none' stops this display).

    The verbose parameter can be set to 0, 1, 2, 3, 4, or 5 - although
    the main difference is 0 (none) and not-zero (the only place verbose
    is relevant beyond this is when calling dmgti).

    """

    _lc_sigma_clip(SigmaUpperClipLightCurve, "upper",
                   filename, outfile=outfile, sigma=sigma,
                   minlength=minlength, plot=plot,
                   rateaxis=rateaxis, pattern=pattern, gcol=gcol,
                   pcol=pcol, erase=erase,
                   verbose=verbose)

# End
