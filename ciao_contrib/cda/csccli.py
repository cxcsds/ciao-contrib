#
# Copyright (C) 2013, 2016, 2019, 2023, 2024
#               Smithsonian Astrophysical Observatory
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
"""
Collection of routines to access the Chandra Source Catalog
command line interface to perform specific queries.

Additionally can be used to retrieve files using the CSC file
retrieve interface.

"""

import os

import ciao_contrib.logger_wrapper as lw


logger = lw.initialize_module_logger("cda.csccli")

verb0 = logger.verbose0
verb1 = logger.verbose1
verb2 = logger.verbose2
verb3 = logger.verbose3
verb4 = logger.verbose4
verb5 = logger.verbose5


__all__ = (
    'check_filetypes',
    'check_bandtypes',
    'search_src_by_ra_dec',
    'search_src_by_obsid',
    'save_results',
    'parse_csc_result',
    'retrieve_files',
    'summarize_results',
    'get_default_columns',
    'check_required_names',
    'extra_cols_to_summarize'
)

# Confirm, need rel1.1 to get HRC data for csc1
__csc_version = {'csc1' : 'rel1.1', 'csc2' : 'rel2.0', 'csc2.1': 'rel2.1',
                 'current': 'cur'}


fileTypes_csc1 = {
    # Note: reg3 aka srcreg is unique in that it is per source, but has det version number
    # HRC does not have pha nor rmf files
    "evt"    : { "extn" : "evt3",    "filetype" : "evt3",       "version" : "cal", "obilevel" : True,  "bands" : False,  "acisonly" : False },
    "exp"    : { "extn" : "exp3",    "filetype" : "expmap",     "version" : "cal", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "ahst"   : { "extn" : "ahst3",   "filetype" : "asphist",    "version" : "cal", "obilevel" : True,  "bands" : False , "acisonly" : False },
    "bpix"   : { "extn" : "bpix3",   "filetype" : "badpix3",    "version" : "cal", "obilevel" : True,  "bands" : False , "acisonly" : False },
    "fov"    : { "extn" : "fov3",    "filetype" : "fov3",       "version" : "cal", "obilevel" : True,  "bands" : False , "acisonly" : False },
    "bkgimg" : { "extn" : "bkgimg3", "filetype" : "bkgimg",     "version" : "det", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "sens"   : { "extn" : "sens3",   "filetype" : "sensity",    "version" : "det", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "img"    : { "extn" : "img3",    "filetype" : "ecorrimg",   "version" : "det", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "reg"    : { "extn" : "reg3",    "filetype" : "srcreg",     "version" : "det", "obilevel" : False, "bands" : False , "acisonly" : False },
    "arf"    : { "extn" : "arf3",    "filetype" : "arf",        "version" : "src", "obilevel" : False, "bands" : False , "acisonly" : False },
    "rmf"    : { "extn" : "rmf3",    "filetype" : "rmf",        "version" : "src", "obilevel" : False, "bands" : False , "acisonly" : True },
    "pha"    : { "extn" : "pha3",    "filetype" : "spectrum",   "version" : "src", "obilevel" : False, "bands" : False , "acisonly" : True },
    "regevt" : { "extn" : "regevt3", "filetype" : "regevt3",    "version" : "src", "obilevel" : False, "bands" : False , "acisonly" : False },
    "regexp" : { "extn" : "regexp3", "filetype" : "regexpmap",  "version" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "regimg" : { "extn" : "regimg3", "filetype" : "regimg",     "version" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "psf"    : { "extn" : "psf3",    "filetype" : "psf",        "version" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "lc"     : { "extn" : "lc3",     "filetype" : "lightcurve", "version" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False }
    }


fileTypes_cur = {
    "evt"    : { "extn" : "evt3",    "filetype" : "evt3",       "prodlevel" : "obi", "obilevel" : True,  "bands" : False,  "acisonly" : False },
    "asol"   : { "extn" : "asol3",   "filetype" : "aspsol3",    "prodlevel" : "obi", "obilevel" : True,  "bands" : False,  "acisonly" : False },
    "ahst"   : { "extn" : "ahst3",   "filetype" : "asphist",    "prodlevel" : "obi", "obilevel" : True,  "bands" : False , "acisonly" : False },
    "bpix"   : { "extn" : "bpix3",   "filetype" : "badpix3",    "prodlevel" : "obi", "obilevel" : True,  "bands" : False , "acisonly" : False },
    "fov"    : { "extn" : "fov3",    "filetype" : "fov3",       "prodlevel" : "obi", "obilevel" : True,  "bands" : False , "acisonly" : False },
    "pixmask": { "extn" : "pixmask3","filetype" : "pixmask",    "prodlevel" : "obi", "obilevel" : True,  "bands" : False , "acisonly" : False },

    "img"    : { "extn" : "img3",    "filetype" : "ecorrimg",   "prodlevel" : "obi", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "bkgimg" : { "extn" : "bkgimg3", "filetype" : "bkgimg",     "prodlevel" : "obi", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "exp"    : { "extn" : "exp3",    "filetype" : "expmap",     "prodlevel" : "obi", "obilevel" : True,  "bands" : True ,  "acisonly" : False },
    "poly"   : { "extn" : "poly3",   "filetype" : "poly3",      "prodlevel" : "obi", "obilevel" : True,  "bands" : True ,  "acisonly" : False },

    # Per obi, per region,     HRC does not have pha nor rmf files
    "regevt" : { "extn" : "regevt3", "filetype" : "regevt3",    "prodlevel" : "src", "obilevel" : False, "bands" : False , "acisonly" : False },
    "pha"    : { "extn" : "pha3",    "filetype" : "spectrum",   "prodlevel" : "src", "obilevel" : False, "bands" : False , "acisonly" : True  },
    "arf"    : { "extn" : "arf3",    "filetype" : "arf",        "prodlevel" : "src", "obilevel" : False, "bands" : False , "acisonly" : False },
    "rmf"    : { "extn" : "rmf3",    "filetype" : "rmf",        "prodlevel" : "src", "obilevel" : False, "bands" : False , "acisonly" : True  },
    "reg"    : { "extn" : "reg3",    "filetype" : "srcreg",     "prodlevel" : "src", "obilevel" : False, "bands" : False , "acisonly" : False },

    "regimg"  : { "extn" : "regimg3", "filetype" : "regimg",     "prodlevel" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "psf"     : { "extn" : "psf3",    "filetype" : "psf",        "prodlevel" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "regexp"  : { "extn" : "regexp3", "filetype" : "regexpmap",  "prodlevel" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "lc"      : { "extn" : "lc3",     "filetype" : "lightcurve", "prodlevel" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "draws"   : { "extn" : "draws3",  "filetype" : "draws",      "prodlevel" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },
    "aperphot": { "extn" : "phot3",   "filetype" : "aperphot",   "prodlevel" : "src", "obilevel" : False, "bands" : True ,  "acisonly" : False },

    # Stack
    "stkevt"      : { "extn" : "evt3",    "filetype" : "stkevt3",    "prodlevel" : "stk", "obilevel" : True , "bands" : False,  "acisonly" : False },
    "stkfov"      : { "extn" : "fov3",    "filetype" : "stkfov3",    "prodlevel" : "stk", "obilevel" : True , "bands" : False,  "acisonly" : False },
    "stkecorrimg" : { "extn" : "img3",    "filetype" : "stkecorrimg","prodlevel" : "stk", "obilevel" : True , "bands" : True ,  "acisonly" : False },
    "stkbkgimg"   : { "extn" : "bkgimg3", "filetype" : "stkbkgimg",  "prodlevel" : "stk", "obilevel" : True , "bands" : True ,  "acisonly" : False },
    "stkexpmap"   : { "extn" : "exp3",    "filetype" : "stkexpmap",  "prodlevel" : "stk", "obilevel" : True , "bands" : True ,  "acisonly" : False },
    "sensity"     : { "extn" : "sens3",   "filetype" : "sensity",    "prodlevel" : "stk", "obilevel" : True , "bands" : True ,  "acisonly" : False },

    # These are per region too
    "stkregevt"   : { "extn" : "regevt3", "filetype" : "stkregevt3", "prodlevel" : "stk", "obilevel" : False, "bands" : False,  "acisonly" : False },
    "stksrcreg"   : { "extn" : "reg3",    "filetype" : "stksrcreg",  "prodlevel" : "stk", "obilevel" : False, "bands" : False,  "acisonly" : False },
    "stkregimg"   : { "extn" : "regimg3", "filetype" : "stkregimg",  "prodlevel" : "stk", "obilevel" : False, "bands" : True,   "acisonly" : False },
    "stkregimg_jpg"   : { "extn" : "regimg3", "filetype" : "stkregimg_jpg",  "prodlevel" : "stk", "obilevel" : False, "bands" : False,   "acisonly" : False },
    "stkregexp"   : { "extn" : "regexp3", "filetype" : "stkregexp",  "prodlevel" : "stk", "obilevel" : False, "bands" : True,   "acisonly" : False },
    "stkdraws"    : { "extn" : "draws3",  "filetype" : "stkdraws",   "prodlevel" : "stk", "obilevel" : False, "bands" : True,   "acisonly" : False },
    "stkaperphot" : { "extn" : "phot3",   "filetype" : "stkaperphot","prodlevel" : "stk", "obilevel" : False, "bands" : True,   "acisonly" : False },

    # master
    "mrgsrc"      : { "extn" : "mrgsrc3", "filetype" : "mrgsrc",     "prodlevel" : "stk", "obilevel" : False, "bands" : False,   "acisonly" : False },
    "bayesblks"   : { "extn" : "blocks3", "filetype" : "bayesblks",  "prodlevel" : "mst", "obilevel" : False, "bands" : False,   "acisonly" : False },
    "srcaperphot" : { "extn" : "phot3",   "filetype" : "srcaperphot","prodlevel" : "mst", "obilevel" : False, "bands" : True,    "acisonly" : False },
    "srcpoly"     : { "extn" : "poly3",   "filetype" : "srcpoly3",   "prodlevel" : "mst", "obilevel" : False, "bands" : False,   "acisonly" : False },
}

fileTypes = {
    "csc1" : fileTypes_csc1,
    "csc2"  : fileTypes_cur,
    "csc2.1" : fileTypes_cur,
    "current" : fileTypes_cur
}


bands = {
    "ACIS" : { 'broad' : 'b', 'soft' : 's', 'medium' : 'm', 'hard' : 'h', 'ultrasoft' : 'u' },
    "HRC"  : { 'wide' : 'w' }
    }

matchtypes = {
    'a' : 'confused',
    'u' : 'unique',
    'n' : 'nodetect'
}


default_cols = """
m.name,
m.ra,
m.dec,
m.err_ellipse_r0,
m.conf_flag,
m.sat_src_flag,
m.significance,
m.flux_aper_b,
m.flux_aper_lolim_b,
m.flux_aper_hilim_b,
m.flux_aper_w,
m.flux_aper_lolim_w,
m.flux_aper_hilim_w,
m.extent_flag,
m.hard_hm,
m.hard_hm_lolim,
m.hard_hm_hilim,
m.hard_ms,
m.hard_ms_lolim,
m.hard_ms_hilim,
m.var_intra_index_b,
m.var_inter_index_b,
m.var_intra_index_w,
m.var_inter_index_w,
a.match_type,
o.obsid,
o.obi,
o.region_id,
o.instrument,
o.theta,
o.phi,
o.livetime,
o.conf_code,
o.sat_src_flag as obi_sat_src_flag,
o.flux_significance_b,
o.flux_significance_w,
o.detector,
o.extent_code,
o.mjr_axis_raw_b,
o.mnr_axis_raw_b,
o.pos_angle_raw_b,
o.mjr_axis_raw_w,
o.mnr_axis_raw_w,
o.pos_angle_raw_w,
o.cnts_aper_b,
o.cnts_aper_w,
o.src_rate_aper_b,
o.src_rate_aper_w,
o.flux_aper_b as obi_flux_aper_b,
o.flux_aper_lolim_b as obi_flux_aper_lolim_b,
o.flux_aper_hilim_b as obi_flux_aper_hilim_b,
o.flux_aper_w as obi_flux_aper_w,
o.flux_aper_lolim_w as obi_flux_aper_lolim_w,
o.flux_aper_hilim_w as obi_flux_aper_hilim_w,
o.hard_hm as obi_hard_hm,
o.hard_hm_lolim as obi_hard_hm_lolim,
o.hard_hm_hilim as obi_hard_hm_hilim,
o.hard_ms as obi_hard_ms,
o.hard_ms_hilim as obi_hard_ms_hilim,
o.hard_ms_lolim as obi_hard_ms_lolim,
o.var_index_b,
o.var_index_w
""".replace("\n", "").split(",")


csc1_columns = {
    'master_source_basic_summary' : """
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,
    m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,
    m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,
    m.flux_aper_hilim_w
    """.replace("\n", "").replace(" ","").split(",") ,

    'master_source_summary' : """
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,
    m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,
    m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.extent_flag,
    m.hard_hm,m.hard_hm_lolim,m.hard_hm_hilim,m.hard_ms,m.hard_ms_lolim,
    m.hard_ms_hilim,m.var_intra_index_b,m.var_inter_index_b,
    m.var_intra_index_w,m.var_inter_index_w
    """.replace("\n", "").replace(" ","").split(",") ,

    'master_source_photometry':"""
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,
    m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,
    m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.flux_aper_s,
    m.flux_aper_lolim_s,m.flux_aper_hilim_s,m.flux_aper_m,
    m.flux_aper_lolim_m,m.flux_aper_hilim_m,m.flux_aper_h,
    m.flux_aper_lolim_h,m.flux_aper_hilim_h,m.flux_powlaw_aper_b,
    m.flux_powlaw_aper_lolim_b,m.flux_powlaw_aper_hilim_b,
    m.flux_powlaw_aper_w,m.flux_powlaw_aper_lolim_w,
    m.flux_powlaw_aper_hilim_w,m.flux_bb_aper_b,m.flux_bb_aper_lolim_b,
    m.flux_bb_aper_hilim_b,m.flux_bb_aper_w,m.flux_bb_aper_lolim_w,
    m.flux_bb_aper_hilim_w
    """.replace("\n", "").replace(" ","").split(","),

    'master_source_variability': """
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,
    m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,
    m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,
    m.var_intra_prob_b,m.var_intra_index_b,m.var_inter_prob_b,
    m.var_inter_index_b,m.var_intra_prob_w,m.var_intra_index_w,
    m.var_inter_prob_w,m.var_inter_index_w,m.var_intra_prob_s,
    m.var_intra_index_s,m.var_inter_prob_s,m.var_inter_index_s,
    m.var_intra_prob_m,m.var_intra_index_m,m.var_inter_prob_m,
    m.var_inter_index_m,m.var_intra_prob_h,m.var_intra_index_h,
    m.var_inter_prob_h,m.var_inter_index_h
    """.replace("\n", "").replace(" ","").split(","),

    'source_observation_summary': """
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,
    m.significance,m.flux_aper_b,m.flux_aper_lolim_b,
    m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,
    m.flux_aper_hilim_w,o.obsid,o.obi,o.region_id,o.theta,o.phi,o.livetime,
    o.conf_code,o.sat_src_flag,o.flux_significance_b,
    o.flux_significance_w,o.detector,o.extent_code,o.mjr_axis_raw_b,
    o.mnr_axis_raw_b,o.pos_angle_raw_b,o.mjr_axis_raw_w,o.mnr_axis_raw_w,
    o.pos_angle_raw_w,o.cnts_aper_b,o.cnts_aper_w,o.src_rate_aper_b,
    o.src_rate_aper_w,o.flux_aper_b,o.flux_aper_lolim_b,
    o.flux_aper_hilim_b,o.flux_aper_w,o.flux_aper_lolim_w,
    o.flux_aper_hilim_w,o.hard_hm,o.hard_hm_lolim,o.hard_hm_hilim,
    o.hard_ms,o.hard_ms_hilim,o.hard_ms_lolim,o.var_index_b,o.var_index_w
    """.replace("\n", "").replace(" ","").split(","),

    'source_observation_photometry' : """
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,
    m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,
    m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,o.obsid,o.obi,
    o.region_id,o.theta,o.phi,o.livetime,o.conf_code,o.sat_src_flag,
    o.flux_significance_b,o.flux_significance_w,o.cnts_aper_b,
    o.cnts_aper_w,o.cnts_aper_s,o.cnts_aper_m,o.cnts_aper_h,
    o.src_rate_aper_b,o.src_rate_aper_w,o.src_rate_aper_s,
    o.src_rate_aper_m,o.src_rate_aper_h,o.flux_aper_b,o.flux_aper_lolim_b,
    o.flux_aper_hilim_b,o.flux_aper_w,o.flux_aper_lolim_w,
    o.flux_aper_hilim_w,o.flux_aper_s,o.flux_aper_lolim_s,
    o.flux_aper_hilim_s,o.flux_aper_m,o.flux_aper_lolim_m,
    o.flux_aper_hilim_m,o.flux_aper_h,o.flux_aper_lolim_h,
    o.flux_aper_hilim_h
    """.replace("\n", "").replace(" ","").split(","),

    'source_observation_variability' :"""
    m.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,
    m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,
    m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,o.obsid,o.obi,
    o.region_id,o.theta,o.phi,o.livetime,o.conf_code,o.sat_src_flag,
    o.flux_significance_b,o.flux_significance_w,o.dither_warning_flag,
    o.ks_prob_b,o.kp_prob_b,o.var_prob_b,o.var_index_b,o.var_mean_b,
    o.var_sigma_b,o.ks_prob_w,o.kp_prob_w,o.var_prob_w,o.var_index_w,
    o.var_mean_w,o.var_sigma_w,o.ks_prob_s,o.kp_prob_s,o.var_prob_s,
    o.var_index_s,o.var_mean_s,o.var_sigma_s,o.ks_prob_m,o.kp_prob_m,
    o.var_prob_m,o.var_index_m,o.var_mean_m,o.var_sigma_m,o.ks_prob_h,
    o.kp_prob_h,o.var_prob_h,o.var_index_h,o.var_mean_h,o.var_sigma_h
    """.replace("\n", "").replace(" ","").split(",")
}


csc2_columns = {
  'master_source_basic_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w'.split(","),                                   
  'master_source_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.extent_flag,m.hard_hm,m.hard_hm_lolim,m.hard_hm_hilim,m.hard_ms,m.hard_ms_lolim,m.hard_ms_hilim,m.var_intra_index_b,m.var_inter_index_b,m.var_intra_index_w,m.var_inter_index_w'.split(","),
  'master_source_photometry' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.flux_aper_s,m.flux_aper_lolim_s,m.flux_aper_hilim_s,m.flux_aper_m,m.flux_aper_lolim_m,m.flux_aper_hilim_m,m.flux_aper_h,m.flux_aper_lolim_h,m.flux_aper_hilim_h,m.flux_powlaw_aper_b,m.flux_powlaw_aper_lolim_b,m.flux_powlaw_aper_hilim_b,m.flux_powlaw_aper_w,m.flux_powlaw_aper_lolim_w,m.flux_powlaw_aper_hilim_w,m.flux_bb_aper_b,m.flux_bb_aper_lolim_b,m.flux_bb_aper_hilim_b,m.flux_bb_aper_w,m.flux_bb_aper_lolim_w,m.flux_bb_aper_hilim_w'.split(","),
  'master_source_variability' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.var_intra_prob_b,m.var_intra_index_b,m.var_inter_prob_b,m.var_inter_index_b,m.var_intra_prob_w,m.var_intra_index_w,m.var_inter_prob_w,m.var_inter_index_w,m.var_intra_prob_s,m.var_intra_index_s,m.var_inter_prob_s,m.var_inter_index_s,m.var_intra_prob_m,m.var_intra_index_m,m.var_inter_prob_m,m.var_inter_index_m,m.var_intra_prob_h,m.var_intra_index_h,m.var_inter_prob_h,m.var_inter_index_h'.split(","),
  'stack_source_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,s.detect_stack_id,s.region_id,s.livetime,s.conf_code,s.sat_src_flag,s.flux_significance_b,s.flux_significance_w,s.extent_code,s.major_axis_b,s.minor_axis_b,s.pos_angle_b,s.major_axis_w,s.minor_axis_w,s.pos_angle_w,s.src_rate_aper_b,s.src_rate_aper_w,s.flux_aper_b,s.flux_aper_lolim_b,s.flux_aper_hilim_b,s.flux_aper_w,s.flux_aper_lolim_w,s.flux_aper_hilim_w,s.hard_hm,s.hard_hm_lolim,s.hard_hm_hilim,s.hard_ms,s.hard_ms_hilim,s.hard_ms_lolim'.split(","),
  'stack_source_photometry' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,s.detect_stack_id,s.region_id,s.livetime,s.conf_code,s.sat_src_flag,s.flux_significance_b,s.flux_significance_w,s.src_rate_aper_b,s.src_rate_aper_w,s.src_rate_aper_s,s.src_rate_aper_m,s.src_rate_aper_h,s.flux_aper_b,s.flux_aper_lolim_b,s.flux_aper_hilim_b,s.flux_aper_w,s.flux_aper_lolim_w,s.flux_aper_hilim_w,s.flux_aper_s,s.flux_aper_lolim_s,s.flux_aper_hilim_s,s.flux_aper_m,s.flux_aper_lolim_m,s.flux_aper_hilim_m,s.flux_aper_h,s.flux_aper_lolim_h,s.flux_aper_hilim_h'.split(","),
  'source_observation_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,o.obsid,o.obi,o.region_id,o.theta,o.phi,o.livetime,o.conf_code,o.sat_src_flag,o.flux_significance_b,o.flux_significance_w,o.detector,o.extent_code,o.major_axis_b,o.minor_axis_b,o.pos_angle_b,o.major_axis_w,o.minor_axis_w,o.pos_angle_w,o.cnts_aper_b,o.cnts_aper_w,o.src_rate_aper_b,o.src_rate_aper_w,o.flux_aper_b,o.flux_aper_lolim_b,o.flux_aper_hilim_b,o.flux_aper_w,o.flux_aper_lolim_w,o.flux_aper_hilim_w,o.hard_hm,o.hard_hm_lolim,o.hard_hm_hilim,o.hard_ms,o.hard_ms_hilim,o.hard_ms_lolim,o.var_index_b,o.var_index_w'.split(","),
  'source_observation_photometry' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,o.obsid,o.obi,o.region_id,o.theta,o.phi,o.livetime,o.conf_code,o.sat_src_flag,o.flux_significance_b,o.flux_significance_w,o.cnts_aper_b,o.cnts_aper_w,o.cnts_aper_s,o.cnts_aper_m,o.cnts_aper_h,o.src_rate_aper_b,o.src_rate_aper_w,o.src_rate_aper_s,o.src_rate_aper_m,o.src_rate_aper_h,o.flux_aper_b,o.flux_aper_lolim_b,o.flux_aper_hilim_b,o.flux_aper_w,o.flux_aper_lolim_w,o.flux_aper_hilim_w,o.flux_aper_s,o.flux_aper_lolim_s,o.flux_aper_hilim_s,o.flux_aper_m,o.flux_aper_lolim_m,o.flux_aper_hilim_m,o.flux_aper_h,o.flux_aper_lolim_h,o.flux_aper_hilim_h'.split(","),
  'source_observation_variability' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.conf_flag,m.sat_src_flag,m.significance,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,o.obsid,o.obi,o.region_id,o.theta,o.phi,o.livetime,o.conf_code,o.sat_src_flag,o.flux_significance_b,o.flux_significance_w,o.dither_warning_flag,o.ks_prob_b,o.kp_prob_b,o.var_prob_b,o.var_index_b,o.var_mean_b,o.var_sigma_b,o.ks_prob_w,o.kp_prob_w,o.var_prob_w,o.var_index_w,o.var_mean_w,o.var_sigma_w,o.ks_prob_s,o.kp_prob_s,o.var_prob_s,o.var_index_s,o.var_mean_s,o.var_sigma_s,o.ks_prob_m,o.kp_prob_m,o.var_prob_m,o.var_index_m,o.var_mean_m,o.var_sigma_m,o.ks_prob_h,o.kp_prob_h,o.var_prob_h,o.var_index_h,o.var_mean_h,o.var_sigma_h'.split(",")
}

csc21_columns = {
    'master_source_basic_summary': 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.significance,m.likelihood_class,m.conf_flag,m.sat_src_flag,m.streak_src_flag,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.flux_aper_avg_b,m.flux_aper_avg_lolim_b,m.flux_aper_avg_hilim_b,m.flux_aper_avg_w,m.flux_aper_avg_lolim_w,m.flux_aper_avg_hilim_w'.split(','),
    'master_source_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.significance,m.likelihood,m.likelihood_class,m.conf_flag,m.extent_flag,m.sat_src_flag,m.streak_src_flag,m.var_flag,m.var_inter_hard_flag,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.flux_aper_avg_b,m.flux_aper_avg_lolim_b,m.flux_aper_avg_hilim_b,m.flux_aper_avg_w,m.flux_aper_avg_lolim_w,m.flux_aper_avg_hilim_w,m.hard_hm,m.hard_hm_lolim,m.hard_hm_hilim,m.hard_ms,m.hard_ms_lolim,m.hard_ms_hilim,m.var_intra_index_b,m.var_intra_index_w,m.var_inter_index_b,m.var_inter_index_w,m.var_inter_hard_prob_hm,m.var_inter_hard_prob_ms,m.acis_time,m.hrc_time'.split(','),
    'master_source_photometry' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.significance,m.likelihood,m.likelihood_class,m.conf_flag,m.sat_src_flag,m.streak_src_flag,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_h,m.flux_aper_lolim_h,m.flux_aper_hilim_h,m.flux_aper_m,m.flux_aper_lolim_m,m.flux_aper_hilim_m,m.flux_aper_s,m.flux_aper_lolim_s,m.flux_aper_hilim_s,m.flux_aper_u,m.flux_aper_lolim_u,m.flux_aper_hilim_u,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.flux_aper_avg_b,m.flux_aper_avg_lolim_b,m.flux_aper_avg_hilim_b,m.flux_aper_avg_h,m.flux_aper_avg_lolim_h,m.flux_aper_avg_hilim_h,m.flux_aper_avg_m,m.flux_aper_avg_lolim_m,m.flux_aper_avg_hilim_m,m.flux_aper_avg_s,m.flux_aper_avg_lolim_s,m.flux_aper_avg_hilim_s,m.flux_aper_avg_u,m.flux_aper_avg_lolim_u,m.flux_aper_avg_hilim_u,m.flux_aper_avg_w,m.flux_aper_avg_lolim_w,m.flux_aper_avg_hilim_w,m.flux_powlaw_aper_b,m.flux_powlaw_aper_lolim_b,m.flux_powlaw_aper_hilim_b,m.flux_powlaw_aper_w,m.flux_powlaw_aper_lolim_w,m.flux_powlaw_aper_hilim_w,m.flux_bb_aper_b,m.flux_bb_aper_lolim_b,m.flux_bb_aper_hilim_b,m.flux_bb_aper_w,m.flux_bb_aper_lolim_w,m.flux_bb_aper_hilim_w,m.flux_brems_aper_b,m.flux_brems_aper_lolim_b,m.flux_brems_aper_hilim_b,m.flux_brems_aper_w,m.flux_brems_aper_lolim_w,m.flux_brems_aper_hilim_w'.split(','),
    'master_source_variability' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.significance,m.likelihood,m.likelihood_class,m.conf_flag,m.dither_warning_flag,m.sat_src_flag,m.streak_src_flag,m.var_flag,m.var_inter_hard_flag,m.flux_aper_b,m.flux_aper_lolim_b,m.flux_aper_hilim_b,m.flux_aper_w,m.flux_aper_lolim_w,m.flux_aper_hilim_w,m.var_intra_index_b,m.var_intra_index_h,m.var_intra_index_m,m.var_intra_index_s,m.var_intra_index_u,m.var_intra_index_w,m.var_intra_prob_b,m.var_intra_prob_h,m.var_intra_prob_m,m.var_intra_prob_s,m.var_intra_prob_u,m.var_intra_prob_w,m.var_inter_index_b,m.var_inter_index_h,m.var_inter_index_m,m.var_inter_index_s,m.var_inter_index_u,m.var_inter_index_w,m.var_inter_prob_b,m.var_inter_prob_h,m.var_inter_prob_m,m.var_inter_prob_s,m.var_inter_prob_u,m.var_inter_prob_w,m.var_inter_hard_prob_hm,m.var_inter_hard_prob_hs,m.var_inter_hard_prob_ms'.split(','),
    'stack_source_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.likelihood_class,s.detect_stack_id,s.region_id,s.theta_mean,s.flux_significance_b,s.flux_significance_w,s.likelihood_b,s.likelihood_w,s.conf_code,s.extent_code,s.sat_src_flag,s.streak_src_flag,s.var_flag,s.var_inter_hard_flag,s.major_axis_b,s.minor_axis_b,s.pos_angle_b,s.major_axis_w,s.minor_axis_w,s.pos_angle_w,s.src_cnts_aper_b,s.src_cnts_aper_w,s.src_rate_aper_b,s.src_rate_aper_w,s.flux_aper_b,s.flux_aper_lolim_b,s.flux_aper_hilim_b,s.flux_aper_w,s.flux_aper_lolim_w,s.flux_aper_hilim_w,s.hard_hm,s.hard_hm_lolim,s.hard_hm_hilim,s.hard_ms,s.hard_ms_lolim,s.hard_ms_hilim,s.var_intra_index_b,s.var_intra_index_w,s.var_inter_index_b,s.var_inter_index_w'.split(','),
    'stack_source_photometry' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.likelihood_class,s.detect_stack_id,s.region_id,s.theta_mean,s.flux_significance_b,s.flux_significance_h,s.flux_significance_m,s.flux_significance_s,s.flux_significance_u,s.flux_significance_w,s.likelihood_b,s.likelihood_h,s.likelihood_m,s.likelihood_s,s.likelihood_u,s.likelihood_w,s.conf_code,s.extent_code,s.sat_src_flag,s.streak_src_flag,s.var_flag,s.src_cnts_aper_b,s.src_cnts_aper_h,s.src_cnts_aper_m,s.src_cnts_aper_s,s.src_cnts_aper_u,s.src_cnts_aper_w,s.src_rate_aper_b,s.src_rate_aper_h,s.src_rate_aper_m,s.src_rate_aper_s,s.src_rate_aper_u,s.src_rate_aper_w,s.flux_aper_b,s.flux_aper_lolim_b,s.flux_aper_hilim_b,s.flux_aper_h,s.flux_aper_lolim_h,s.flux_aper_hilim_h,s.flux_aper_m,s.flux_aper_lolim_m,s.flux_aper_hilim_m,s.flux_aper_s,s.flux_aper_lolim_s,s.flux_aper_hilim_s,s.flux_aper_u,s.flux_aper_lolim_u,s.flux_aper_hilim_u,s.flux_aper_w,s.flux_aper_lolim_w,s.flux_aper_hilim_w '.split(','),
    'source_observation_summary' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.likelihood_class,o.obsid,o.obi,o.gti_obs,o.gti_end,o.region_id,o.theta,o.phi,o.flux_significance_b,o.flux_significance_w,o.likelihood_b,o.likelihood_w,o.conf_code,o.extent_code,o.sat_src_flag,o.streak_src_flag,o.var_code,o.major_axis_b,o.minor_axis_b,o.pos_angle_b,o.major_axis_w,o.minor_axis_w,o.pos_angle_w,o.cnts_aper_b,o.cnts_aper_w,o.src_cnts_aper_b,o.src_cnts_aper_w,o.src_rate_aper_b,o.src_rate_aper_w,o.flux_aper_b,o.flux_aper_lolim_b,o.flux_aper_hilim_b,o.flux_aper_w,o.flux_aper_lolim_w,o.flux_aper_hilim_w,o.hard_hm,o.hard_hm_lolim,o.hard_hm_hilim,o.hard_ms,o.hard_ms_lolim,o.hard_ms_hilim,o.var_index_b,o.var_index_w,o.livetime,o.detector'.split(','),
    'source_observation_photometry' :  'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.likelihood_class,o.obsid,o.obi,o.gti_obs,o.gti_end,o.region_id,o.theta,o.phi,o.flux_significance_b,o.flux_significance_h,o.flux_significance_m,o.flux_significance_s,o.flux_significance_u,o.flux_significance_w,o.likelihood_b,o.likelihood_h,o.likelihood_m,o.likelihood_s,o.likelihood_u,o.likelihood_w,o.conf_code,o.extent_code,o.sat_src_flag,o.streak_src_flag,o.var_code,o.cnts_aper_b,o.cnts_aper_h,o.cnts_aper_m,o.cnts_aper_s,o.cnts_aper_u,o.cnts_aper_w,o.src_cnts_aper_b,o.src_cnts_aper_h,o.src_cnts_aper_m,o.src_cnts_aper_s,o.src_cnts_aper_u,o.src_cnts_aper_w,o.src_rate_aper_b,o.src_rate_aper_h,o.src_rate_aper_m,o.src_rate_aper_s,o.src_rate_aper_u,o.src_rate_aper_w,o.flux_aper_b,o.flux_aper_lolim_b,o.flux_aper_hilim_b,o.flux_aper_h,o.flux_aper_lolim_h,o.flux_aper_hilim_h,o.flux_aper_m,o.flux_aper_lolim_m,o.flux_aper_hilim_m,o.flux_aper_s,o.flux_aper_lolim_s,o.flux_aper_hilim_s,o.flux_aper_u,o.flux_aper_lolim_u,o.flux_aper_hilim_u,o.flux_aper_w,o.flux_aper_lolim_w,o.flux_aper_hilim_w,o.flux_powlaw_aper_b,o.flux_powlaw_aper_lolim_b,o.flux_powlaw_aper_hilim_b,o.flux_powlaw_aper_w,o.flux_powlaw_aper_lolim_w,o.flux_powlaw_aper_hilim_w,o.flux_bb_aper_b,o.flux_bb_aper_lolim_b,o.flux_bb_aper_hilim_b,o.flux_bb_aper_w,o.flux_bb_aper_lolim_w,o.flux_bb_aper_hilim_w,o.flux_brems_aper_b,o.flux_brems_aper_lolim_b,o.flux_brems_aper_hilim_b,o.flux_brems_aper_w,o.flux_brems_aper_lolim_w,o.flux_brems_aper_hilim_w '.split(','),
    'source_observation_variability' : 'm.name,m.ra,m.dec,m.err_ellipse_r0,m.err_ellipse_r1,m.err_ellipse_ang,m.likelihood_class,o.obsid,o.obi,o.gti_obs,o.gti_end,o.region_id,o.theta,o.phi,o.flux_significance_b,o.flux_significance_w,o.likelihood_b,o.likelihood_w,o.conf_code,o.dither_warning_flag,o.extent_code,o.sat_src_flag,o.streak_src_flag,o.var_code,o.flux_aper_b,o.flux_aper_lolim_b,o.flux_aper_hilim_b,o.flux_aper_w,o.flux_aper_lolim_w,o.flux_aper_hilim_w,o.var_index_b,o.var_index_h,o.var_index_m,o.var_index_s,o.var_index_u,o.var_index_w,o.var_prob_b,o.var_prob_h,o.var_prob_m,o.var_prob_s,o.var_prob_u,o.var_prob_w,o.ks_prob_b,o.ks_prob_h,o.ks_prob_m,o.ks_prob_s,o.ks_prob_u,o.kp_prob_w,o.var_sigma_b,o.var_sigma_h,o.var_sigma_m,o.var_sigma_s,o.var_sigma_u,o.var_sigma_w,o.var_mean_b,o.var_mean_h,o.var_mean_m,o.var_mean_s,o.var_mean_u,o.var_mean_w,o.var_min_b,o.var_min_h,o.var_min_m,o.var_min_s,o.var_min_u,o.var_min_w,o.var_max_b,o.var_max_h,o.var_max_m,o.var_max_s,o.var_max_u,o.var_max_w'.split(','),
}



required_cols = """
m.name,
m.ra,
m.dec,
o.instrument,
o.obsid,
o.obi,
o.region_id,
a.match_type
""".replace("\n", "").split(",")

__all_retieved_files__ = {}

__filename_cache__ = []

__filename_version_db__ = {}


def get_radec_lim( ra_deg, dec_deg, radius_arcmin ):
    """
    To improve performance, the dbo.cone_dist() search is augmented with
    a range check on ra and dec.  Need special logic to deal with
    ra's crossing 0:360 and for decs at the poles.

    This will return two conditional expressions that are added
    to the CSC query.
    """
    from math import cos, radians
    radius_deg = radius_arcmin / 60.0
    cos_rad = radius_deg / cos( radians( dec_deg ))
    ra_min = ra_deg - cos_rad
    ra_max = ra_deg + cos_rad

    if (ra_min < 0) | ( ra_max > 360.0):
        # Need to change query ra between A and B to
        # ra > (A mod 360) OR ra < (B mod 360)
        #
        ra_condition = "m.ra > {0:.8f} OR m.ra < {1:.8f}".format( ra_min % 360.0, ra_max % 360.0 )
    else:
        ra_condition = "m.ra BETWEEN {0:.8f} AND {1:.8f}".format( ra_min, ra_max )

    dec_min = dec_deg - radius_deg
    dec_max = dec_deg + radius_deg

    if ( dec_min < -90 ) | ( dec_max > 90 ):
        #Crosses pole, so all ra's are allowed.
        #CSCView is OK w/ dec outside -90:90
        ra_condition = "m.ra >= 0"
    dec_condition = "m.dec BETWEEN {0:.8f} AND {1:.8f}".format( dec_min, dec_max)

    return ra_condition, dec_condition


def make_URL_request( resource, vals ):
    """
    Query and retrieve results from resourse using dictionary of
    vals values.
    """
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    verb5( "Querying resource " + resource )
    verb5( "with parameters" + str( vals ) )

    params = urlencode( vals )  # Encode into URL string, escape stuff/etc.
    request = Request( resource, params.encode("ascii") )

    # make easy to ID in logs
    request.add_header('User-Agent', 'ciao_contrib.cda.csccli/1.1')

    try:
        response = urlopen( request )
        page = response.read()

        verb5( "URL Code: {0}".format( response.getcode() ))
        if response.getcode() != 200:
            # If we get a redirect, 30x, then fall through to curl too
            raise Exception( page )

    except Exception:
        page = make_CURL_request( resource, vals )

    if len(page) == 0:
        raise Exception("Problem accessing resource {0}".format(resource))

    return page


def make_CURL_request( resource, vals ):
    """
    Query and retrieve results from resourse using dictionary of
    vals values.  This is a fallback in case https:// is not supported
    in python.
    """

    from urllib.parse import urlencode

    params = urlencode( vals )  # Encode into URL string, escape stuff/etc.
    url = "{}?{}".format(resource, params)

    verb2("Contacting resource '{}'".format(url))

    import subprocess as sp

    try:
        page = sp.check_output( ['curl', '--silent', '-L', url ]) # Need the '-L' to enable curl to follow redirect
    except Exception as e:
        print(e)
        raise

    if len(page) == 0:
        raise RuntimeError("Problem accessing resource {0}".format(resource))

    return page


def cone_query_cli_cscview( ra_deg, dec_deg, radius_arcmin, ra_condition, dec_condition, columns):
    """
    Perform the cone search query on the CSC using the getProperties API.

    Because we add the dbo.separation column, sepn, that add +1 to all

    """

    resource="http://cda.cfa.harvard.edu/csccli/getProperties"

    selstr="dbo.separation(ra,dec,{0},{1}) as sepn,".format(ra_deg, dec_deg)
    selstr+=",".join(columns)

    query_string="""
        SELECT
          {5}
        FROM
          master_obi_assoc a , master_source m , obi_source o
        WHERE
          ({3}) AND
          ({4}) AND
          dbo.cone_distance(ra,dec,{0:.8f},{1:.8f})<={2:.8f} AND
          a.posid=o.posid  AND a.msid=m.msid
        ORDER BY
          name ASC
        """.format( ra_deg, dec_deg, radius_arcmin, ra_condition, dec_condition, selstr)

    verb5("CSCCLI query string is {}\n".format(query_string))

    vals = {
        'query' : " ".join(query_string.split()) , # removes excess white spaces
        'coordFormat' : 'decimal',
        'nullAppearance' : 'NaN',
        'version' : __csc_version["csc1"]
        }

    page = make_URL_request( resource, vals )
    page = page.decode("ascii")

    if "Error executing query:" in page:
        k=page.replace( "\n", " ")
        raise Exception( k )

    cols = ["sep"]
    cols.extend( columns )
    return page,cols


def cone_query_cli_cscview_ver2( ra_deg, dec_deg, radius_arcmin, ra_condition, dec_condition, columns, cat_ver):
    """
    Perform the cone search query on the CSC using the getProperties API.

    Because we add the dbo.separation column, sepn, that add +1 to all

    """

    resource="http://cda.cfa.harvard.edu/csccli/getProperties"

    selstr="dbo.separation(m.ra,m.dec,{0},{1}) as sepn,".format(ra_deg, dec_deg)
    selstr+=",".join(columns)

    query_string="""
        SELECT
          {5}
        FROM
          master_source m , master_stack_assoc a , observation_source o , stack_observation_assoc b , stack_source s
        WHERE
          ((( ({3}) AND
          ({4})) AND
          dbo.cone_distance(m.ra,m.dec,{0:.8f},{1:.8f})<={2:.8f})) AND
          (m.name = a.name) AND (s.detect_stack_id = a.detect_stack_id and s.region_id = a.region_id) AND (s.detect_stack_id = b.detect_stack_id and s.region_id = b.region_id) AND (o.obsid = b.obsid and o.obi = b.obi and o.region_id = b.region_id)
        ORDER BY
          name ASC
        """.format( ra_deg, dec_deg, radius_arcmin, ra_condition, dec_condition, selstr)

    verb5("CSCCLI query string is {}\n".format(query_string))

    vals = {
        'query' : " ".join(query_string.split()) , # removes excess white spaces
        'version' : __csc_version[cat_ver],
        'coordFormat' : 'decimal',
        'nullAppearance' : 'NaN',
        }

    page = make_URL_request( resource, vals )
    page = page.decode("ascii")

    if "Error executing query:" in page:
        k=page.replace( "\n", " ")
        raise Exception( k )

    cols = ["sep"]
    cols.extend( columns )
    return page,cols


def obsid_query_cli_cscview( obsid, columns ):
    """
    Perform the cone search query on the CSC using the getProperties API.

    """

    resource="http://cda.cfa.harvard.edu/csccli/getProperties"

    selstr = ",".join(columns)

    query_string="""
        SELECT
          {1}
        FROM
          master_obi_assoc a , master_source m , obi_source o
        WHERE
          o.obsid IN ({0}) AND
          a.posid=o.posid  AND a.msid=m.msid
        ORDER BY
          name ASC
        """.format( obsid, selstr)

    verb5("CSCCLI query string is {}\n".format(query_string))

    vals = {
        'query' : " ".join(query_string.split()) , # removes excess white spaces
        'coordFormat' : 'decimal',
        'nullAppearance' : 'NaN',
        'version' : __csc_version["csc1"]
        }

    page = make_URL_request( resource, vals )
    page = page.decode("ascii")
    if "Error executing query:" in page:
        k=page.replace( "\n", " ")
        raise Exception( k )

    cols = columns

    return page,cols


def obsid_query_cli_cscview_ver2( obsid, columns, catver ):
    """
    Perform the cone search query on the CSC using the getProperties API.

    """

    resource="http://cda.cfa.harvard.edu/csccli/getProperties"

    selstr = ",".join(columns)

    query_string="""
        SELECT
          {1}
        FROM
          master_source m , master_stack_assoc a , observation_source o , stack_observation_assoc b , stack_source s
        WHERE
          ((o.obsid IN ({0}))) AND
          (m.name = a.name) AND (s.detect_stack_id = a.detect_stack_id and s.region_id = a.region_id) AND (s.detect_stack_id = b.detect_stack_id and s.region_id = b.region_id) AND (o.obsid = b.obsid and o.obi = b.obi and o.region_id = b.region_id)
        ORDER BY
          name ASC
        """.format( obsid, selstr)

    verb5("CSCCLI query string is {}\n".format(query_string))

    vals = {
        'query' : " ".join(query_string.split()) , # removes excess white spaces
        'coordFormat' : 'decimal',
        'nullAppearance' : 'NaN',
        'version' : __csc_version[catver]
        }

    page = make_URL_request( resource, vals )
    page = page.decode("ascii")
    if "Error executing query:" in page:
        k=page.replace( "\n", " ")
        raise Exception( k )

    cols = columns

    return page,cols


def summarize_properties( cols, results ):
    """
    Can be used for different list of properties
    """
    if len(results) == 0:
        return

    for cc in cols:
        if cc[0] not in results[0]:
            raise ValueError("Bad column, '{}' name requested in summarize".format(cc[0]))

    # Print banner line
    retstr = ""
    for cc in cols:
        retstr += cc[1].format(cc[0])
        retstr += "\t"
    verb1( retstr )

    # Print 1 row per source
    for mysrc in results:
        retstr = ""
        for cc in cols:
            retstr += cc[1].format( cc[2]( mysrc[cc[0]]))
            retstr += "\t"
        verb1( retstr)

    #verb1("\nIf you use this data, please cite Evans et al 2010, ApJS 189, 37\n")


def __arcsec_to_deg( val ):
    retval = float(val)
    retval /= 3600.0
    return "{:.2g}".format(retval)


def __arcsec_to_arcsec(val):
    retval = float(val)
    return '{:.2g}"'.format(retval)


def __arcsec_to_arcmin(val):
    retval = float(val)
    retval /= 60.0
    return "{:.2g}'".format(retval)


def summarize_source_short( results, units, extracols=None ):
    """
    Provide a short on-screen summary of results
    """
    # TODO: should probaly use a named tuple or dict instead of list

    # This list contains a 3-tuple:
    #   column name
    #   format
    #   conversion function
    cols = [ ("name", "{:20s}", str),
             ("ra" , "{:12s}", str),
             ("dec","{:12s}", str),
             ("obsid","{:5s}", str),
             ]

    if 'sepn' in results[0]:
        if "arcsec" == units:
            fun = __arcsec_to_arcsec
        elif "arcmin" == units:
            fun = __arcsec_to_arcmin
        elif "deg" == units:
            fun = __arcsec_to_deg
        else:
            raise ValueError("Unknown units")

        cols.insert(3, ("sepn", "{}", fun ))

    if extracols:
        for ecol in extracols:
            if ecol not in ["name", "ra", "dec", "obsid"]:
                cols.append( (ecol, "{}", str ) )

    summarize_properties( cols, results )


def extra_cols_to_summarize( mysrcs, requested_cols, cat_ver ):
    """
    Match requested cols to mypage[1] (columns) returned by cscview.
    The 'm.' and 'o.' are dropped and/or replaced by obi_ or mstr_
    if both obi and master level properties are returned.
    """
    import stk as stk

    if "INDEF" == requested_cols or len(requested_cols) == 0:
        return None

    rc_stk = expand_standard_cols(stk.build( requested_cols ), cat_ver)

    if len(mysrcs) == 0:
        return None

    row = mysrcs[0]

    retval = []
    for rc in rc_stk:
        just_name = rc.split()  # col name may be o.blah as obi_ already
        rc_parts = just_name[0].split(".")

        if len(rc_parts) == 1:
            if rc_parts[0] in row and rc_parts[0] not in retval:
                retval.append( rc_parts[0] )
            else:
                maybe = [x for x in row if x.endswith(rc_parts[0]) ]
                if len(maybe) == 1:
                    retval.append( maybe[0])
        elif rc_parts[1] in row and rc_parts[1] not in retval:
            retval.append( rc_parts[1] )
        elif rc_parts[0] == 'o' and "obi_"+rc_parts[1] in row:
            retval.append( "obi_"+rc_parts[1])
        elif rc_parts[0] == 'm' and "mstr_"+rc_parts[1] in row:
            retval.append( "mstr_"+rc_parts[1])
        elif rc_parts[0] == 's' and "stk_"+rc_parts[1] in row:
            retval.append( "stk_"+rc_parts[1])
        else:
            raise IOError("Column {} was not returned by cscview".format( rc ))

    return retval


def summarize_results( results, units="arcmin", extracols=None):
    """
    Provide summary stats of query and summary table
    """
    def count_values( name ):
        dd = {}
        for rr in results:
            dd[ rr[name] ] = None
        return len(dd)

    verb1("\n{} rows returned by query".format(len(results)))
    verb1( "{} Different Master Source(s).".format( count_values( "name" )))
    verb1( "{} Different Observation(s).\n".format( count_values( "tag" )))

    if len(results) > 0:
        summarize_source_short(results, units, extracols)


def parse_csc_result( page_and_cols ):
    """
    The table returned is TSV format.  First N-many rows are "#" comments
    with column information, one for each column

    Then 1 row w/ column names, tab separated (no comment character)
    Then 1 row for each source, values are tab separated will contain spaces.

    finished off with 1 blank line.

        #Column sepn      (E9.6)          (.sepn)   [""]    []
        ...
        sepn      name    ra      dec     err_ellipse_r0  conf_flag ...
        1.555089e+01    CXO J162623.5-242439     16 26 23.59    -24 24 39.58       0.44 TRUE
        ...

    We parse this into a list of dictionaries.  Each item in the list
    is 1 row with a dictionary of columnname = value.

    Currenly we only use the name, region_id, obsid, and obi but other values
    are available for future expansion.

    """
    #
    # parse rows, make list of lists
    #
    page = page_and_cols[0]
    cols = page_and_cols[1]

    rows = [ pp.split("\t") for pp in page.split("\n") ]

    #
    # 1st N-rows are the column defintions (skip), followed by data
    # end of file may contain new lines
    #
    startat = len( cols )

    if len(rows) < startat:
        raise IOError("ERROR: Problem accessing CSC site.  Server responded with the following message: {0}".format(page))

    cols = rows[startat]

    # make list of dictionaries
    retvals = [ dict(zip( cols, pp )) for pp in rows[startat+1:] if len(pp) > 1 ]

    # we add an extra dictionary item, ["tag"] that is obsid_obi
    # which is used in the file names and in the directories.
    for pp in retvals:
        pp["tag"]="{0:05d}_{1:03d}".format( int(pp["obsid"]),int(pp["obi"]))

    return retvals


def fix_dm_no_g_type( page ):
    """
      The DM ascii kernel does not understand the "G" format that
      cscview returns.  The distinction between D, E, F and G,
      are only on output.  When read in, they are all parsed the
      same (atof or strtod) so we can just change the "(Gnumber)"
      to be "(Fnumber)"
    """
    import re as re

    fixed = re.sub(r'\(G[0-9\.]*\)',
                   lambda x: x.group(0).replace("G", "F"),
                   page)
    return fixed


def save_results( page_and_cols, outfile, clobber ):
    """
    DM ascii kernel can read .tsv format returned by cscview just
    need to be told that it is tsv format.

    dmlist out.tsv[opt kernel=text/tsv] cols

    """
    page = page_and_cols[0]
    cols = page_and_cols[1]

    import re as re
    from ciao_contrib._tools.fileio import outfile_clobber_checks

    if not outfile:
        return

    outfile_clobber_checks( clobber, outfile )

    p2 = fix_dm_no_g_type( page )
    with open( outfile, "w+") as fp:
        fp.write( p2 )


def search_src_by_ra_dec( ra, dec, radius_arcmin, columns, cat_ver ):
    """
    Perform a cone search on CSC CLI.
    """
    from coords.format import sex2deg
    ra_deg,dec_deg = sex2deg(ra, dec )
    ra_condition, dec_condition = get_radec_lim( ra_deg, dec_deg, radius_arcmin )

    if "csc1" == cat_ver:
        page = cone_query_cli_cscview( ra_deg, dec_deg, radius_arcmin, ra_condition, dec_condition, columns)
    elif cat_ver in ["csc2", "csc2.1", "current"]:
        page = cone_query_cli_cscview_ver2( ra_deg, dec_deg, radius_arcmin, ra_condition, dec_condition, columns, cat_ver)
    else:
        raise ValueError("Unknown catalog version")

    return page


def search_src_by_obsid( obsid, columns, cat_ver ):
    """
    Perform a obsid search on CSC CLI.
    """

    if 'csc1' == cat_ver :
        page = obsid_query_cli_cscview( obsid, columns )
    elif cat_ver in ["csc2", "csc2.1", "current"] :
        page = obsid_query_cli_cscview_ver2( obsid, columns, cat_ver )
    else:
        raise ValueError("Unknown catalog version")
    return page


#~ def find_filename_match_in_rows( rows, filetype, obsid, obi, region, band, instrume):
    #~ """
    #~ Look for file name in a list of file names
    #~ """
    #~ if region:
        #~ # Look for r????_ in the name
        #~ regs = filter( lambda x: "r{0:04d}".format(int(region)) in x, rows)
    #~ else:
        #~ regs = rows

    #~ if band:
        #~ # Look for band_
        #~ bnds = filter( lambda x: "{0}_".format(band) in x, regs)
    #~ else:
        #~ bnds = regs

    #~ # Filter on file type since cached list may contain many
    #~ myfile = fileTypes[ filetype ]
    #~ ftyp = filter( lambda x: "_{0}.fits".format( myfile["extn"] ) in x, bnds )

    #~ # Finally filter on obi number, usually a no-op
    #~ obis = filter( lambda x: "f{0:05d}_{1:03d}N".format(int(obsid),int(obi)) in x, ftyp )

    #~ # Check return, should have 1 row left from service
    #~ if len(obis) > 1:
        #~ oo = [ o.split("\t")[0] for o in obis ]
        #~ oo.sort()
        #~ obis=[oo[-1]]  # sort, take last one, highest version
        #~ verb2("Found multiple files for {0}\n".format( (filetype, obsid, obi, region, band, instrume)))
        #~ #raise IOError("Only 1 file should be found")
    #~ if len(obis) == 0 :
        #~ raise IOError("No files found matching query")

    #~ filename = obis[0].split("\t")[0]
    #~ return filename


def discover_filename_by_force( filetype, obsid, obi, region, band, instrume):
    """
    This is only for catalog='csc1'

    """
    global __filename_version_db__
    if 0 == len(__filename_version_db__):
        tab = make_URL_request( "https://cxc.harvard.edu/ciao/threads/csccli/cscrel1_version_info.txt", {} )
        tab = tab.decode("ascii")
        __filename_version_db__ = {}
        for row in tab.split("\n"):
            vals = row.split()
            if len(vals) == 5:
                __filename_version_db__[vals[0]] = { 'calver' : vals[3], 'detver' : vals[1], 'srcver' : vals[2], 'inst' : vals[4] }
            else:
                pass
    obistr = "{0:05d}_{1:03d}".format( int(obsid), int(obi) )
    filename = "{0}f{1}N".format( instrume.lower(),obistr)

    if obistr not in __filename_version_db__:
        print("Version info not available for {}".format(obistr))
        return None

    if fileTypes['csc1'][filetype]["version"] == "cal":
        ver = __filename_version_db__[obistr]["calver"]
    elif fileTypes['csc1'][filetype]["version"] == "det":
        ver = __filename_version_db__[obistr]["detver"]
    elif fileTypes['csc1'][filetype]["version"] == "src":
        ver = __filename_version_db__[obistr]["srcver"]
    else:
        raise ValueError("Internal error: unknown filetype")

    filename += ver+"_"

    if fileTypes['csc1'][filetype]["obilevel"]:
        pass
    else:
        filename += "r{:04d}".format( int(region))

    if fileTypes['csc1'][filetype]["bands"]:

        filename += band

    filename += "_"+fileTypes['csc1'][filetype]["extn"]+".fits"

    return filename.replace("__", "_")


#~ def discover_filename_from_archive( filetype, obsid, obi, region, band, instrume):
    #~ """
    #~ Use the archiveFileList service to file the filename to use
    #~ in the query to retrive the file based on the filetype and
    #~ observation info
    #~ """

    #~ filename = ""
    #~ try:
        #~ # try cache of filenames 1st
        #~ filename = find_filename_match_in_rows(__filename_cache__, filetype, obsid, obi, region, band, instrume)
        #~ verb2( "Found {0} in cache".format(filename))
    #~ except IOError:
        #~ # if not found, then query archive
        #~ myfile = fileTypes[filetype]
        #~ resource = "http://cda.harvard.edu/srservices/archiveFileList.do"
        #~ vals = {
            #~ "obsid"    : obsid,
            #~ "detector" : instrume,
            #~ "filetype" : myfile["filetype"],
            #~ "dataset"  : "flight",
            #~ "level"    : "3"
            #~ }
        #~ qry = make_URL_request( resource, vals )
        #~ qry = qry.decode("ascii")
        #~ # parse string
        #~ rows = qry.split("\n")
        #~ __filename_cache__.extend( rows ) # add rows to cache
        #~ filename = find_filename_match_in_rows(rows, filetype, obsid, obi, region, band, instrume)

    #~ return filename


def discover_filename_via_archive(myfile, obsid, obi, region, band, instrume, catalog):
    """
    Use the csccli browse interface for release 2 file names.

    """

    pkg = "{obs}.{obi}.{reg}/{typ}/{band}".format(
        obs=obsid.strip(), obi=obi.strip(),
        reg=region.strip(), typ=myfile, band=band)

    resource = "http://cda.cfa.harvard.edu/csccli/browse"
    vals = {
        "packageset" : pkg,
        "version" : __csc_version[catalog],
        }

    try:
        qry = make_URL_request( resource, vals )
        qry = qry.decode("ascii")

        import json as json
        retval = json.loads(qry)
        filename = [ f["filename"] for f in retval ]
    except Exception:
        filename = [None]

    return filename[0]


def discover_filenames_per_type( mysrc, myfile, mybands, catalog ):
    """
    To discover the filename we need to make a wide query to the
    archive for data products associated with the obisid
    for the filetype.  Then we will parse by band, obi, and
    region id.
    """
    myfileType = fileTypes[catalog][myfile]
    myinst = mysrc["instrument"].replace(" ", "")

    if ("ACIS" != myinst ) & myfileType["acisonly"]:
        verb1("{0} is not available for {1} observation {2}".format( myfile, myinst, mysrc["tag"]))
        return []

    if not myfileType["obilevel"] :
        rr = mysrc["region_id"]
    else:
        rr=""

    if myfileType["bands"]:
        filenames = []
        for name in bands[ myinst ]:
            abbrv=bands[myinst][name]
            # compare list of all bands to those requested
            if name not in mybands.split(","):
                continue

            if 'csc1' == catalog:
                ff = discover_filename_by_force( myfile, mysrc["obsid"], mysrc["obi"], rr, abbrv, myinst )
            else:
                ff = discover_filename_via_archive( myfileType["filetype"], mysrc["obsid"], mysrc["obi"], rr, abbrv, myinst, catalog )
            filenames.append( ff )
    else:
        if 'csc1' == catalog:
            ff = discover_filename_by_force( myfile , mysrc["obsid"], mysrc["obi"], rr, "", myinst )
        else:
            ff = discover_filename_via_archive( myfileType["filetype"], mysrc["obsid"], mysrc["obi"], rr, "", myinst, catalog )
        filenames = [ ff ]

    return filenames


def check_existing( ff, off ):
    """
    Check if a file exists or has already been downloaded
    """
    from os.path import exists

    if exists( off ) :
        verb2("File {0} already exists".format(off))
        return True

    if exists( off+".gz" ):
        verb2("File {0}.gz already exists".format(off))
        return True

    if ff in __all_retieved_files__:
        verb2("File {0} already retrieved, will make a copy".format(ff))
        import shutil as shutil
        shutil.copyfile( __all_retieved_files__[ff]+"/{0}.gz".format(ff) , off+".gz")
        return True

    return False


def retrieve_files_per_type( filenames, filetype, root, catalog ):
    """
    Retrieve the files using the retrieveFile interface.

    This requires the file name and the file type.

    Added extra logic to skip if the file already exists on
    disk. Also if already retrieve, then skip.  File may
    already have been retrieved if the source is an
    ambigious match -- that is the per-obi source belongs to
    2 or more master sources.
    """

    for ff in filenames:
        if ff is None:
            continue

        off = root + os.sep + ff # path + filename

        if check_existing( ff, off ):
            continue

        resource = "http://cda.cfa.harvard.edu/csccli/retrieveFile"
        vals = {
            "filetype" : fileTypes[catalog][filetype]["filetype"],
            "filename" : ff,
            }

        if "csc2" == catalog:
            vals['version'] = __csc_version["csc2"]
        elif "csc2.1" == catalog:
            vals['version'] = __csc_version["csc2.1"]
        elif "csc1" == catalog:
            vals['version'] = __csc_version["csc1"]
        elif "current" == catalog:
            vals['version'] = __csc_version["current"]
        else:
            raise ValueError("Unknown catalog version")

        try:
            page = make_URL_request( resource, vals )
        except Exception:
            verb0("Problem retrieveing file {0}".format(ff))
            raise

        # Possible RFE would be to unzip in memory ala chandra_repro
        with open( off+".gz", 'wb' ) as fp:
            fp.write(page)

        verb1("Retrieved file {}".format(off))

        # Save file name and directory where 1st saved
        __all_retieved_files__[ff] = root


def create_output_dir( inroot, mysrc, myfiletype, byObi, catalog ):
    """
    To make managing the files easier, the files are retrieved into
    directories based on the master source name and obsid_obi
    """

    if 'csc1' == catalog:
        if byObi:
            root = (inroot+os.sep+mysrc["obsid"]).replace(" ","")
            if not fileTypes[catalog][myfiletype]["obilevel"]:
                root += (os.sep+mysrc["name"]).replace(" ", "")

        else:
            root = (inroot+os.sep+mysrc["name"]+os.sep+mysrc["tag"] ).replace(" ","") # remove space in name
            if not fileTypes[catalog][myfiletype]["obilevel"]:
                root += os.sep+"r{0:04d}".format(int(mysrc["region_id"]))

    else:  # csc2, aka cur
        if byObi:
            root = os.path.join(inroot,mysrc["obsid"])
            if fileTypes[catalog][myfiletype]["prodlevel"] == 'stk':
                root = os.path.join(root, mysrc["detect_stack_id"])
            elif fileTypes[catalog][myfiletype]["prodlevel"] == 'mst':
                root = os.path.join( root, mysrc["name"])
            elif fileTypes[catalog][myfiletype]["prodlevel"] == 'src':
                root = os.path.join( root, "r{:04d}".format(int(mysrc["region_id"])))
        else:
            root = os.path.join( inroot, mysrc["name"] )
            if fileTypes[catalog][myfiletype]["prodlevel"] == 'stk':
                root = os.path.join(root, mysrc["detect_stack_id"])
            elif fileTypes[catalog][myfiletype]["prodlevel"] in ['obi','src']:
                root = os.path.join( root, mysrc["tag"])

    root=root.replace(" ","")

    if not os.path.exists( root ):
        os.makedirs( root )

    if not os.path.isdir( root ):
        raise IOError("{0} exists but is not a directory".format(root))

    return root


def process_ask( ask, pp ):
    """

    """

    if 'all' == ask:
        return 'y'
    elif 'none' == ask:
        return 'n'
    elif 'ask' == ask:
        pass
    else:
        raise NotImplementedError("Internal Error: invalid ask value")

    while True:
        resp = input( "Download data for {} [y,n,a,q]: ".format(pp) )
        ans = resp.strip().lower()

        if ans == "":
            continue
        if ans in 'ynqa':
            return ans
        else:
            verb0("Unrecognized option '{}'".format( resp ))


def retrieve_files( mysrcs, root, myfiles, mybands, ask, catalog, byObi=False ):
    """
    Loop over sources and retrieve files
    """
    for mysrc in mysrcs:

        pp = process_ask( ask, mysrc["name"]+" in "+mysrc["tag"] )
        if 'n' == pp:
            continue
        elif 'q' == pp:
            verb0( "Skipping remaining sources")
            return
        elif 'a' == pp:
            ask = "all"
        elif 'y' == pp:
            pass
        else:
            raise NotImplementedError("Internal Error: invalid ask value")

        try:
            retrieve_files_per_src( mysrc, root, myfiles, mybands, catalog, byObi )
        except ValueError as e:
            verb0( str(e) )
            verb0("  Continuing")


def retrieve_files_per_src( mysrc, inroot, myfiles, mybands, catalog, byObi=False ):
    """
    For a single source, loop over file types and retrieve each
    """
    verb1("Retrieving files for obsid_obi {}".format(mysrc["tag"]))

    #
    # Loop overy file types
    #
    for ft in fileTypes[catalog]:
        # compare full list to those requested
        if ft not in myfiles.split(","):
            continue
        root = create_output_dir( inroot, mysrc, ft, byObi, catalog )
        fnames = discover_filenames_per_type( mysrc, ft, mybands, catalog )
        if fnames:
            retrieve_files_per_type( fnames, ft, root, catalog )


def check_filetypes( alist, catalog ):
    """
    Check list of files against those input and shorten list
    """

    retval=[]
    for aa in alist.split(","):
        aa=aa.strip()
        if aa in fileTypes[catalog]:
            retval.append(aa)
        else:
            verb1("Unrecongnized file type '{0}', skipping it".format(aa))
    return ",".join(retval)


def all_bands( ):
    """
    return list of all bands regardless of instrumet
    """
    return [ band for inst in bands for band in bands[inst]]


def check_bandtypes( alist ):
    """
    Check user supplied list of bands against all available
    """
    allbands = all_bands()
    retval=[]
    for aa in alist.split(","):
        aa=aa.strip()
        if aa in allbands:
            retval.append(aa)
        else:
            verb1("Unrecongnized energy band '{0}', skipping it".format(aa))
    rr=",".join( retval )

    return rr


def get_default_columns(cat_version=None):
    """
    The default set of columns to return
    """
    retval = default_cols

    if cat_version in ["csc2", "csc2.1", "current"]:
        default_cols.append("s.detect_stack_id")
        retval = default_cols # may be diff for ver2

    return default_cols


def append_cols_check_conflict( retval, val ):
    """
    The column names in the master source table are the same as those
    in the per-obi source table which makes for a bad  .tsv file
    (file should not contain duplicate column names).  This routine
    will check if column is already in list and if so rename
    it will not cause conflict.
    """
    vv = val.split(".")

    ## TODO: replace dups in likely stack, detect stack, ...

    if vv[0] == 'o' and len(vv) == 2:
        if "m.{}".format(vv[1]) in retval:
            verb2( "OBI column {} has same name as master column and has been renamed obi_{}".format(vv[1],vv[1]))
            val = val + " as obi_{}".format(vv[1])
        elif "s.{}".format(vv[1]) in retval:
            verb2( "OBI column {} has same name as stack column and has been renamed obi_{}".format(vv[1],vv[1]))
            val = val + " as obi_{}".format(vv[1])

    elif vv[0] == 'm' and len(vv) == 2:
        if "o.{}".format(vv[1]) in retval:
            verb2( "Master column {} has same name as obi column and has been rename mstr_{}".format(vv[1],vv[1]))
            val = val + " as mstr_{}".format(vv[1])
        if "s.{}".format(vv[1]) in retval:
            verb2( "Master column {} has same name as stack column and has been rename mstr_{}".format(vv[1],vv[1]))
            val = val + " as mstr_{}".format(vv[1])
    elif vv[0] == 's' and len(vv) == 2:
        if "o.{}".format(vv[1]) in retval:
            verb2( "Stack column {} has same name as obi column and has been rename stk_{}".format(vv[1],vv[1]))
            val = val + " as stk_{}".format(vv[1])
        if "m.{}".format(vv[1]) in retval:
            verb2( "Stack column {} has same name as master column and has been rename stk_{}".format(vv[1],vv[1]))
            val = val + " as stk_{}".format(vv[1])
    else:
        pass

    if val not in retval:
        retval.append(val)


def expand_standard_cols( cols, cat_version=None ):
    """
    The catalog contains some default column definitions.  These
    are avialable as tokens
    """

    if cat_version in ["csc2"]:
        check_list = { "MSBS" : csc2_columns["master_source_basic_summary"] ,
                       "MSS"  : csc2_columns["master_source_summary"],
                       "MSP"  : csc2_columns["master_source_photometry"],
                       "MSV"  : csc2_columns["master_source_variability"],
                       "SOS"  : csc2_columns["source_observation_summary"],
                       "SOP"  : csc2_columns["source_observation_photometry"],
                       "SOV"  : csc2_columns["source_observation_variability"],
                       "SSS"  : csc2_columns["stack_source_summary"],
                       "SSP"  : csc2_columns["stack_source_photometry"]
                       }
    elif cat_version in ["csc2.1", "current"]:
        check_list = { "MSBS" : csc21_columns["master_source_basic_summary"] ,
                       "MSS"  : csc21_columns["master_source_summary"],
                       "MSP"  : csc21_columns["master_source_photometry"],
                       "MSV"  : csc21_columns["master_source_variability"],
                       "SOS"  : csc21_columns["source_observation_summary"],
                       "SOP"  : csc21_columns["source_observation_photometry"],
                       "SOV"  : csc21_columns["source_observation_variability"],
                       "SSS"  : csc21_columns["stack_source_summary"],
                       "SSP"  : csc21_columns["stack_source_photometry"]
                       }
    else:
        check_list = { "MSBS" : csc1_columns["master_source_basic_summary"] ,
                       "MSS"  : csc1_columns["master_source_summary"],
                       "MSP"  : csc1_columns["master_source_photometry"],
                       "MSV"  : csc1_columns["master_source_variability"],
                       "SOS"  : csc1_columns["source_observation_summary"],
                       "SOP"  : csc1_columns["source_observation_photometry"],
                       "SOV"  : csc1_columns["source_observation_variability"]
                       }

    retval = []
    for cc in cols:
        # if column is special token, then expand it
        if cc in check_list:
            for ee in check_list[cc]:
                append_cols_check_conflict( retval, ee )
        else:
            append_cols_check_conflict( retval, cc )

    return retval


def check_required_names( cols, cat_version=None ):
    """
    The returned columns must include a subset that are needed to
    do the rest of the parsing/etc, especially to retrieve
    files.
    """
    c2 = expand_standard_cols( cols, cat_version )

    if cat_version in ['current','csc2', 'csc2.1'] and 's.detect_stack_id' not in required_cols:
        required_cols.append( 's.detect_stack_id' )

    required_cols.reverse()

    for mm in required_cols:
        if mm not in c2:
            verb2( "Required column {} was added to columns".format(mm))
            c2.insert( 0, mm )

    return c2


def query_csc1_limsens( ra, dec ):
    """
    """
    resource = "https://cxc.cfa.harvard.edu/csc1/sens/sensmap.php"
    vals = {
      "ra" : str(ra),
      "dec" : str(dec),
      "_submit_radec" : "1"
      }

    page = make_URL_request( resource, vals )
    page = page.decode("ascii")
    return page


def parse_limsens( page ):
    """
    Usage:
        page = query_csc1_limsens( ra, dec )
        values, units = parse_limsens( page )

    The limiting sensitivity page is (bad) HTML with multiple
    html, head, and body elements so it cannot be simply parsed with
    existing routines.

    We strip out just the sensitivity <table ... /table> data
    and parse that into a dictionary of { 'band' : value }

    The HTML looks like
      <table stuff>
      <tr>
      <th>band</th>
      ...
      </tr>
      <tr>
      <td>value</td>
      ...
      </tr>
      </table>

    which is sufficiently close to valid XML to be parsed
    as an xml ElementTree.

    The a 2-element tuple is returned:
      a dictionary of band and values
      and the units.

    The old CSC limsens .php only accepts POST requests, not GETs
    so the CURL path doesn't work.  That's OK since different
    server shouldn't go down that path anyways.
    """
    import re as re
    me_re = re.compile("<table.*table>", flags=re.DOTALL|re.MULTILINE)
    mytab = re.search( me_re, page )
    if mytab is None:
        raise RuntimeError("No table found in limsens results")
    mytab = mytab.group(0).replace("\n","")

    import xml.etree.ElementTree as ET

    tree = ET.fromstring(mytab)
    rows = tree.findall( "tr" ) # <tr>, find both rows.
    if len(rows) != 2:
        raise Exception("Should only be two rows returned by CSC LimSens service")

    #
    # Parse columns, 1st row, they are wrapped in <th>'s.  We lower
    # case them to make dictionary easier to match
    #
    reversebands = {
        'B' : 'broad',
        'U' : 'ultrasoft',
        'S' : 'soft',
        'M' : 'medium',
        'H' : 'hard',
        'W' : 'wide',
        'Q' : 'q',
        'QW' : 'qw'
        }

    cols = [ reversebands[ee.text]  for ee in rows[0].findall("th")]

    #
    # Parse the values, 2nd row, they are wrapped in <td>'s.
    # When the area is not covered, the limsens returns a
    # values of -999.  We go ahead and replace that with a
    # more informative NaN.
    #
    vals = [ ee.text.strip().replace("-999", "NaN")  for ee in rows[1].findall("td")]

    return dict(zip( cols, vals )), "photons/cm^2/s"
