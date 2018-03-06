#! /bin/sh
ds9=$1

multiplier=10

nxpa=`xpaaccess -n ${ds9}`
if test $nxpa -ne 1
then
  echo "# -------------------"
  echo "Multiple (${nxpa}) ds9's are running using the same title: '${ds9}'.  Please close the other windows and restart."
  exit 1
fi


echo " (1/5) Parsing Regions" 

src=`xpaget ${ds9} regions -format ciao source -strip -selected | tr -d ";"`


fmt=`xpaget ${ds9} fits type`

if test x$fmt = xtable
then
  :
else
  echo "Must be using an event file"
  exit 1
fi


file=`xpaget ${ds9} file`


echo " (2/5) Getting coordinates"
punlearn dmcoords dmstat

dmstat "${file}[(x,y)=${src}][cols x,y]"  verb=0
xx=`stk_read_num ")dmstat.out_mean" 1 e+ `
yy=`stk_read_num ")dmstat.out_mean" 2 e+ `

dmcoords "${file}" asol= op=sky x=$xx y=$yy verb=0
theta=`pget dmcoords theta`
phi=`pget dmcoords phi`

exptime=`dmkeypar "${file}" exposure ec+ | awk '{print $1/1000.0}'`


echo " (3/5) Extracting spectrum"

eff2evt "${file}[(x,y)=${src}]" ${ASCDS_WORK_PATH}/evt.fits clob+ ; dmextract "${ASCDS_WORK_PATH}/evt.fits[bin energy=300:9000:100;flux]" - op=generic | dmtcalc "-[cols energy,counts]" - expr="energy=(energy/1000.0);flux=(${multiplier}*counts*exposure*1000)" | dmcopy "-[cols energy,flux][flux>0]" ${ASCDS_WORK_PATH}/spectrum.dat'[opt kernel=text/simple;sep="\t"]' clob+

echo " (4/5) Running raytrace"

saotrace ${ASCDS_WORK_PATH}/rays $theta $phi ${ASCDS_WORK_PATH}/spectrum.dat $exptime  |\
   grep -v "Output ray" | grep -v '^$'

echo " (5/5) Projecting events"

xpaset -p $ds9 frame new
psf_project_ray ${ASCDS_WORK_PATH}/rays.fits - "${file}" | xpaset $ds9 fits


echo "Done!"

/bin/rm ${ASCDS_WORK_PATH}/{evt.fits,spectrum.dat,rays.fits}
