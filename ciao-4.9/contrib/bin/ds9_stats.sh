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

if test x$stat = xcntrd
then
  cen="cen+"
else
  cen="cen-"
fi

if test x$stat = xsig
then
  sig="sig+"
else
  sig="sig-"
fi

if test x$stat = xmedian
then
  med="med+"
else
  med="med-"
fi


if test x$stat = xmoments
then
  cat - | imgmoment  -"${regions}" 
  pdump imgmoment | egrep -v "infile|mode|EOF"
else
  if test x$stat = xallc
  then
    cat - | dmstat -"${regions}" sig+ med+ cen+
  else
    if test x$stat = xallnoc
    then
      cat - | dmstat -"${regions}" sig+ med+ cen-
    else
      cat - | dmstat -"${regions}" $sig $med $cen | grep $stat
    fi
  fi
fi

echo "# --------------------"
