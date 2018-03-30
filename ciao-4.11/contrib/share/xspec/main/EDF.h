//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EDF_H
#define EDF_H 1
#include <xsTypes.h>
#include <XSContainer.h>
#include <XSstreams.h>
#include <XSFit/Fit/Fit.h>
#include <XSModel/Data/SpectralData.h>
#include <XSModel/Data/Detector/Response.h>
#include <XSModel/Data/BackCorr/Background.h>
#include <XSModel/GlobalContainer/DataContainer.h>
#include <XSModel/GlobalContainer/DataSetTypes.h>
#include <XSModel/GlobalContainer/ModelContainer.h>
#include <XSModel/GlobalContainer/ModelTypes.h>
#include <XSModel/Model/Model.h>
#include <iostream>
#include <iomanip>
#include <set>

// StatMethod
#include <XSFit/Fit/StatMethod.h>




template <typename Strategy>
class EDF : public StatMethod  //## Inherits: <unnamed>%45A2A73E0089
{

  private:



    typedef std::pair<size_t,RealArray> SpecFactors;
    //	Key = spectrum number, Value = pair consisting of
    //	starting position in m_accumulated arrays and area*time
    //	factors.



    typedef std::map<size_t,SpecFactors> FactorContainer;

  public:
      EDF();
      virtual ~EDF();

      //      virtual StatMethod* clone () const;
      virtual const string& fullName () const;
      //	return string used to denote stat method while plotting.
      //
      //	abstract.
      virtual const string& scriptName () const;

    // Additional Public Declarations

  protected:
      virtual void doPerform (Fit* fit);
      virtual void doDeallocate ();

    // Additional Protected Declarations

  private:
      EDF(const EDF< Strategy > &right);
      EDF< Strategy > & operator=(const EDF< Strategy > &right);

      virtual void doReport () const;
      virtual void doReset (Fit* fit);
      virtual ArrayContainer getDifferences (const Fit* fit) const;
      virtual std::pair<Real,Real> adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen);
      void accumulateCounts (Fit* fit);
      void accumulateModel (Fit* fit);

    // Additional Private Declarations

  private: //## implementation
      virtual void doInitialize (Fit* fit);

    // Data Members for Class Attributes
      RealArray m_accumulatedCounts;
      RealArray m_accumulatedModel;
      Real m_totalCounts;

    // Additional Implementation Declarations
      FactorContainer m_cachedFactors;
};

// Parameterized Class EDF 

// Parameterized Class EDF 

template <typename Strategy>
EDF<Strategy>::EDF()
  : StatMethod(Strategy::cmdName),
    m_totalCounts(.0)
{
   isDerivAnalytic(false);
}

template <typename Strategy>
EDF<Strategy>::EDF(const EDF<Strategy> &right)
  : StatMethod(right),
    m_accumulatedCounts(right.m_accumulatedCounts),
    m_accumulatedModel(right.m_accumulatedModel),
    m_totalCounts(right.m_totalCounts),
    m_cachedFactors(right.m_cachedFactors)
{
}


template <typename Strategy>
EDF<Strategy>::~EDF()
{
}


//template <typename Strategy>
//StatMethod* EDF<Strategy>::clone () const
//{
//   return new EDF<Strategy>(*this);
//}

template <typename Strategy>
const string& EDF<Strategy>::fullName () const
{
   return Strategy::fullName;
}

template <typename Strategy>
const string& EDF<Strategy>::scriptName () const
{
   return Strategy::scriptName;
}

template <typename Strategy>
void EDF<Strategy>::doReport () const
{
  using namespace std;
  using namespace XSContainer;
  if (!getSpectraForStat().empty())
  {
     ios_base::fmtflags saveFmt(tcout.flags());
     streamsize savePrec(tcout.precision());
     const size_t bins = nBinsUsed();
     Real truncatedStat = StatMethod::setOutputFormat(statistic());
     tcout << Strategy::fullName <<" = " << setw(14) << truncatedStat << " using " 
                     << bins << " PHA bins";
     const StatMethod* singleStat = fit->statManager()->usingSingleStat();
     if (singleStat == this)
     {
        std::pair<int,size_t> dofVals = fit->statManager()->totalDegreesOfFreedom();
        tcout << " and " << dofVals.first << " degrees of freedom.";
     }
     else
        tcout <<".";
     tcout << endl;

     tcout.precision(savePrec);
     tcout.flags(saveFmt);
  }
}

