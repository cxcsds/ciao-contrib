//C++
#ifndef CSTAT_H
#define CSTAT_H 1

#include <xsTypes.h>
#include <XSstreams.h>
#include <XSContainer.h>
#include <XSFit/Fit/Fit.h>
#include <XSFit/Fit/StatManager.h>
#include <XSFit/Fit/StatMethod.h>
#include <XSModel/Data/SpectralData.h>
#include <XSModel/Data/BackCorr/Background.h>
#include <XSModel/GlobalContainer/DataSetTypes.h>
#include <XSModel/GlobalContainer/ModelContainer.h>
#include <XSModel/GlobalContainer/ModelTypes.h>
#include <XSModel/Model/Model.h>
#include <XSUtil/Error/Error.h>
#include <algorithm>
#include <cmath>
#include <map>
#include <utility>
#include <sstream>
#include <numeric>

class Model;

template <typename T>
class Cstat : public StatMethod
{
  public:

     Cstat();
     virtual ~Cstat(); 

     virtual Real plotChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;
     virtual Real plotDeltaChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const;
     virtual Real sumDerivs (const ArrayContainer& dFolded, int parameterIndex) const;
     virtual Real sumSecondDerivs (const std::map<size_t,ArrayContainer>& dFolded, int pi, int pj);
     virtual const std::string& fullName () const;
     virtual const std::string& scriptName () const;

  private:

     Cstat(const Cstat<T> &right);
     Cstat<T>& operator=(const Cstat<T>& right);

     virtual void doReport () const;
     virtual void doPerform (Fit* fit);
     virtual void doInitialize (Fit* fit);
     virtual void doDeallocate ();
     virtual void doReset (Fit* fit);

     virtual ArrayContainer getDifferences (const Fit* fit) const;
     virtual std::pair<Real,Real> adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen);

     bool checkForPoissonSource () const;
     bool checkForPoissonBackground () const;
     ArrayContainer& firstDerivCoefficient ();
     void firstDerivCoefficient (const ArrayContainer& value);
     ArrayContainer& secondDerivCoefficient ();
     void secondDerivCoefficient (const ArrayContainer& value);

     ArrayContainer m_firstDerivCoefficient;
     ArrayContainer m_secondDerivCoefficient;

};

template <typename T>
Cstat<T>::Cstat()
 : StatMethod(T::cmdName),
  m_firstDerivCoefficient(),
  m_secondDerivCoefficient()
{
   isDerivAnalytic(true);
}

template <typename T>
Cstat<T>::~Cstat()
{
}

