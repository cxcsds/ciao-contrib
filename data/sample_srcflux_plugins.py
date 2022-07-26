
"Sample plugin file for srcflux"


"""
Files used for spectral fits:
    ${outroot}.arf
    ${outroot}.pi
    ${outroot}.rmf
    ${outroot}_bkg.pi
    ${outroot}_grp.pi
    ${outroot}_nopsf.arf

Region files:
    ${outroot}_bkgreg.fits
    ${outroot}_srcreg.fits

Light curves
    ${outroot}_${band}.gllc
    ${outroot}_${band}.lc

Postage stamp images
    ${outroot}_${band}_flux.img
    ${outroot}_${band}_thresh.expmap
    ${outroot}_${band}_thresh.img

PSF (only if psfmethod=marx)
    ${outroot}_${band}_projrays.fits
    ${outroot}_${band}.psf

aprates probability density function
    ${outroot}_${band}_rates.prob

"""


import sys
import os
from collections import namedtuple
ReturnValue = namedtuple('ReturnValue', 'name value units description')

import numpy as np

def srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin:  Compute hardness ratios
    
    This is an example of a plugin where we know (require) there to be 
    multiple energy bands.  We use the output .flux files to get the 
    counts and compute several hardness ratio values.    
    """

    from pycrates import read_file

    if band != "hard":
        return []

    base_root = outroot.replace(f"_{src_num:04d}","")

    soft_file = f"{base_root}_soft.flux"
    medium_file = f"{base_root}_medium.flux"
    hard_file = f"{base_root}_medium.flux"
    
    for check in [soft_file, medium_file, hard_file]:    
        if not os.path.exists(check):
            sys.stderr.write(f"ERROR: Cannot find the flux file: {check}")
            return []

    # Note: python index = src_num - 1 
    soft_counts = read_file(soft_file).get_column("COUNTS").values[src_num-1]
    medium_counts = read_file(medium_file).get_column("COUNTS").values[src_num-1]
    hard_counts = read_file(hard_file).get_column("COUNTS").values[src_num-1]
    
    hard_hm = (hard_counts - medium_counts)/(hard_counts + medium_counts)
    hard_hs = (hard_counts - soft_counts)/(hard_counts + soft_counts)
    hard_ms = (medium_counts - soft_counts)/(medium_counts + soft_counts)

    retval = [ReturnValue("hard_hm", hard_hm, "", "Hardness Ration (hard to medium)"),
              ReturnValue("hard_hs", hard_hm, "", "Hardness Ration (hard to soft)"),
              ReturnValue("hard_ms", hard_hm, "", "Hardness Ration (medium to soft)"),
              ]

    return retval
    



def radial_profile_example_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin: running dmextract to create radial profiles
    
    This sample plugin uses dmextract to create radial profiles
    of both the source and the PSF. This plugin shows how to 
    use the infile (event file) and the energy lo/hi parameters.    
    """
    from ciao_contrib.runtool import make_tool
    from pycrates import read_file
    
    tab = read_file(f"{outroot}_srcreg.fits")
    x = tab.get_column("x").values[0]
    y = tab.get_column("y").values[0]
    rr = max(tab.get_column("r").values[0])
    rlo = 0
    rhi = 2*rr
    nbin = 10
    step = (rhi-rlo)/nbin

    bin_cmd = f"[bin sky=annulus({x},{y},{rlo}:{rhi}:{step})]"

    dme = make_tool("dmextract")
    dme.infile = f"{infile}[energy={elo}:{ehi}]"+bin_cmd
    dme.outfile = f"{outroot}_{band}.evt.rprof"
    dme(clobber=True, opt="generic")
    
    dme.infile = f"{outroot}_{band}_projrays.fits"+bin_cmd
    dme.outfile = f"{outroot}_{band}.psf.rprof"
    dme(clobber=True, opt="generic")
    
    return []
    


