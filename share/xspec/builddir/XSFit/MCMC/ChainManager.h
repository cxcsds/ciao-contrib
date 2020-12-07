//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CHAINMANAGER_H
#define CHAINMANAGER_H 1
#include <xsTypes.h>
#include <memory>
#include <iosfwd>

// Chain
#include <XSFit/MCMC/Chain.h>

class MarginGrid;
class RandomizerBase;




class ChainManager 
{

  public:



    typedef std::map<string,Chain*> ChainContainer;



    struct Stats 
    {
          Stats();

        // Data Members for Class Attributes
          std::vector<Real> means;
          Real totalMean;
          Real totalVar;
          Real varInChains;
          Real rubinGelman;
          std::vector<Real> fracRepeats;
          std::vector<Real> geweke;

      public:
      protected:
      private:
      private: //## implementation
    };
      ~ChainManager();

      static ChainManager* Instance ();
      void addChain (Chain* chain);
      bool removeChain (const string& fileName);
      void clearChains ();
      bool widthConflict (const Chain* newChain) const;
      void recalc ();
      void calcStat (size_t iPar, const string& modName);
      void calcDevInfCrit (Real& effNumPars, Real& devInfCrit);
      void findBestFit(RealArray& parVals, Real& statVal);
      void removeChains (const IntegerVector& chainNums);
      bool checkLengths ();
      void getRandomPoint (RealArray& parVals) const;
      void getLastPoint (RealArray& parVals) const;
      void setChainProposal (const string& proposalName, const string& optInitArg = string(""));
      void reportChainProposal () const;
      bool checkCovarForSynch () const;
      std::pair<Real,Real> getParErrorRange (const Real confidence, const size_t parNum, const string& modName) const;
      void appendToChain (const string& chainName, const size_t addLength, const Real temperature, const string& format);
      void appendToChain (const string& chainName, const size_t addLength, const size_t walkers, const string& format);
      size_t length () const;
      size_t width () const;
      bool allLengthsSame () const;
      bool isSynchedWithFitParams () const;
      void isSynchedWithFitParams (bool value);
      //	Internal bookkeeping array, primarily used to determine
      //	which file contains the nth point numbered from the
      //	start of the first chain file.
      const std::vector<size_t>& accumulatedLengths () const;
      RandomizerBase* chainProposal ();
      const RealArray& chainSVDevalue () const;
      const RealArray& chainSVDevector () const;
      const RealArray& chainCovariance () const;
      const ChainManager::Stats& lastStatCalc () const;
      const Real& lastDevInfCritCalc () const;
      const Real& lastEffNumParsCalc () const;
      const ChainManager::ChainContainer& chains () const;
      const Chain* getChain (const string& fileName) const;
      MarginGrid* marginGrid () const;
      void marginGrid (MarginGrid* value);

  public:
    // Additional Public Declarations

      // Functors which can be passed to forEachChainPoint.

      class CollectParVals
      {
         public:
            CollectParVals(size_t iPar) : m_iPar(iPar) {} 
            void operator () (const std::vector<Real>& chainPoint)
            {
               // For speed, no checking performed here.
               m_parVals.push_back(chainPoint[m_iPar]);
            }
            std::vector<Real>& parVals() {return m_parVals;}
         private:
            const size_t m_iPar;
            std::vector<Real> m_parVals;
      };

      class CollectSumVar
      {
         public:
            CollectSumVar(size_t nPar);
            void operator () (const std::vector<Real>& chainPoint)
            {
               for (size_t j=0; j<m_nPar; ++j)
               {
                  Real chainVals_j = chainPoint[j];
                  m_chainSum[j] += chainVals_j;
                  const size_t jOffset = j*m_nPar;
                  for (size_t k=0; k<m_nPar; ++k)
                  {
                     m_chainVariance[jOffset+k] += chainPoint[k]*chainVals_j;
                  }
               }
            }
            double* getChainSum() {return m_chainSum;}
            double* getChainVariance() {return m_chainVariance;}
         private:
            const size_t m_nPar;
            std::unique_ptr<double[]> m_apChainSum;
            std::unique_ptr<double[]> m_apChainVariance;
            double* m_chainSum;
            double* m_chainVariance;
      };
  protected:
      ChainManager();