template <typename T>
void Cstat<T>::doPerform(Fit* fit)
{
  using namespace XSContainer;

  doReset(fit);

  // for each model,
  ArrayContainer tmpQ(protoWorkspace());
  ArrayContainer::iterator itTmpQEnd = tmpQ.end();
  ModelMapConstIter ml (models->modelSet().begin());
  ModelMapConstIter mlEnd (models->modelSet().end());
  while (ml != mlEnd) {
    // add up the folded models for each spectrum [ >= indicates multiple sources]
    Model* m (ml->second);
    if (!m->isActive()) {
      ++ml;
      continue;
    }
    ArrayContainer::const_iterator itFold = m->foldedModel().begin();
    ArrayContainer::const_iterator itFoldEnd = m->foldedModel().end();
    while (itFold != itFoldEnd) {
      size_t spectrumIndex (itFold->first);
      ArrayContainer::iterator itTmpQ = tmpQ.find(spectrumIndex);
      if (itTmpQ != itTmpQEnd) {
	SpectralData* spectrum = m->spectrum(spectrumIndex);          
	const std::valarray<size_t>& IN = spectrum->indirectNotice();
	RealArray mod (itFold->second[IN]);
	if (itTmpQ->second.size() != IN.size()) {
	  std::ostringstream oss;
	  oss <<"Array size error for spectrum "<<spectrumIndex
	      << " in Cstat::doPerform.";
	  throw RedAlert(oss.str());
	}
	itTmpQ->second += mod;
      }
      ++itFold;
    }
    ++ml;
  }

  std::vector<const SpectralData*>::const_iterator itSpec =
    spectraForStat().begin();
  std::vector<const SpectralData*>::const_iterator itSpecEnd =
    spectraForStat().end();

  // for each spectrum sum contributions.
  // stat is C/2

  Real stat = 0.0;
  while(itSpec != itSpecEnd) {
    const SpectralData* spectrum = *itSpec;
    const size_t spectrumIndex = spectrum->spectrumNumber();
    const std::valarray<size_t>& IN = spectrum->indirectNotice();

    RealArray ts (spectrum->exposureTime()*spectrum->areaScale()[IN]);
    RealArray S (ts * spectrum->spectrum()[IN]);
    const RealArray& model = tmpQ[spectrumIndex];
    const Background* background (spectrum->background());
    const Background* correction (spectrum->correction());

    if (!background) {
      int ifail = T::specificPerform(S,ts,model,number(),modifier(),stat);
      if ( std::isnan(stat) && ifail >= 0 && !std::isnan(model[ifail]) ) {
	tcout << "NaN detected when calculating statistic for bin " 
	      << ifail << " of spectrum " << spectrum->spectrumNumber() 
	      << std::endl;
	tcout << S[ifail] << " " << " " << ts[ifail] << " " << model[ifail] << std::endl;
	statistic(stat);
	return;
      }
    } else {
      Real bTime (background->data()->exposureTime());
      RealArray tb (background->data()->areaScale()[IN]);
      tb *= background->data()->backgroundScale()[IN];
      tb /= spectrum->backgroundScale()[IN];
      tb *= bTime;
      RealArray B (tb * background->spectrum()[IN]);
      RealArray Berr (tb * background->variance()[IN]);

      if (correction && spectrum->correctionScale() != 0) {
	Real cTime (correction->data()->exposureTime());
	RealArray tc (correction->data()->areaScale()[IN]);
	tc *= correction->data()->backgroundScale()[IN];
	tc /= spectrum->backgroundScale()[IN];
	tc *= spectrum->correctionScale();
	tc *= cTime;
	RealArray C (tc * correction->spectrum()[IN]);
	for (size_t i=0; i<B.size(); i++) B[i] += C[i];
      }

      int ifail = T::specificPerformB(S,B,Berr,ts,tb,model,number(),modifier(),stat);
      if (std::isnan(stat) && ifail >= 0 && 
	   !std::isnan(model[ifail]) && !std::isinf(model[ifail]) ) {
	tcout << "NaN detected when calculating statistic for bin " 
	      << ifail << " of spectrum " << spectrum->spectrumNumber() 
	      << std::endl;
	tcout << S[ifail] << " " << B[ifail] << " " << Berr[ifail] << " " 
	      << ts[ifail] << " " << tb[ifail] << " " << model[ifail] << std::endl;
	statistic(stat);
	return;
      }
    }

    ++itSpec;
  } // end spectra loop

  statistic(2.0*stat);

}

template <typename T>
void Cstat<T>::doInitialize(Fit* fit)
{
  StatMethod::doInitialize(fit);

  // allocate for derivative coefficient arrays.
  std::vector<const SpectralData*>::const_iterator itSpec =
                spectraForStat().begin();
  std::vector<const SpectralData*>::const_iterator itSpecEnd =
                spectraForStat().end();
  while (itSpec != itSpecEnd)
  {
     const size_t N = (*itSpec)->indirectNotice().size();
     const size_t specNum = (*itSpec)->spectrumNumber();
     m_firstDerivCoefficient[specNum].resize(N,0.);
     m_secondDerivCoefficient[specNum].resize(N,0.);
     ++itSpec;
  }
}

template <typename T>
void Cstat<T>::doDeallocate()
{
    StatMethod::doDeallocate();
    m_firstDerivCoefficient.clear();
    m_secondDerivCoefficient.clear();
}

