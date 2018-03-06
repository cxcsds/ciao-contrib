// C++

#ifndef ASTROFUNCTIONS_H
#define ASTROFUNCTIONS_H

#include "xsTypes.h"
#include <cmath>
namespace Numerics {

   namespace AstroFunctions {

      bool sexagesimalToDecimal(const string& input,  Real& decDegrees); 

      bool isIntValue(Real inVal);
   }
}

inline bool Numerics::AstroFunctions::isIntValue(Real inVal)
{
   return std::abs(inVal - std::floor(inVal)) < 1.E-06;
}

#endif
