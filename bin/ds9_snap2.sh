#! /bin/sh
# 
#  Copyright (C) 2004-2008, 2014, 2019, 2025
#  Smithsonian Astrophysical Observatory
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

xpaget $ds9 regions -format ds9 -system physical > $DAX_OUTDIR/$$_all.reg
grab=`xpaget $ds9 regions -format ds9 selected -system physical | tail -1 | grep -v ^global| cut -d# -f1`
if test x"${grab}" = x
then
  /bin/rm $DAX_OUTDIR/$$_all.reg
  exit 0
fi


old=`echo $grab | cut -d"(" -f2 | cut -d, -f1,2`



dmstat "-[(x,y)=$grab]" cen+ sig- clip+ nsig=10 > /dev/null
if test $? -ne 0
then
  \rm -f  $DAX_OUTDIR/$$_all.reg
  exit 1
fi

new=`pget dmstat out_cntrd_phys`

xpaset -p $ds9 regions delete all
cat $DAX_OUTDIR/$$_all.reg | sed "s/$old/$new/" | xpaset $ds9 regions -format ds9 -system physical
\rm -f  $DAX_OUTDIR/$$_all.reg


exit 0
