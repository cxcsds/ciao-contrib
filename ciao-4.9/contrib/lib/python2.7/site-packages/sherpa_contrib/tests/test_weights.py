#
#  Copyright (C) 2016
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

"""
Test routines for the weighted exposure map code in
sherpa_contrib.utils.
"""

import unittest

import numpy as np

from sherpa.astro import ui
from sherpa.utils.err import IdentifierErr

from sherpa_contrib import utils

import sys
sys.tracebacklimit = 4


class TestSimple(unittest.TestCase):
    """Basic tests"""

    def setUp(self):
        ui.dataspace1d(0.01, 11, 0.01, id=1)
        ui.dataspace1d(2, 5, 0.1, id="tst")
        ui.dataspace1d(0.1, 1, 0.1, id="not-used")

        # self.nbins = {}
        # for idval in [1, 'tst']:
        #     self.nbins[idval] = ui.get_data(1).xlo.size
        self.nbins = {1: 1099, 'tst': 30}

        ui.set_source(1, ui.powlaw1d.pl1)
        ui.set_source("tst", ui.powlaw1d.pltst)

        # when gamma=0, weight is the same for each bin (when equally
        # spaced)
        pl1.gamma = 0.0
        pl1.ampl = 1.2
        pltst.gamma = -1.0
        pltst.ampl = 2.1

        arfgrid = np.arange(0.5, 5, 0.02)
        self.arflo = arfgrid[:-1]
        self.arfhi = arfgrid[1:]
        self.flatarf = self.arflo * 0 + 10.1
        amid = (self.arflo + self.arfhi) / 2.0
        self.arf = 10 - (3.0 - amid)**2

    def tearDown(self):
        # there's an issue in CIAO 4.8 with delete_model and
        # delete_model_component, so just call clean
        """
        for idval in [1, "tst"]:
            ui.delete_model(id=idval)
            ui.delete_model_component("pl{}".format(idval))
            ui.delete_data(id=idval)

        ui.delete_data(id="not-used")
        """
        ui.clean()

    def test_invalid_id(self):
        self.assertRaises(IdentifierErr, utils.get_instmap_weights,
                          'nonsense')

    def test_no_source(self):
        self.assertRaises(IdentifierErr, utils.get_instmap_weights,
                          id='not-used')

    def test_invalid_fluxtype(self):
        self.assertRaises(ValueError, utils.get_instmap_weights,
                          fluxtype='nonsense')

    def check_spacing(self, wgt, nbins, lo, hi, step):
        xlo = wgt.xlo
        xhi = wgt.xhi
        xmid = wgt.xmid
        self.assertEqual(nbins, xlo.size)
        self.assertEqual(xlo.size, xhi.size)
        self.assertEqual(xlo.size, xmid.size)
        self.assertAlmostEqual(lo, xlo[0])
        self.assertAlmostEqual(hi, xhi[-1])
        self.assertAlmostEqual(step, (xmid[-1] - xmid[0]) /
                               (xlo.size - 1))

    def test_grid1(self):
        wgt = utils.get_instmap_weights()
        self.check_spacing(wgt, self.nbins[1], 0.01, 11.0, 0.01)

    def test_grid1_erg(self):
        wgt = utils.get_instmap_weights(fluxtype='erg')
        self.check_spacing(wgt, self.nbins[1], 0.01, 11.0, 0.01)

    def test_gridtst(self):
        wgt = utils.get_instmap_weights('tst')
        self.check_spacing(wgt, self.nbins['tst'], 2.0, 5.0, 0.1)

    def test_gridtst_erg(self):
        wgt = utils.get_instmap_weights('tst', fluxtype='erg')
        self.check_spacing(wgt, self.nbins['tst'], 2.0, 5.0, 0.1)

    def test_sum1(self):
        wgt = utils.get_instmap_weights().weight
        self.assertAlmostEqual(1.0, wgt.sum())
        self.assertAlmostEqual(wgt[0], wgt[-1])
        self.assertEqual(self.nbins[1], wgt.size)

    def test_sumtst(self):
        wgt = utils.get_instmap_weights(id="tst").weight
        self.assertAlmostEqual(1.0, wgt.sum())
        self.assertLess(wgt[0], wgt[-1])
        self.assertEqual(self.nbins['tst'], wgt.size)

    def test_estimate1_flat(self):
        wgt = utils.get_instmap_weights()
        emap = wgt.estimate_expmap(self.arflo, self.arfhi,
                                   self.flatarf)
        self.assertAlmostEqual(self.flatarf[0], emap)

    def test_estimatetst_flat(self):
        wgt = utils.get_instmap_weights('tst')
        emap = wgt.estimate_expmap(self.arflo, self.arfhi,
                                   self.flatarf)
        self.assertAlmostEqual(self.flatarf[0], emap)

    # hard code the answers (so it's a regression test)
    def test_estimate1_flat_erg(self):
        wgt = utils.get_instmap_weights(fluxtype='erg')
        emap = wgt.estimate_expmap(self.arflo, self.arfhi,
                                   self.flatarf)
        self.assertAlmostEqual(1145127079.8190367, emap)

    def test_estimatetst_flat_erg(self):
        wgt = utils.get_instmap_weights('tst', fluxtype='erg')
        emap = wgt.estimate_expmap(self.arflo, self.arfhi,
                                   self.flatarf)
        self.assertAlmostEqual(1697319264.8564615, emap)

    def test_estimate1(self):
        wgt = utils.get_instmap_weights()
        emap = wgt.estimate_expmap(self.arflo, self.arfhi,
                                   self.arf)
        self.assertAlmostEqual(3.9091039, emap)

    def test_estimatetst(self):
        wgt = utils.get_instmap_weights('tst')
        emap = wgt.estimate_expmap(self.arflo, self.arfhi,
                                   self.arf)
        self.assertAlmostEqual(8.7867857, emap)


if __name__ == "__main__":
    unittest.main()
