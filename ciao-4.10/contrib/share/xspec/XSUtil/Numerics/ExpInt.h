//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EXPINT_H
#define EXPINT_H 1
#include <xsTypes.h>

namespace Numerics {
     // Evaluate the exponential integral for the specific
     // case of E1(x), using polynomial and rational approximations.
     //
     // Valid for 0 <= x < inf
     //



    class E1 
    {

      public:
          E1();

          Real operator () (const Real x) const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
        // Additional Private Declarations
           static const Real a[];
           static const Real b[];
           static const Real c[];
      private: //## implementation
        // Additional Implementation Declarations

    };

    // Class Numerics::E1 

} // namespace Numerics


#endif
