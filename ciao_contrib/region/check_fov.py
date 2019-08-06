# 
# Copyright (C) 2014  Smithsonian Astrophysical Observatory
# 
# 
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

# KJG: 2016-09-13 check, no changes needed for P3

"""
Routines to support check_fov tool

"""

__all__ = (  )


import ciao_contrib.logger_wrapper as lw

lgr = lw.initialize_logger("ciao_contrib.region.check_fov")
verb0 = lgr.verbose0
verb1 = lgr.verbose1

from region import *

class FOVFiles():
    """
    Manage a stack of Field of View (FOV) files
    """

    def __init__(self, infile ):
        """
        Load a stack of Field of View files.  Celestial coordinates
        are used.

        Examples include:

        >>> myfovs = FOVFiles("*fov1.fits")
        >>> myfovs = FOVFiles("@obs.lis")
        >>> myfovs = FOVFiles("acisf00635_000N000_fov1.fits")

        See ahelp("stack") for more stack examples.

        """
        
        self._get_fovs(infile)
        

    def _get_fovs( self, infile ):
        """
        Load a stack of FOV files.

        """
        from pycrates import read_file
        import stk as stk

        fovs = stk.build( infile )
        if len(fovs) == 0:
            raise IOError("No fov files found in "+infile)
        
        self.fovs = {}
        for ff in fovs:
            # Just use the file name.  Previous version tried
            # to use obsid/obi, but this is most generic
            oo = ff

            if oo in self.fovs:
                # This may happen for interleaved mode datasets (e1, e2)
                # or for other reasons.  No reason to error out, just
                # skip and continue
                verb1("Multiple files for obsid {}. Skipping file {}".format(oo,ff))
                continue

            # By selecting the ra,dec columns we get the region
            # in degrees, not pixels, so we can ask 
            # whether a point in cel coords is inside or not.
            rr = regParse( "region({}[cols ra,dec,shape,component])".format(ff))

            # Store region object
            self.fovs[oo] = rr


    def inside( self, ra, dec ):
        """
        Check if RA / Dec in decimal degress (J2000), is inside any of the
        FOV files.  An unsorted list of FOV file names is returned.
        
        Example:
        
        >>> myfov = FOVFiles("*fov1.fits.gz")
        >>> infov = myfov.inside( 56.32114, -32.12245)
        >>> print infov
        [ "acisf00635_repro_fov1.fits", "acisf00637_repro_fov1.fits"]

        See ahelp("sex2deg") for examples of how to convert HMS to 
        decimal degrees.
        
        """
        retval = []
        for ff in self.fovs:
            if regInsideRegion( self.fovs[ff], ra,dec ):
                retval.append(ff)
        return retval

    def __repr__( self ):
        """
        print list of region files.  Values are not sorted.
        """

        ss ="List of FOV files\n"
        for ff in self.fovs:
            ss=ss+"  "+ff+"\n"        
        return ss

