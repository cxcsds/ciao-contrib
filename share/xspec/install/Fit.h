//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef FIT_H
#define FIT_H 1

// Error
#include <XSUtil/Error/Error.h>
// set
#include <set>
// list
#include <list>
// memory
#include <memory>
// Observer
#include <XSUtil/Utils/Observer.h>
// ModParam
#include <XSModel/Parameter/ModParam.h>
// Step
#include <XSFit/Fit/Step.h>
#include <XSUtil/Utils/ProcessManager.h>

class SpectralData;
class FitMethod;
class ChainManager;
class StatManager;
class RandomizerBase;
#include "xsTypes.h"
#include <memory>
#include <utility>
#include <XSModel/GlobalContainer/ModelTypes.h>
#include <queue>




class Fit : public Observer, public Subject  //## Inherits: <unnamed>%3C348E360100
{

  public:



    class NoSuchFitMethod : public YellowAlert  //## Inherits: <unnamed>%3B7BE22E02D7
    {
      public:
          NoSuchFitMethod (const string& name);

      protected:
      private:
      private: //## implementation
    };



    class NoSuchStatMethod : public YellowAlert  //## Inherits: <unnamed>%3B7BE233006B
    {
      public:
          NoSuchStatMethod (const string& name);

      protected:
      private:
      private: //## implementation
    };



    class FitOverDetermined : public YellowAlert  //## Inherits: <unnamed>%3C879AF30149
    {
      public:
          FitOverDetermined();

      protected:
      private:
      private: //## implementation
    };



    class ParameterLookupError : public RedAlert  //## Inherits: <unnamed>%3C879AE4001E
    {
      public:
          ParameterLookupError();

      protected:
      private:
      private: //## implementation
    };



    class NotVariable : public YellowAlert  //## Inherits: <unnamed>%3C87DF0802C2
    {
      public:
          NotVariable();

      protected:
      private:
      private: //## implementation
    };



    class CantInitialize : public YellowAlert  //## Inherits: <unnamed>%3D514EED0203
    {
      public:
          CantInitialize (const string& diag);

      protected:
      private:
      private: //## implementation
    };

  private:



    class HoldSpecVar 
    {

      public:
          HoldSpecVar();
          ~HoldSpecVar();

          void saveSpecVar (const SpectralData& data);
          void restoreSpecVar (SpectralData& data) const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          RealArray m_spectrum;
          RealArray m_rawVariance;
          RealArray m_variance;
          RealArray m_bckSpectrum;
          RealArray m_bckRawVariance;
          RealArray m_bckVariance;

        // Additional Implementation Declarations

    };
    
    class ErrorCmd : public ParallelFunc
    {
         virtual void execute(const bool isParallel, const TransferStruct& input,
                        TransferStruct& output);
        
         private:
            void transferMessageQueue(TransferStruct& output, std::queue<std::pair<string,int> >& messages);
    };
    
    class ParallelSim : public ParallelFunc
    {
         virtual void execute(const bool isParallel, const TransferStruct& input,
                        TransferStruct& output);        
    };
    
    

  public:



    typedef enum { ON, YES, NO } querySetting;



    typedef enum {NONE,PREFIT,AUTO} RenormSetting;



    class FitInterrupt : public YellowAlert  //## Inherits: <unnamed>%40B24263007A
    {
      public:
          FitInterrupt ();

      protected:
      private:
      private: //## implementation
    };
      ~Fit();

