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
  ex=no
else
  ex=yes
fi



xpaget $ds9 regions source | awk ' NR <5 {print $0; next} 0 == index($0,"tag=") { if ( 0==index($0,"#")) {s=" # "  } else {s=" "}  print $0""s"tag={dummy "NR"}"; next } {print $0}' > $ASCDS_WORK_PATH/$$_src.reg
xpaget $ds9 regions background | awk ' NR <5 { print $0; next} 0 == index($0,"tag=") { if ( 0==index($0,"#")) {s=" # "  } else {s=" "}  print $0""s"tag={dummy "NR"}"; next } {print $0}' > $ASCDS_WORK_PATH/$$_bkg.reg

cat $ASCDS_WORK_PATH/$$_src.reg $ASCDS_WORK_PATH/$$_bkg.reg > $ASCDS_WORK_PATH/$$_all.reg

dmgroupreg $ASCDS_WORK_PATH/$$_all.reg  $ASCDS_WORK_PATH/$$_src.reg $ASCDS_WORK_PATH/$$_bkg.reg clob+ exclude=$ex


dmfilth - - $meth @-$ASCDS_WORK_PATH/$$_src.reg @-$ASCDS_WORK_PATH/$$_bkg.reg 2>&1 | xpaset $ds9 fits new

\rm -f  $ASCDS_WORK_PATH/$$_all.reg  $ASCDS_WORK_PATH/$$_src.reg $ASCDS_WORK_PATH/$$_bkg.reg 

exit 0
