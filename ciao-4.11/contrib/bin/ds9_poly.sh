#! /bin/sh
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
  egrep polygon > $DAX_OUTDIR/$$_poly.reg

np=`wc -l  $DAX_OUTDIR/$$_poly.reg | awk '{print $1}'`
if test "$np" -eq 0
then
  echo "# ---------------------"
  echo "ERROR:  No polygon regions found"
  exit 1
fi


dmmakereg region="region($DAX_OUTDIR/$$_poly.reg)" \
  outfile=$DAX_OUTDIR/$$_poly.fits ker=fits


echo "#--------------------"
echo `date`
echo ""

dmimgpick $DAX_OUTDIR/$$_poly.fits"[cols x,y]" - - $meth | \
  tee $DAX_OUTDIR/$$_polypick.fits | \
  dmlist - data,clean,array

echo ""
echo "Output file is $DAX_OUTDIR/$$_polypick.fits"

\rm -f $DAX_OUTDIR/$$_poly.reg $DAX_OUTDIR/$$_poly.fits

exit 0
