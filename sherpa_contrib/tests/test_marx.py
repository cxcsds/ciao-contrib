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

from sherpa_contrib import marx

import sys
sys.tracebacklimit = 4


class TestSimple(unittest.TestCase):
    """Basic tests"""

    def setUp(self):
        ui.set_source('no-arf-flat', ui.const1d.c1)

    def tearDown(self):
        # there's an issue in CIAO 4.8 with delete_model and
        # delete_model_component, so just call clean
        ui.clean()

    def test_spec_flat(self):
        res = marx.get_marx_spectrum(elow=1., ehigh=4.,
                                     ewidth=1., id='no-arf-flat')
        self.assertTrue(np.all(res[1] == 1))

        # Different bin width
        res = marx.get_marx_spectrum(elow=1., ehigh=4.,
                                     ewidth=.5, id='no-arf-flat')
        self.assertTrue(np.all(res[1] == 1))


if __name__ == "__main__":
    unittest.main()
