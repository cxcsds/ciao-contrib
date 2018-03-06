#!/usr/bin/env python
# 
#  Copyright (C) 2004-2008,2010  Smithsonian Astrophysical Observatory
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


import sys
import os
import paramio

X_AXIS         = 1   # label x for blt plot
Y_AXIS         = 2

#
#  for blt plot 
#
def exe_task (tool, cmd) :
   paramio.punlearn( tool )
   os.system ( tool+" "+cmd )

#
#  infile = filename[cols x,y] || filename[cols x=,y=] .. etc.
#
def blt_colname( infile ) :
   col1  = infile.split('[cols ')
   xycol = col1[1].split(']')
   col2  = xycol[0].split(',')
   xcol  = col2[0].split('=')
   xcol  = string.upper( xcol[0] )
   ycol  = col2[1].split('=')
   ycol  = string.upper( ycol[0] )
   return xcol, ycol

#
#  { the Title }
#
def blt_title( title, ds9XPA ) :
   title = r'{'+title+'}' 
   cmd = 'xpaset -p '+ds9XPA+r' plot graph labels title "'+title+'"'
   os.system( cmd )

#
# get column unit 
#
def blt_unit ( baseFile, Col ) :
   cmd=baseFile+" "+Col+r" echo-"
   exe_task("dmkeypar", cmd )
   unit = paramio.pget("dmkeypar", "unit")
   return unit

#
# if unit!=blank, set label='{colname (unit)}' ;
# else  set label='colname'
#
def blt_label ( baseFile, Col, axis, ds9XPA ) :
   label = Col 
   uu = blt_unit ( baseFile, Col )
   unit=uu.replace("\n"," ").replace("\r"," ").replace("\\n"," ").replace("\\r"," ").strip(" ")
   if len(unit) > 0 :
      label  = r'{'+Col+r' ('+unit+r')}'    # {Col unit} 

   if axis == X_AXIS :
      cmd = 'xpaset -p '+ds9XPA+r' plot graph labels xaxis "'+label+'"'
      os.system( cmd )

   if axis == Y_AXIS :
      cmd = 'xpaset -p '+ds9XPA+r' plot graph labels yaxis "'+label+'"'
      os.system( cmd )


def  make_blt_plot( infile, ds9XPA, title, baseFile ) :
   xcol, ycol = blt_colname ( infile )

   cmd = r'"'+infile+r'" data,clean | egrep -vi "'+xcol+r'|NaN" | xpaset '+ds9XPA+r' plot new'
   exe_task("dmlist", cmd )

   blt_title(title, ds9XPA )
   blt_label(baseFile, xcol, X_AXIS, ds9XPA)
   blt_label(baseFile, ycol, Y_AXIS, ds9XPA)

   cmd = 'xpaset -p '+ds9XPA+r' plot view linear no'
   os.system( cmd )
   cmd = 'xpaset -p '+ds9XPA+r' plot view step yes'
   os.system( cmd )
   cmd = 'xpaset -p '+ds9XPA+r' plot line step width 2'
   os.system( cmd )

   ww = ['title','labels','numbers']
   for ii in range(0, len(ww)) :
       cmd = 'xpaset -p '+ds9XPA+r' plot font '+ww[ii]+r' style bold'
       os.system( cmd )

def warning_msg( msg ) :
   sys.stderr.write( msg )


if __name__ == '__main__':

   pkgNotLoad     = 0  # can't find chips pkg
   pkgIsLoad      = 1  # find chips pkg

   # check chips package and set pkg_flag properly
   pkg_flag =  pkgIsLoad
   try :
      import pychips
   except :
      pkg_flag = pkgNotLoad        # startchips issued warning
      pass
   if ( pkg_flag == pkgIsLoad ) :
      ee = os.environ.get("ASCDS_INSTALL") + r'/bin/chipsServer'
      if os.path.exists(ee) == False :
         pkg_flag = pkgNotLoad     # startchips issued warning

   if pkg_flag == pkgIsLoad :
      try:
         from pychips import *
         from pychips.hlui import *
         import pycrates
      except:                      # warning
         warning_msg ("WARNING: Could not load ChIPS. continue plotting w/ BLT.\n")
         pkg_flag = pkgNotLoad

   infile=sys.argv[1]
   title=sys.argv[2]
   ds9XPA=sys.argv[3]

   baseFile = infile.split ('[')
   baseFile = baseFile[0]

   if pkg_flag == pkgIsLoad :     #   CHIPS plot
      import time

      # connect to chips -- try a couple of time in case the server is slow to 
      # start up
      for ii in range (3):
         try:
            connect (ds9XPA)
         except:
            time.sleep (.1)

      add_window();

      # overwrite the get_filename function so that chips controls the file names
      crate = pycrates.read_file (infile)
      crate.get_filename = lambda: ''

      make_figure(crate, "histogram");
      set_plot_title(title);

   else :                         #   BLT plot
      import string 
      import subprocess
      make_blt_plot( infile, ds9XPA, title, baseFile) 

   os.remove (baseFile)
