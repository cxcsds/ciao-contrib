#! /bin/sh

# 
#  Copyright (C) 2010-2015,2018  Smithsonian Astrophysical Observatory
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
getconf=$4



nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi




src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes selected | tr -d ";"`

if test "x${src}" = x
then
  echo "No sources **selected** "
  exit 1
fi

if test x$getconf = x1
then
  conf="sherpa.conf()"
else
  conf=""
fi


echo "  (1/3) Getting data"

xpaget $ds9 fits > $ASCDS_WORK_PATH/$$_img.fits 

echo "  (2/3) Getting moments to provide better guess"

punlearn imgmoment
imgmoment "$ASCDS_WORK_PATH/$$_img.fits[(x,y)=$src]" 
xx=`pget imgmoment x_mu`
yy=`pget imgmoment y_mu`
mjr=`pget imgmoment xsig`
mnr=`pget imgmoment ysig`
phi=`pget imgmoment phi | awk '{print (($1+360.0)%360)*3.141592/180.0}'`


cat <<EOF > $ASCDS_WORK_PATH/$$_img.cmd

import sherpa.astro.ui as sherpa
import numpy as np

sherpa.load_data("$ASCDS_WORK_PATH/$$_img.fits")
sherpa.set_coord("physical")

sherpa.set_source("${model}.mdl1+${modelbkg}.bkg1")
sherpa.ignore2d()
sherpa.notice2d("${src}")
sherpa.thaw(mdl1)
sherpa.thaw(bkg1)
sherpa.guess(mdl1)
sherpa.guess(bkg1)

mdl1.theta=$phi
ee=${mnr}/${mjr}
if (ee>1):
  ee=(1/ee)
mdl1.ellip=np.sqrt( 1-(ee*ee))
mdl1.xpos=$xx
mdl1.ypos=$yy
try:
  sherpa.fit()
  ${conf}
except:
  pass


sherpa.notice()
sherpa.save_source("$ASCDS_WORK_PATH/$$_out.fits", clobber=True)
EOF

echo "  (3/3) Doing fit"

python $ASCDS_WORK_PATH/$$_img.cmd

xpaset -p $ds9 frame new
cat $ASCDS_WORK_PATH/$$_out.fits | xpaset $ds9 fits

echo "Done!"


/bin/rm -f  $ASCDS_WORK_PATH/$$_img.fits $ASCDS_WORK_PATH/$$_img.cmd $ASCDS_WORK_PATH/$$_out.fits