template <typename Strategy>
void EDF<Strategy>::doReset (Fit* fit)
{
   using namespace XSContainer;
   std::set<string>::iterator ss (fit->activeModels().begin());
   std::set<string>::iterator ssEnd (fit->activeModels().end());
   while ( ss != ssEnd)
   {
         models->calculate(*ss);
         models->fold(*ss);
	 ++ss;
   }   
}

template <typename Strategy>
ArrayContainer EDF<Strategy>::getDifferences (const Fit* fit) const
{
   ArrayContainer differences;
   XSContainer::SpectralDataMapConstIt itSp = fit->spectraToFit().begin();
   XSContainer::SpectralDataMapConstIt itSpEnd = fit->spectraToFit().end();
   while (itSp != itSpEnd)
   {
      const size_t specNum = itSp->first;
      const SpectralData* pSpec = itSp->second;
      const std::valarray<size_t>& IN = pSpec->indirectNotice();
      const size_t sz = IN.size();
      const size_t pos = m_cachedFactors.find(specNum)->first;
      RealArray& diffArray = differences[specNum];
      diffArray.resize(sz);
      diffArray = m_accumulatedCounts[std::slice(pos,sz,1)];
      diffArray -= m_accumulatedModel[std::slice(pos,sz,1)];
      ++itSp;
   }
   return differences;
}

template <typename Strategy>
std::pair<Real,Real> EDF<Strategy>::adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen)
{
  std::pair<Real,Real> fSums (0.,0.);
  static size_t iSpecCount = 1;
  static Real totModCounts = .0;
  static Real totFrozenCounts = .0;
  const size_t nFitSpecs = XSContainer::fit->spectraToFit().size();

  // Assume all information set in doInitialize is current.
  // Need to keep track of the total model counts (which includes
  // the contributions from frozen norms).  In this context, the 
  // order these are analyzed is unimportant.
  const std::valarray<size_t>& IN = spec->indirectNotice();
  const size_t N = IN.size(); 
  const size_t specNum = spec->spectrumNumber();
  RealArray totalModel(.0,N);
  RealArray totalModFroz(.0,N);
  for (size_t i=0; i<models.size(); ++i)
  {
     Model* mod = models[i];
      std::map<Model*,ArrayContainer >::const_iterator itSaved =
                savedValsForFrozen.find(mod);
      if (itSaved != savedValsForFrozen.end())
      {
         totalModel += itSaved->second.find(specNum)->second[IN];
         totalModFroz += mod->foldedModel(specNum)[IN];
      }
      else
      {
         totalModel += mod->foldedModel(specNum)[IN];
      }     
  }
  totalModel *= spec->areaScale()[IN];
  totalModel *= spec->exposureTime();
  totalModFroz *= spec->areaScale()[IN];
  totalModFroz *= spec->exposureTime();
  totModCounts += totalModel.sum();
  totFrozenCounts += totalModFroz.sum();

  // This is a rather inelegant way of dealing with the fact that 
  // StatMethod::renormalize calls this function once for every fit 
  // spectrum, since that's what other statistics need.  EDF stats
  // however can only calculate adjustment at the end.  So just return
  // zeros until called for the last spectrum.  Also, CAN'T ASSUME that
  // renormalize is sending the spectra in numbered order.

  if (iSpecCount == nFitSpecs)
  {
     // The final renorm factor should be: 
     // (totalPhaCounts - frozenNormCounts)/(totalModCounts - frozenNormCounts)
     fSums.first = m_totalCounts - totFrozenCounts;
     fSums.second = totModCounts - totFrozenCounts;
     totModCounts = .0;
     totFrozenCounts = .0;
     iSpecCount = 1;
  }
  else
  {     
     ++iSpecCount;
  }
  return fSums;
}

template <typename Strategy>
void EDF<Strategy>::doInitialize (Fit* fit)
{
   StatMethod::doInitialize(fit);
   m_cachedFactors.clear();
   size_t pos = 0;
   XSContainer::SpectralDataMapConstIt itSp = fit->spectraToFit().begin();
   XSContainer::SpectralDataMapConstIt itSpEnd = fit->spectraToFit().end();
   while (itSp != itSpEnd)
   {
      const size_t specNum = itSp->first;
      const SpectralData* pSpec = itSp->second;
      const std::valarray<size_t>& IN = pSpec->indirectNotice();
      SpecFactors& specFacts = m_cachedFactors[specNum];
      specFacts.first = pos;
      specFacts.second.resize(IN.size());
      specFacts.second = pSpec->exposureTime()*pSpec->areaScale()[IN];
      pos += IN.size();
      ++itSp;
   }
   m_accumulatedCounts.resize(pos, .0);
   m_accumulatedModel.resize(pos, .0); 
   accumulateCounts(fit);
}

