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


stat=$1
axis=$2

_r=`echo "$3" | egrep ^@`
if test x$_r = x
then
  reg=`echo "$3" | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
else
  _r=`echo $_r | tr -d @`
  reg=`cat $_r | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
fi

ds9=$4



if test x$reg = x
then
 regions=""
else
 regions="[(x,y)=${reg}]"
fi



cat - | dmimgproject -"${regions}" - $axis > \
  $ASCDS_WORK_PATH/$$_project.fits


ds9_plot.py "$ASCDS_WORK_PATH/$$_project.fits[cols ${axis},${stat}]" "Project ${stat} Profile" $ds9