      void renormalize ();
      //	initialize fit object, grabbing existing data from
      //	the global containers.
      //
      //	The one argument, saveParameters, determines whether
      //	the Fit object saves the current parameter values. This
      //	is done to allow a reset on error or possibly interrupt.
      //
      //	initialize needs to be called by commands such as renorm
      //	which need to update the Fit object to whatever is
      //	current. In this case it is not relevant to save the
      //	parameters, so
      //	this can be optionally switched off.
      void reinitialize (bool saveParameters = true);
      FitMethod* fitMethod ();
      void fitMethod (FitMethod* method);
      static Fit* Instance (const string& fitMethodName);
      virtual void Update (Subject* changed = 0);
      void cleanup ();
      void resetParameters ();
      //	report current parameter values. When parameter header
      //	is true, print
      //	output header.
      void reportParameters (std::ostream& s, bool header = false);
      void report ();
      //	goodness command driver
      //
      //	Parameters: realizations:
      //
      //	Number of realizations to produce in the Monte-Carlo
      //	calculation. It will be initialized to a default value of
      //	MCrealizations if not set.
      //
      //	simulateParams:
      //
      //	If true, produce models computed with
      //	gaussian distributed random values of
      //	the parameters with mean taken as the
      //	best fit value. If false, use the best fit values.
      //
      //	doFit:
      //
      //	If true, perform a fit on each simulation
      //        before calculating the test statistic.
      //
      //	statMode
      //
      //	Mode for randomizing the model. Currently
      //	1 mean use Poisson variates:
      //	but 0 should mean "don't randomize"
      //	(for testing) and other values could eventually mean
      //	use different statistic. Only the value 1 (default) is
      //	implemented (8/2002).
      void goodness (int realizations, bool simulateParams = false, bool doFit = false, int statMode = 1);
      void calculateModel ();
      //	If chains are loaded, draws random parameters from
      //	chains.  Otherwise generates random parameters on a
      //	Gaussian distribution with mean equal to the (usually
      //	best fit) parameter and with sigma equal to the standard
      //	errors as generated by the fitting method.
      void randomizeModelParameters (bool callInitialize, Real fSigma = 1.0);
      void fluxes (bool lumin, bool error, int nTrials, Real level, Real eMin, Real eMax, Real redshift);
      bool getErrors (const IntegerVector& paramNums);
      Step* stepGrid ();
      void stepGrid (Step* value);
      //	function to wrap up task of making the statistic.
      //	will throw if either data or model is not present,
      //	or if the fit is overdetermined.
      //
      //	Also saves the parameter set if the input saveParameters
      //	flag is set.
      void initializeStatistic (bool isUpdate = false);
      void freezeByIndex (int index);
      Real statistic () const;
      void perform ();
      static int RESPAR_INDEX ();
      void calcEqErrors (const XSContainer::EqWidthRecord& currComp, const std::vector<Model*>& mods, size_t iMod, size_t nIter, Real confLevel);
      const ChainManager* chainManager () const;

      const StatManager* statManager () const;
      const RealArray& getSVDevalue () const;
      const RealArray& getSVDevector () const;
      const RealArray& getSVDcovariance () const;
      bool checkChainsForSynch () const;
      void reportErrorSimulationMethod () const;
      void randomizeForChain (bool onlyInit = false, bool useChainPropSetting = true);
      string getChainProposalNames () const;
      void registerRandomizingStrategy (const string& name, RandomizerBase* strategy);
      RandomizerBase* getRandomizingStrategy (const string& name);
      //	This is meant to be called once and only once.  It
      //	copies the names of Randomizers from the m_randomizing
      //	Strategies container into m_nativeRandomizerNames.
      void initNativeRandomizerNames ();
      void reportChainAcceptance (bool isAccepted) const;
      static bool errorCalc ();
      static void errorCalc (bool value);
      static Real& deltaStat ();
      static int& errorTry ();
      static Real& tolerance ();
      static Real& chiMax ();
      static bool& doNewMinRecalc ();
      const bool isStillValid () const;
      void isStillValid (bool value);
      //	setting for default number of Monte-Carlo realizations
      //	in the goodness command.
      static int& MCrealizations ();
      static Real lastFtest ();
      static void lastFtest (Real value);
      ChainManager* chainManager ();