template <typename Strategy>
void EDF<Strategy>::accumulateCounts (Fit* fit)
{
   //This is only called per each initialization.  
   XSContainer::SpectralDataMapConstIt itSp = fit->spectraToFit().begin();
   XSContainer::SpectralDataMapConstIt itSpEnd = fit->spectraToFit().end();
   while (itSp != itSpEnd)
   {
      const SpecFactors& specFacts = m_cachedFactors[itSp->first];      
      const SpectralData* pSpec = itSp->second;
      const std::valarray<size_t>& IN = pSpec->indirectNotice();
      RealArray spectrum(pSpec->spectrum()[IN]);
      if (pSpec->background())
      {
         spectrum -= pSpec->background()->spectrum()[IN];
      }
      if (pSpec->correction() && pSpec->correctionScale())
      {
         spectrum -= pSpec->correctionScale()*pSpec->correction()->spectrum()[IN];
      }
      spectrum *= specFacts.second;
      m_accumulatedCounts[std::slice(specFacts.first,IN.size(),1)] = spectrum;
      ++itSp;
   }
   // Perhaps this will speed things up by doing it C-style.
   const size_t totalSz = m_accumulatedCounts.size();
   Real* pStart = &m_accumulatedCounts[0]; 
   for (size_t i=1; i<totalSz; ++i)
   {
      pStart[i] += pStart[i-1];
   }
   // Normalize
   m_totalCounts = m_accumulatedCounts[totalSz-1];
   m_accumulatedCounts /= m_totalCounts;
}

template <typename Strategy>
void EDF<Strategy>::accumulateModel (Fit* fit)
{
   // ASSUMES models are all calculated.
   // Unlike accumulateCounts, this gets called every fit iteration.
   // Therefore don't want to resize m_accumulatedModels in here.
   // ASSUME it has been sized properly during the doInitialize phase.
   using namespace XSContainer;

   m_accumulatedModel = .0;  
   ModelMapConstIter itMod (models->modelSet().begin());      
   ModelMapConstIter  itModEnd (models->modelSet().end());      
   while (itMod != itModEnd)
   {
      const Model* mod = itMod->second;
      if (mod->isActive())
      {
         ArrayContainer::const_iterator itFolded = mod->foldedModel().begin();
         ArrayContainer::const_iterator itFoldedEnd = mod->foldedModel().end();
         while (itFolded != itFoldedEnd)
         {
            const size_t specNum = itFolded->first;
            const SpectralData* spec = datasets->lookup(specNum);
            const size_t pos = m_cachedFactors[specNum].first;
            const std::valarray<size_t>& IN = spec->indirectNotice();
            m_accumulatedModel[std::slice(pos, IN.size(), 1)]
                   += itFolded->second[IN];
            ++itFolded;
         }
      }
      ++itMod;
   }

   // Trying to minimize the number of multiplications by doing
   // this AFTER all folded model arrays have been gathered for
   // each spectrum.
   FactorContainer::const_iterator itFact = m_cachedFactors.begin();
   FactorContainer::const_iterator itFactEnd = m_cachedFactors.end();
   while (itFact != itFactEnd)
   {
      const SpecFactors& specFacts = itFact->second;
      const size_t pos = specFacts.first;
      const RealArray& areaTime = specFacts.second;
      m_accumulatedModel[std::slice(pos, areaTime.size(), 1)]
                *= areaTime;      
      ++itFact;
   }
   const size_t totalSz = m_accumulatedModel.size();
   Real* pStart = &m_accumulatedModel[0];
   for (size_t i=1; i<totalSz; ++i)
   {
      pStart[i] += pStart[i-1];
   }
   Real totalModCounts = m_accumulatedModel[totalSz-1];
   m_accumulatedModel /= totalModCounts;   
}

template <typename Strategy>
void EDF<Strategy>::doPerform (Fit* fit)
{
   doReset(fit);
   accumulateCounts(fit);
   accumulateModel(fit);
   Real statVal = Strategy::calculate(m_accumulatedCounts, m_accumulatedModel,
                m_totalCounts);
   statistic(log(statVal));
}

template <typename Strategy>
void EDF<Strategy>::doDeallocate ()
{
   StatMethod::doDeallocate();

   m_accumulatedCounts.resize(0);
   m_accumulatedModel.resize(0);
   m_cachedFactors.clear();  
}

// Additional Declarations


#endif
