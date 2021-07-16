#! /bin/bash
# 
#  Copyright (C) 2012-2019  Smithsonian Astrophysical Observatory
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

bands="$2"
mdl="$3"
mdlp="$4"
amdl="$5"
amdlp="$6"
psfmethod="$7"


echo "# -------------------"
echo ""
echo `date`
echo ""


nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "***"
  echo "*** Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  echo "***"
  exit 1
fi


fmt=`xpaget ${ds9} fits type`
if test x$fmt = xtable
then
  :
else
  echo "***"
  echo "*** Must be using an event file"
  echo "***"
  exit 1
fi


src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes selected | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
if test x$src = x
then
  src=`xpaget ${ds9} regions -format ciao -system physical source -strip yes | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g' `
  if test x$src = x
  then  
      echo "***"
      echo "*** No source region found. Please try again."
      echo "***"
      exit 1
  else
      echo "***"
      echo "*** No source regions **selected**.  Using data combined from all source regions: "
      echo "***    ${src}"  
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


bkg=`xpaget ${ds9} regions -format ciao -system physical background -strip yes selected | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'` 
if test x$bkg = x
then
  bkg=`xpaget ${ds9} regions -format ciao -system physical background -strip yes | tr ";" "+" | sed 's,\+$,,;s,\+\-,\-,g'` 
  if test x$bkg = x
  then
      echo "***"
      echo "*** No background region found. Please specify background and try again."
      echo "***"
      exit 1
  else
      echo "***"
      echo "*** No background regions **selected**.  Using data combined from all background regions: "
      echo "***     ${bkg}"
      echo "***"
  fi
fi

nbkg=`echo "${bkg}" | grep "^-"`
if test x"${bkg}" = x"${nbkg}"
then
  echo "***"
  echo "*** Background region cannot begin with an excluded shape: ${bkg}"
  echo "***"
  exit 1
fi


# ds9 filters should not be used, remove them.
file=`xpaget ${ds9} file | sed 's,\[.*,,'`

rdir=$DAX_OUTDIR/aper/$$/
root=${rdir}/out
mkdir -p $rdir


dmcopy "${file}[(x,y)=${src}]" - | dmstat "-[cols ra,dec]"  verb=0
ra=`stk_read_num ")dmstat.out_mean" 1 e+ `
dec=`stk_read_num ")dmstat.out_mean" 2 e+ `

xpaset -p ${ds9} tcl  "{start_dax_progress {srcflux}}" 

echo "#-------------"
srcflux infile="${file}" \
  band="${bands}" \
  model="${mdl}"\
  paramvals="${mdlp}" \
  absmodel="${amdl}" \
  absparams="${amdlp}" \
  pos="${ra},${dec}" \
  outroot="${root}" \
  bkgresp=no \
  srcreg="${src}" \
  bkgreg="${bkg}" \
  psfmethod="${psfmethod}" \
  clobber=yes \
  tmpdir=${rdir} 2>&1

if test $? -ne 0
then
  xpaset -p ${ds9} tcl  "{stop_dax_progress {srcflux}}" 
  if test x$rdir != x
  then  
    /bin/rm ${rdir}/*
  fi
  echo "Error running srcflux command"
  exit 1
fi

xpaset -p ${ds9} tcl  "{stop_dax_progress {srcflux}}" 
echo ""
echo "Output files are located in $rdir"

if test x`pget dax prism` = xyes
then
  fluxfile=`/bin/ls ${rdir}/*.flux`
  for ff in $fluxfile
  do
    xpaset -p $ds9 prism "$fluxfile"
  done
fi




exit 0
