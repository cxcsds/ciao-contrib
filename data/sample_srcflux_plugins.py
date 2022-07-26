
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

from sherpa.astro.ui import *
import numpy as np



def srcflux_obsid_plugin(infile, outroot, band, elo, ehi):
    from ciao_contrib.runtool import make_tool
    from pycrates import read_file
    
    ri = make_tool("reproject_image")
    ri.infile = f"{outroot}_{band}.psf"
    ri.matchfile =f"{outroot}_{band}_thresh.img"
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
        print(wrong)
    
    return []  #  No values are returned



def srcextent_sample_srcflux_obsid_plugin(infile, outroot, band, elo, ehi):

    from ciao_contrib.runtool import make_tool
    from pycrates import read_file
    sext = make_tool("srcextent")
    
    sext.srcfile = f"{outroot}_{band}_thresh.img"
    sext.psffile = f"{outroot}_{band}_projrays.fits"
    if not os.path.exists(sext.psffile):
        sys.stderr.write("Cannot find PSF file for user plugin")
        return [ReturnValue("EXTENT_FLAG", False, "", "Does srcextent think src is extended")]
    sext.regfile = f"{outroot}_srcreg.fits"
    sext.outfile = f"{outroot}_{band}.srcext"

    try:
        sext(clobber=True)
        tab = read_file(sext.outfile)
        is_extended = (tab.get_column("EXTENT_FLAG").values[0] == 1)
        
        retval = [ReturnValue("EXTENT_FLAG", is_extended, "", "Does srcextent think src is extended")]
        
    except Exception as wrong:
        print(wrong)
        retval = [ReturnValue("EXTENT_FLAG", False, "", "Does srcextent think src is extended")]
    
    return retval
    
    



def spectral_fit_sammple_srcflux_obsid_plugin(infile, outroot, band, elo, ehi):
    """    
    
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
        print(wrong)
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
    
