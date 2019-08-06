#! /usr/bin/env awk
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



BEGIN {FS="[,() ]"; OFS=",";}
substr($1,1,1) == "#" {next;}
substr($1,1,6) == "global" {next;}
$1 == "physical" {next;}
$1 == "line" {next;}
length($1) == 0 {next;}


$1 == "annulus" {
  for (ii=5;ii<NF;ii+=1) {
    print "circle("$2,$3,$(ii)")"\
         "-circle("$2,$3,$(ii-1)")";
  }
  next; 
}

$1 == "ellipse" || $1 == "box" {
  if ( NF == 7 ) { print $0; next; }

  for (ii=6;ii<NF-2;ii+=2) {
    print $1"("$2,$3,$(ii),$(ii+1),$(NF-1)")" \
       "-"$1"("$2,$3,$(ii-2),$(ii-1),$(NF-1)")";
  }
  next;
}

$1 == "panda" {
  center=$2","$3;
  shape="circle";
  nrad=$9;
  nang=$6;
  lo_ang=$4;
  hi_ang=$5;
  lo_rad=$7;
  hi_rad=$8;
  d_rad=(hi_rad-lo_rad)/nrad;
  d_ang=(hi_ang-lo_ang)/nang;

  for (ii=0;ii<nrad;ii++) {
    for (jj=0;jj<nang;jj++) {
      irad=lo_rad+ii*d_rad;
      orad=irad + d_rad;
      iang=lo_ang+jj*d_ang;
      oang=iang+d_ang;
      print shape"("center,orad")*sector("center,iang,oang")" \
	 "-"shape"("center,irad")" \
    }
  }
  next;
}

$1 == "epanda" || $1 == "bpanda" {
#epanda(4062.5,3938.5,270,0,3,204,118,408,236,2,0)
  center=$2","$3;
  if ( $1 == "epanda" ) {
    shape="ellipse";
  } else {
    shape="box";
  }
  lo_ang=$4;
  hi_ang=$5;
  if (hi_ang == 0 ) hi_ang=360;
  nang=$6;

  lo_xrad=$7;
  lo_yrad=$8;
  hi_xrad=$9;
  hi_yrad=$10;
  nrad=$11;
  angle=$12

  d_xrad=(hi_xrad-lo_xrad)/nrad;
  d_yrad=(hi_yrad-lo_yrad)/nrad;
  d_ang=(hi_ang-lo_ang)/nang;

  for (ii=0;ii<nrad;ii++) {
    for (jj=0;jj<nang;jj++) {
      ixrad=lo_xrad+ii*d_xrad;
      oxrad=ixrad + d_xrad;
      iyrad=lo_yrad+ii*d_yrad;
      oyrad=iyrad + d_yrad;

      iang=lo_ang+jj*d_ang;
      oang=iang+d_ang;
      print shape"("center,oxrad,oyrad,angle")*sector("center,iang,oang")" \
	 "-"shape"("center,ixrad,iyrad,angle")" \
    }
  }
  next;
}


{print $0}
