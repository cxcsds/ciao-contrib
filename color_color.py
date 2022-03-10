#!/usr/bin/env python

#
# Copyright (C) 2017, 2019 Smithsonian Astrophysical Observatory
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""Color Color Plot maker

Creates a plot showing how model parameters affect hardness ratios
given a user supplied ARF and RMF.

"""

import numpy as np
import sherpa.astro.ui as ui

# import sys must follow sherpa (sorry pylint)
import sys
sys.tracebacklimit = 999


__all__ = ["EnergyBand", "ModelParameter", "HardnessRatioAxis",
           "ColorColor", "ColorColorDiagram"]


def make_acis_diagonal_rmf(arf):
    """
    Create a diagonal RMF for ACIS dataset to match an ARF.


    I could probably do this directly in energy in which case
    I would need to use an RMF; but right now I'm working
    in channel space so I do.  But they can be a POS to make/match
    to the ARF so let's just use a diagonal matrix.

    """

    from sherpa.astro.data import DataRMF
    from sherpa.astro.instrument import RMF1D

    acis_gain = 0.0146   # keV per channel
    detchans = 1024

    elo = arf.energ_lo
    ehi = arf.energ_hi
    _emid = [(a+b)/2 for a, b in zip(elo, ehi)]

    n_energies = len(elo)

    n_grp = [1]*n_energies
    n_chan = [1]*n_energies
    matrix = np.array([1.0]*n_energies)
    f_chan = [int(e/acis_gain)+1 for e in _emid]

    eb_lo = np.arange(detchans)*acis_gain
    eb_hi = eb_lo + acis_gain
    eb_lo[0] = 0.001

    _rmf = DataRMF("diagonal", detchans, elo, ehi, n_grp, f_chan,
                   n_chan, matrix, 0, eb_lo, eb_hi, None)

    rmf = RMF1D(_rmf)
    return rmf


class EnergyBand():
    """Something to hold all the energy band specific stuff

    The energy band is defined by the low energy cutoff, high energy
    cutoff, and a label to be use eg when plotting.

    >>> broad = EnergyBand(0.5, 7.0, "B")
    """

    def __init__(self, lo, hi, token):
        self._lo = lo
        self._hi = hi
        self._token = token

    @property
    def lo(self):
        'Lowe energy limit'
        return self._lo

    @property
    def hi(self):
        'Upper energy limit'
        return self._hi

    @property
    def token(self):
        'Label to use for columns and plots'
        return self._token


class ModelParameter():
    """Hold info about each model parameter that is to be varied

    parameter_object should be a sherpa model parameter

    >>> type(abs1.nH)
           sherpa.models.parameter.Parameter

    parameter_value_grid is grid of values to iterate over.

    Example:

    >>> absorption = ModelParameter(abs1.nH, [0.001, 0.01, 0.1, 0.2, 0.5, 1, 10])

    will evalue the abs1.nH parameter on the grid of 7 values.

    """

    def __init__(self, parameter_object, parameter_value_grid, fine_grid_resolution=20):
        """
        Store the model parameter information
        """
        self._pobj = parameter_object
        self._pgrid = parameter_value_grid
        self._fine_grid_resolution = fine_grid_resolution
        self._lab_style = {"color": "black"}
        self._curve_style = {"color": "black", "linestyle": "-"}

    def finegrid(self):
        """
        This is a simple linear interpolation -- you could replace w/
        more fancy function but this is good enough for plotting methinks.
        """
        x_in = np.arange(len(self._pgrid))
        x_tmp = np.arange(self._fine_grid_resolution*len(self._pgrid))
        x_out = x_tmp/float(self._fine_grid_resolution)

        y_out = np.interp(x_out, x_in, self._pgrid)

        ymax = self._fine_grid_resolution*(len(self._pgrid)-1)+1

        return y_out[0:ymax]

    @property
    def obj(self):
        'The parameter object'
        return self._pobj

    @property
    def grid(self):
        'The parameter grid'
        return self._pgrid

    @property
    def curve_style(self):
        "Get the curve style for plotting"
        return self._curve_style

    @property
    def label_style(self):
        "Get the label style for plotting"
        return self._lab_style

    def set_curve_style(self, **style):
        "Set the curve style for plotting"
        self._curve_style = style

    def set_label_style(self, **style):
        "Set the label style for plotting"
        self._lab_style = style


class HardnessRatioAxis():
    """The X or Y axis to be plotted

    This object contains that energy limits for the band being
    compute, the energy limits for the Total (ie denominator),
    and a function used to compute the X-coordinate, ie hardness ratio
    in the input band


    >>> soft = EnergyBand(0.5, 1.2, "S")
    >>> medium = EnergyBand(1.2, 2.0, "M")
    >>> total = None
    >>> fluxfunc = lambda lo,hi: (hi-lo)
    >>> axis = HardnessRatioAxis(soft, medium, total, fluxfunc)

    """

    def __init__(self, lo, hi, total, fluxfunc):
        self.soft = lo
        self.hard = hi
        self.total = total
        self.fluxfunc = fluxfunc

    def __call__(self):
        """
        Compute the hardness ratio
        """
        hard = self.fluxfunc(self.hard.lo, self.hard.hi)
        soft = self.fluxfunc(self.soft.lo, self.soft.hi)

        if self.total is None:
            total = hard+soft
        else:
            total = self.fluxfunc(self.total.lo, self.total.hi)

        hr = (hard-soft)/total

        return hr, hard, soft

    @property
    def label(self):
        """
        Create the label for the axis from the band info
        """
        numerator = "({}-{})".format(self.hard.token, self.soft.token)
        if self.total is None:
            denominator = "({}+{})".format(self.hard.token, self.soft.token)
        else:
            denominator = self.total.token

        label = "{}/{}".format(numerator, denominator)
        return label


class ColorColor():
    """
    Create a color-color diagram for a given model, parameters, and energies

    So the basic idea is this

    : create a sherpa model
    : pick 2 parameters.
    : for each parameter pick a grid to evaluate it over. This gives us
    : a 2D grid in model-parameter space.

    : For each point in the 2D grid:
    :   fake() a spectrum using the model parameters at that location
    :   compute the hardness ratio in 2 energy ranges:  hard_to_medium
        and medium_to_soft.
    :
    : use the 2 HR values as the x,y values and draw lines connecting
    : constant model parameter values.

    The point of doing this is that you may not have enough counts to
    get a good model fit, but by putting your datapoint on top of this
    kind of color-color plot w/ an assumed spectral model shape, then you can
    guestimate the actual model parameter w/o needing to fit the data.

    Example:

    >>> mymodel = xswabs.abs1 * xspowerlaw.pwrlaw
    >>> arffile = "acissD2006-10-26pimmsN0009.fits"
    >>> cc = ColorColor(mymodel, arffile)

    To then compute the HR values, we need to pick our
    energy bands, and which model parameters+grid to evalute over

    >>> pho_grid = [1., 2., 3., 4.]
    >>> photon_index = ModelParameter(pwrlaw.PhoIndex, pho_grid)

    >>> sg = [1.e20, 1.e21, 2.e21, 5.e21, 1.e22, 1e23]
    >>> nh_grid = [x/1e22 for x in sg]
    >>> absorption = ModelParameter(abs1.nH, nh_grid)

    >>> soft = EnergyBand(0.5, 1.2, 'S')
    >>> medium = EnergyBand(1.2, 2.0, 'M')
    >>> hard = EnergyBand(2.0, 7.0, 'H')
    >>> broad = EnergyBand(0.5,7.0, 'B')

    >>> cc = ColorColor(mymodel, arffile)
    >>> matrix = cc(photon_index, absorption, soft, medium, hard, broad)
    >>> matrix.plot()
    """

    _dataset_id = "color_color"

    def __init__(self, model, arffile, rmffile=None, axis_class=HardnessRatioAxis):
        """Create the ColorColor object

        This store the needed data, and creates the sherpa dataset that
        will be used to fake the specturm.

        You can define you own "HardnessRatio" metric by providing a
        different HardnessRatioAxis class.
        """
        self.model = model
        self.arffile = arffile
        self.rmffile = rmffile
        self._load()
        self.make_axis = axis_class

    def _load(self):
        """
        Setup sherpa dataset, set model, arf, rmf

        OK -- I'm using 1024 channels here.  That is acis-specific
        but it shouldn't matter that much eg if one were to use
        HRC, esp if using a diagonal RMF.


        TODO:
        I could probably re-write this to use a different dstype
        which would not require an RMF at all; just need to pull
        the grid from the ARF and probably need to load it as a
        table model scaling the rest of the model.

        """
        ui.dataspace1d(1, 1024, id=self._dataset_id, dstype=ui.DataPHA)
        ui.set_model(self._dataset_id, self.model)

        self.model = ui.get_source(self._dataset_id)

        ui.load_arf(self._dataset_id, self.arffile)
        arf = ui.get_arf(self._dataset_id)
        if self.rmffile is None:
            rmf = make_acis_diagonal_rmf(arf)
            ui.set_rmf(self._dataset_id, rmf)
        else:
            ui.load_rmf(self._dataset_id, self.rmffile)

    def _setx(self, soft_band, hard_band, total_band):
        """Compute the HR for the X-axis"""
        self.xx = self.make_axis(soft_band, hard_band, total_band, self.sum)

    def _sety(self, soft_band, hard_band, total_band):
        """Compute the HR for the Y-axis"""
        self.yy = self.make_axis(soft_band, hard_band, total_band, self.sum)

    def sum(self, lo, hi):
        """Wrapper around calc_data_sum to set the right dataset ID"""
        counts = ui.calc_data_sum(lo, hi, id=self._dataset_id)
        return counts

    def fakeit(self):
        """Wrapper around fake() to set right ID"""
        ui.fake(self._dataset_id)

    def iterate(self, pri_obj, sec_obj):
        """Compute the HR for each grid point in the pri_obj grid

        Okay, so forget what I said above.  That's not REALLY how
        this works.

        Instead I realized that we need to geneate a line for
        each specified grid point the user specified but the line
        need to sample the other axis on a finer grid to generate
        a smooth curve.

        So for each axis, I step through the user supplied grid values.
        At each point, I then step through the 2nd parameter on a
        finer grid.  And then what is returned is the x,y values
        for that primary grid point.

        This has to be done twice.  Once with the 1st model parameter
        as "primary", and again with the 2nd model parameter primary.

        """

        retvals = {}

        # Get the fine grid for the secondary axis
        sec_fine_grid = sec_obj.finegrid()

        # Loop over values in the primary axis grid
        for aa in pri_obj.grid:
            # Set sherpa model parameter value
            setattr(pri_obj.obj, "val", aa)

            # Loop over the fine grid on secondary axis
            lx = []
            ly = []
            lhard = []
            lsoft = []
            lmedium = []
            for bb in sec_fine_grid:
                # Set sherpa model parameter value
                setattr(sec_obj.obj, "val", bb)

                # fake the spectrum w/ these model paramters
                self.fakeit()

                # Compute the HR in 2 separate energy bands
                xx, hard, medium = self.xx()
                yy, medium2, soft = self.yy()

                assert medium == medium2, "Whoops"

                # Save the values
                lx.append(xx)
                ly.append(yy)
                lhard.append(hard)
                lsoft.append(soft)
                lmedium.append(medium)

            retvals[aa] = (lx, ly, lhard, lmedium, lsoft)

        return retvals

    def __call__(self, pri_param, sec_param, soft_band, medium_band,
                 hard_band, total_band=None):
        """Compute the ColorColorDiagram values in the specified bands

        The two model parameters (pri_param, sec_param)
        are varied over their respecitive grids and the HR are
        computed in the specified energy bands.

        The X-axis is hard-medium/total
        The Y-axis is medium-soft/total

        total can be None, in which case

        The X-axis is hard-medium/hard+medium
        The Y-axis is medium-soft/medium+soft

        >>> matrix = cc(photon_index, absorption, soft, medium, hard, broad,total=None)

        """

        # Setup the HR axes
        self._setx(medium_band, hard_band, total_band)
        self._sety(soft_band, medium_band, total_band)

        # We loop over the 1st model parameter, varying the 2nd on
        # a fine grid

        retvals = {}
        pri_ret = self.iterate(pri_param, sec_param)
        for v in pri_ret:
            retvals[(v, None)] = pri_ret[v]

        # Then we loop over the 2nd model parameter, varying the 1st
        # on a fine grid.
        sec_ret = self.iterate(sec_param, pri_param)
        for v in sec_ret:
            retvals[(None, v)] = sec_ret[v]

        # And then we save the values so we can plot things separately
        matrix = ColorColorDiagram(retvals, self, pri_param, sec_param, total_band is None)

        return matrix


class ColorColorDiagram():
    """
    Object to plot the color-color diagram
    """

    def __init__(self, values, color_color, pri_param, sec_param, square):
        self.cc = color_color
        self.pri_param = pri_param
        self.sec_param = sec_param
        self.matrix = values
        self.square = square
        self._cr = None

    def get_results(self):
        '''Get all the results so user can do something special with them

        This returns a dictionary with the parameter values,
        the hardness ratios, and the counts in each of the 3 bands.

        >>> matrix = cc(photon_index, absorption, soft, medium, hard, broad)
        >>> results = matrix.get_results()
        >>> print(results.keys())
        dict_keys(['PhoIndex', 'nH', 'HARD_HM', 'HARD_MS', 'H_COUNTS', 'M_COUNTS', 'S_COUNTS'])
        '''
        axis1_name = self.pri_param.obj.name
        axis2_name = self.sec_param.obj.name
        hr1_name = "HARD_HM"
        hr2_name = "HARD_MS"
        soft_name = self.cc.yy.soft.token+"_COUNTS"
        med_name = self.cc.yy.hard.token+"_COUNTS"
        hard_name = self.cc.xx.hard.token+"_COUNTS"

        out_pri = []
        out_sec = []
        out_soft = []
        out_medium = []
        out_hard = []
        out_hm = []
        out_ms = []

        sec_fine_grid = self.sec_param.finegrid()
        pri_fine_grid = self.pri_param.finegrid()

        for a1 in self.pri_param.grid:
            xx = self.matrix[a1, None][0]
            yy = self.matrix[a1, None][1]
            out_pri.extend([a1]*len(xx))
            out_sec.extend(sec_fine_grid)
            out_hm.extend(xx)
            out_ms.extend(yy)
            out_hard.extend(self.matrix[a1, None][2])
            out_medium.extend(self.matrix[a1, None][3])
            out_soft.extend(self.matrix[a1, None][4])

        for a2 in self.sec_param.grid:
            xx = self.matrix[None, a2][0]
            yy = self.matrix[None, a2][1]
            out_pri.extend(pri_fine_grid)
            out_sec.extend([a2]*len(xx))
            out_hm.extend(xx)
            out_ms.extend(yy)
            out_hard.extend(self.matrix[None, a2][2])
            out_medium.extend(self.matrix[None, a2][3])
            out_soft.extend(self.matrix[None, a2][4])

        retval = {axis1_name: out_pri,
                  axis2_name: out_sec,
                  hr1_name: out_hm,
                  hr2_name: out_ms,
                  hard_name: out_hard,
                  med_name: out_medium,
                  soft_name: out_soft}
        return retval

    def _write_columns(self):
        # Column values
        out_pri = []
        out_sec = []
        out_soft = []
        out_medium = []
        out_hard = []
        out_hm = []
        out_ms = []

        sec_fine_grid = self.sec_param.finegrid()
        res = self.sec_param._fine_grid_resolution
        for a1 in self.pri_param.grid:
            xx = self.matrix[a1, None][0]
            yy = self.matrix[a1, None][1]
            hard = self.matrix[a1, None][2]
            medium = self.matrix[a1, None][3]
            soft = self.matrix[a1, None][4]
            pri_grid = [a1]*len(xx)

            assert len(xx) == len(sec_fine_grid)

            # Only write out the results on the user grid -- not on the fine grid.
            out_pri.extend(pri_grid[::res])
            out_sec.extend(sec_fine_grid[::res])
            out_hm.extend(xx[::res])
            out_ms.extend(yy[::res])
            out_hard.extend(hard[::res])
            out_soft.extend(soft[::res])
            out_medium.extend(medium[::res])

        # Create output crate
        from crates_contrib.utils import make_table_crate

        # Column names
        pri_col_name = self.pri_param.obj.name
        sec_col_name = self.sec_param.obj.name
        hm_col_name = "HARD_HM"
        ms_col_name = "HARD_MS"
        colnames = [pri_col_name, sec_col_name,
                    self.cc.yy.soft.token+"_COUNTS",
                    self.cc.yy.hard.token+"_COUNTS",
                    self.cc.xx.hard.token+"_COUNTS",
                    hm_col_name, ms_col_name]

        out_cr = make_table_crate(out_pri, out_sec,
                                  out_soft, out_medium, out_hard,
                                  out_hm, out_ms,
                                  colnames=colnames)

        self._cr = out_cr

    def _write_keywords(self, toolname):
        # Add a bunch of meta-data
        from pycrates import set_key
        from os.path import basename
        set_key(self._cr, "SHRPAVER", ui._sherpa_version_string)
        set_key(self._cr, "MODEL", self.cc.model.name)
        set_key(self._cr, "ARFFILE", basename(self.cc.arffile))

        if self.cc.rmffile is None:
            set_key(self._cr, "RMFFILE", "NONE", desc="diagnonal RMF was used")
        else:
            set_key(self._cr, "RMFFILE", basename(self.cc.rmffile))

        set_key(self._cr, "HMCOL", self.cc.xx.label)
        set_key(self._cr, "MSCOL", self.cc.yy.label)

        set_key(self._cr, "SBAND_LO", self.cc.yy.soft.lo, unit="keV",
                desc="{} band low energy".format(self.cc.yy.soft.token))
        set_key(self._cr, "SBAND_HI", self.cc.yy.soft.hi, unit="keV",
                desc="{} band high energy".format(self.cc.yy.soft.token))
        set_key(self._cr, "MBAND_LO", self.cc.yy.hard.lo, unit="keV",
                desc="{} band low energy".format(self.cc.yy.hard.token))
        set_key(self._cr, "MBAND_HI", self.cc.yy.hard.hi, unit="keV",
                desc="{} band high energy".format(self.cc.yy.hard.token))
        set_key(self._cr, "HBAND_LO", self.cc.xx.hard.lo, unit="keV",
                desc="{} band low energy".format(self.cc.xx.hard.token))
        set_key(self._cr, "HBAND_HI", self.cc.xx.hard.hi, unit="keV",
                desc="{} band high energy".format(self.cc.xx.hard.token))

        if self.cc.xx.total is not None:
            set_key(self._cr, "BBAND_LO", self.cc.xx.total.lo, unit="keV",
                    desc="Total {} band low energy".format(self.cc.xx.total.token))
            set_key(self._cr, "BBAND_HI", self.cc.xx.total.hi, unit="keV",
                    desc="Total {} band high energy".format(self.cc.xx.total.token))

        set_key(self._cr, "CREATOR", toolname)

    def write(self, outfile, toolname="color_color"):
        """
        Write out the results
        """
        self._write_columns()
        self._write_keywords(toolname)
        self._cr.write(outfile, clobber=True)

    def plot(self, outfile=None):
        """
        Plot the color-color diagram -- now using matplotlib

        Since this object contains a refernce to the primary and
        secondary parameters, you can set/change the curve and
        label properties before plotting:

        >>> matrix = cc(photon_index, absorption, soft, medium, hard, broad)
        >>> photon_index.set_curve_style(marker="", color="green", linestyle="-", linewidth=2)
        >>> photon_index.set_label_style(color="green")
        >>> absorption.set_curve_style(marker="", color="black", linestyle="-.")
        >>> absorption.set_label_style(color="black")
        >>> matrix.plot()
        """
        import matplotlib.pylab as plt

        # Plot 1st model parameter curves
        for a1 in self.pri_param.grid:
            xx = self.matrix[a1, None][0]
            yy = self.matrix[a1, None][1]

            plt.plot(xx, yy, **self.pri_param.curve_style)

            if a1 == self.pri_param.grid[-1]:
                lab = "{}={}".format(self.pri_param.obj.name, a1)
            else:
                lab = "{}".format(a1)

            plt.text(xx[0], yy[0], lab, **self.pri_param.label_style)

        # Plot 2nd model parameter curves
        for a2 in self.sec_param.grid:
            xx = self.matrix[None, a2][0]
            yy = self.matrix[None, a2][1]
            plt.plot(xx, yy, **self.sec_param.curve_style)

            if a2 == self.sec_param.grid[-1]:
                lab = "{}={}".format(self.sec_param.obj.name, a2)
            else:
                lab = "{}".format(a2)
            plt.text(xx[0], yy[0], lab, **self.sec_param.label_style)

        # Add labels and limits
        plt.xlim(-1.1, 1.1)
        plt.ylim(-1.1, 1.1)

        plt.gca().set_aspect('equal', 'box')

        plt.xlabel(self.cc.xx.label)
        plt.ylabel(self.cc.yy.label)
        plt.title("{} :: {}".format(self.cc.model.name, self.cc.arffile))

        if self.square:
            px, py = ([-1, 1, 1, -1], [-1, -1, 1, 1])
        else:
            px, py = ([1, -1, 0], [0, 1, -1])
        plt.fill(px, py, color="lightgray")

        if outfile is not None:
            plt.savefig(outfile)


def test():
    'Run test routine'

    #
    # Define energy bands
    #
    soft = EnergyBand(0.5, 1.2, 'S')
    medium = EnergyBand(1.2, 2.0, 'M')
    hard = EnergyBand(2.0, 7.0, 'H')

    #
    # Define model
    #
    mymodel = ui.xswabs.abs1 * ui.xspowerlaw.pwrlaw
    arffile = "acissD2006-10-26pimmsN0009.fits"

    #
    # First model parameter axis
    #
    pho_grid = [1., 2., 3., 4.]
    photon_index = ModelParameter(pwrlaw.PhoIndex, pho_grid, fine_grid_resolution=20)

    #
    # Second model parameter axis
    #
    sg = [1.e20, 1.e21, 2.e21, 5.e21, 1.e22, 1e23]
    nh_grid = [x/1e22 for x in sg]
    absorption = ModelParameter(abs1.nH, nh_grid, fine_grid_resolution=20)

    #
    # Get to work.
    #
    ao09 = ColorColor(mymodel, arffile)
    matrix_09 = ao09(photon_index, absorption, soft, medium, hard)

    ao19 = ColorColor(mymodel, "acissD2016-11-22pimmsN0019.fits")
    matrix_19 = ao19(photon_index, absorption, soft, medium, hard)

    photon_index.set_curve_style(marker="", linestyle="-", linewidth=2, color="black")
    photon_index.set_label_style(color="black")
    absorption.set_curve_style(marker="", linestyle="-", linewidth=2, color="forestgreen")
    absorption.set_label_style(color="forestgreen")

    matrix_09.plot()
    import matplotlib.pylab as plt
    plt.show()

    matrix_09.write('foo.fits')

    matrix_19.plot()
    plt.show()
