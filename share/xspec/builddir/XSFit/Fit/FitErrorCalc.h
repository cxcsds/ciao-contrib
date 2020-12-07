//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef FITERRORCALC_H
#define FITERRORCALC_H 1
#include <xsTypes.h>

// Error
#include <XSUtil/Error/Error.h>
#include <queue>
#include <utility>

class Fit;
class ModParam;
class FitErrorOutput;



class FitErrorCalc 
{

  public:



    typedef std::pair<Real,Real> Coord2D;



    class ParamCalcError : public YellowAlertNS  //## Inherits: <unnamed>%40C5E3300226
    {
      public:
          ParamCalcError (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    class NewMinFound : public YellowAlertNS  //## Inherits: <unnamed>%42443A560065
    {
      public:
          NewMinFound (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    typedef enum {OK=0, NEWMIN=1, NONMON=2, GENPROB=4, LOWLIM=8, UPLIM=16, FROZEPAR=32, NEGFAIL=64, POSFAIL=128, TOOLARGE=256}  ErrorCalcCodes;
      FitErrorCalc (Fit* fit, const int iParam, bool isParallel);
      ~FitErrorCalc();

      void perform ();
      ModParam* parameter () const;
      std::queue<std::pair<string,int> >& msgQueue();
      
      static int fit3Points (const std::vector<Coord2D >& fitPoints, std::vector<Real>& coeffs);
      static int fit2Points (const std::vector<Coord2D >& fitPoints, std::vector<Real>& coeffs);
      static string errCodeToString (FitErrorCalc::ErrorCalcCodes errCode);
      static FitErrorCalc::ErrorCalcCodes stringToErrCode (const string& errString);
      FitErrorCalc::ErrorCalcCodes status () const;

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void interpolate ();
      void calcUncertainty ();
      void commonRestore ();
      void resetFit ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Fit* m_fit;
      const int m_fullIndex;
      int m_direction;
      int m_savedChatter;
      Real m_bestStat;
      Real m_deltaStat;
      Real m_currentDeltaStat;
      Real m_hardLimit;
      Real m_xTrial;
      std::pair<Coord2D,Coord2D > m_limits;
      std::vector<Real> m_coeffs;
      std::vector<Coord2D > m_interpPoints;
      ModParam* const m_param;
      Real m_bestParValue;
      FitErrorCalc::ErrorCalcCodes m_status;
      
      // These members are for handling the FitErrorCalc implementation
      //  differences between single and parallel processing modes.
      //  Note that the mode cannot be changed during the FitErrorCalc 
      //  object's lifetime.      
      const bool m_isParallel;
      FitErrorOutput* m_msgWriter;
      // This will be used in the parallel implementation to store
      //  various messages that otherwise would have been output directly
      //  to the screen or log.
      std::queue<std::pair<string, int> > m_msgQueue;
      
      static const int s_outVerbose;

    // Additional Implementation Declarations

};

// Class FitErrorCalc::ErrorCalcError 

// Class FitErrorCalc::ParamCalcError 

// Class FitErrorCalc::NewMinFound 

// Class FitErrorCalc 
inline ModParam* FitErrorCalc::parameter () const
{
   return m_param;
}

inline FitErrorCalc::ErrorCalcCodes FitErrorCalc::status () const
{
  return m_status;
}

inline std::queue<std::pair<string,int> >& FitErrorCalc::msgQueue ()
{
   return m_msgQueue;
}

#endif
