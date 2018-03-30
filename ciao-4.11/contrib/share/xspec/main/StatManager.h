//C++

#ifndef STATMANAGER_H
#define STATMANAGER_H 1

#include <xsTypes.h>
#include <XSFit/Fit/Bayes.h>
#include <XSUtil/Utils/Observer.h>
#include <XSUtil/Utils/ProcessManager.h>
#include <map>
#include <utility>

class StatMethod;
class SpectralData;
namespace XSContainer {
    class Weight;
}

class StatManager : public Observer
{
   public:

      ~StatManager();
      static StatManager* Instance();

      virtual void Update (Subject* changed = 0);

      // Returns the dof and number of bins for the total statistic.
      std::pair<int,size_t> totalDegreesOfFreedom() const;

      void differentiateStats(const IntegerArray& which);
      // This will return 0 if name is not a registered stat method.
      StatMethod* getStatMethod(const string& name) const;
      StatMethod* getStatMethodForSpectrum(size_t specNum) const;
      StatMethod* getTestStatMethod(const string& name) const;
      StatMethod* getTestStatMethodForSpectrum(size_t specNum) const;
      void initializeStats();
      void peakResidual(std::pair<Real,Real>&  max, std::pair<Real,Real>&  min, size_t spectrum, const std::pair<Real,Real>& range) const;
      // doCalcFold flag was originally added for when calling from StatManager's Update function,
      //  where it should avoid doing redundant 'calculate' and 'fold' operations.
      void performStats(bool doCalcFold=true);
      void registerStatMethod(const string& name, StatMethod* method);
      void registerTestStatMethod(const string& name, StatMethod* method);
      void renormalizeStats() const;
      void reportStats() const;
      string statNames() const;
      string testStatNames() const;
      // After Fit has determined which spectra are suitable for a fit 
      // (ie. have active models), this function will deal out those 
      // spectra to the various StatMethod objects.  SpectralData
      // statNames should already have been validated by this point.
      // This also calls buildSpecNumToStatMethod to build the reverse
      // spec-to-stat lookup array.
      void setSpectraForStatMethods(const std::map<size_t,SpectralData*>& spectraToFit);
      void setSpectraForTestStatMethods(const std::map<size_t,SpectralData*>& spectraToFit);

      // If the default AND all in-use stats are compatible with weightName,
      // this resets DataUtility's weightScheme pointer.  If not, 
      // DataUtility's weightScheme will be reset to standard weighting.
      // In both cases it will set m_weightCmdSetting to weightName.
      // However if weightName does not correspond to a registered weight, 
      // this will throw a YellowAlert and NOT set m_weightCmdSetting. 
      void setStatWeight(const string& weightName);

      // The setting of the stat value from an external caller (ie. Fit) is
      // useful in the context of specifying a value to indicate an error
      // condition. 
      void totalStatistic(Real val);
      Real totalStatistic() const;
      void totalTestStatistic(Real val);
      Real totalTestStatistic() const;
      static void setBayes(bool flag);
      static bool getBayes();

      // Derivative arrays.  If FitMethod is not calculating a second
      // derivative, alpha will be size 0. betaNorm returns the L2 norm
      // of the first derivatives.
      const RealArray& alpha() const;
      const RealArray& beta() const;
      Real betaNorm();

      // If all loaded suitable-for-fit spectra are using the same StatMethod 
      // (which is the most likely case), returns pointer to that StatMethod.
      // If not, or no suitable-for-fit spectra, returns 0.
      const StatMethod* usingSingleStat() const;
      const StatMethod* usingSingleTestStat() const;

      // The default StatMethod is what is applied whenever new spectra are
      // loaded, or when the "statistic" command is called without specifying
      // a spectrum range.  It is originally set by the user's Xspec.init file.
      // If successful, the set function returns a pointer to the new default.
      // If not, it returns 0 and the previous default stat is retained.
      // Once the default has been successfully set during start-up, the
      // get function is always guaranteed to return a valid pointer.
      StatMethod* defaultStat() const;
      StatMethod* setDefaultStat(const string& name);
      StatMethod* defaultTestStat() const;
      StatMethod* setDefaultTestStat(const string& name);

      const string& weightCmdSetting() const;
      
      ProcessManager& jacobianCalc();

