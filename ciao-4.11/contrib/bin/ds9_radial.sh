#!/bin/bash
# 
#  Copyright (C) 2004-2008,2015,2019  Smithsonian Astrophysical Observatory
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
#####file=$2
units=$2

nxpa=`xpaaccess -n ${xpa}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${xpa}'.  Please close the other windows and restart."
  exit 1
fi


if test x$units = xphysical
then
    outcol=rmid
else if test x$units = xarcsec
then
    outcol=cel_rmid
else
    echo "ERROR: Unexpected value for units: ${units}"
    exit 1
fi
fi



xpaget $xpa regions -format ds9 -system physical > $DAX_OUTDIR/$$_ds9.reg 
convert_ds9_region_to_ciao_stack $DAX_OUTDIR/$$_ds9.reg $DAX_OUTDIR/$$_ciao.lis clob+ verb=0

# dmextract can't take pipe'd images :(  Make temp file
cat - > $DAX_OUTDIR/$$_ds9.fits

dmextract "$DAX_OUTDIR/$$_ds9.fits[bin (x,y)=@-$DAX_OUTDIR/$$_ciao.lis]" op=generic \
  outfile=$DAX_OUTDIR/$$_radial.fits

ds9_plot_blt "$DAX_OUTDIR/$$_radial.fits[cols ${outcol},sur_bri]" "Radial Profile $$_radial.fits" $xpa

\rm -f $DAX_OUTDIR/$$_ds9.reg $DAX_OUTDIR/$$_ciao.lis $DAX_OUTDIR/$$_ds9.fits

echo "-----------------------------"
echo `date`
echo ""
echo "outfile: $DAX_OUTDIR/$$_radial.fits"
echo ""


exit 0
