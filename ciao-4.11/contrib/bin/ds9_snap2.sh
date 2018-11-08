#! /bin/sh
# 
#  Copyright (C) 2004-2008, 2014  Smithsonian Astrophysical Observatory
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

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi


xpaget $ds9 regions -format ds9 -system physical > $ASCDS_WORK_PATH/$$_all.reg
grab=`xpaget $ds9 regions -format ds9 selected -system physical | tail -1 | cut -d# -f1`
old=`echo $grab | cut -d"(" -f2 | cut -d, -f1,2`

dmstat "-[(x,y)=$grab]" cen+ sig- > /dev/null
if test $? -ne 0
then
  \rm -f  $ASCDS_WORK_PATH/$$_all.reg
  exit 1
fi

new=`pget dmstat out_cntrd_phys`

xpaset -p $ds9 regions delete all
cat $ASCDS_WORK_PATH/$$_all.reg | sed "s/$old/$new/" | xpaset $ds9 regions
\rm -f  $ASCDS_WORK_PATH/$$_all.reg


exit 0
