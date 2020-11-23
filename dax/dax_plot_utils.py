#
#  Copyright (C) 2020
#  Smithsonian Astrophysical Observatory
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

"""
Emulate the sherpa plot commands using blt via ds9


sherpa has various plot commands to plot data, models, residuals, etc.
dax needs to emulate this plots but instead of using sherpa plotting
backends (eg matplotlib), we are  using the BLT plotting available 
through ds9.  This way dax doesn't have to spawn background processes
and keep track of things running in the background to cleanup/etc.

"""


import subprocess

__all__ = ( "blt_plot_data", "blt_plot_model", "blt_plot_delchisqr" )

def xpa_plot_cmd( access_point, command ):
    """Wrapper around xpaset for plot commands"""
    
    cc = ["xpaset", "-p", access_point, "plot" ]
    cc.extend( command.split(' '))    
    xpa = subprocess.Popen(cc)
    xpa.communicate()


def blt_plot_data(access_point,xx, ex, yy, ey):
    """Plot the data"""
    cmd = ["xpaset", access_point, "plot"]
    cmd.extend( ["data", "xyey"] )

    # Plot the data
    xpa = subprocess.Popen( cmd, stdin=subprocess.PIPE ) 
    for vv in zip(xx, yy, ey):
        pair = " ".join( [str(x) for x in vv])+"\n"        
        pb = pair.encode()
        xpa.stdin.write(pb)        
    xpa.communicate()

    make_pretty(access_point)
    xpa_plot_cmd(access_point, "legend yes")
    xpa_plot_cmd(access_point, "legend position right")


def blt_plot_model(access_point,x_vals, y_vals, title, x_label, y_label, 
        new=True, winname="dax"):
    """Plot the model"""
    
    if new is False:
        cmd = xpa_plot_cmd(access_point, "{} close".format(winname))

    cmd = ["xpaset", access_point, "plot", "new"]            
    cmd.extend( ["name", winname, "line", 
        "{{{0}}}".format(title), 
        "{{{0} }}".format(x_label), 
        "{{{0} }}".format(y_label),
        "xy"
        ] )
    # ~ else:
        # ~ xpa_plot_cmd( access_point, "layout grid")
        # ~ xpa_plot_cmd(access_point, winname+" delete dataset")
        # ~ xpa_plot_cmd(access_point, winname+" delete graph")        
        # ~ xpa_plot_cmd(access_point, winname+" delete dataset")
        # ~ xpa_plot_cmd(access_point, winname+" delete dataset")
        # ~ cmd = ["xpaset", access_point, "plot", "data", "xy"]

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
    xpa_plot_cmd(access_point, "smooth step")
    xpa_plot_cmd(access_point, "name Model")


def blt_plot_delchisqr(access_point,xx, ex, yy, ey, y_label):
    """Plot the residuals""" 

    # This requires ds9 v8.1    
    xpa_plot_cmd( access_point, "add graph line")
    xpa_plot_cmd( access_point, "layout strip")
    

    # Add line through 0
    x0 = [xx[0]-ex[0], xx[-1]+ex[-1]]
    y0 = [0, 0]
    cmd = ["xpaset", access_point, "plot", "data", "xy"]    
    xpa = subprocess.Popen( cmd, stdin=subprocess.PIPE ) 
    for vv in zip(x0, y0):
        pair = " ".join( [str(x) for x in vv])+"\n"        
        pb = pair.encode()
        xpa.stdin.write(pb)        
    xpa.communicate()
    xpa_plot_cmd(access_point, "shape none")
    xpa_plot_cmd(access_point, "shape fill no")
    xpa_plot_cmd(access_point, "color grey")
    xpa_plot_cmd(access_point, "name zero")
    xpa_plot_cmd(access_point, "width 1")
    xpa_plot_cmd(access_point, "dash yes")

        
    # Plot the data
    cmd = ["xpaset", access_point, "plot", "data", "xyexey"]    
    xpa = subprocess.Popen( cmd, stdin=subprocess.PIPE ) 
    for vv in zip(xx, yy, ex, ey):
        pair = " ".join( [str(x) for x in vv])+"\n"        
        pb = pair.encode()
        xpa.stdin.write(pb)        
    xpa.communicate()

    make_pretty(access_point)
    xpa_plot_cmd( access_point, "title y {delta chisqr}")
    xpa_plot_cmd( access_point, "name {delchi}")


def make_pretty(access_point):
    """make pretty plots"""
    xpa_plot_cmd(access_point, "shape circle")
    xpa_plot_cmd(access_point, "shape fill yes")
    xpa_plot_cmd(access_point, "shape color cornflowerblue")
    xpa_plot_cmd(access_point, "error color cornflowerblue")
    xpa_plot_cmd(access_point, "width 0")
    xpa_plot_cmd(access_point, "name {Data }")    
    xpa_plot_cmd(access_point, "axis x grid no")
    xpa_plot_cmd(access_point, "axis y grid no")


