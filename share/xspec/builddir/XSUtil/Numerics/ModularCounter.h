//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MODULARCOUNTER_H
#define MODULARCOUNTER_H 1
#include <xsTypes.h>

namespace Numerics {



    class ModularCounter 
    {

      public:
          // If isRasterScan is 'true', the counter will increment
          // in back-and-forth sweeps within each digit.  Otherwise
          // an increment always increases the value of a digit and 
          // resets to zero after reaching the max.
          ModularCounter (const IntegerVector& bases, bool isRasterScan=false);
          ~ModularCounter();

          // startingPos MUST ALWAYS be less than the last value in m_factors.
          void reset (int startingPos);
          ModularCounter& operator ++ ();
          const ModularCounter operator ++ (int i);
          const IntegerVector& bases () const;
          const IntegerVector& counter () const;
          int currentPos () const;
          // Converts the currentPos value to the position it would have
          //  in a standard rather than back-and-forth sweep.
          int rasterToStandardPos() const;         
          bool isRasterScan() const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          ModularCounter & operator=(const ModularCounter &right);
          
          // Directions are calculated only when isRasterScan is true.
          void calcDirections();
          void calcCoordinates();
          
      private: //## implementation
        // Data Members for Class Attributes
          const IntegerVector m_bases;
          // Example: If m_bases={3,2,4}, m_factors will be {1,3,6,24}.
          IntegerVector m_factors;
          IntegerVector m_counter;
          int m_currentPos;
          const bool m_isRasterScan;
          IntegerVector m_direction;

        // Additional Implementation Declarations

    };

    // Class Numerics::ModularCounter 

    inline const IntegerVector& ModularCounter::bases () const
    {
      return m_bases;
    }

    inline const IntegerVector& ModularCounter::counter () const
    {
      return m_counter;
    }

    inline int ModularCounter::currentPos () const
    {
      return m_currentPos;
    }
    
    inline bool ModularCounter::isRasterScan () const
    {
       return m_isRasterScan;
    }
    
} // namespace Numerics


#endif
