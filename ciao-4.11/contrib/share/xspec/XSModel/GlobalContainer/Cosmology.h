//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef COSMOLOGY_H
#define COSMOLOGY_H 1
#include "xsTypes.h"

namespace XSContainer {



    struct Cosmology 
    {
          Cosmology (Real H = 50, Real q = 0.5, Real lambda = 0);

        // Data Members for Class Attributes
          Real H0;
          Real q0;
          Real lambda0;

      public:
      protected:
      private:
      private: //## implementation
    };

    // Class XSContainer::Cosmology 

} // namespace XSContainer


#endif
