# -- Emulate the 'plot_fit()' sherpa command, 

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


def blt_plot_model(access_point,x_vals, y_vals, title, x_label, y_label):
    """Plot the model"""
    
    cmd = ["xpaset", access_point, "plot"]    
    cmd.extend( ["new", "name", "dax", "line", 
        "{{{0}}}".format(title), 
        "{{{0}}}".format(x_label), 
        "{{{0}}}".format(y_label),
        "xy"
        ] )

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


def blt_plot_delchisqr(access_point,xx, ex, yy, ey, y_label):
    """Plot the residuals""" 

    # This requires ds9 v8.1    
    xpa_plot_cmd( access_point, "add graph line")
    xpa_plot_cmd( access_point, "layout strip")
    
    cmd = ["xpaset", access_point, "plot", "data", "xyey"]    

    # Plot the data
    xpa = subprocess.Popen( cmd, stdin=subprocess.PIPE ) 
    for vv in zip(xx, yy, ey):
        pair = " ".join( [str(x) for x in vv])+"\n"        
        pb = pair.encode()
        xpa.stdin.write(pb)        
    xpa.communicate()

    make_pretty(access_point)
    xpa_plot_cmd( access_point, "title y {delta chisqr}")


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


