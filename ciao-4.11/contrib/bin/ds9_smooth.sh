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



ker=$1
xx=$2
yy=$3
meth=$4

nrad=4


case $ker in
    gaus)
      cat - | aconvolve - - lib:${ker}"(2,${nrad},1,$xx,$yy)" meth=$meth 
      ;;
    mexhat)
      cat - | aconvolve - - lib:${ker}"(2,${nrad},1,$xx,$yy)" meth=$meth 
      ;;
    power)
      cat - | aconvolve - - lib:${ker}"(2,${nrad},1,$xx,$yy)" meth=$meth 
      ;;
    exp)
      cat - | aconvolve - - lib:${ker}"(2,${nrad},1,$xx,$yy)" meth=$meth 
      ;;
    tophat)
      cat - | aconvolve - - lib:${ker}"(2,1,$xx,$yy)" meth=$meth 
      ;;
    box)
      cat - | aconvolve - - lib:${ker}"(2,1,$xx,$yy)" meth=$meth 
      ;;
    sinc)
      cat - | aconvolve - - lib:${ker}"(2,${nrad},1,$xx)" meth=$meth 
      ;;
    beta)
      cat - | aconvolve - - lib:${ker}"(2,${nrad},1,$xx)" meth=$meth 
      ;;
    cone)
      cat - | aconvolve - - lib:${ker}"(2,1,$xx)" meth=$meth 
      ;;
    pyramid)
      cat - | aconvolve - - lib:${ker}"(2,1,$xx)" meth=$meth 
      ;;
    sphere)
      cat - | aconvolve - - lib:${ker}"(2,$xx)" meth=$meth 
      ;;
esac

