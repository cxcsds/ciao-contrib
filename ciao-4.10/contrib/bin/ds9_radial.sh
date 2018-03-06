#! /bin/sh
# 
#  Copyright (C) 2004-2008,2015  Smithsonian Astrophysical Observatory
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


xpa=$1
file=$2

nxpa=`xpaaccess -n ${xpa}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${xpa}'.  Please close the other windows and restart."
  exit 1
fi



\rm -f $ASCDS_WORK_PATH/$$_ds9.reg
xpaget $xpa regions -format ds9 -coord physical | cut -d"#" -f1 | sed 's, *$,,' | \
  awk -f $ASCDS_CONTRIB/config/ds9_region_expand.awk > $ASCDS_WORK_PATH/$$_ds9.reg

dmextract "${file}[bin sky=@$ASCDS_WORK_PATH/$$_ds9.reg]" - op=generic | \
  dmtcalc - - expr="radius=r[0]" > \
  $ASCDS_WORK_PATH/$$_radial.fits

ds9_plot.py "$ASCDS_WORK_PATH/$$_radial.fits[cols radius,sur_bri]" "Radial Profile" $xpa


\rm -f $ASCDS_WORK_PATH/$$_ds9.reg

exit 0
