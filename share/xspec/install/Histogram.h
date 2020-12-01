//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef HISTOGRAM_H
#define HISTOGRAM_H 1
#include <xsTypes.h>
#include <XSUtil/Error/Error.h>
#include <cmath>

namespace Numerics {
    class LinearBinning
    {
       public:
          template <typename T>
          static int calcIndex(const T& min, const T& max, const T& val, const int nSteps,
                                const bool parIsLog = false)
          {
             // parIsLog flag is ignored for this case
             Real delta = (max - min)/static_cast<Real>(nSteps);
             return static_cast<int>(floor((val - min)/delta));
          }
          template <typename T>
          static void calcBoundaries(const T& min, const T& max, const int idx, 
                const int nSteps, std::pair<Real,Real>& boundaries, const bool parIsLog = false)
          {
             Real delta = (max - min)/static_cast<Real>(nSteps);
             boundaries.first = min + idx*delta;
             boundaries.second = min + (idx+1.0)*delta;
          }
          template <typename T>
          static int verify(const std::vector<T>& mins, const std::vector<T>& maxes, 
                        const BoolArray& isLog = BoolArray())
          {
             for (size_t i=0; i<mins.size(); ++i)
             {
                if (maxes[i] == mins[i]) return -2;
             }
             return 0;
          }
    };

    class LogBinning
    {
       public:
          template <typename T>
          static int calcIndex(const T& min, const T& max, const T& val, const int nSteps,
                                const bool parIsLog = true)
          {
             // parIsLogflag is ignored for this case
             using namespace std;
             const int BAD = -9999;
             if (val <= .0)  return BAD;
             Real delta = (log(max) - log(min))/static_cast<Real>(nSteps);
             return static_cast<int>(floor((log(val) - log(min))/delta));
          }
          template <typename T>
          static void calcBoundaries(const T& min, const T& max, const int idx, 
                const int nSteps, std::pair<Real,Real>& boundaries, const bool parIsLog = true)
          {
             using namespace std;
             Real delta = (log(max) - log(min))/static_cast<Real>(nSteps);
             boundaries.first = min*exp(idx*delta);
             boundaries.second = min*exp((idx+1.0)*delta);
          }
          template <typename T>
          static int verify(const std::vector<T>& mins, const std::vector<T>& maxes,
                        const BoolArray& isLog = BoolArray())
          {
             for (size_t i=0; i<mins.size(); ++i)
             {
                if (mins[i] <= .0 || maxes[i] <=.0 || maxes[i] == mins[i])  
                        return -1;
             }
             return 0;
          }
    };

    class MixedBinning
    {
       public:
          template <typename T>
          static int calcIndex(const T& min, const T& max, const T& val, const int nSteps,
                                const bool parIsLog = false)
          {
             if (parIsLog)  return LogBinning::calcIndex(min, max, val, nSteps);
             else  return LinearBinning::calcIndex(min, max, val, nSteps);
          }
          template <typename T>
          static void calcBoundaries(const T& min, const T& max, const int idx, 
                const int nSteps, std::pair<Real,Real>& boundaries, const bool parIsLog = false)
          {
             if (parIsLog) LogBinning::calcBoundaries(min, max, idx, 
                nSteps, boundaries);
             else LinearBinning::calcBoundaries(min, max, idx, 
                nSteps, boundaries);
          }
          template <typename T>
          static int verify(const std::vector<T>& mins, const std::vector<T>& maxes,
                        const BoolArray& isLog = BoolArray())
          {
             if (isLog.size())
             {
                for (size_t i=0; i<mins.size(); ++i)
                {
                   if (isLog[i])
                   {
                      if (mins[i] <= .0 || maxes[i] <=.0 || maxes[i] == mins[i])  
                           return -1;                
                   }
                   else
                   {
                      if (maxes[i] == mins[i]) return -2;
                   }
                }
             }
             else
             {
                for (size_t i=0; i<mins.size(); ++i)
                   if (maxes[i] == mins[i]) return -2;
             }
             return 0;
          }
    };



    template <typename T, typename Policy = LinearBinning>
    class Histogram 
    {

      public:
          Histogram (const std::vector<T>& minRanges, const std::vector<T>& maxRanges, const IntegerVector& nSteps, const BoolArray& isLog = BoolArray());
          ~Histogram();

          size_t nDim () const;
          bool addToHist (const std::vector<T>& entry);
          void calcBoundaries (int index, std::vector<Real>& boundaries) const;
          const std::vector<T>& minRanges () const;
          const std::vector<T>& maxRanges () const;
          const IntegerVector& nSteps () const;
          long totalEntries () const;
          const std::valarray<long>& counts () const;
          const BoolArray& isLog () const;
          long totalAttempts () const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          Histogram(const Histogram< T,Policy > &right);
          Histogram< T,Policy > & operator=(const Histogram< T,Policy > &right);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          const size_t m_nDim;
          std::vector<T> m_minRanges;
          std::vector<T> m_maxRanges;
          IntegerVector m_nSteps;
          long m_totalEntries;
          std::valarray<long> m_counts;
          BoolArray m_isLog;
          long m_totalAttempts;

