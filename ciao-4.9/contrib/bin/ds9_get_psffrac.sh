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
eng=$2

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi





calquiz none chandra default reef CALDB > /dev/null 2>&1

cal=`pget calquiz outfile | cut -d"[" -f1`

if test x$cal = x
then
  echo "Could not find necessary CALDB file.  Sorry"
  exit 1
fi


myreg=`xpaget ${ds9} regions selected -system wcs -skyformat degrees -strip | tr ";" "\012" | egrep "circle|ellipse|box|annulus" | tail -1 | tr "(),"'"'  " " `


if test "x$myreg" = x
then
  echo "Please select a single region. Make sure only a circle, ellipse, or box shapes is selected"
  exit 1
fi


rr=`echo $myreg | awk ' $1 == "circle" { print $4 } \
		        $1 == "ellipse" {print sqrt( $4*$4 + $5+$5 )} \
		        $1 == "box" {print sqrt( $4*$4 + $5+$5 )} '`

ra=`echo $myreg | cut -d" " -f2`
dec=`echo $myreg | cut -d" " -f3`

f=`xpaget $ds9 file `

punlearn dmcoords 
dmcoords "${f}" asol= op=cel ra=$ra dec=$dec mode=h celfmt=deg verb=0 > /dev/null 2>&1

theta=`pget dmcoords theta`
phi=`pget dmcoords phi`


frac=`cat <<EOF | $ASCDS_INSTALL/bin/python 
from psf import *
pp=psfInit("${cal}")
ff=psfFrac(pp, ${eng}, ${theta}, ${phi}, ${rr})
print(ff)
EOF
`


printf 'frac=%g\tr_mean=%g"\tenergy=%g keV\ttheta=%g'"'"'\tphi=%g deg\n---\n' \
  $frac $rr $eng $theta $phi   


 
exit 0

