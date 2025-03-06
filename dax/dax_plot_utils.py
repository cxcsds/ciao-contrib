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

__all__ = ("blt_plot_data", "blt_plot_model", "blt_plot_delchisqr")


def xpa_plot_cmd(access_point, command):
    """Wrapper around xpaset for plot commands"""

    cc = ["xpaset", "-p", access_point, "plot"]
    cc.extend(command.split(' '))
    with subprocess.Popen(cc) as xpa:
        xpa.communicate()


def __pipe_values_to_plot(cmd, vals):

    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as xpa:
        for vv in vals:
            pair = " ".join([str(x) for x in vv])+"\n"
            pb = pair.encode()
            xpa.stdin.write(pb)
        xpa.communicate()
    

def blt_plot_data(access_point, xx, ex, yy, ey):
    """Plot the data"""
    cmd = ["xpaset", access_point, "plot"]
    cmd.extend(["data", "xyey"])
    __pipe_values_to_plot(cmd, zip(xx, yy, ey))

    make_pretty(access_point)
    xpa_plot_cmd(access_point, "legend yes")
    xpa_plot_cmd(access_point, "legend position right")


def blt_plot_model(access_point, x_vals, y_vals, title, x_label, y_label,
                   new=True, winname="dax", step=True):
    """Plot the model"""

    if not new:
        xpa_plot_cmd(access_point, f"{winname} close")

    cmd = ["xpaset", access_point, "plot", "new"]
    cmd.extend(["name", winname, "line",
                f"{{{title}}}", f"{{{x_label} }}", f"{{{y_label} }}",
                "xy"])
    __pipe_values_to_plot(cmd, zip(x_vals, y_vals))

    xpa_plot_cmd(access_point, "shape none")
    xpa_plot_cmd(access_point, "shape fill no")
    xpa_plot_cmd(access_point, "color orange")
    xpa_plot_cmd(access_point, "shape color orange")
    xpa_plot_cmd(access_point, "width 2")
    if step:
        xpa_plot_cmd(access_point, "smooth step")
    xpa_plot_cmd(access_point, "name Model")


def blt_plot_delchisqr(access_point, xx, ex, yy, ey, y_label):
    """Plot the residuals"""

    # This requires ds9 v8.1
    xpa_plot_cmd(access_point, "add graph line")
    xpa_plot_cmd(access_point, "layout strip")

    # Add line through 0
    x0 = [xx[0]-2*ex[0], xx[-1]+2*ex[-1]]
    y0 = [0, 0]
    cmd = ["xpaset", access_point, "plot", "data", "xy"]
    __pipe_values_to_plot(cmd, zip(x0, y0))

    xpa_plot_cmd(access_point, "shape none")
    xpa_plot_cmd(access_point, "shape fill no")
    xpa_plot_cmd(access_point, "color grey")
    xpa_plot_cmd(access_point, "name zero")
    xpa_plot_cmd(access_point, "width 1")
    xpa_plot_cmd(access_point, "dash yes")

    # Plot the data
    step_x = [x-2*e for x, e in zip(xx,ex)]
    step_x.append(xx[-1]+2*ex[-1])

    step_y = [y for y in yy]   # make a copy
    step_y.append(yy[-1])

    # plot steps if binned data
    if not all(ex==0):
        cmd = ["xpaset", access_point, "plot", "data", "xy"]
        __pipe_values_to_plot(cmd, zip(step_x, step_y))
        make_pretty(access_point)
        xpa_plot_cmd(access_point, "width 2")
        xpa_plot_cmd(access_point, "line smooth step")
        xpa_plot_cmd(access_point, "shape none")
        xpa_plot_cmd(access_point, "shape fill no")
        xpa_plot_cmd(access_point, "color cornflowerblue")
    
    cmd = ["xpaset", access_point, "plot", "data", "xyexey"]
    __pipe_values_to_plot(cmd, zip(xx, yy, 2*ex, ey))

    make_pretty(access_point)
    xpa_plot_cmd(access_point, "title y {delta chisqr}")
    xpa_plot_cmd(access_point, "name {delchi}")
    xpa_plot_cmd(access_point, "width 0")
    if not all(ex==0):
        xpa_plot_cmd(access_point, "shape none")
        xpa_plot_cmd(access_point, "shape fill no")
        


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
