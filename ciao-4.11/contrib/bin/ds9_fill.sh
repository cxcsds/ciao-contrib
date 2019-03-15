#! /bin/bash
# 
#  Copyright (C) 2004-2008,2019 Smithsonian Astrophysical Observatory
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



if test x$meth = xPOLY
then
  exclude=no
else
  exclude=yes
fi

# Get source and background regions.  Tag them.
xpaget $ds9 regions source -format ds9 -system physical -strip |  \
  tr ";" "\012" | egrep -v 'physical' | cat - | \
  awk '{print $0" # tag={"NR"}"}' > $DAX_OUTDIR/$$_src.reg
xpaget $ds9 regions background -format ds9 -system physical -strip | \
  tr ";" "\012" | egrep -v 'physical' | cat - |\
  awk '{print $0" # background tag={"NR"}"}' > $DAX_OUTDIR/$$_bkg.reg
cat $DAX_OUTDIR/$$_src.reg $DAX_OUTDIR/$$_bkg.reg > $DAX_OUTDIR/$$_all.reg

# Groupreg to match groups -- maybe not necessary
dmgroupreg $DAX_OUTDIR/$$_all.reg  $DAX_OUTDIR/$$_src.reg $DAX_OUTDIR/$$_bkg.reg clob+ exclude=$exclude


dmfilth - - $meth @-$DAX_OUTDIR/$$_src.reg @-$DAX_OUTDIR/$$_bkg.reg 2>&1 | xpaset $ds9 fits new

\rm -f  $DAX_OUTDIR/$$_all.reg  $DAX_OUTDIR/$$_src.reg $DAX_OUTDIR/$$_bkg.reg 

exit 0
