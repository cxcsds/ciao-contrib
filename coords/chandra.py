#
#  Copyright (C) 2013-2014,2019  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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

# KJG: 2016-09013 no changes needed for P3


"""
Routines related specifically to converting to/from Chandra coordinates

"""

__all__ = [ "cel_to_chandra", "sky_to_chandra" ]


from pixlib import Pixlib

myPixlib = None

import ciao_contrib.logger_wrapper as lw
logger = lw.initialize_module_logger("coords.chandra")

v0 = logger.verbose0

def _setup_sim( keyword_list ):
    """
    Get the kewywords related to the SIM location    
    """
    #
    # Get SIM if all keys are present -- should be unless merged then
    # all bets are off anyways.
    #
    if all( [x in keyword_list for x in ["SIM_X", "SIM_Y", "SIM_Z"] ]):
        sim = [ keyword_list["SIM_X"], keyword_list["SIM_Y"], keyword_list["SIM_Z"] ]
    else:
        v0("WARNING: Missing one or more of the following keywords: "+
          "SIM_X, SIM_Y, SIM_Z.  Using default aimpoint for this detector; the "+
          "coordinates will not be accurate.")
        sim = None

    #
    # Get mean sim offset if all keys are present
    #
    if all( [x in keyword_list for x in ["DY_AVG", "DZ_AVG", "DTH_AVG" ] ]):
        dsim = (float(0.0), -1*float(keyword_list["DY_AVG"]), -1*float(keyword_list["DZ_AVG"]) )
        droll = float(keyword_list["DTH_AVG"])
    else:
        v0("WARNING: Missing one or more of the following keywords: "+
        "DY_AVG, DZ_AVG, DTH_AVG.  Assuming the offsets are all 0.0; the "+
        "coordinates will not be accurate.")

        _f = float(0.0)
        dsim = (_f,_f,_f)
        droll = -f
    
    return sim, dsim, droll


def _make_transform( crota, crpix, crval, cdelt ):
    """
    
    """        
    import pytransform as pt
    mytan = pt.WCSTANTransform()
    mytan.get_parameter("CROTA").set_value( crota )
    mytan.get_parameter("CRPIX").set_value( crpix )
    mytan.get_parameter("CRVAL").set_value( crval )
    mytan.get_parameter("CDELT").set_value( cdelt )
    return mytan


def _check_keyword_list( keyword_list):
    """Some error checking that keyword list has enough values"""


    # There are others that may be merged, these are the most
    # common.
    maybe_merged = ["OBJECT", "OBSERVER", "TITLE", "OBS_ID" ]
    for k in maybe_merged:
        if k in keyword_list and 'MERGED' == keyword_list[k].upper():
            print("Found keyword {}={}. ".format(k,keyword_list[k])+
            "This may be a merged dataset.  "+
            "Coordinates for merged datasets may not be accurate")

    # Do this after maybe_merged check 
    must_have = ["TELESCOP", "INSTRUME", "DETNAM", "RA_PNT", "DEC_PNT", 
        "ROLL_PNT", "RA_NOM", "DEC_NOM"]
    missing = [ k for k in must_have if k not in keyword_list ]
    if len(missing) !=0:
        k = ", ".join(missing)
        raise ValueError("Input keyword list is missing the following values: {}".format(k))

    if 'CHANDRA' != keyword_list["TELESCOP"].upper():
        e = "This routine only works with Chandra data, not '{}'"
        raise ValueError(e.format( keyword_list["TELESCOP"]))

    if keyword_list["INSTRUME"] not in ['ACIS', 'HRC']:
        e = "Unknown instrument '{}'"
        raise ValueError(e.format(keyword_list["INSTRUME"]))
        
    

def _setup( keyword_list ):
    """
    Setup pixlib and create transformation routines

    Input is a dictionary of keyword values that must contain
    the following values:
        
        INSTRUME
        DETNAM
        RA_NOM
        DEC_NOM
        RA_PNT
        DEC_PNT
        ROLL_PNT
        SIM_X
        SIM_Y
        SIM_Z
        DY_AVG
        DZ_AVG
        DTH_AVG

    """

    # Pixlib can only be init'ed once (and cannot successfully re-init'ed
    # after it's been closed.  So we have to use a hack to make sure
    # that if this routine is called multiple times that it only
    # gets setup once -- thus the global (which is global only to 
    # this module).  If someone init's pixlib outside of this routine
    # bad things will happen (results won't always be correct).

    global myPixlib


    _check_keyword_list( keyword_list )

    inst = keyword_list["INSTRUME"]
    if 'HRC' == inst:
        inst = keyword_list["DETNAM"]  # HRC-I and -S

    if myPixlib is None:
        pix = Pixlib( "chandra", "geom.par")
        myPixlib = pix
    else:
        pix = myPixlib

    pix.detector = inst
    
    # PNT gives us the optical axis and S/C roll
    crval = [ keyword_list["RA_PNT"], keyword_list["DEC_PNT"]  ]
    crota = keyword_list["ROLL_PNT"]
    
    # NOM gives us the tangent point
    crnom = [ keyword_list["RA_NOM"] ,keyword_list["DEC_NOM"] ]

    # Get SIM related info
    sim, dsim, droll = _setup_sim( keyword_list )

    if sim: 
        pix.aimpoint = sim
    pix.mirror = (tuple(dsim), droll )
    
    # get center of DET coord system by asking for on-axis
    # location (0,0)
    crpix = pix.msc2fpc( (-pix.flength, 0, 0 )  )
    cdelt = [ pix.fp_scale / 3600.0 ]*2 # replicate value
    cdelt[0] *= -1    

    my_dettan = _make_transform( crota, crpix, crval, cdelt )
    my_skytan = _make_transform( 0.0,   crpix, crnom, cdelt ) # 0.0 : North is up
    
    return pix, my_dettan, my_skytan, cdelt


