//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RANDOMLUXADAPTER
#define RANDOMLUXADAPTER 1

namespace Numerics {
    class RandomLux;

} // namespace Numerics
#include <xsTypes.h>


namespace Numerics {



    class RandomLuxAdapter 
    {

      public:
          RandomLuxAdapter();
          ~RandomLuxAdapter();

          void initialize (int seed, const std::vector<Real>& extraPars);
          void getRandom (std::vector<Real>& randNumbers, const std::vector<Real>& extraPars);
          void getRandom (float* randNumbers, int length, const std::vector<Real>& extraPars);
          void getRandom (Real* randNumbers, int length, const std::vector<Real>& extraPars);

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          RandomLuxAdapter(const RandomLuxAdapter &right);
          RandomLuxAdapter & operator=(const RandomLuxAdapter &right);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          RandomLux* m_generator;

        // Additional Implementation Declarations

    };

    // Class Numerics::RandomLuxAdapter 

} // namespace Numerics


#endif
