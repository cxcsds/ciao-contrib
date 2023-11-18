#! /bin/sh
# 
#  Copyright (C) 2020  Smithsonian Astrophysical Observatory
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
energies=$2
orders=$3


echo "# -------------------"
echo ""
echo `date`
echo ""


nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "ERROR: Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi


if test x`xpaget $ds9 mode` = xcrosshair
then
    x=`xpaget $ds9 crosshair | awk '{print $1}'`
    y=`xpaget $ds9 crosshair | awk '{print $2}'`
else 
    # If region is selected then use it
    reg=`xpaget $ds9 region -format ciao -system physical selected | grep -E 'circle|box|ellipse|annulus' `
    if test x"${reg}" = x
    then
        # Okay, just the 1st region
        reg=`xpaget $ds9 region -format ciao -system physical | grep -E 'circle|box|ellipse|annulus' `
    fi

    if test x"${reg}" = x
    then
        echo "ERROR: Please either use crosshair mode or draw a region"
        exit 1
    fi

    x=`echo "${reg}" | head -1 | tr "()," " " | awk '{print $2}'`
    y=`echo "${reg}" | head -1 | tr "()," " " | awk '{print $3}'`
    
fi



f=`xpaget $ds9 file `

ff=`echo "${f}" | cut -d "[" -f1`
if test -e "${ff}"
then
  :
else
  echo "ERROR: This tasks only works with files on local disk"
  exit 1
fi



tt=`dmkeypar "${f}" TELESCOP echo+ 2>&1 `
if test "x${tt}" != "xCHANDRA"
then
  echo "ERROR: Chandra data is required for this task"
  exit 1
fi


tt=`dmkeypar "${f}" GRATING echo+ 2>&1 `
if test "x${tt}" = "xNONE"
then
  echo "ERROR: Chandra grating data is required for this task"
  exit 1
fi
grt=$tt

# Get zero order in degrees

punlearn dmcoords
dmcoords "${f}" op=sky x=$x y=$y mode=hl celfmt=deg verb=0
razo=`pget dmcoords ra`
deczo=`pget dmcoords dec`


ooo=`stk_build "${orders}" out=stdout`
eee=`stk_build "${energies}" out=stdout`


for order in $ooo
do
    if test $order -gt 0
    then
        order="+${order}"
    fi

    for energy in $eee
    do

        if test x$grt = xLETG
        then

            punlearn dmcoords
            dmcoords "${f}" op=cel ra=$razo dec=$deczo energy=$energy order=$order \
              celfmt=deg verb=0 mode=hl grating=leg

            ex=`pget dmcoords x`
            ey=`pget dmcoords y`
            
            echo "point $ex $ey # "point=circle text="{${energy},L${order}}"
            echo "point $ex $ey # "point=circle text="{${energy},L${order}}" | \
              xpaset ${ds9} regions -format ds9 -system physical
          
        else # HETG, do both

            punlearn dmcoords
            dmcoords "${f}" op=cel ra=$razo dec=$deczo energy=$energy order=$order \
              celfmt=deg verb=0 mode=hl grating=heg
            ex=`pget dmcoords x`
            ey=`pget dmcoords y`
            
            echo "point $ex $ey # "point=circle text="{${energy},H${order}}"
            echo "point $ex $ey # "point=circle text="{${energy},H${order}}" | \
              xpaset ${ds9} regions format ds9 -system physical

            punlearn dmcoords
            dmcoords "${f}" op=cel ra=$razo dec=$deczo energy=$energy order=$order \
              celfmt=deg verb=0 mode=hl grating=meg
            ex=`pget dmcoords x`
            ey=`pget dmcoords y`
            
            echo "point $ex $ey # "point=circle text="{${energy},M${order}}"
            echo "point $ex $ey # "point=circle text="{${energy},M${order}}" | \
              xpaset ${ds9} regions format ds9 -system physical

        fi

    done #end energies

done # end orders


