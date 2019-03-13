#! /bin/sh

#  Copyright (C) 2013,2015,2016,2018-2019  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
grpcts=$3
elo=$4
ehi=$5
method=$6
stat=$7
absmodel=$8
xtra="$9"

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi



echo "--------------------------------------------------------"
echo " (1/4) Parsing Regions" 

src=`xpaget ${ds9} regions -format ciao source -strip yes selected | tr -d ";"`
bkg=`xpaget ${ds9} regions -format ciao background -strip yes selected | tr -d ";" ` 


if test "x$src" = x
then
  echo "Please **select** a source region"
  exit 1
fi

nsrc=`echo "${src}" | grep "^-" `
if test x"${src}" = x"${nsrc}"
then
  echo "#--------"
  echo "Source region cannot begin with an excluded shape: ${src}"
  exit 1
fi


if test x"${bkg}" = x
then
  echo "No background region **selected**, ignoring background."
else
    nbkg=`echo "${bkg}" | grep "^-"`
    if test x"${bkg}" = x"${nbkg}"
    then
      echo "#--------"
      echo "Background region cannot begin with an excluded shape: ${bkg}"
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
  echo "Must be using an event file"
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

if test "x$bkg" = x
then
  bg=""
  subtract=""
else
  bg="${file}[sky=${bkg}]"
  subtract="sherpa.subtract()"
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
import pychips

sherpa.load_data("$spi")

sherpa.group_counts(${grpcts})
sherpa.notice(${elo},${ehi})
$subtract
sherpa.set_source("${model}.mdl1 * ${absmodel}.abs1")
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


# -- Emulate the 'plot_fit()' sherpa command, 

import subprocess

def xpa_plot_cmd( access_point, command ):
    """Wrapper around xpaset for plot commands"""
    
    cc = ["xpaset", "-p", access_point, "plot" ]
    cc.extend( command.split(' '))    
    xpa = subprocess.Popen(cc)
    xpa.communicate()


def blt_plot_data(access_point,xx, ex, yy, ey, title, x_label, y_label):
    """Plot the data"""
    
    cmd = ["xpaset", access_point, "plot"]    
    cmd.extend( ["new", "line", 
        "{{{0}}}".format(title), 
        "{{{0}}}".format(x_label), 
        "{{{0}}}".format(y_label),
        "xyey"
        ] )

    # Plot the data
    xpa = subprocess.Popen( cmd, stdin=subprocess.PIPE ) 
    for vv in zip(xx, yy, ey):
        pair = " ".join( [str(x) for x in vv])+"\n"        
        pb = pair.encode()
        xpa.stdin.write(pb)        
    xpa.communicate()

    # Make pretty
    xpa_plot_cmd(access_point, "shape circle")
    xpa_plot_cmd(access_point, "shape fill yes")
    xpa_plot_cmd(access_point, "shape color cornflowerblue")
    xpa_plot_cmd(access_point, "error color cornflowerblue")
    xpa_plot_cmd(access_point, "width 0")
    xpa_plot_cmd(access_point, "legend yes")
    xpa_plot_cmd(access_point, "legend position right")
    xpa_plot_cmd(access_point, "name {Data }")    
    xpa_plot_cmd(access_point, "axis x grid no")
    xpa_plot_cmd(access_point, "axis y grid no")

def blt_plot_model(access_point,x_vals, y_vals):
    """Plot the model"""
    
    cmd = ["xpaset", access_point, "plot"]
    cmd.extend( ["data", "xy"] )

    xpa = subprocess.Popen( cmd, stdin=subprocess.PIPE ) 
    for x,y in zip(x_vals, y_vals):
        pair = "{} {}\n".format(x,y)
        pb = pair.encode()
        xpa.stdin.write(pb)        
    xpa.communicate()
    xpa_plot_cmd(access_point, "shape none")
    xpa_plot_cmd(access_point, "shape fill no")
    xpa_plot_cmd(access_point, "color orange")
    xpa_plot_cmd(access_point, "shape color orange")
    xpa_plot_cmd(access_point, "width 2")
    xpa_plot_cmd(access_point, "name Model")

_f = sherpa.get_fit_plot()
_d = _f.dataplot
_m = _f.modelplot

blt_plot_data( "${ds9}", _d.x, _d.xerr/2.0, _d.y, _d.yerr, 
    "${spi}", "Energy [keV]", "Count Rate [c/s]")

blt_plot_model( "${ds9}", _m.x, _m.y)


EOF


python $cmd 2>&1 ### | grep -v "^read" | grep -v "grouping flags"

echo ""
echo "To restore session, start sherpa and type"
echo ""
echo "restore('$sav')"




