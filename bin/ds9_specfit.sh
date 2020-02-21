#! /bin/sh

#  Copyright (C) 2013,2015,2016,2018-2020  Smithsonian Astrophysical Observatory
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


ds9=$1
model=$2
addmodel=$3
grpcts=$4
elo=$5
ehi=$6
method=$7
stat=$8
absmodel=$9
shift 9
xtra="$1"



nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi



echo "--------------------------------------------------------"
echo ""
echo `date`
echo ""
echo " (1/4) Parsing Regions" 


src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes selected | tr -s ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'`
if test "x$src" = x
then
  src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes | tr -s ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
  if test "x$src" = x
  then  
      echo "***"
      echo "*** No source regions found!"
      echo "***"
      exit 1
  else
      echo "***"
      echo "*** No source region **selected**.  Using combined data from all source regions: "
      echo "***     ${src}"
      echo "***"
  fi
fi

nsrc=`echo "${src}" | grep "^-" `
if test x"${src}" = x"${nsrc}"
then
  echo "***"
  echo "*** Source region cannot begin with an excluded shape: ${src}"
  echo "***"
  exit 1
fi

bkg=`xpaget ${ds9} regions -format ciao -system physical background -strip yes selected | tr -s ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'` 
if test x"${bkg}" = x
then
  bkg=`xpaget ${ds9} regions -format ciao -system physical background -strip yes | tr -s ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'` 
  if test x"${bkg}" = x
  then
    echo "***"
    echo "*** No background region found, ignoring background."
    echo "***"
  else
    echo "***"
    echo "*** No background region **selected**.  Using combined data from all background regions: "
    echo "***    ${bkg}"
    echo "***"
  fi
fi

if test x"${bkg}" = x
then
    :
else
    nbkg=`echo "${bkg}" | grep "^-"`
    if test x"${bkg}" = x"${nbkg}"
    then
      echo "***"
      echo "*** Background region cannot begin with an excluded shape: ${bkg}"
      echo "***"
      exit 1
    fi
fi

# strip off any filters
file=`xpaget ${ds9} file | sed 's,\[.*,,'` 



fmt=`xpaget ${ds9} fits type`
if test x$fmt = xtable
then
  :
else
    echo "***"
    echo "*** Must be using an event file!"
    echo "***"
  exit 1
fi





#
# Setup output directory
#
checksum=`dmkeypar "${file}" checksum echo+`

root=`echo "${file} $checksum ${src} ${bkg}" | python -c 'import hashlib;import sys;print(hashlib.md5(sys.stdin.readline().encode("ascii")).hexdigest())' `

RUNDIR=$DAX_OUTDIR/specfit/${root}

mkdir -p $RUNDIR/param

rmf=$RUNDIR/out.rmf
arf=$RUNDIR/out.arf
spi=$RUNDIR/out.pi
bpi=$RUNDIR/out_bkg.pi
sav=$RUNDIR/sav
cmd=$RUNDIR/cmd

redo=0
for d in $rmf $arf $spi
do
  if test -e $d
  then
    :
  else
    redo=1  # we need to run specextract
  fi
done



PFILES=$RUNDIR/param\;$ASCDS_INSTALL/param:$ASCDS_INSTALL/contrib/param
punlearn ardlib mkarf asphist mkacisrmf dmextract dmcoords


# get center of source region
dmstat "${file}[cols x,y][sky=${src}]" sig- med- cen- verb=0
xx=`stk_read_num ")dmstat.out_mean" 1 echo+`
yy=`stk_read_num ")dmstat.out_mean" 2 echo+`




#
# Get nH value via colden; not sure how robust this is 
# if nrao or bell has data for all sky; but a starting place
#
#
echo " (2/4) Getting NRAO nH"

dmcoords "${file}" op=sky x=$xx y=$yy celfmt=hms verb=0 asol=
ra=`pget dmcoords ra | tr ":" " " | cut -d"." -f1`
ra_hms=`pget dmcoords ra`
dec=`pget dmcoords dec | tr ":" " " | cut -d"." -f1`
dec_hms=`pget dmcoords dec`
nH=`prop_colden d nrao eval $ra $dec 2>&1 | grep "Hydrogen" | awk '{x=$NF*1.0; print x/100.0}' `





#
# Run spextract
# 
echo " (3/4) Extracting spectrum and making responses"

subtract=""
if test "x$bkg" = x
then
  bg=""
else
  bg="${file}[sky=${bkg}]"

  if test ${stat} = "cash" || test ${stat} = "cstat" || test ${stat} = "wstat"
  then
    echo ""
    echo "*****"
    echo "WARNING: Background will not be subtracted when using ${stat} statistic."
    echo ""
  else
    subtract="sherpa.subtract()"
  fi
  
fi




if test $redo -eq 1
then
  specextract \
    infile="${file}[sky=${src}]" \
    bkgfile="${bg}" \
    outroot=$RUNDIR/out \
    bkgresp=no \
    weight=no\
    refcoord="$ra_hms $dec_hms" \
    weight_rmf=no \
    correctpsf=no \
    clob+  2>&1
  
  if test $? -ne 0
  then
    exit 1
  fi

  echo "Created spectrum $spi"

else
  echo "Using existing spectrum $spi"

fi

echo "$root ${file} ${src} ${bkg}" >> $RUNDIR/../inventory.lis
echo "${file} ${src} ${bkg}" >> $RUNDIR/info.txt


if test x"${xtra}" = x
then
  extra=""
else
  extra="exec(${xtra})"
fi

echo " (4/4) Fitting spectrum"



cat <<EOF > $cmd

import sherpa.astro.ui as sherpa

sherpa.load_data("$spi")

sherpa.group_counts(${grpcts})
sherpa.notice(${elo},${ehi})
$subtract

if "${addmodel}" == "none":
    sherpa.set_source("${model}.mdl1 * ${absmodel}.abs1")
else:
    sherpa.set_source("(${model}.mdl1 + ${addmodel}.mdl2) * ${absmodel}.abs1")


abs1.nH = $nH

sherpa.set_method("${method}")
sherpa.set_stat("${stat}")

$extra

try:
  sherpa.fit()
  sherpa.conf()
except:
  pass

print( "\nPhoton Flux = %s photon/cm^2/s\n" % sherpa.calc_photon_flux())
print( "Energy Flux = %s ergs/cm^2/s\n" % sherpa.calc_energy_flux())

sherpa.save("$sav", clobber=True)


from ciao_contrib._tools.dax_plot_utils import *

_f = sherpa.get_fit_plot()
_d = _f.dataplot
_m = _f.modelplot

blt_plot_model( "${ds9}", _m.x, _m.y,
    "${spi}", "Energy [keV]", "Count Rate [counts/sec/keV]")

blt_plot_data( "${ds9}", _d.x, _d.xerr/2.0, _d.y, _d.yerr)


delta = (_d.y-_m.y)/_d.yerr
ones = _d.yerr*0.0+1.0

blt_plot_delchisqr( "${ds9}", _d.x, _d.x, delta, ones, "")


EOF


python $cmd 2>&1 ### | grep -v "^read" | grep -v "grouping flags"

echo ""
echo "To restore session, start sherpa and type"
echo ""
echo "restore('$sav')"




