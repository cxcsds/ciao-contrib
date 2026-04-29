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

# This file holds some constants used throughout criss-cross.
# They are all found in the CALDB, but are unlikely to change and
# are thus hardcoded in this location.
tg_part_name = ["zeroth order", "heg", "meg", "leg"]

X_R = 8632.48  # rowland diameter in mm constant

# period in angstroms constant. Note, this is value from telD1999-07-23geomN0006.fits in CALDB
Period = {
    "meg": 4001.95,  # however in marxsim it uses 4001.41 A
    "heg": 2000.81,
}
mm_per_pix = 0.023987  # pixel size in mm for acis same for I and S
arcsec_per_pix = 0.492  # arcsec per pixel for ACIS

hc = 4.1357e-15 * 2.998e18
"conversion for E = hc/lamda where h and c are units of plancks const and angstrom/s"

wavelength_scale = {arm: mm_per_pix / X_R * Period[arm] for arm in ["heg", "meg"]}