
"Sample plugin file for srcflux"


"""
These are the files that will be available for the plugin to use.
For a single input event file, the ${outroot} will be the same as 
the outroot parameter.  For multiple input event files, 
the obi number is appended to the outroot parameter.

    The main output files w/ all the src properties:
        ${outroot}_${band}.flux

    Files used for spectral fits:
        ${outroot}.arf
        ${outroot}.pi
        ${outroot}.rmf
        ${outroot}_bkg.pi
        ${outroot}_bkg.arf   (only if bkgresp=yes)
        ${outroot}_bkg.rmf   (only if bkgresp=yes)
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

For multiple input event files, these files will be available to the 
plugin. The outroot is the same as the outroot parameter.

    The main output files w/ all the src properties:
        ${outroot}_${band}.flux

    Files used for spectral fits:
        ${outroot}_src.arf   \
        ${outroot}_src.pi     - Note: merge file names have _src 
        ${outroot}_src.rmf   /
        ${outroot}_bkg.pi
        ${outroot}_bkg.arf   (only if bkgresp=yes)
        ${outroot}_bkg.rmf   (only if bkgresp=yes)



"""


import sys
import os
from collections import namedtuple
ReturnValue = namedtuple('ReturnValue', 'name value units description')

import numpy as np

def srcflux_merge_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin: combining obi images
    
    This sample plugin combines the per-source images and exposure maps
    for each observation where the source is inside the field of view.
    
    This is a little bit more tricky only because we need to 
    use different file name roots to access the merged .flux file
    and for the individual per-source, per-band files.
    """

    from pycrates import read_file
    from ciao_contrib.runtool import make_tool

    src_num_str = f"_{src_num:04d}"
    merge_root = outroot.replace(src_num_str, "")
    
    valid_obi = read_file(merge_root+f"_{band}.flux").get_column("INSIDE_FOV").values[src_num-1]
    
    img_files = []
    expmap_files = []
    for obi,flag in enumerate(valid_obi):
        # Check to see if source is inside the FOV, if not, then skip it.
        if not flag:
            continue

        obi_num = obi+1
        obi_root = outroot.replace(src_num_str, f"_obi{obi_num:03d}{src_num_str}")
        
        img_file = obi_root+f"_{band}_thresh.img"
        if not os.path.exists(img_file):
            print(f"MISSING {img_file}")
            continue

        expmap_file = obi_root+f"_{band}_thresh.expmap"
        if not os.path.exists(expmap_file):
            print(f"MISSING {expmap_file}")
            continue        

        img_files.append(img_file)
        expmap_files.append(expmap_file)

    if len(img_files) == 0:
        return []

    #
    # Note: This is just for illustrative purposes.  For the counts image, 
    # it would be better to reproject the events to a common tangent 
    # point and combine them that way.  Luckily since we used
    # fluximage to create the images, they are all nicely aligned on 
    # half-pixel boundaries so we don't end up with any odd partial-pixels
    # when regridding (essentially a 'blurring' effect).
    #
        
    reproj_img = make_tool("reproject_image")
    
    reproj_img.infile = img_files
    reproj_img.outfile = outroot+"_merge.img"
    reproj_img.matchfile = img_files[0]
    reproj_img.method = "sum"
    reproj_img(clobber=True)

    reproj_img.infile = expmap_files
    reproj_img.outfile = outroot+"_merge.expmap"
    reproj_img.matchfile = expmap_files[0]
    reproj_img.method = "average"
    reproj_img(clobber=True)
        
    return []


def spectral_fit_sample_srcflux_merge_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin: fit combined spectra.
    
    This sample plugin shows how to use the same per-obi plugin on
    the already combined spectrum files.    
    """

    retval = spectral_fit_sample_srcflux_obsid_plugin( infile, outroot, band, elo, ehi, src_num)
    return retval



def hardness_ratio_sample_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
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
def spectral_fit_sample_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """    
    Sample plugin: fitting spectrum.
    
    This sample plugin uses sherpa to fit a spectral model, and 
    return an estimate of the flux w/ errors calculated with
    the sample_flux routine.    
    """
    from sherpa.utils.logging import SherpaVerbosity
    

    try:
        if os.path.exists(outroot+".pi"):
            pi_file = outroot+".pi"
        elif os.path.exists(outroot+"_src.pi"):
            pi_file = outroot+"_src.pi"
        else:
            raise IOError(f"Unable to locate source spectrum for this source number: {src_num}")

        load_data(pi_file)
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
    


def aplimits_srcflux_obsid_plugin(infile, outroot, band, elo, ehi, src_num):
    """
    Sample plugin: aplimits
    
    This plugin runs the new `aplimits` script to compute
    upper limits and rate limits on false detections.    
    """

    from paramio import pgetd, pgeti
    from ciao_contrib.runtool import make_tool
    from pycrates import read_file
    
    index = src_num-1
    aplimits = make_tool("aplimits")

    aplimits.prob_false_detection = 0.05
    aplimits.prob_missed_detection = 0.5

    base_root = outroot.replace(f"_{src_num:04d}","")
    infile = f"{base_root}_{band}.flux"

    tab = read_file(infile)
    aplimits.T_s = tab.get_column("EXPOSURE").values[index]
    aplimits.A_s = tab.get_column("AREA").values[index]
    aplimits.m = tab.get_column("BG_COUNTS").values[index]
    aplimits.T_b = aplimits.T_s
    aplimits.A_b = tab.get_column("BG_AREA").values[index]
    aplimits.outfile = f"{outroot}_lims.par"
    aplimits(clobber=True)
    
    psf_frac = tab.get_column("PSFFRAC").values[index]

    return [ReturnValue('SRC_RATE_UPPER_LIMIT', 
                        pgetd(aplimits.outfile, "upper_limit")/psf_frac, 
                        "counts/sec", 
                        "Upper limit on 50% probability of missed source"),
            ReturnValue('SRC_MIN_COUNTS_DETECT',
                        pgeti(aplimits.outfile, "min_counts_detect"),
                        "counts",
                        "Min counts for 5% probability of false detect")]
     
    
    