      static void registerWeightingMethod (const std::string& name, XSContainer::Weight* weightMethod);
      // Case-insensitive, returns 0 if weighting method not found.
      static XSContainer::Weight* getWeightingMethod (const std::string& name);
      static string weightNames ();
      static void clearWeightingMethods ();
      static void recalculateWeightVariances();

   protected:

      StatManager();

   private:

      StatManager(const StatManager &right);
      StatManager & operator=(const StatManager &right);
      
      class ParDiff : public ParallelFunc
      {
         virtual void execute(const bool isParallel, const TransferStruct& input,
                        TransferStruct& output);
      };

      void buildSpecNumToStatMethod();
      void buildSpecNumToTestStatMethod();
      void checkForSingleStat();
      void checkForSingleTestStat();

      void numericalDifferentiate (const IntegerArray& parNums);
      void analyticDifferentiate (const IntegerArray& parNums);

      // If the default stat AND all in-use stats are compatibile with 
      // m_weightCmdSetting, returns an empty string.  Otherwise returns the 
      // name of the first in-use StatMethod it finds that has a problem.
      string checkStatsWeighting() const;

      static StatManager* s_instance;

      // The string key is the same name as accepted by the "statistic" command.
      std::map<string, StatMethod*> m_statMethods;
      std::map<string, StatMethod*> m_testStatMethods;

      // Bookkeeping array to allow quick access to a spectrum's current
      // StatMethod object.  We do this here since SpectralData objects
      // are unable to hold their own StatMethod pointers (being as they
      // are down in libXSModel).  This array will be of size nLoadedSpecs.

      // Note that whereas this array associates every spectrum with a
      // StatMethod, the StatMethod objects' spectraForStat container only
      // holds those Spectra which are suitable for a fit.
      std::vector<StatMethod*> m_specNumToStatMethod;
      std::vector<StatMethod*> m_specNumToTestStatMethod;
      Real m_totalStatistic;
      Real m_totalTestStatistic;
      Real m_bayesianPrior;
      static Bayes s_bayes;

      StatMethod* m_usingSingleStat;
      StatMethod* m_defaultStat;

      StatMethod* m_usingSingleTestStat;
      StatMethod* m_defaultTestStat;

      // Derivative arrays
      RealArray m_alpha;
      RealArray m_beta;

      string m_weightCmdSetting;
      
      ProcessManager m_jacobianCalc;
      
      static std::map<string, XSContainer::Weight*> s_weightingMethods;
};

inline StatMethod* StatManager::getStatMethodForSpectrum(size_t specNum) const
{
   return m_specNumToStatMethod[specNum-1];
}
inline StatMethod* StatManager::getTestStatMethodForSpectrum(size_t specNum) const
{
   return m_specNumToTestStatMethod[specNum-1];
}

inline void StatManager::totalStatistic(Real val)
{
   m_totalStatistic = val;
}
inline void StatManager::totalTestStatistic(Real val)
{
   m_totalTestStatistic = val;
}

inline Real StatManager::totalStatistic() const
{
   return m_totalStatistic;
}
inline Real StatManager::totalTestStatistic() const
{
   return m_totalTestStatistic;
}

inline void StatManager::setBayes(bool flag)
{
   s_bayes.isOn(flag);
}

inline bool StatManager::getBayes()
{
   return s_bayes.isOn();
}

inline const StatMethod* StatManager::usingSingleStat() const
{
   return m_usingSingleStat;
}
inline const StatMethod* StatManager::usingSingleTestStat() const
{
   return m_usingSingleTestStat;
}

inline StatMethod* StatManager::defaultStat() const
{
   return m_defaultStat; 
}
inline StatMethod* StatManager::defaultTestStat() const
{
   return m_defaultTestStat; 
}

inline const string& StatManager::weightCmdSetting() const
{
   return m_weightCmdSetting;
}

inline const RealArray& StatManager::alpha() const
{
   return m_alpha;
}

inline const RealArray& StatManager::beta() const
{
   return m_beta;
}

inline Real StatManager::betaNorm()
{
   return sqrt((m_beta*m_beta).sum());
}

inline ProcessManager& StatManager::jacobianCalc()
{
   return m_jacobianCalc;
}
#endif