      StatManager* statManager();
      static Real lastGoodness ();
      static RealArray goodnessSims ();
      //	This contains a subset of the names of the Randomizer
      //	classes stored in the m_randomizingStrategies
      //	container.  It is meant to distinguish the built-in
      //	classes from user-added ones.
      const std::set<string>& nativeRandomizerNames () const;
      //	If true, this will always force a numerical calculation
      //	of the parameter derivatives, regardless of the setting
      //	in the individual StatMethod classes.
      bool useNumericalDifferentiation () const;
      void useNumericalDifferentiation (bool value);
      ModParam* oldParameterValues (int index) const;
      const std::map<int,ModParam*>& variableParameters () const;
      ModParam* variableParameters (int index) const;
      void variableParameters (int index, ModParam* value);
      RealArray variableParameterValues(const char key = 'v');
      void setVariableParameterValues(const RealArray& values, const char key = 'v');
      bool goodVariableParameterValues(const RealArray& values, const char key = 'v');
      const std::map<size_t, SpectralData*>& spectraToFit () const;
      SpectralData* spectraToFit (size_t spectrumNumber) const;
      const querySetting queryMode () const;
      void queryMode (querySetting value);
      const std::set< string >& activeModels () const;
      const RenormSetting renormType () const;
      void renormType (RenormSetting value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      Fit(const Fit &right);
      Fit (const string& fitMethodName);
      Fit & operator=(const Fit &right);

      void deleteSavedParams ();
      void simulate (std::vector<Real>& trialValues, 	// value of the statistic from each realization.
		     bool simulateParams, bool doFit, int statMode);
      //	randomizeIndicator: 0 = no randomizing, 1 = randomize, 2
      //	= initialize randomizer then randomize.
      void simulateModel (ArrayContainer& simSpec, int randomizeIndicator);
      void initializeFitModels ();
      void initializeFitSpectra (std::vector<size_t>& missingModels);
      void initializeFitParameters ();
      static std::vector<Model*> getModsForFlux (const SpectralData* sd);
      void clearRandomizingStrategies ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static Fit* s_instance;
      static bool s_errorCalc;
      static Real s_deltaStat;
      static int s_errorTry;
      static Real s_tolerance;
      static Real s_chiMax;
      static bool s_doNewMinRecalc;
      bool m_isStillValid;
      static int s_MCrealizations;
      static Real s_lastFtest;
      static const int s_RESPAR_INDEX;
      ChainManager* m_chainManager;

      StatManager* m_statManager;
      static Real s_lastGoodness;
      static RealArray s_goodnessSims;
      std::set<string> m_nativeRandomizerNames;
      bool m_useNumericalDifferentiation;

    // Data Members for Associations
      std::unique_ptr<FitMethod> m_fitMethod;
      std::map<int, ModParam*> m_oldParameterValues;
      std::map<int,ModParam*> m_variableParameters;
      std::map<size_t, SpectralData*> m_spectraToFit;
      querySetting m_queryMode;
      std::unique_ptr<Step> m_stepGrid;
      std::set< string > m_activeModels;
      std::map<string,RandomizerBase*> m_randomizingStrategies;
      RenormSetting m_renormType;

    // Additional Implementation Declarations

};

// Class Fit::NoSuchFitMethod 

// Class Fit::NoSuchStatMethod 

// Class Fit::FitOverDetermined 

// Class Fit::ParameterLookupError 

// Class Fit::NotVariable 

// Class Fit::CantInitialize 

// Class Fit::HoldSpecVar 

// Class Fit::FitInterrupt 

// Class Fit 

inline int Fit::RESPAR_INDEX ()
{
  return s_RESPAR_INDEX;
}

inline const ChainManager* Fit::chainManager () const
{
   return m_chainManager;
}

inline const StatManager* Fit::statManager() const
{
   return m_statManager;
}

inline bool Fit::errorCalc ()
{
  return s_errorCalc;
}

inline void Fit::errorCalc (bool value)
{
  s_errorCalc = value;
}

inline Real& Fit::deltaStat ()
{
  return s_deltaStat;
}

inline int& Fit::errorTry ()
{
  return s_errorTry;
}

inline Real& Fit::tolerance ()
{
  return s_tolerance;
}

inline Real& Fit::chiMax ()
{
  return s_chiMax;
}

inline bool& Fit::doNewMinRecalc ()
{
   return s_doNewMinRecalc;
}

inline const bool Fit::isStillValid () const
{
  return m_isStillValid;
}

inline void Fit::isStillValid (bool value)
{
  m_isStillValid = value;
}

inline int& Fit::MCrealizations ()
{
  return s_MCrealizations;
}

inline Real Fit::lastFtest ()
{
  return s_lastFtest;
}

inline void Fit::lastFtest (Real value)
{
  s_lastFtest = value;
}

inline ChainManager* Fit::chainManager ()
{
  return m_chainManager;
}

inline StatManager* Fit::statManager()
{
   return m_statManager;
}

inline Real Fit::lastGoodness ()
{
  return s_lastGoodness;
}

inline RealArray Fit::goodnessSims ()
{
  return s_goodnessSims;
}

inline const std::set<string>& Fit::nativeRandomizerNames () const
{
  return m_nativeRandomizerNames;
}

inline bool Fit::useNumericalDifferentiation () const
{
  return m_useNumericalDifferentiation;
}

inline void Fit::useNumericalDifferentiation (bool value)
{
  m_useNumericalDifferentiation = value;
}

inline const std::map<int,ModParam*>& Fit::variableParameters () const
{
  return m_variableParameters;
}

inline void Fit::variableParameters (int index, ModParam* value)
{
  m_variableParameters[index] = value;
}

inline const std::map<size_t, SpectralData*>& Fit::spectraToFit () const
{
  return m_spectraToFit;
}

inline SpectralData* Fit::spectraToFit (size_t spectrumNumber) const
{
  std::map<size_t,SpectralData*>::const_iterator f = m_spectraToFit.find(spectrumNumber);
  if ( f != m_spectraToFit.end()) return f->second;
  else return 0;
}

inline const Fit::querySetting Fit::queryMode () const
{
  return m_queryMode;
}

inline void Fit::queryMode (Fit::querySetting value)
{
  m_queryMode = value;
}

inline const std::set< string >& Fit::activeModels () const
{
  return m_activeModels;
}

inline const Fit::RenormSetting Fit::renormType () const
{
  return m_renormType;
}

inline void Fit::renormType (Fit::RenormSetting value)
{
  m_renormType = value;
}


#endif
