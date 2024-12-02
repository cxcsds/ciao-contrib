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
Test routines for the ChART code in
sherpa_contrib.chart.
"""

import unittest

import numpy as np

from sherpa.astro import ui
from sherpa.utils.err import IdentifierErr
from sherpa.astro.data import DataARF, DataPHA


from sherpa_contrib import chart

import sys
sys.tracebacklimit = 4


class TestSimple(unittest.TestCase):
    """Basic tests"""

    def setUp(self):
        ui.dataspace1d(0.2, 10, 0.01, id=1)
        ui.dataspace1d(2, 5, 0.1, id="tst")
        ui.dataspace1d(0.1, 1, 0.1, id="not-used")
        ui.dataspace1d(0.1, 1, 0.1, id="no-arf")

        ui.dataspace1d(0.1, 11, 0.01, id='arf1', dstype=DataPHA)
        ui.dataspace1d(0.2, 10, 0.01, id='flatarf', dstype=DataPHA)

        # self.nbins = {}
        # for idval in [1, 'tst']:
        #     self.nbins[idval] = ui.get_data(1).xlo.size
        self.nbins = {1: 980, 'tst': 30, 'arf1': 1090,
                      'arf1-arf': 489}

        self.grid = {
            1: (0.2, 10, 0.01),
            'tst': (2.0, 5.0, 0.1),
            'arf1': (0.1, 11, 0.01),
            'arf1-arf': (0.2, 9.98, 0.02)  # note: ehigh is not 10.0
            }

        ui.set_source(1, ui.powlaw1d.pl1)
        ui.set_source("tst", ui.powlaw1d.pltst)
        ui.set_source('no-arf', pl1)
        ui.set_source('arf1', pltst)
        ui.set_source('flatarf', pltst)
        ui.set_source('no-arf-flat', ui.const1d.c1)

        pl1.gamma = 0.0
        pl1.ampl = 1.2
        pltst.gamma = -1.0
        pltst.ampl = 2.1

        arfgrid = np.arange(0.2, 10, 0.02)
        arflo = arfgrid[:-1]
        arfhi = arfgrid[1:]
        amid = (arflo + arfhi) / 2.0

        flatarf = DataARF('flat', energ_lo=arflo, energ_hi=arfhi,
                          specresp=arflo * 0 + 10.1)
        arf = DataARF('arf', energ_lo=arflo, energ_hi=arfhi,
                      specresp=20 - (4.5 - amid)**2)
        ui.set_arf('arf1', arf)
        ui.set_arf('flatarf', flatarf)

    def tearDown(self):
        # there's an issue in CIAO 4.8 with delete_model and
        # delete_model_component, so just call clean
        ui.clean()

    def test_invalid_id(self):
        self.assertRaises(IdentifierErr, chart.get_chart_spectrum,
                          'nonsense')

    def test_no_source(self):
        self.assertRaises(IdentifierErr, chart.get_chart_spectrum,
                          id='not-used')

    def test_no_arf(self):
        self.assertRaises(TypeError, chart.get_chart_spectrum,
                          id='no-arf')

    def check_spacing(self, res, nbins, lo, hi, step):
        xlo = res["xlo"]
        xhi = res["xhi"]
        xmid = res["x"]
        self.assertEqual(nbins, xlo.size)
        self.assertEqual(xlo.size, xhi.size)
        self.assertEqual(xlo.size, xmid.size)
        self.assertAlmostEqual(lo, xlo[0])
        self.assertAlmostEqual(hi, xhi[-1])
        self.assertAlmostEqual(step, (xmid[-1] - xmid[0]) /
                               (xlo.size - 1))

    def test_grid1(self):
        elo, ehi, de = self.grid[1]
        res = chart._get_chart_spectrum(elow=elo, ehigh=ehi,
                                        ewidth=de)
        self.check_spacing(res, self.nbins[1], elo, ehi, de)

    def test_gridtst(self):
        elo, ehi, de = self.grid['tst']
        res = chart._get_chart_spectrum(elow=elo, ehigh=ehi,
                                        ewidth=de, id='tst')
        self.check_spacing(res, self.nbins['tst'], elo, ehi, de)

    def test_gridarf(self):
        elo, ehi, de = self.grid['arf1-arf']
        res = chart._get_chart_spectrum(id='arf1')
        self.check_spacing(res, self.nbins['arf1-arf'], elo, ehi, de)

    def test_gridarf_explicit(self):
        elo, ehi, de = self.grid['arf1']
        res = chart._get_chart_spectrum(elow=elo, ehigh=ehi,
                                        ewidth=de, id='arf1')
        self.check_spacing(res, self.nbins['arf1'], elo, ehi, de)

    def test_positive1(self):
        elo, ehi, de = self.grid[1]
        res = chart._get_chart_spectrum(elow=elo, ehigh=ehi,
                                        ewidth=de)
        # self.assertGreater(res['y'].sum(), 0.0)
        self.assertTrue(np.all(res['y'] > 0))

    def test_positivetst(self):
        elo, ehi, de = self.grid['tst']
        res = chart._get_chart_spectrum(elow=elo, ehigh=ehi,
                                        ewidth=de, id='tst')
        # self.assertGreater(res['y'].sum(), 0.0)
        self.assertTrue(np.all(res['y'] > 0))

    def test_positivearf(self):
        res = chart._get_chart_spectrum(id='arf1')
        # self.assertGreater(res['y'].sum(), 0.0)
        self.assertTrue(np.all(res['y'] > 0))

    def test_positivearf_explicit(self):
        elo, ehi, de = self.grid['arf1']
        res = chart._get_chart_spectrum(elow=elo, ehigh=ehi,
                                        ewidth=de, id='arf1')
        # self.assertGreater(res['y'].sum(), 0.0)
        self.assertTrue(np.all(res['y'] > 0))

    def test_spec_flat(self):
        res = chart.get_chart_spectrum(elow=2, ehigh=6,
                                       ewidth=1, id='no-arf-flat')
        self.assertTrue(np.all(res[2] == 1))

if __name__ == "__main__":
    unittest.main()
