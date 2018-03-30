

#ifndef NUMERICS_H
#define NUMERICS_H

#include "Beta.h"
#include "Gamma.h"
#include "CosmologyFunction.h"
#include "RandomGenerator.h"
#include "AstroFunctions.h"
#include "xsTypes.h"

namespace Numerics {

  static const Real KEVTOA = 12.39841974;     // CODATA 2014
  static const Real KEVTOHZ = 2.4179884076620228e17;
  static const Real KEVTOERG = 1.60217733e-9;
  static const Real KEVTOJY = 1.60217733e14;
  static const Real DEGTORAD = .01745329252;
  static const Real LIGHTSPEED = 299792.458;   // defined km/s
  static const Real AMU = 1.660539040e-24;     // Unified atomic mass unit in g

}

#endif
