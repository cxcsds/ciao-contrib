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




coord=$1
ds9=$2

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "ERROR: Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi


punlearn dmcoords

x=`xpaget $ds9 crosshair | awk '{print $1}'`
y=`xpaget $ds9 crosshair | awk '{print $2}'`
f=`xpaget $ds9 file `

ff=`echo "${f}" | cut -d "[" -f1`
if test -e "${ff}"
then
  :
else
  echo "# -------------------"
  echo "ERROR: This tasks only works with files on local disk"
  exit 1
fi



tt=`dmkeypar "${f}" TELESCOP echo+ 2>&1 `
if test "x${tt}" != "xCHANDRA"
then
  echo "# -------------------"
  echo "WARNING: Chandra specific coordinates may be inaccurate for this dataset"
fi


echo "# -------------------"

dmcoords "${f}" op=sky x=$x y=$y mode=h verb=0

case $coord in

  all)
    pdump dmcoords | egrep -v "infile|mode|asolfile|option|EOF"
  ;;

  theta)
    theta=`pget dmcoords theta`
    phi=`pget dmcoords phi`
    echo "Theta = $theta [arcmin]"
    echo "Phi   = $phi [deg]"
   ;;

  chip)
    echo "Chip   =" `pget dmcoords chip_id`
    echo "Chip X =" `pget dmcoords chipx`
    echo "Chip Y =" `pget dmcoords chipy`
   ;;

  phys)
    echo "Physical X =" `pget dmcoords x`
    echo "Physical Y =" `pget dmcoords y`

   ;;
  cel)
    echo "RA  =" `pget dmcoords ra`
    echo "DEC =" `pget dmcoords dec`

   ;;
  log)
    echo "Logical X =" `pget dmcoords logicalx`
    echo "Logical Y =" `pget dmcoords logicaly`
   ;;

  det)
    echo "DET X =" `pget dmcoords detx`
    echo "DET Y =" `pget dmcoords dety`
   ;;


  tdet)
    echo "TDET X =" `pget dmcoords tdetx`
    echo "TDET Y =" `pget dmcoords tdety`
   ;;


esac

echo "# -------------------"
