#ifndef RANDOMIZERPOLICIES_H
#define RANDOMIZERPOLICIES_H 1

#include <xsTypes.h>

class Fit;
class ChainManager;

//These classes don't need to do anything other than be types.
class RandomizerCovarFile {};
class RandomizerCmdLine {};

// Source traits class, though additional function fillVarInfo() actually
// makes this a traits/policy combo.

// Note that due to the structural similarities in the specialized classes,
// a slightly better design would move this commonality into the generic
// RandomizerSourceInfo<T> class.  However a problem with Sun CC 
// (naturally) prevents doing this.  The sticking point is that it's
// unable to properly deal with individually specializing the
// static const name data member.  This was verified on CC 5.3
// and 5.4, and likely exists on other versions too. 

template <class Source>
class RandomizerSourceInfo;

template <>
class RandomizerSourceInfo<Fit>
{
   public:
      static const string name;

      const RealArray& eigenValues() const {return m_eigenValues;}
      const RealArray& eigenVectors() const {return m_eigenVectors;}
      const RealArray& covariance(const Fit* fit);
      void validate(const string& initStr) {}
      void fillVarInfo(const Fit* fit);

   private:
      RealArray m_eigenValues;
      RealArray m_eigenVectors;
      RealArray m_covariance;
};

template <>
class RandomizerSourceInfo<ChainManager>
{
   public:
      static const string name;

      const RealArray& eigenValues() const {return m_eigenValues;}
      const RealArray& eigenVectors() const {return m_eigenVectors;}
      const RealArray& covariance(const Fit* fit);
      void validate(const string& initStr) {}
      void fillVarInfo(const Fit* fit);

   private:
      RealArray m_eigenValues;
      RealArray m_eigenVectors;
      RealArray m_covariance;
};

template <>
class RandomizerSourceInfo<RandomizerCovarFile>
{
   public:
      static const string name;

      const RealArray& eigenValues() const {return m_eigenValues;}
      const RealArray& eigenVectors() const {return m_eigenVectors;}
      const RealArray& covariance(const Fit* fit) const {return m_covariance;}

      // This function will enforce the constraint that the matrix
      // stored in the file is a square matrix (To be more 
      // precise, it enforces that the lower half belongs to a
      // square.  Terms above the diagonal are ignored.), and that
      // the number of pars matches the current number of 
      // variable fit pars. 
      void validate(const string& initStr);
      void fillVarInfo(const Fit* fit);

   private:
      void readFromFile(const string& fileName);

      RealArray m_eigenValues;
      RealArray m_eigenVectors;
      RealArray m_covariance;
};

template <>
class RandomizerSourceInfo<RandomizerCmdLine>
{
   public:
      static const string name;

      const RealArray& eigenValues() const {return m_eigenValues;}
      const RealArray& eigenVectors() const {return m_eigenVectors;}
      const RealArray& covariance(const Fit* fit) const {return m_covariance;}

      void validate(const string& initStr);
      void fillVarInfo(const Fit* fit);

   private:
      int parseCmdLine(const string& lineArgs);

      RealArray m_eigenValues;
      RealArray m_eigenVectors;
      RealArray m_covariance;
      bool m_onlyDiag;
};


class RandomizerGaussDist
{
   public:
      static const string name;

      static void getValuesFromDistribution(const RealArray& scaling, RealArray& randVals);
};

class RandomizerCauchyDist
{
   public:
      static const string name;

      static void getValuesFromDistribution(const RealArray& scaling, RealArray& randVals);
};

#endif
