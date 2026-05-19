#
#  Copyright (C) 2025-2026
#            MIT
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
from caldb4 import Caldb
from pycrates import read_file

caldb = Caldb(telescope="Chandra", instrume="", product="GEOM")
for f in caldb.search:
    # ephin/geom/ephinD1999-07-22geomNXXX is also found that way, but that's not the one we want
    if "tel" in f:
        break
    else:
        raise ValueError("Could not find geom file in CALDB")

geom = read_file(f.split("[")[0] + "[GRATINGS]")

tg_part_name = ["zeroth order", "heg", "meg", "leg"]

X_R = {}
Period = {}
Alpha = {}

for arm in tg_part_name[1:]:
    row = (
        (geom.INSTRUMENT.values == "ACIS") & (geom.GRATING_ARM.values == arm.upper())
    ).nonzero()[0][0]
    X_R[arm] = geom.ROWLAND.values[row]
    Period[arm] = geom.PERIOD.values[row]
    Alpha[arm] = geom.ALPHA.values[row]

mm_per_pix = 0.023987  # pixel size in mm for acis same for I and S
arcsec_per_pix = 0.492  # arcsec per pixel for ACIS

hc = 4.1357e-15 * 2.998e18
"conversion for E = hc/lamda where h and c are units of plancks const and angstrom/s"

wavelength_scale = {
    arm: mm_per_pix / X_R[arm] * Period[arm] for arm in tg_part_name[1:]
}