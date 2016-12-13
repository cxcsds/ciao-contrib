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
frac=$3

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
  echo "Missing necessary CALDB file"
  exit 1
fi


if test `xpaget $ds9 mode` = crosshair
then

  x=`xpaget $ds9 crosshair -system physical -skyformat degrees | awk '{print $1}'`
  y=`xpaget $ds9 crosshair -system physical -skyformat degrees | awk '{print $2}'`

else

  x=`xpaget $ds9 regions selected -format ciao -system physical -strip | tr ";" "\012" | tail -1 | tr "()," " " | cut -d" " -f2`
  y=`xpaget $ds9 regions selected -format ciao -system physical -strip | tr ";" "\012" | tail -1 | tr "()," " " | cut -d" " -f3`
fi


if test x$x = x
then
  echo "ERROR getting coordinates"
  exit 1
fi

if test x$y = x
then
  echo "ERROR getting coordinates"
  exit 1
fi




f=`xpaget $ds9 file `

punlearn dmcoords
dmcoords "${f}" op=sky x=$x y=$y mode=h celfmt=deg verb=0 asol=

theta=`pget dmcoords theta`
phi=`pget dmcoords phi`
ra=`pget dmcoords ra`
dec=`pget dmcoords dec`



rad=`cat <<EOF | $ASCDS_INSTALL/bin/python 
from psf import *
pp=psfInit("${cal}")
ff=psfSize(pp, ${eng}, ${theta}, ${phi}, ${frac})
print(ff)
EOF
`




echo 'fk5; circle '$ra $dec $rad'" # tag={psfsize} tag={frac='${frac}'} tag={eng='${eng}'}' | xpaset $ds9 regions -format ds9

exit 0