template <typename T>
void Cstat<T>::doReset(Fit* fit)
{
    using namespace XSContainer;

    // for each model,
    ArrayContainer tmpQ(protoWorkspace()); 
    ArrayContainer::iterator itTmpQEnd = tmpQ.end();
    ModelMapConstIter itMod (models->modelSet().begin());      
    ModelMapConstIter itModEnd (models->modelSet().end());      
    while (itMod != itModEnd)
    {
        // add up the folded models for each spectrum [ >= indicates multiple sources]
        Model* m (itMod->second);
        if (!m->isActive()) 
        {
           ++itMod;
           continue;
        }
        ArrayContainer::const_iterator itFold    = m->foldedModel().begin();
        ArrayContainer::const_iterator itFoldEnd = m->foldedModel().end();
        while (itFold != itFoldEnd)
        {
           size_t spectrumIndex (itFold->first);
           ArrayContainer::iterator itTmpQ = tmpQ.find(spectrumIndex);
           if (itTmpQ != itTmpQEnd)
           {
              SpectralData* spectrum = m->spectrum(spectrumIndex);
              const std::valarray<size_t>& IN = spectrum->indirectNotice();
              RealArray mod (itFold->second[IN]);
              if (itTmpQ->second.size() != IN.size())
              {
                 std::ostringstream oss;
                 oss <<"Array size error for spectrum "<<spectrumIndex
                   << " in Cstat::doPerform.";
                 throw RedAlert(oss.str());
              }
              itTmpQ->second += mod;
           }
           ++itFold;
        }
        ++itMod;
    }    

    std::vector<const SpectralData*>::const_iterator itSpec =
                  spectraForStat().begin();
    std::vector<const SpectralData*>::const_iterator itSpecEnd =
                  spectraForStat().end();
    while(itSpec != itSpecEnd) 
    {
        const SpectralData* spectrum  = *itSpec;        
        const size_t spectrumIndex = spectrum->spectrumNumber();
        const std::valarray<size_t>& IN  = spectrum->indirectNotice();

        RealArray ts (spectrum->exposureTime()*spectrum->areaScale()[IN]);
        RealArray S (ts * spectrum->spectrum()[IN]);
	// output arrays for derivative coefficients.
	// diff1 is -C'/2 and diff2 is C''/2
        RealArray& diff1 = m_firstDerivCoefficient[spectrumIndex];
        RealArray& diff2 = m_secondDerivCoefficient[spectrumIndex];
        RealArray& model = tmpQ[spectrumIndex];
        const Background* background (spectrum->background());
        if (!background)
        {
	  T::specificResetCalc(S, ts, model, number(), modifier(), diff1, diff2);
        }
        else
        {
           // Variable definitions follow Appendix B of manual.
           Real bTime (background->data()->exposureTime());
           RealArray tb (background->data()->areaScale()[IN]);
           tb *= background->data()->backgroundScale()[IN];
           tb /= spectrum->backgroundScale()[IN];
           tb *= bTime;
           RealArray B (tb * background->spectrum()[IN]);
           RealArray Berr (tb * background->variance()[IN]);

           T::specificResetCalcB(S, B, Berr, ts, tb, model, number(), modifier(), diff1, diff2);
        }
	++itSpec;
    }
}
// end doReset

template <typename T>
void Cstat<T>::doReport () const
{
  using namespace std;
  using namespace XSContainer;

  if (!getSpectraForStat().empty())
  {
     ios_base::fmtflags saveFmt(tcout.flags());
     streamsize savePrec(tcout.precision());
     const size_t bins = nBinsUsed();
     Real truncatedStat = StatMethod::setOutputFormat(statistic());
     tcout << fullName() <<" = " << setw(14) << truncatedStat << " using " 
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
     bool PoissonSource = checkForPoissonSource();
     bool PoissonBackground = checkForPoissonBackground();

     if (!T::specificValidStatistic(PoissonSource, PoissonBackground)) {
       tcout << "\nWarning: "<< T::cmdName <<" statistic is only valid for Poisson data." << std::endl;
       if (!PoissonSource)
	 tcout << "    Source file is not Poisson" << std::endl;
       if (!PoissonBackground)
	 tcout << "    Background file is not Poisson" << std::endl;
       tcout << std::endl;
     }
     tcout.precision(savePrec);
     tcout.flags(saveFmt);
  }
}

template <typename T>
Real Cstat<T>::plotChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const
{
  Real point (0);
  // Presumeably areaTime is not .0 or it wouldn't have made it here.
  if ( obs > 0 )
  {
       obs *= areaTime;
       mod *= areaTime;
       if (mod > 0)
       {
          Real sign = (obs >= mod) ? 1.0 : -1.0;
          point = 2.0*sign*(mod - obs*(1 - (log(obs) - log(mod))));
       }
       else
          point = NODATA;
  }
  else
  {
        point = 2*mod*areaTime;       
  }      
  return point;                    
}

