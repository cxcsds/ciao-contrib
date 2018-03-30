//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef INCGAMMA_H
#define INCGAMMA_H 1
#include <xsTypes.h>

namespace Numerics {
    //	The IncGamma class computes the unnormalized incomplete
    //	Gamma function:
    //
    //	                 [inf]
    //	  Gamma(a,x) = Int   exp^(-t)*t^(a-1)dt
    //	                 [x]
    //	                   = Gamma(a)*Q(a,x)
    //
    //	with the restriction that x > 0.0.  If x <= 0.0, the
    //	operator() function will throw a YellowAlert.  'a' is
    //	allowed to be pos, zero, or neg.



    class IncGamma 
    {

      public:
          IncGamma();

          Real operator () (const Real a, const Real x) const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          static Real continuousFraction (const Real a, const Real x);
          static Real seriesSolution (const Real a, const Real x);
          //	This is needed for small 'x' and negative 'a'.
          static Real integrateByParts (const Real a, const Real x);

        // Additional Private Declarations

      private: //## implementation
        // Additional Implementation Declarations

    };

    // Class Numerics::IncGamma 

} // namespace Numerics


#endif
