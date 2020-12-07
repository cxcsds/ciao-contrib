//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RANDOMIZER_H
#define RANDOMIZER_H 1

// xsTypes
#include <xsTypes.h>
// Fit
#include <XSFit/Fit/Fit.h>
// RandomizerBase
#include <XSFit/Randomizer/RandomizerBase.h>
#include <XSFit/Randomizer/RandomizerPolicies.h>

#include <XSUtil/Error/Error.h>
//	This is a host class to combine the policy and trait
//	classes for determining:  1.  The source of the variance
//	information, and 2.  The randomizing distribution
//	function.



template <class Source, class Dist>
class Randomizer : public RandomizerBase  //## Inherits: <unnamed>%4629007402BE
{

  public:
      Randomizer();

      Randomizer(const Randomizer< Source,Dist > &right);
      virtual ~Randomizer();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      //	Note that this host class makes no use of the Fit
      //	pointer passed as a function argument, which is
      //	redundant with the Source trait classes.  It is included
      //	as part of the  interface though for the benefit of
      //	users who wish to write their own non-templated subclass
      //	of RandomizerBase.
      virtual void doRandomize (RealArray& parameterValues, const Fit* fit);
      virtual void doInitializeRun (const Fit* fit);
      void apply (const RealArray& randVals, RealArray& parameterValues) const;
      virtual const RealArray* getCovariance (const Fit* fit);
      virtual void doInitializeLoad ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      RandomizerSourceInfo<Source> m_sourceInfo;

    // Additional Implementation Declarations

};

// Parameterized Class Randomizer 

// Parameterized Class Randomizer 

template <class Source, class Dist>
Randomizer<Source,Dist>::Randomizer()
  :RandomizerBase(Dist::name + string(" ") + RandomizerSourceInfo<Source>::name),
   m_sourceInfo()
{
}

template <class Source, class Dist>
Randomizer<Source,Dist>::Randomizer(const Randomizer<Source,Dist> &right)
  :RandomizerBase(right),
   m_sourceInfo(right.m_sourceInfo)
{
}


template <class Source, class Dist>
Randomizer<Source,Dist>::~Randomizer()
{
}


template <class Source, class Dist>
void Randomizer<Source,Dist>::doRandomize (RealArray& parameterValues, const Fit* fit)
{
   // Can ASSUME parameterValues contains current values of
   // all variable fit parameters.
   const size_t nPars = parameterValues.size();
   const RealArray& scaling = m_sourceInfo.eigenValues();
   if (nPars != scaling.size())
   {
      throw RedAlert("Array size mismatch in Randomizer<Source,Dist>::doRandomize.");
   }
   RealArray randVals(.0,nPars);
   Dist::getValuesFromDistribution(scaling, randVals);
   apply(randVals, parameterValues);
}

template <class Source, class Dist>
void Randomizer<Source,Dist>::doInitializeRun (const Fit* fit)
{
   m_sourceInfo.fillVarInfo(fit);
}

template <class Source, class Dist>
void Randomizer<Source,Dist>::apply (const RealArray& randVals, RealArray& parameterValues) const
{
   const size_t nPars = parameterValues.size();
   const RealArray& eVector = m_sourceInfo.eigenVectors();
   if (eVector.size() != nPars*nPars)
   {
      string errMsg("Eigenvector size mismatch in Randomizer<Source,Dist>::apply.");
      throw RedAlert(errMsg);
   }
   RealArray sigma(.0,nPars);
   for (size_t j=0; j<nPars; ++j)
   {
      Real& sig_j = sigma[j];
      for (size_t k=0; k<nPars; ++k)
      {
         sig_j += randVals[k]*eVector[j*nPars + k];
      }
   }
   parameterValues += sigma;
}

template <class Source, class Dist>
const RealArray* Randomizer<Source,Dist>::getCovariance (const Fit* fit)
{
   return &(m_sourceInfo.covariance(fit));
}

template <class Source, class Dist>
void Randomizer<Source,Dist>::doInitializeLoad ()
{
   m_sourceInfo.validate(initString());
}

// Additional Declarations


#endif
