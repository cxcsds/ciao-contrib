#
#  Copyright (C) 2009-2010, 2011, 2016, 2019
#        Smithsonian Astrophysical Observatory
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
Contributed CIAO routines from the CXC.

This module loads in the following packages

  crates_contrib
  sherpa_contrib

as well as

  ciao_contrib.caldb
  ciao_contrib.region.all
  ciao_contrib.smooth
  ciao_contrib.stacklib
  ciao_contrib.utils

Note that the ciao_contrib.runtool module is not loaded
by this module.
"""

from __future__ import absolute_import

from crates_contrib.all import *
from sherpa_contrib.all import *

from .caldb import *
from .smooth import *
from .stacklib import *
from .region.all import *
from .utils import *
