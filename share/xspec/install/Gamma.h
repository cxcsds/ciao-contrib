// C++


#ifndef GAMMA_H
#define GAMMA_H

#include "xsTypes.h"
#include <vector>

namespace Numerics
{

        extern const Real STP;
        extern const Real FPF;
        extern std::vector<Real> C; 
        extern const Real EPS;
        extern const size_t ITMAX;

        struct GammaLN
        {
            public:

                GammaLN();

                Real operator()(Real xx) const;

            private:   

                static bool s_init;

        };

        struct GammaQ
        {
                Real operator()(Real a, Real x) const;

        };

        struct GammaP
        {
                Real operator()(Real a, Real x) const;

        };

        struct Erf
        {
                Real operator()(Real x) const;

        };
        struct Erfc
        {
                Real operator()(Real x) const;

        };

        void Gser(Real& gamSer, Real a, Real x, Real& gln);

        void Gcf (Real& gammCF, Real a, Real x, Real& gln);
}

#endif
