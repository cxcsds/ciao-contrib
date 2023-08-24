
#
# Copyright (C) 2018,2020 Smithsonian Astrophysical Observatory
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


from pycrates import IMAGECrate
import numpy as np

class MaskedIMAGECrate( IMAGECrate ):
    """
    This class extends the basic IMAGECrate by adding a 'valid' 
    method.  
    
    The valid method takes the 0-based image index and sees if 
    the pixel is valid, where valid means:
    
     - pixel is not a special IEEE value, eg NaN or +/- INF
     - pixel is not an integer NULL value, eg -999 (if set)
     - pixel is inside the data subspace, ie region filter
    """

    def __init__(self, filename, mode="r"):
        super(MaskedIMAGECrate, self).__init__( filename, mode)
        
        if ( 2 != len(self.get_image().values.shape)):
            raise NotImplementedError("Only 2D images are supported")
    
        self._pix = self.get_image().values
        self.__make_valid_mask()


    def __check_finite(self):
        """Check for NaN|Inf
        
        """
        badidx = np.where( ~(np.isfinite(self._pix)))
        self._mask[badidx[0]] = 0


    def __check_null(self):
        """Check for integer NULL values """
        nullval = self.get_image().get_nullval()
        if nullval is None:  # is None, not == None (nor 0)
            return
        nullidx = np.where( self._pix == nullval )
        self._mask[nullidx[0]] = 0
        
        
    def __check_subspace(self):
        """Check to see if pixels are in subspace        
        """
        _a = [x.lower() for x in self.get_axisnames()]
        if 'sky' in _a:
            sky = 'sky'
        elif 'pos' in _a:
            sky = 'pos'
        else:
            #warning()
            return
                
        try:
            xform = self.get_axis(sky).get_transform()
            subspace = self.get_subspace_data(1, sky)
            assert subspace.region is not None, "No region in subpsace"
        except Exception as ee:
            #warnings
            return

        # We need to check regInside using physical coords. Compute 'em all.
        ylen,xlen = self._pix.shape        
        ivals = [x+1.0 for x in range(xlen)] # +1 -> image coords
        jvals = [y+1.0 for y in range(ylen)]
        ivals = np.array( ivals*ylen) # this is why using lists instead of np.arrays
        jvals = np.repeat( jvals,xlen)
        ijvals = list(zip(ivals,jvals))
        xyvals = xform.apply( ijvals ) # Due to memory leaks/etc, best to send all i,j in at once.
        
        import region as old        
        for ij,xy in zip( ijvals, xyvals):
            i=int(ij[0])-1
            j=int(ij[1])-1
            x=xy[0]
            y=xy[1]
            self._mask[j][i] = 1 if old.regInsideRegion( subspace.region, x,y) else 0


    def __make_valid_mask( self ):
        """
        Apply all the filters to create the mask array
        """
        self._mask = np.ones_like( self._pix ) # Assume everything is good
        self.__check_finite()
        self.__check_null()
        self.__check_subspace()


    def valid( self, i, j ):
        """
        Is pixel at 0-based indices i,j valid?  
        """
        return self._mask[j][i] == 1
