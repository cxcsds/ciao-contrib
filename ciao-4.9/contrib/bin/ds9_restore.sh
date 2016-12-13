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



ds9=$1

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi



_r=`echo "$2" | egrep ^@`
if test x$_r = x
then
  reg=`echo "$2" | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
else
  _r=`echo $_r | tr -d @`
  reg=`cat $_r | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
fi


xpaget $ds9 fits | dmcopy "-[(x,y)=$reg]" $ASCDS_WORK_PATH/$$_psf.fits clob+
xpaget $ds9 fits | arestore - $ASCDS_WORK_PATH/$$_psf.fits - 20 | \
  xpaset $ds9 fits new

\rm -f $ASCDS_WORK_PATH/$$_psf.fits


exit 0