template <typename T>
Real Cstat<T>::plotDeltaChi (Real obs, Real mod, Real error, Real areaTime, const Real& NODATA) const
{
  Real oN = obs * areaTime;
  Real mN = mod * areaTime;

  Real point = oN - mN;

  // Use the model as the estimator for the variance unless the model is zero
  // in which case use the data - if that is zero too then use the Gehrels error
  // on zero counts

  Real weight = sqrt(mN);
  if ( weight <= 0.0 ) {
    weight = sqrt(oN);
    if ( weight <= 0.0 ) {
      weight = (1.0 + sqrt(0.75));
    }
  }

  //  tcout << oN << " " << mN << " " << weight << " " << point/weight << std::endl;

  return point/weight;                    
}

template <typename T>
ArrayContainer Cstat<T>::getDifferences (const Fit* fit) const
{
  using namespace XSContainer;
  ArrayContainer result;

  std::vector<const SpectralData*>::const_iterator itSpec =
                getSpectraForStat().begin();
  std::vector<const SpectralData*>::const_iterator itSpecEnd =
                getSpectraForStat().end();
  while (itSpec != itSpecEnd)
  {
     const SpectralData* spectrum = *itSpec;
     const size_t index = spectrum->spectrumNumber();
     const std::valarray<size_t>& IN = spectrum->indirectNotice();
     result[index].resize(IN.size());
     result[index] = spectrum->spectrum()[IN];
     if (spectrum->background())
     {
        result[index] -= spectrum->background()->spectrum()[IN];
     }
     ++itSpec;  
  }


  ModelMapConstIter ml (models->modelSet().begin());      
  ModelMapConstIter  mlEnd (models->modelSet().end()); 
  while ( ml != mlEnd )
  {
     // D - F for each model. In the case where there are multiple
     // sources difference will be iteratively defined.
     Model* m (ml->second);
     if (m->isActive())
     {
        m->difference(result);                  
     }
     ++ml;
  }    
  return result;
}
// end getDifferences

template <typename T>
Real Cstat<T>::sumDerivs (const ArrayContainer& dFolded, int parameterIndex) const
{

    //dFolded = container of array containers of derivatives for each parameter.
    // See comments in ChiSquare::sumDerivs for a detailed explanation.
    ArrayContainer::const_iterator itDmEnd = dFolded.end();
    Real dSdpj(0);

    ArrayContainer::const_iterator itDeriv = m_firstDerivCoefficient.begin();
    ArrayContainer::const_iterator itDerivEnd = m_firstDerivCoefficient.end();
    while(itDeriv != itDerivEnd) 
    {
       size_t spectrumIndex = itDeriv->first;
       // This could be a response par, in which case dFolded will have
       // just one spectrum.
       ArrayContainer::const_iterator itDm = dFolded.find(spectrumIndex);
       if (itDm != itDmEnd)
       {
          const RealArray& dv = itDm->second;
          RealArray dSdpA (itDeriv->second);
          dSdpA *= dv;
          dSdpj += -2.0*dSdpA.sum();
          if (false)
          {
	      size_t N = m_firstDerivCoefficient.find(spectrumIndex)->second.size();
              tcout << N << std::endl;
	      std::vector<Real> PS(N);
	      std::partial_sum(&dSdpA[0],&dSdpA[0]+N,PS.begin());
	      tcout << " Spectrum " << itDm->first << " Parameter# " << parameterIndex  
                              << " D:  " << dSdpj << '\n';
	      for (size_t j = 0; j < N; ++j)
	      {
	          tcout << j << " " << std::setw(12) 
		        << std::setw(12) << m_firstDerivCoefficient.find(spectrumIndex)->second[j] << " "
		        << std::setw(12) << dv[j]  << " "
		        << std::setw(12) << dSdpA[j] << " "
		        << std::setw(12) << PS[j]  << '\n'; 
	      }
	      tcout << " d " << spectrumIndex << "  " << dSdpj << '\n';  
          }
       }               
       ++itDeriv;
    }
    return dSdpj;

}
// end sumDerivs

