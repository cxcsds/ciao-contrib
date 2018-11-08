//C++

#ifndef INTEGRATE_H
#define INTEGRATE_H

#include <xsTypes.h>
#include <utility>


namespace Numerics {

   //	Integrates a flux array between limits and returns
   //	photon flux and erg flux.
   std::pair<Real,Real> integrationKernel (const RealArray& energy, 
        const RealArray& fluxArray, const Real& eMin, const Real& eMax);

}


#endif
