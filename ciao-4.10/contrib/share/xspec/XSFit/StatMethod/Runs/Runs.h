//   Class definition for the Runs statistic

#ifndef RUNS_H
#define RUNS_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// StatMethod
#include <XSFit/Fit/StatMethod.h>

class Fit;




class Runs : public StatMethod  //## Inherits: <unnamed>%3B7BFB9003E4
{

  public:
      Runs();

      virtual bool checkWeight (const XSContainer::Weight* weightMethod) const;
      virtual Real plotChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;
      virtual Real plotDeltaChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;

      virtual Real sumDerivs (const ArrayContainer& dFolded, int parameterIndex) const;

      virtual Real sumSecondDerivs (const std::map<size_t,ArrayContainer>& dFolded, int pi, int pj);
      virtual const std::string& fullName () const;
      virtual const std::string& scriptName () const;

    // Additional Public Declarations

  protected:

    // Additional Protected Declarations

  private:

      Runs(const Runs &right);

      Runs& operator=(const Runs& right);
      virtual void doReport () const;
      virtual ArrayContainer getDifferences (const Fit* fit) const;
      virtual std::pair<Real,Real> adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen);

    // Additional Private Declarations

  private: //## implementation
      virtual void doPerform (Fit* fit);
      virtual void doInitialize (Fit* fit);
      virtual void doDeallocate ();
      virtual void doReset (Fit* fit);

    // Data Members for Class Attributes

    // Data Members for Associations
      ArrayContainer m_difference;
      std::string m_fullName;
      std::string m_scriptName;

    // Additional Implementation Declarations

};

// Class Runs 

inline const std::string& Runs::fullName () const
{
  return m_fullName;
}

inline const std::string& Runs::scriptName () const
{
  return m_scriptName;
}


#endif
