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
istep=$2
file=`echo "$3" | sed 's/EVENTS,/EVENTS][/g'`
srcreg=`echo $4 | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
bkgreg=`echo $5 | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
ds9=$6





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

  pha) min=1
       max=4096
       step=$istep
       type=pha1
	;;

 pi)   min=1
       max=1023
       step=$istep
       type=pha1
	;;

  time) min=
	max=
	step=`dmkeypar $file TIMEDEL echo+`
        step=`echo "$step * 100" | bc -l `
	step=$istep
	type=ltc1
	if test x$bkgreg = x
	then
	  outcol=count_rate
        else
          outcol=net_rate
	fi
	;;


  expno) min=1
	 max=`dmstat "${file}[cols expno]" sig- med- cen- | grep max | cut -d: -f2 | cut -d@ -f1`
	 step=$istep
	 type=ltc1
	;;

esac


dmextract "${file}${src}[bin ${hist}=${min}:${max}:${step}]" - op=$type \
  bkg="${file}${bkg}"   > \
  $ASCDS_WORK_PATH/$$_${hist}.fits



ds9_plot.py "$ASCDS_WORK_PATH/$$_${hist}.fits[cols $hist,$outcol]" "$hist" $ds9
