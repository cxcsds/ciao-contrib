//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RANDOMLUX
#define RANDOMLUX 1

namespace Numerics {
/*       Subtract-and-borrow random number generator proposed by
         Marsaglia and Zaman, implemented by F. James with the name
         RCARRY in 1991, and later improved by Martin Luescher
         in 1993 to produce "Luxury Pseudorandom Numbers".
     Fortran 77 coded by F. James, 1993
     Translated to C++ by C. Gordon, 2006

   LUXURY LEVELS.
   ------ ------      The available luxury levels are:

  level 0  (p=24): equivalent to the original RCARRY of Marsaglia
           and Zaman, very long period, but fails many tests.
  level 1  (p=48): considerable improvement in quality over level 0,
           now passes the gap test, but still fails spectral test.
  level 2  (p=97): passes all known tests, but theoretically still
           defective.
  level 3  (p=223): DEFAULT VALUE.  Any theoretically possible
           correlations have very small chance of being observed.
  level 4  (p=389): highest possible luxury, all 24 bits chaotic.

!!! ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
!!!  Calling sequences for RANLUX:                                  ++
!!!      CALL RANLUX (RVEC, LEN)   returns a vector RVEC of LEN     ++
!!!                   32-bit random floating point numbers between  ++
!!!                   zero (not included) and one (also not incl.). ++
!!!      CALL RLUXGO(LUX,INT,K1,K2) initializes the generator from  ++
!!!               one 32-bit integer INT and sets Luxury Level LUX  ++
!!!               which is integer between zero and MAXLEV, or if   ++
!!!               LUX .GT. 24, it sets p=LUX directly.  K1 and K2   ++
!!!               should be set to zero unless restarting at a break++ 
!!!               point given by output of RLUXAT (see RLUXAT).     ++
!!!      CALL RLUXAT(LUX,INT,K1,K2) gets the values of four integers++
!!!               which can be used to restart the RANLUX generator ++
!!!               at the current point by calling RLUXGO.  K1 and K2++
!!!               specify how many numbers were generated since the ++
!!!               initialization with LUX and INT.  The restarting  ++
!!!               skips over  K1+K2*E9   numbers, so it can be long.++
!!!   A more efficient but less convenient way of restarting is by: ++
!!!      CALL RLUXIN(ISVEC)    restarts the generator from vector   ++
!!!                   ISVEC of 25 32-bit integers (see RLUXUT)      ++
!!!                (Note that unlike RLUXGO this does NOT seed an   ++
!!!                uninitialized generator -C.G.)                   ++                
!!!      CALL RLUXUT(ISVEC)    outputs the current values of the 25 ++
!!!                 32-bit integer seeds, to be used for restarting ++
!!!      ISVEC must be dimensioned 25 in the calling program        ++
!!! ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
*/



    class RandomLux 
    {

      public:
          RandomLux();
          ~RandomLux();

          void rluxgo (int lux, int ins, int k1, int k2);
          void ranlux (float* rvec, int lenv);
          void rluxin (const int* isdext);
          void rluxut (int* isdext) const;
          void rluxat (int& lout, int& inout, int& k1, int& k2) const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          RandomLux(const RandomLux &right);
          RandomLux & operator=(const RandomLux &right);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          static const int s_LXDFLT;
          static const int s_IGIGA;
          static const int s_JSDFLT;
          static const int s_ITWO24;
          static const int s_ICONS;
          static float s_TWOP12;
          static float s_twom24;
          static float s_twom12;
          static int s_next[24];
          bool m_notyet;
          int m_i24;
          int m_j24;
          float m_carry;
          int m_luxlev;
          int m_nskip;
          int m_in24;
          int m_kount;
          int m_mkount;
          int m_inseed;
          float m_seeds[24];

        // Additional Implementation Declarations
          const static int s_MAXLEV;
          const static int s_ndskip[];
    };

    // Class Numerics::RandomLux 

} // namespace Numerics


#endif
