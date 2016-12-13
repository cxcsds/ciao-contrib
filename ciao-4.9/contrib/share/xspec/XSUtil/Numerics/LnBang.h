#ifndef LNBANG_H
#define LNBANG_H

#include <xsTypes.h>

namespace Numerics {

   class LnBang
   {
      // Class to return LN N!. Uses a look-up table for N<=1000 
      // and Log Gamma approximation for larger N.
      public:
         Real operator () (int n);
      private:
         static const Real s_logFact[];
         static const int s_NFACT;
         static const Real s_coeff[];
         static const int s_NCOEFF;
         static const Real s_step;
   };

}

#endif