    // Additional Protected Declarations

  private:
      ChainManager(const ChainManager &right);
      ChainManager & operator=(const ChainManager &right);

      const Chain* getChainForRandomPoint (size_t globalLocation, size_t& locInChain) const;
      size_t findParPosition (const size_t parNum, const string& modName) const;

    // Additional Private Declarations
      template <class Op>
      void forEachChainPoint(Op& oper) const;
  private: //## implementation
    // Data Members for Class Attributes
      static ChainManager* s_instance;
      size_t m_length;
      size_t m_width;
      bool m_allLengthsSame;
      bool m_isSynchedWithFitParams;
      std::vector<size_t> m_accumulatedLengths;
      RandomizerBase* m_chainProposal;
      RealArray m_chainSVDevalue;
      RealArray m_chainSVDevector;
      RealArray m_chainCovariance;
      ChainManager::Stats m_lastStatCalc;
      Real m_lastDevInfCritCalc;
      Real m_lastEffNumParsCalc;

    // Data Members for Associations
      ChainManager::ChainContainer m_chains;
      MarginGrid* m_marginGrid;
      std::vector<Chain::ParamID> m_covarParams;

    // Additional Implementation Declarations

};
std::ostream& operator<< (std::ostream& os, const ChainManager::Stats& right);


template <class Op>
void ChainManager::forEachChainPoint(Op& oper) const
{
   ChainContainer::const_iterator itChain = m_chains.begin();
   ChainContainer::const_iterator itEnd = m_chains.end();
   while (itChain != itEnd)
   {
      Chain* chain = itChain->second;
      const int len = chain->length();
      chain->openForReadPoints();
      for (int i=0; i<len; ++i)
      {
         std::vector<Real> chainVals;
         chain->readPoint(chainVals);
         oper(chainVals);
      }
      chain->closeFile();
      ++itChain;
   }
}

// Class ChainManager::Stats 

// Class ChainManager 

inline size_t ChainManager::length () const
{
  return m_length;
}

inline size_t ChainManager::width () const
{
  return m_width;
}

inline bool ChainManager::allLengthsSame () const
{
  return m_allLengthsSame;
}

inline bool ChainManager::isSynchedWithFitParams () const
{
  return m_isSynchedWithFitParams;
}

inline void ChainManager::isSynchedWithFitParams (bool value)
{
  m_isSynchedWithFitParams = value;
}

inline const std::vector<size_t>& ChainManager::accumulatedLengths () const
{
  return m_accumulatedLengths;
}

inline RandomizerBase* ChainManager::chainProposal ()
{
  return m_chainProposal;
}

inline const RealArray& ChainManager::chainSVDevalue () const
{
  return m_chainSVDevalue;
}

inline const RealArray& ChainManager::chainSVDevector () const
{
  return m_chainSVDevector;
}

inline const RealArray& ChainManager::chainCovariance () const
{
  return m_chainCovariance;
}

inline const ChainManager::Stats& ChainManager::lastStatCalc () const
{
  return m_lastStatCalc;
}

inline const Real& ChainManager::lastDevInfCritCalc () const
{
  return m_lastDevInfCritCalc;
}

inline const Real& ChainManager::lastEffNumParsCalc () const
{
  return m_lastEffNumParsCalc;
}

inline const ChainManager::ChainContainer& ChainManager::chains () const
{
  return m_chains;
}

inline const Chain* ChainManager::getChain (const string& fileName) const
{
  ChainContainer::const_iterator it = m_chains.find(fileName);
  const Chain* chain = (it != m_chains.end()) ? it->second : 0;
  return chain;
}

inline MarginGrid* ChainManager::marginGrid () const
{
  return m_marginGrid;
}

inline void ChainManager::marginGrid (MarginGrid* value)
{
  m_marginGrid = value;
}


#endif