template <typename T>
Real Cstat<T>::sumSecondDerivs (const std::map<size_t,ArrayContainer>& dFolded, int pi, int pj)
{

  // If pi or pj is a response parameter, its corresponding
  // dFolded ArrayContainer will have just one spectrum.  Otherwise all 
  // dFolded ArrayContainers should have entries for all fit spectra.
  // Only the subset of spectra that are using cstat should be accessed in here.

   Real alpha_ij=.0;
   ArrayContainer::const_iterator itCoeff = m_secondDerivCoefficient.begin();
   ArrayContainer::const_iterator itCoeffEnd = m_secondDerivCoefficient.end();
   // Calculate 2*(dF/dpi)(dF/dpj) summed over fit spectra using cstat.
   const ArrayContainer& piBins = dFolded.find(pi)->second;
   const ArrayContainer& pjBins = dFolded.find(pj)->second;
   ArrayContainer::const_iterator piEnd = piBins.end();
   ArrayContainer::const_iterator pjEnd = pjBins.end();
   while (itCoeff != itCoeffEnd)
   {
      size_t specNum = itCoeff->first;
      ArrayContainer::const_iterator piSpec = piBins.find(specNum);
      ArrayContainer::const_iterator pjSpec = pjBins.find(specNum);
      if (piSpec != piEnd && pjSpec != pjEnd)
      {
         RealArray secondDeriv(itCoeff->second);
         secondDeriv *= piSpec->second;
         secondDeriv *= pjSpec->second;
         alpha_ij += secondDeriv.sum();
      }
      ++itCoeff;
   } 
   alpha_ij *= 2.0;  
   return alpha_ij;
} 
// end sumSecondDerivs

template <typename T>
std::pair<Real,Real> Cstat<T>::adjustForFrozen (const SpectralData* spec, const std::vector<Model*>& models, const std::map<Model*,ArrayContainer >& savedValsForFrozen)
{

    const std::valarray<size_t>& IN = spec->indirectNotice();
    const size_t N = IN.size();
    const size_t specNum = spec->spectrumNumber();

    std::pair<Real,Real> fSums (0.,0.);

    RealArray data (spec->spectrum()[IN]);
    RealArray ts (spec->exposureTime()*spec->areaScale()[IN]);
    RealArray totModFroz(0., N); 
    RealArray totalModel(0., N);

    for (size_t i=0; i<models.size(); ++i)
    {
      Model* mod = models[i];
      std::map<Model*,ArrayContainer >::const_iterator itSaved =
                savedValsForFrozen.find(mod);
      if (itSaved != savedValsForFrozen.end())
      {
         totalModel += itSaved->second.find(specNum)->second[IN];
         totModFroz += mod->foldedModel(specNum)[IN];
      }
      else
      {
         totalModel += mod->foldedModel(specNum)[IN];
      }
    }

    fSums.first = ((data - totModFroz)*ts).sum();
    fSums.second = ((totalModel - totModFroz)*ts).sum();

   return fSums;
}

template <typename T>
bool Cstat<T>::checkForPoissonSource () const
{
   using namespace XSContainer;

   bool allPoisson = true;
   std::vector<const SpectralData*>::const_iterator itSpec =
                 getSpectraForStat().begin();
   std::vector<const SpectralData*>::const_iterator itSpecEnd =
                 getSpectraForStat().end();
   while (itSpec != itSpecEnd)
   {
      const SpectralData* sd = *itSpec;
      if (!sd->isPoisson())
      {
         allPoisson = false;
         break;
      }
      ++itSpec;
   }
   return allPoisson;
}

template <typename T>
bool Cstat<T>::checkForPoissonBackground () const
{
   using namespace XSContainer;

   bool allPoisson = true;
   std::vector<const SpectralData*>::const_iterator itSpec =
                 getSpectraForStat().begin();
   std::vector<const SpectralData*>::const_iterator itSpecEnd =
                 getSpectraForStat().end();
   while (itSpec != itSpecEnd)
   {
      const SpectralData* sd = *itSpec;
      if (sd->background())
      {
         if (!sd->background()->data()->isPoisson())
         {
            allPoisson = false;
            break;
         }
      }
      ++itSpec;
   }
   return allPoisson;
}


template <typename T>
inline ArrayContainer& Cstat<T>::firstDerivCoefficient ()
{
  return m_firstDerivCoefficient;
}

template <typename T>
inline void Cstat<T>::firstDerivCoefficient (const ArrayContainer& value)
{
  m_firstDerivCoefficient = value;
}

template <typename T>
inline ArrayContainer& Cstat<T>::secondDerivCoefficient ()
{
  return m_secondDerivCoefficient;
}

template <typename T>
inline void Cstat<T>::secondDerivCoefficient (const ArrayContainer& value)
{
  m_secondDerivCoefficient = value;
}

template <typename T>
inline const std::string& Cstat<T>::fullName () const
{
  return T::fullName(number(), modifier());
}

template <typename T>
inline const std::string& Cstat<T>::scriptName () const
{
  return T::scriptName(number(), modifier());
}

#endif
