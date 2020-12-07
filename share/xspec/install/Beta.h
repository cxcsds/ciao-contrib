// C++

#ifndef BETA_H
#define BETA_H

#include "xsTypes.h"
#include <vector>

namespace Numerics {

        struct BetaCf
        {
                public:
                        Real operator () (Real a, Real b, Real x);
                private:
                        static const int ITMAX;
                        static const Real epsilon;
        };


        Real betaI( Real a, Real b, Real x);
}

#endif
