//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

// This is the class for Chi-square with the model denominator irrespective of the weighting set.
// It is used as the test statistic.

#ifndef PEARSONCHISQUARE_H
#define PEARSONCHISQUARE_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// StatMethod
#include <XSFit/Fit/StatMethod.h>

class Fit;




class PearsonChiSquare : public StatMethod  //## Inherits: <unnamed>%3B7BFB9003E4
{

  public:
      PearsonChiSquare();

      virtual bool checkWeight (const XSContainer::Weight* weightMethod) const;
      virtual Real plotChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;
      virtual Real plotDeltaChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;

      virtual Real sumDerivs (const ArrayContainer& dFolded, int parameterIndex) const;

      virtual Real sumSecondDerivs (const std::map<size_t,ArrayContainer>& dFolded, int pi, int pj);
      static Real calcMinVariance (Real areaTime, Real backAreaTime, Real bscaleRatio);
      virtual const std::string& fullName () const;
      virtual const std::string& scriptName () const;

    // Additional Public Declarations

  protected:

    // Additional Protected Declarations

  private:

      PearsonChiSquare(const PearsonChiSquare &right);

      PearsonChiSquare& operator=(const PearsonChiSquare& right);
      virtual void doReport () const;
      virtual ArrayContainer getDifferences (const Fit* fit) const;
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

    // Additional Implementation Declarations

};

// Class PearsonChiSquare 

inline const std::string& PearsonChiSquare::fullName () const
{
  return m_fullName;
}

inline const std::string& PearsonChiSquare::scriptName () const
{
  return m_scriptName;
}


#endif
