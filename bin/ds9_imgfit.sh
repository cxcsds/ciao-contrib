#! /bin/sh

# 
#  Copyright (C) 2010-2015,2018,2019  Smithsonian Astrophysical Observatory
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
model=$2
modelbkg=$3
method=$4
stat=$5

echo "# -------------------"
echo ""
echo `date`
echo ""


nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi



src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes selected | tr -s ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'`
if test "x${src}" = x
then
    src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes | tr -s ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'`
    if test "x${src}" = x
    then
      echo "***"
      echo "*** No source region found "
      echo "***"
      exit 1
    else
      echo "***"
      echo "*** No source regions **selected**.  Using data combined from all source regions : "
      echo "***   ${src}"
      echo "***"
    fi
fi


#~ if test x$getconf = x1
#~ then
  #~ conf="sherpa.conf()"
#~ else
  #~ conf=""
#~ fi

DAX_OUTDIR=$DAX_OUTDIR/imgfit/$$/
mkdir -p $DAX_OUTDIR

echo "  (1/3) Getting data"

xpaget $ds9 fits > ${DAX_OUTDIR}/img.fits 

echo "  (2/3) Getting moments to provide better guess"

punlearn imgmoment
imgmoment "${DAX_OUTDIR}/img.fits[(x,y)=$src]" 
xx=`pget imgmoment x_mu`
yy=`pget imgmoment y_mu`
mjr=`pget imgmoment xsig`
mnr=`pget imgmoment ysig`
phi=`pget imgmoment phi | awk '{print (($1+360.0)%360)*3.141592/180.0}'`


cat <<EOF > ${DAX_OUTDIR}/fit.cmd

import sherpa.astro.ui as sherpa
import numpy as np

sherpa.load_data("${DAX_OUTDIR}/img.fits")
sherpa.set_coord("physical")
sherpa.set_method("${method}")
sherpa.set_stat("${stat}")



sherpa.set_source("${model}.mdl1+${modelbkg}.bkg1")
sherpa.ignore2d()
sherpa.notice2d("${src}")
sherpa.thaw(mdl1)
sherpa.thaw(bkg1)
sherpa.guess(mdl1)
sherpa.guess(bkg1)


if hasattr(mdl1, "theta"):
    mdl1.theta=$phi

if hasattr(mdl1, "ellip"):
    ee=${mnr}/${mjr}
    if (ee>1):
      ee=(1/ee)
    mdl1.ellip=np.sqrt( 1-(ee*ee))

if hasattr(mdl1,"xpos") and hasattr(mdl1,"ypos"):
  mdl1.xpos=$xx
  mdl1.ypos=$yy

from dax.dax_model_editor import *
mod_edit = DaxModelEditor([mdl1,bkg1], hide_plot_button=True)
mod_edit.run(sherpa.fit, sherpa.conf)


#~ try:
  #~ sherpa.fit()
#~ except:
  #~ pass


sherpa.notice()
sherpa.save_source("${DAX_OUTDIR}/out.fits", clobber=True)
EOF

echo "  (3/3) Doing fit"

python ${DAX_OUTDIR}/fit.cmd
if test $? -ne 0
then
  exit 1
fi

xpaset -p $ds9 tile

xpaset -p $ds9 frame new
cat ${DAX_OUTDIR}/out.fits | xpaset $ds9 fits

dmimgcalc ${DAX_OUTDIR}/img.fits ${DAX_OUTDIR}/out.fits ${DAX_OUTDIR}/residual.fits op=sub look= clob+
xpaset -p $ds9 frame new
cat ${DAX_OUTDIR}/residual.fits | xpaset $ds9 fits

echo ""
echo "Data products and fitting script are in: ${DAX_OUTDIR}"


