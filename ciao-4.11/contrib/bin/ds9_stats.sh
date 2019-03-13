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



stat=$1

_r=`echo "$2" | egrep ^@`
if test x$_r = x
then
  reg=`echo "$2" | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
else
  _r=`echo $_r | tr -d @`
  reg=`cat $_r | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
fi


if test x$reg = x
then
 regions=""
else
 regions="[(x,y)=${reg}][opt full]"
fi

#~ if test x$stat = xcntrd
#~ then
  #~ cen="cen+"
#~ else
  #~ cen="cen-"
#~ fi

#~ if test x$stat = xsig
#~ then
  #~ sig="sig+"
#~ else
  #~ sig="sig-"
#~ fi

#~ if test x$stat = xmedian
#~ then
  #~ med="med+"
#~ else
  #~ med="med-"
#~ fi

printf "`date`\n"


if test x$stat = xmoments
then
  cat - | imgmoment  -"${regions}" 
  #~ pdump imgmoment | egrep -v "infile|mode|EOF"

  printf "%20s : %s\n" "Total (0th)" "`pget imgmoment m_0_0`"
  printf "%20s : %s\n" "Centroid (1st)" "`pget imgmoment x_mu` `pget imgmoment y_mu`"
  printf "%20s : %s\n" "Angle abt centroid" "`pget imgmoment phi`"
  printf "%20s : %s\n" "1-sigma in X" "`pget imgmoment xsig`"    
  printf "%20s : %s\n" "1-sigma in Y" "`pget imgmoment ysig`"    
  printf "%20s : %s\n" "Moment matrix:"
  printf "%22s %12.5g\t%12.5g\t%12.5g\n" " " `pget imgmoment m_0_0` `pget imgmoment m_0_1` `pget imgmoment m_0_2`
  printf "%22s %12.5g\t%12.5g\t%12.5g\n" " " `pget imgmoment m_1_0` `pget imgmoment m_1_1` `pget imgmoment m_1_2`
  printf "%22s %12.5g\t%12.5g\t%12.5g\n" " " `pget imgmoment m_2_0` `pget imgmoment m_2_1` `pget imgmoment m_2_2`

else
  if test x$stat = xallc
  then
    cat - | dmstat -"${regions}" sig+ med+ cen+ verb=0
  else
    if test x$stat = xallnoc
    then
      cat - | dmstat -"${regions}" sig+ med+ cen- verb=0
    fi
  fi

  printf "%20s : %s\n" "Image Axes" "`pget dmstat out_columns`"
  printf "%20s : %s\n" "Minimum" "`pget dmstat out_min`"
  printf "%20s : %s\n" "Maximum" "`pget dmstat out_max`"
  printf "%20s : %s\n" "Average" "`pget dmstat out_mean`"
  printf "%20s : %s\n" "Sum" "`pget dmstat out_sum`"
  printf "%20s : %s\n" "Median" "`pget dmstat out_median`"
  printf "%20s : %s\n" "Area (pixels)" "`pget dmstat out_good`"
  printf "%20s : %s\n" "NULL pixels" "`pget dmstat out_null`"
  printf "%20s : %s\n" "Centroid (physical)" "`pget dmstat out_cntrd_phys`"
  printf "%20s : %s\n" "Coords min pix" "`pget dmstat out_min_loc`"
  printf "%20s : %s\n" "Coords max pix" "`pget dmstat out_max_loc`"



fi

echo "# --------------------"
