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

bincol=$2
binspec=$3
ftype=$4

grptype=$5
grpval=$6


nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi


file=`xpaget $ds9 file`

xpaget $ds9 regions -format ciao source | \
  egrep -v "^#" > $ASCDS_WORK_PATH/$$_src.reg
xpaget $ds9 regions -format ciao background | \
  egrep -v "^#" > $ASCDS_WORK_PATH/$$_bkg.reg

mm=`wc -m $ASCDS_WORK_PATH/$$_bkg.reg | awk '{print $1}'`

src="${file}[sky=region($ASCDS_WORK_PATH/$$_src.reg)]"

if test $mm -gt 5
then
  bkg="${file}[sky=region($ASCDS_WORK_PATH/$$_bkg.reg)]"
  grpcol=net_counts
else
  bkg=""
  grpcol=counts
fi

dmextract "${src}[bin ${bincol}=${binspec}]" - op=$ftype  bkg="${bkg}" | \
 dmgroup - -  $grptype grouptypeval=$grpval binspec="" xcolumn=$bincol ycol=$grpcol 2> /dev/null > \
  $ASCDS_WORK_PATH/$$_hist.fits 


ds9_plot.py "$ASCDS_WORK_PATH/$$_hist.fits[grouping=0:][cols ${bincol},counts=GRP_DATA]" "$ftype" $ds9

/bin/rm -f $ASCDS_WORK_PATH/$$_src.reg $ASCDS_WORK_PATH/$$_bkg.reg

exit 0
