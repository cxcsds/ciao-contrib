// C++


#ifndef COSMO_H
#define COSMO_H

#include "xsTypes.h"
#include <cmath>


namespace Numerics
{

        // eta function used in Pen's approximation for luminosity distance
        // in a flat universe.



        struct Eta
        {
                Real operator()(Real A, Real Omega) const;

                private:
                        static const Real c1;
                        static const Real c2;
                        static const Real c3;
                        static const Real c4;
                        static const Real c5;
                        static const Real m8th;
                        static const Real thrd;
        };

        struct FZSQ 
        {
                // compute function for luminosity distance (use expansion up
                // to Q0^2 for small Q0). The luminosity distance is (c/H0)*fZ.
                // if there is a non-zero cosmological constant, use the Pen 
                // approximation (ApJS 1990, 120, 49).

                Real  operator()(Real z, Real q0, Real lambda) const;      
        };



}
#endif