def arestore_sample_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin: running arestore to create a deconvolved image
    
    This plugin runs the arestore tool to create a deconvolved image.
    It does not return any values to store in the output .flux file
    (so it needs to return an empty list).
    
    This plugin creates some temporary files so it also must delete them.    
    """
    
    
    from ciao_contrib.runtool import make_tool
    from pycrates import read_file
    
    ri = make_tool("reproject_image")
    ri.infile = f"{outroot}_{band}.psf"
    ri.matchfile = f"{outroot}_{band}_thresh.img"
    ri.outfile = f"{outroot}_{band}.psf_crop"
    ri(clobber=True)

    tab = read_file(f"{outroot}_srcreg.fits")
    x = tab.get_column("x").values[0]
    y = tab.get_column("y").values[0]
    dmc = make_tool("dmcoords")
    dmc.punlearn()
    dmc(infile=f"{outroot}_{band}_thresh.img", x=x, y=y, op="sky")
    
    arestore = make_tool("arestore")
    arestore.infile = f"{outroot}_{band}_thresh.img"
    arestore.psffile = ri.outfile
    arestore.outfile = f"{outroot}_{band}.deconvolve"
    arestore.psf_x_center = dmc.logicalx
    arestore.psf_y_center = dmc.logicaly
    
    try:
        arestore(numiter=50, clobber=True)
    except Exception as wrong:
        sys.stderr.write(str(wrong)+"\n")
    finally:
        if os.path.exists(ri.outfile):
            os.unlink(ri.outfile)
    
    return []  #  No values are returned



def srcextent_sample_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin: running srcextent to check for source extent
    
    A simple plugin to run the srcextent tool to check for source extent.    
    """

    from ciao_contrib.runtool import make_tool
    from pycrates import read_file
    sext = make_tool("srcextent")
    
    sext.srcfile = f"{outroot}_{band}_thresh.img"
    sext.psffile = f"{outroot}_{band}_projrays.fits"
    if not os.path.exists(sext.psffile):
        sys.stderr.write(f"ERROR: Cannot find PSF file '{sext.psffile}' for user plugin")
        return [ReturnValue("EXTENT_FLAG", False, "", "Does srcextent think src is extended")]
    sext.regfile = f"{outroot}_srcreg.fits"
    sext.outfile = f"{outroot}_{band}.srcext"

    try:
        sext(clobber=True)
        tab = read_file(sext.outfile)
        is_extended = (tab.get_column("EXTENT_FLAG").values[0] == 1)
        
        retval = [ReturnValue("EXTENT_FLAG", is_extended, "", "Does srcextent think src is extended")]
        
    except Exception as wrong:
        sys.stderr.write(str(wrong)+"\n")
        retval = [ReturnValue("EXTENT_FLAG", False, "", "Does srcextent think src is extended")]
    
    return retval
        

from sherpa.astro.ui import *
def spectral_fit_sammple_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """    
    Sample plugin: fitting spectrum.
    
    This sample plugin uses sherpa to fit a spectral model, and 
    return an estimate of the flux w/ errors calculated with
    the sample_flux routine.    
    """
    from sherpa.utils.logging import SherpaVerbosity
    
    try:
        load_data(outroot+".pi")
        group_counts(1)
        set_source(xsphabs.abs1*xspowerlaw.pl1)
        set_method("simplex")
        notice(0.5,8.0)
        with SherpaVerbosity('WARN'):
            fit()        
            fit_info = get_fit_results()            
            fflux, cflux, vals = sample_flux(lo=2.0, hi=10.0)
            f0, fhi, flo = cflux
                
        retval = [ReturnValue("fitted_Nh", abs1.nH.val, "cm**-22", "Fitted Absorption value"),
                  ReturnValue("photon_index", pl1.PhoIndex.val, "", "Fitted Photon Index"),
                  ReturnValue("normalization", pl1.norm.val, "", "Spectrum Normalization"),
                  ReturnValue("reduced_statistic", fit_info.rstat, "", "Reduced Fit Statistic"),
                  ReturnValue("fit_statistic", fit_info.statval, "", "Fit Statistic"),
                  ReturnValue("dof", fit_info.dof, "", "Degrees of Freedom"),
                  ReturnValue("sample_flux", f0, "", "2-10 keV Sample Flux"),
                  ReturnValue("sample_flux_lo", flo, "", "2-10 keV Sample Flux Uncertainty Low"),
                  ReturnValue("sample_flux_hi", fhi, "", "2-10 Sample Flux Uncertainty Low"),
                  ]
    except Exception as wrong:
        sys.stderr.write(str(wrong)+"\n")
        sys.stderr.write(f"Problem fitting {outroot} spectrum. Skipping it.")

        retval = [ReturnValue("fitted_Nh", np.nan, "cm**22", "Fitted Absorption value"),
                  ReturnValue("photon_index", np.nan, "", "Fitted Photon Index"),
                  ReturnValue("normalization", np.nan, "", "Spectrum Normalization"),
                  ReturnValue("reduced_statistic", np.nan, "", "Reduced Fit Statistic"),
                  ReturnValue("fit_statistic", np.nan, "", "Fit Statistic"),
                  ReturnValue("dof", np.nan, "", "Degrees of Freedom"),
                  ReturnValue("sample_flux", np.nan, "", "2-10 keV Sample Flux"),
                  ReturnValue("sample_flux_lo", np.nan, "", "2-10 Sample Flux Uncertainty Low"),
                  ReturnValue("sample_flux_hi", np.nan, "", "2-10 Sample Flux Uncertainty Low"),                  
                  ]


    return retval
    
