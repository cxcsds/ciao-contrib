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


ds9=$1
meth=$2

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi



xpaget $ds9 regions -format ciao -system physical | egrep -v "^#" | \
  egrep polygon > $ASCDS_WORK_PATH/$$_poly.reg

np=`wc -l  $ASCDS_WORK_PATH/$$_poly.reg | awk '{print $1}'`
if test "$np" -eq 0
then
  echo "# ---------------------"
  echo "ERROR:  No polygon regions found"
  exit 1
fi


dmmakereg region="region($ASCDS_WORK_PATH/$$_poly.reg)" \
  outfile=$ASCDS_WORK_PATH/$$_poly.fits ker=fits

dmimgpick $ASCDS_WORK_PATH/$$_poly.fits"[cols x,y]" - - $meth | \
  dmlist - data,clean,array


\rm -f $ASCDS_WORK_PATH/$$_poly.fits $ASCDS_WORK_PATH/$$_poly.reg

exit 0
