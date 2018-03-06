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



hist=$1
file=`echo "$2" | sed 's/EVENTS,/EVENTS][/g'`
min=$3
max=$4
srcreg=`echo $5 | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
bkgreg=`echo $6 | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
ds9=$7




if test x$srcreg = x
then
 src=""
else
 src="[(x,y)=${srcreg}]"
fi


if test x$bkgreg = x
then
 bkg=""
 outcol=counts
else
 bkg="[(x,y)=${bkgreg}]"
 outcol=net_counts
fi



case $hist in
    pfold)
    punlearn pfold
    pfold "${file}${src}" - "${min}:${max}:1" > \
	${ASCDS_WORK_PATH}/$$_period.fits

    ds9_plot.py "$ASCDS_WORK_PATH/$$_period.fits[cols period,sigma_rate]" "Period Fold" $ds9 2>&1 > /dev/null 

    /bin/rm -f $ASCDS_WORK_PATH/$$_period.fits

    ;;
    
    gl)	
    punlearn glvary
    glvary "${file}${src}" $ASCDS_WORK_PATH/$$_foo.fits \
	$ASCDS_WORK_PATH/$$_lc.fits none mmin=$min mmax=$max clob+ 

    /bin/rm -f  $ASCDS_WORK_PATH/$$_foo.fits

    ds9_plot.py "$ASCDS_WORK_PATH/$$_lc.fits[cols time,count_rate]" "GL Lightcurve" $ds9 2>&1 > /dev/null

    /bin/rm -f $ASCDS_WORK_PATH/$$_lc.fits

        ;;
esac

