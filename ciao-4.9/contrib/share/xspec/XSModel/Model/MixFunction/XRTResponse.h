//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XRTRESPONSE_H
#define XRTRESPONSE_H 1

// Error
#include <XSUtil/Error/Error.h>




class XRTResponse 
{

  public:



    class XRTResponseError : public YellowAlert  //## Inherits: <unnamed>%404F67000000
    {
      public:
          XRTResponseError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      XRTResponse (const string& fileName);
      ~XRTResponse();

      Real ebinEffectiveArea (Real eMin, Real eMax, Real theta, Real phi);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void readEffectiveArea ();
      Real calcEffectiveArea ();
      void order ();
      Real getSmoothRsp (int ie, int iTheta, int iPhi);
      Real smooth (const RealArray& X, const RealArray& Y);
      Real effAreaInterp (int ie, int iTheta, int iPhi);
      Real getWeightTheta (int iTheta);
      Real getWeightPhi (int iPhi);
      Real weightAverage (bool isPhi);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_fileName;
      RealArray m_energy;
      RealArray m_theta;
      RealArray m_phi;
      RealArray m_effectiveArea;
      static StringArray s_colNames;
      static string s_ENERG_LO;
      static string s_THETA;
      static string s_PHI;
      static string s_EFFAREA;
      Real m_inEng;
      IntegerArray m_eOrder;
      Real m_inTheta;
      Real m_inPhi;
      RealArray m_rspTheta;
      RealArray m_rspPhi;
      RealArray m_wghtTheta;
      RealArray m_wghtPhi;

    // Additional Implementation Declarations

};

// Class XRTResponse::XRTResponseError 

// Class XRTResponse 


#endif