        // Additional Implementation Declarations

    };

    // Parameterized Class Numerics::Histogram 

    template <typename T, typename Policy>
    inline size_t Histogram<T,Policy>::nDim () const
    {
      return m_nDim;
    }

    template <typename T, typename Policy>
    inline const std::vector<T>& Histogram<T,Policy>::minRanges () const
    {
      return m_minRanges;
    }

    template <typename T, typename Policy>
    inline const std::vector<T>& Histogram<T,Policy>::maxRanges () const
    {
      return m_maxRanges;
    }

    template <typename T, typename Policy>
    inline const IntegerVector& Histogram<T,Policy>::nSteps () const
    {
      return m_nSteps;
    }

    template <typename T, typename Policy>
    inline long Histogram<T,Policy>::totalEntries () const
    {
      return m_totalEntries;
    }

    template <typename T, typename Policy>
    inline const std::valarray<long>& Histogram<T,Policy>::counts () const
    {
      return m_counts;
    }

    template <typename T, typename Policy>
    inline const BoolArray& Histogram<T,Policy>::isLog () const
    {
      return m_isLog;
    }

    template <typename T, typename Policy>
    inline long Histogram<T,Policy>::totalAttempts () const
    {
      return m_totalAttempts;
    }

    // Parameterized Class Numerics::Histogram 

    template <typename T, typename Policy>
    Histogram<T,Policy>::Histogram (const std::vector<T>& minRanges, const std::vector<T>& maxRanges, const IntegerVector& nSteps, const BoolArray& isLog)
      : m_nDim(minRanges.size()),
        m_minRanges(minRanges),
        m_maxRanges(maxRanges),
        m_nSteps(nSteps),
        m_totalEntries(0),
        m_counts(),
        m_isLog(),
        m_totalAttempts(0)
    {
       const string msg("Histogram construction error.");
       if (!m_nDim || m_maxRanges.size() != m_nDim || m_nSteps.size() != m_nDim)
       {
           throw RedAlert(msg);
       }

       if (isLog.size())
       {
          if (isLog.size() != m_nDim)   throw RedAlert(msg);
          m_isLog = isLog;
       }
       else
       {
          m_isLog.resize(m_nDim, false);
       }
       size_t nGridPoints = 1;
       for (size_t i=0; i<m_nDim; ++i)
       {
          nGridPoints *= m_nSteps[i];
       }
       if (!nGridPoints)
       {
          throw RedAlert(msg);
       }
       m_counts.resize(nGridPoints, 0);
       int status = Policy::verify(m_minRanges, m_maxRanges, m_isLog);
       if (status == -1)
       {
          const string binErr("Improper limits for log binning.\n");
          throw YellowAlert(binErr);
       }
       else if (status == -2)
       {
          const string binErr("Improper limits for binning.\n");
          throw YellowAlert(binErr);
       }
    }


    template <typename T, typename Policy>
    Histogram<T,Policy>::~Histogram()
    {
    }


    template <typename T, typename Policy>
    bool Histogram<T,Policy>::addToHist (const std::vector<T>& entry)
    {
       size_t idxTot = 0;
       size_t parIncr = 1;
       ++m_totalAttempts;
       // LOWEST parameter number varies fastest in counts array.
       // Example: if 2 pars, par1 = 2 steps, par2 = 2 steps,
       // counts = [(par1=0,par2=0),(par1=1,par2=0),(par1=0,par2=1),(par1=1,par2=1)] 
       for (size_t i=0; i<m_nDim; ++i)
       {
          bool parIsLog = m_isLog[i];
          int nStep_i = m_nSteps[i];
          int idxPar = Policy::calcIndex(m_minRanges[i], m_maxRanges[i], entry[i], nStep_i,
                                parIsLog);
          if (idxPar < 0 || idxPar >= nStep_i)
          {
             // If ANY indices are out of bounds, point will not get binned.
             return false;
          }
          else
          {
             idxTot += idxPar*parIncr;
             parIncr *= nStep_i;
          }
       }
       m_counts[idxTot] += 1;
       ++m_totalEntries;
       return true;
    }

    template <typename T, typename Policy>
    void Histogram<T,Policy>::calcBoundaries (int index, std::vector<Real>& boundaries) const
    {
       boundaries.resize(m_nDim*2, .0);
       int accum = 1;
       for (size_t i=0; i<m_nDim; ++i)
       {
          int nSteps_i = m_nSteps[i];
          // truncation is deliberate
          int parIdx = (index % (m_nSteps[i]*accum))/accum;
          if (parIdx < 0 || parIdx >= nSteps_i)
          {
             throw YellowAlert("Out of bounds error in Histogram::calcBoundaries\n");
          }
          std::pair<Real, Real> parBnd;
          Policy::calcBoundaries(m_minRanges[i], m_maxRanges[i], parIdx, 
                nSteps_i, parBnd, m_isLog[i]);
          boundaries[2*i] = parBnd.first;
          boundaries[2*i+1] = parBnd.second;
          accum *= m_nSteps[i];
       }
    }

    // Additional Declarations

} // namespace Numerics


#endif
