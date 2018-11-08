// C++

#ifndef LINEARINTERP_H
#define LINEARINTERP_H

#include "xsTypes.h"


namespace Numerics {

        namespace Rebin {

                // the engine of the subroutine previously coded in fortran as 'inibin'.
                // has to include potential redshifts.
                // computes the array of start,finish, and fractional weighting of an array
                // that is being rebinned or interpolated to a different array.

                // inputs:  inputArray 
                //          shiftedArray
                //          FUZZY - fuzz factor for determining equality in bin locations
                //      The interpolant  (defined on inputArray) is in general defined on a 
                //      different range than the required outputArray. 
                //      The calling routine will supply these.
                //      The first task is to locate in the 
                //          inputBin - first point of interest in the input Array, given
                //                     the outputArray
                //          outputBin - first point of interest in the output Array

                // outputs:  startBin, endBin
                //          startWeight, endWeight


                void initializeBins(const RealArray& inputArray, const RealArray& interpolant,
                         const Real FUZZY, size_t& inputBin, size_t& outputBin,
                         IntegerArray& startBin, IntegerArray& endBin, 
                         RealArray& startWeight, RealArray& endWeight);

                // rebin an array using the bin start/end, weight start/end arrays
                // generated in the above code.

                void rebin(const RealArray& inputArray, const IntegerArray& startBin, 
                      const IntegerArray& endBin, const RealArray& startWeight, 
                      const RealArray& endWeight, RealArray& outputArray);

                // interpolate an array. This is where the output array contains the
                // average value of the numbers in the bin, rather than their sum.
                // (In xspec table models this one is used for multiplicative models
                //  whereas the 'rebin' operation occurs for additive situations).
                // The exponential flag changes the behaviour of zero bins so that 
                // exp(-output) = 1 [==0], rather than output = 1 and ensures numeric limits
                // are respected.

                void interpolate(const RealArray& inputArray, const IntegerArray& startBin, 
                      const IntegerArray& endBin, const RealArray& startWeight, 
                      const RealArray& endWeight, RealArray& outputArray, bool exponential);


               // Find initial starting bins to plug into initializeBins function.
               // Returns false if there is no overlap between inputArray and
               // outputArray, true otherwise.   
                bool findFirstBins(const RealArray& inputArray, const RealArray& outputArray,
                        const Real FUZZY, size_t& inputStart, size_t& outputStart);

                // Rebinning with aspects particular to gain command.        
                void gainRebin(const RealArray& inputArray, const IntegerArray &startBin,
                        const IntegerArray& endBin, const RealArray& startWeight,
                        const RealArray& endWeight, RealArray& outputArray);

		// Linearly interpolate on an input in photons/cm^2/s/keV and
		// integrate over output bin sizes. This option works better when
		// the input is less frequently sampled than the output bins.
		void linInterpInteg(const RealArray& inputEnergy, const RealArray& inputdFlux, 
		       const RealArray& outputEnergy, RealArray& outputFlux, 
                       size_t& inputBin, size_t& outputBin);

        }
}


#endif