def cel_to_chandra( keyword_list, ra_vals, dec_vals ):
    """
    Convert RA/DEC to various chandra coordinates
        - chip
        - det
        - sky
        - msc (theta/phi)
    RA/Dec must be decimal degrees, J2000, etc.
    
    The input keyword dictionary must contain the follow
    values:
    
        INSTRUME
        DETNAM
        RA_NOM
        DEC_NOM
        RA_PNT
        DEC_PNT
        ROLL_PNT
    
    The input keyword dictionary should also contain the following
    values:        

        SIM_X
        SIM_Y
        SIM_Z
        DY_AVG
        DZ_AVG
        DTH_AVG

    If they are missing the coordinate transforms will be inaccurate
    (SIM defaults based on INSTRUME|DETNAM).
    """    

    try:
        rd_vals = zip( ra_vals, dec_vals )
    except:
        rd_vals =  [ ( ra_vals,dec_vals ) ]


    pix, my_dettan, my_skytan, cdelt = _setup( keyword_list)
    
    # loop over ra,dec's 
    theta = []
    phi = []
    chip = []
    det = []
    sky = []

    for ra,dec in rd_vals:

        detxy = my_dettan.invert( [[ra*1.0,dec*1.0]] )  # *1.0 make sure is a float
        dxy = [ detxy[0][0], detxy[0][1] ]
        det.append( dxy )

        skyxy = my_skytan.invert( [[ra,dec]] )
        sxy = [ skyxy[0][0], skyxy[0][1] ]
        sky.append( sxy )

        msc = pix.fpc2msc( dxy )    # msc[0] is focal len
        theta.append(msc[1] * 60.0) # arcmin
        phi.append( msc[2]*1.0 )
            
        try:
            cixy = pix.fpc2chip( dxy )
            if cixy[0] < 0:
                raise ValueError("Unknow chip")
            chip.append( cixy )
        except:
            chip.append( (-999, (-999,-999)))
    

    return { 'pixsize' : cdelt[1]*3600.0, # deg to arcsec
             'theta'   : theta, # arcmin
             'phi'     : phi,    # deg
             'x'       : [x[0] for x in sky],
             'y'       : [x[1] for x in sky],
             'detx'    : [x[0] for x in det],
             'dety'    : [x[1] for x in det],
             'chip_id' : [x[0] for x in chip],
             'chipx'   : [x[1][0] for x in chip],
             'chipy'   : [x[1][1] for x in chip]
             }


def sky_to_chandra( keyword_list, x_vals, y_vals ):
    """
    Convert sky x,y to
        - chip
        - det
        - ra,dec
        - msc (theta/phi)

    The input keyword dictionary must contain the follow
    values:
    
        INSTRUME
        DETNAM
        RA_NOM
        DEC_NOM
        RA_PNT
        DEC_PNT
        ROLL_PNT
    
    The input keyword dictionary should also contain the following
    values:        
        SIM_X
        SIM_Y
        SIM_Z
        DY_AVG
        DZ_AVG
        DTH_AVG

    If they are missing the coordinate transforms will be inaccurate
    (SIM defaults based on INSTRUME|DETNAM).

    """    

    pix, my_dettan, my_skytan, cdelt = _setup( keyword_list)

    # loop over ra,dec's 
    theta = []
    phi = []
    chip = []
    det = []
    eqpos = []

    try:
        xy_vals = zip( x_vals, y_vals )
    except:
        xy_vals =  [ ( x_vals, y_vals ) ] 


    for x,y in xy_vals:

        radec = my_skytan.apply( [[x*1.0,y*1.0]] )  # *1.0 make sure is a float
        rd = [ radec[0][0], radec[0][1] ]
        eqpos.append( rd )
        
        detxy = my_dettan.invert( [rd] )
        dxy = [ detxy[0][0], detxy[0][1] ]
        det.append( dxy )
        msc = pix.fpc2msc( dxy )    # msc[0] is focal len

        theta.append(msc[1] * 60.0) # arcmin
        phi.append( msc[2]*1.0 )
 
        try:
            cixy = pix.fpc2chip( dxy )
            if cixy[0] < 0:
                raise ValueError("Unknow chip")
            chip.append( cixy )
        except:
            chip.append( (-999, (-999,-999)))
    

    return { 'pixsize' : cdelt[1]*3600.0, # deg to arcsec
             'theta'   : theta, # arcmin
             'phi'     : phi,    # deg
             'ra'      : [x[0] for x in eqpos],
             'dec'     : [x[1] for x in eqpos],
             'detx'    : [x[0] for x in det],
             'dety'    : [x[1] for x in det],
             'chip_id' : [x[0] for x in chip],
             'chipx'   : [x[1][0] for x in chip],
             'chipy'   : [x[1][1] for x in chip]
             }
