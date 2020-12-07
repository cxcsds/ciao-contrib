//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef STATMETHOD_H
#define STATMETHOD_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// map
#include <map>
// Error
#include <XSUtil/Error/Error.h>
// FitStrategy
#include <XSFit/Fit/FitStrategy.h>
namespace XSContainer {
    class Weight;

} // namespace XSContainer
//#include "Global/XSGlobal.h"
class Model;
class ModParam;
class SpectralData;




class StatMethod : public FitStrategy  //## Inherits: <unnamed>%3A7EC47E028F
{

  public:
    //	Invalid spectrum number thrown by lookup error for
    //	the Spectrum's workspace arrays. This will be fatal.



    class InvalidSpectrumNumber : public RedAlert  //## Inherits: <unnamed>%3C59959C01D7
    {
      public:
          InvalidSpectrumNumber (size_t num);

      protected:
      private:
      private: //## implementation
    };



    class InvalidParameterError : public RedAlert  //## Inherits: <unnamed>%3C5AAA3000C1
    {
      public:
          InvalidParameterError ();

      protected:
      private:
      private: //## implementation
    };



    class FitNotDefined : public YellowAlert  //## Inherits: <unnamed>%3CF4E0A60153
    {
      public:
          FitNotDefined (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class NoSuchSpectrum : public YellowAlert  //## Inherits: <unnamed>%3CF4E7000102
    {
      public:
          NoSuchSpectrum (const string& diag);

      protected:
      private:
      private: //## implementation
    };
      virtual ~StatMethod();

      bool isDerivAnalytic () const;

      //  Public virtual to check weighting scheme.  The base class
      //  implementation only returns true for standard weighting.
      //  This will be overriden by statistics that behave like chi^2 
      //  and do admit other weightings.
      virtual bool checkWeight (const XSContainer::Weight* weightMethod) const;
      void initialize (Fit* fit);
      void deallocate ();
      void renormalize (Fit* fit);

      size_t nBinsUsed() const;
      void report () const;
      void peakResidual (const Fit* fit, std::pair<Real,Real>& max, std::pair<Real,Real>& min, size_t spectrum, const std::pair<Real,Real> range) const;
      virtual Real plotChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;
      virtual Real plotDeltaChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;

      virtual void getWeightDerivs();

      virtual Real sumDerivs (const ArrayContainer& dFolded, int parameterIndex) const;

      virtual Real sumSecondDerivs (const std::map<size_t,ArrayContainer>& dFolded, int pi, int pj);
      virtual const string& fullName () const = 0;
      //	return string used to denote stat method while plotting.
      //
      //	abstract.
      virtual const string& scriptName () const = 0;
      Real statistic () const;
      void statistic (Real value);

      const std::vector<const SpectralData*>& getSpectraForStat() const;
      std::vector<const SpectralData*>& spectraForStat();

      static Real setOutputFormat (const Real statistic, int degrees = 0);

      const std::string& name () const;
      void name (const std::string& value);

      const int number () const;
      void number (const int value);

      const std::string modifier () const;
      void modifier (const std::string& value);

  public:
    // Additional Public Declarations

  protected:
      StatMethod (const std::string& name);

      virtual void doInitialize (Fit* fit);
      virtual void doDeallocate ();
      //	StatMethods which set this flag to true need to make
      //	sure sumDerivs and sumSecondDerivs functions are
      //	properly overriden.  These will be called by analytic
      //	Differentiate function.
      void isDerivAnalytic (bool value);
      const ArrayContainer& protoWorkspace () const;

    // Additional Protected Declarations

  private:

      StatMethod(const StatMethod &right);

      StatMethod& operator=(const StatMethod& right);
      virtual void doReport () const = 0;
      virtual void doReset (Fit* fit) = 0;
      void doPeakResidual (const Fit* fit, const ArrayContainer& difference, std::pair<Real,Real>& max, std::pair<Real,Real>& min, size_t spectrum, const std::pair<Real,Real> range) const;
      virtual ArrayContainer getDifferences (const Fit* fit) const = 0;
      virtual std::pair<Real,Real> adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen) = 0;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_statistic;
      bool m_isDerivAnalytic;

      std::vector<const SpectralData*> m_spectraForStat;

    // Data Members for Associations
      std::string m_name;
      ArrayContainer m_protoWorkspace;

    // this is needed by the whittle and cstat statistics but included in general in case it
    // is useful later
      int m_number;
      string m_modifier;

    // Additional Implementation Declarations

};

// Class StatMethod::InvalidSpectrumNumber 

// Class StatMethod::InvalidParameterError 

// Class StatMethod::FitNotDefined 

// Class StatMethod::NoSuchSpectrum 

// Class StatMethod 


inline Real StatMethod::statistic () const
{
  return m_statistic;
}

inline void StatMethod::statistic (Real value)
{
  m_statistic = value;
}

inline bool StatMethod::isDerivAnalytic () const
{
  return m_isDerivAnalytic;
}

inline void StatMethod::isDerivAnalytic (bool value)
{
  m_isDerivAnalytic = value;
}

inline const std::vector<const SpectralData*>& StatMethod::getSpectraForStat() const
{
   return m_spectraForStat;
}

inline std::vector<const SpectralData*>& StatMethod::spectraForStat()
{
   return m_spectraForStat;
}

inline const std::string& StatMethod::name () const
{
  return m_name;
}

inline void StatMethod::name (const std::string& value)
{
  m_name = value;
}

inline const ArrayContainer& StatMethod::protoWorkspace () const
{
  return m_protoWorkspace;
}

inline const int StatMethod::number () const
{
  return m_number;
}

inline void StatMethod::number (const int value)
{
  m_number = value;
}

inline const std::string StatMethod::modifier () const
{
  return m_modifier;
}

inline void StatMethod::modifier (const std::string& value)
{
  m_modifier = value;
}


#endif
