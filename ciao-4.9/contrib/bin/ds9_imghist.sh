#! /bin/sh
# 
#  Copyright (C) 2004-2008  Smithsonian Astrophysical Observatory
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



reg=`echo $1 | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
ds9=$2



if test x$reg = x
then
 regions=""
else
 regions="[(x,y)=${reg}]"
fi

cat - | dmimghist -"$regions" - 1 > \
 $ASCDS_WORK_PATH/$$_hist.fits


ds9_plot.py "$ASCDS_WORK_PATH/$$_hist.fits[cols bin,counts]" "Pixel Histogram" $ds9
