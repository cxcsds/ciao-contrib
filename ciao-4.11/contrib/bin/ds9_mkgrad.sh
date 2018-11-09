#! /bin/sh 

d=$ASCDS_WORK_PATH/$$_lut.dat
res=220
#black="0.0 0.0 0.0"
#white="1.0 1.0 1.0"

myds9=$1
name=`echo $2 $3 $4 $5 $6 $7 $8 $9 | tr " " "_"`



#echo $black >  $d
pget colors $2 $3 $4 $5 $6 $7 $8 $9 >> $d
#echo $white >> $d


cat -n $d > ${d}.num
max=`tail -1 ${d}.num | awk '{print $1}'`


env PAGER=cat slsh -e "print(1+[1:${res}:1]*((${max}-1.0)/${res}));" > ${d}.grid

dmjoin ${d}.grid ${d}.num - col1 | \
  dmlist -"[cols col2,col3,col4]" data,clean | \
  egrep -v "^#" | \
  tr -s " " " " > $ASCDS_WORK_PATH/${name}.lut


xpaset -p $myds9 cmap file $ASCDS_WORK_PATH/${name}.lut
xpaset -p $myds9 cmap ${name}

\rm -f $d ${d}.num ${d}.grid $ASCDS_WORK_PATH/${name}.lut

exit 0
