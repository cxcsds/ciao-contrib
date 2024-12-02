# 
# Copyright (C) 2013,2014, 2024 Smithsonian Astrophysical Observatory
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


__all__ = ["get_radec_from_pos"]

from ciao_contrib.logger_wrapper import initialize_module_logger
logger = initialize_module_logger("parse_pos")
verb0 = logger.verbose0


def _get_radec_from_str(pos):
    """
    Get the ra/dec values from the input string.
    """    
    from coords.format import sex2deg
    ps = pos.split(",")
    if len(ps) != 2:
        ps = pos.split("+")
    if len(ps) != 2:
        ps = pos.split("-")
        if len(ps) != 2:
            raise ValueError("ERROR: position value must be a filename or have a +, -, or comma separator")
        ps[1] = "-"+ps[1]
    
    ra_deg,dec_deg = sex2deg(ps[0].strip(), ps[1].strip() ) 
  
    ra = float( ra_deg )
    dec = float( dec_deg )
    return ra,dec

    
def _get_radec_from_file(pos):
    """
    Get ra/dec values from a table.  Will 
    try to use ra/dec columns if they exist and then
    will fail over to use first two columns.
    """
    from pycrates import read_file
    mytab = read_file( pos )
    
    cls = [ x.lower() for x in mytab.get_colnames(vectors=False) ]

    if "ra" in cls and "dec" in cls:
        ra="ra"
        dec="dec"
    else:  
        # Use first two columns in file
        ra = 0
        dec = 1

    ra = mytab.get_column( ra).values.tolist()
    dec = mytab.get_column( dec).values.tolist()        
    zz = list(zip(ra,dec))
    
    if isinstance(ra[0],str) and isinstance( dec[0], str):
        # if columns are string, then use above to parse

        _radec = [ _get_radec_from_str( r+","+d ) for r,d in zz ]
        ra = [ r[0] for r in _radec]
        dec = [r[1] for r in _radec]    
    elif isinstance(ra[0],str) or isinstance( dec[0], str):
        raise IOError("Both RA and Dec values must be strings if either is")

    if len(zz) != len(set(zz)):
        verb0("WARNING:  The same source position was input more than once.  This may produce unexpected results\n")

    return ra,dec
    

def get_radec_from_pos( pos ):
    """
    Pick whether to get from file or parse arguments
    """
    try:
        return _get_radec_from_file(pos)
    except:
        ra, dec = _get_radec_from_str(pos)
        return [ra], [dec]

