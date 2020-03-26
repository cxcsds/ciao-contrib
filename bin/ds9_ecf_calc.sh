#!/bin/sh
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
fracs="$2"


echo "# -------------------"
echo `date`
echo ""


nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi


# try selected 1st
myreg=`xpaget ${ds9} regions selected -format ciao -system physical -strip | tr ";" "\012" | egrep "circle|ellipse|box" | tail -1 | tr "(),"'"'  " " `

if test "x$myreg" = x
then
  # try unselected
  myreg=`xpaget ${ds9} regions -format ciao -system physical -strip | tr ";" "\012" | egrep "circle|ellipse|box" | tail -1 | tr "(),"'"'  " " `

  if test "x$myreg" = x
  then
    echo "Please select a single region. Make sure only a circle, ellipse, or box shapes is selected"
    exit 1
  fi
fi


rr=`echo $myreg | awk ' $1 == "circle" { print $4 } \
		        $1 == "ellipse" {print sqrt( $4*$4 + $5+$5 )} \
		        $1 == "box" {print sqrt( $4*$4 + $5+$5 )} '`

xx=`echo $myreg | cut -d" " -f2`
yy=`echo $myreg | cut -d" " -f3`
ff=`xpaget $ds9 file `

echo "Computing ECFs for ${ff} @ (${xx},${yy}) w/ radius ${rr}"

if test x${fracs} = x"default"
then
  fracs="0.01,0.025,0.05,0.075,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.85,0.9,0.95,0.99"
fi


xpaget $ds9 fits > $DAX_OUTDIR/$$_ecf.img 

ecf_calc \
  infile=$DAX_OUTDIR/$$_ecf.img  \
  outfile=$DAX_OUTDIR/$$_ecf.fits \
  radius=$rr xpos=$xx ypos=$yy \
  bin=1 plot=no clobber=yes \
  fraction="${fracs}"

/bin/rm $DAX_OUTDIR/$$_ecf.img 

echo "ECFs are in $DAX_OUTDIR/$$_ecf.fits"

ds9_plot_blt "$DAX_OUTDIR/$$_ecf.fits[cols r_mid,fraction]" \
  "Enclosed Counts Fraction $$_ecf.fits" $ds9 
xpaset -p $ds9 plot shape circle
xpaset -p $ds9 plot smooth linear

 
exit 0

