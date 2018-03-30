//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CHISQUARE_H
#define CHISQUARE_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// StatMethod
#include <XSFit/Fit/StatMethod.h>

class Fit;




class ChiSquare : public StatMethod  //## Inherits: <unnamed>%3B7BFB9003E4
{

  public:
      ChiSquare();

      virtual bool checkWeight (const XSContainer::Weight* weightMethod) const;
      virtual Real plotChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;
      virtual Real plotDeltaChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;

      virtual void getWeightDerivs ();

      virtual Real sumDerivs (const ArrayContainer& dFolded, int parameterIndex) const;

      virtual Real sumSecondDerivs (const std::map<size_t,ArrayContainer>& dFolded, int pi, int pj);
      static Real calcMinVariance (Real areaTime, Real backAreaTime, Real bscaleRatio);
      virtual const std::string& fullName () const;
      virtual const std::string& scriptName () const;

    // Additional Public Declarations

  protected:

    // Additional Protected Declarations

  private:

      ChiSquare(const ChiSquare &right);

      ChiSquare& operator=(const ChiSquare& right);
      virtual void doReport () const;
      virtual ArrayContainer getDifferences (const Fit* fit) const;
      void calcD2Sigma (size_t specNum, RealArray& correction) const;
      virtual std::pair<Real,Real> adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen);
      //	Returns true if any channel's variance required that a
      //	minimum value be added.
      static bool applyMinVariance (const SpectralData* sd, RealArray& variance);

    // Additional Private Declarations

  private: //## implementation
      virtual void doPerform (Fit* fit);
      virtual void doInitialize (Fit* fit);
      virtual void doDeallocate ();
      virtual void doReset (Fit* fit);

    // Data Members for Class Attributes
      //	Contains the 1-based spectrum numbers of any spectra
      //	which required an applied minimum variance during the
      //	most recent doPerform call.
      std::vector<size_t> m_specsWithZeroVarChans;

    // Data Members for Associations
      ArrayContainer m_difference;
      ArrayContainer m_variance;
      std::string m_fullName;
      std::string m_scriptName;
      ArrayContainer m_dSigma;

    // Additional Implementation Declarations

};

// Class ChiSquare 

inline const std::string& ChiSquare::fullName () const
{
  return m_fullName;
}

inline const std::string& ChiSquare::scriptName () const
{
  return m_scriptName;
}


#endif
