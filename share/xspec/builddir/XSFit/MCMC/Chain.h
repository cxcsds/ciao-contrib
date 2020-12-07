//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CHAIN_H
#define CHAIN_H 1

// Error
#include <XSUtil/Error/Error.h>

class ChainIO;
#include <xsTypes.h>




class Chain 
{

  public:



    class ChainError : public YellowAlert  //## Inherits: <unnamed>%41813D4103C5
    {
      public:
          ChainError (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    struct ParamID 
    {
          int operator==(const ParamID &right) const;

          int operator!=(const ParamID &right) const;

        // Data Members for Class Attributes
          string modName;
          string parName;
          size_t index;
          string units;

      public:
      protected:
      private:
      private: //## implementation
    };



    class ChainInterrupt : public YellowAlert  //## Inherits: <unnamed>%460140E001CB
    {
      public:
          ChainInterrupt ();

      protected:
      private:
      private: //## implementation
    };



    typedef std::vector<std::pair<size_t,Real> > TemperInfoContainer;
      Chain (ChainIO* pIO, const string& fileName, size_t burnLength, size_t length, bool rand);
      Chain (ChainIO* pIO, const string& fileName, size_t burnLength, size_t length, size_t walkers);
      Chain (ChainIO* pIO, const string& fileName);
      ~Chain();

      const string& getFileName () const;
      void run (const size_t appendLength, const Real temperature);
      void runMH (const size_t appendLength, const Real temperature);
      void runGW (const size_t appendLength);
      void initializeWalkers(const RealArray& originalParamValues,
			     std::vector<RealArray>& walkerParamValues,
			     std::vector<Real>& walkerStatisticValue);
      //	This is needed to initialize a sequence of readPoint
      //	calls.
      void openForReadPoints () const;
      void closeFile () const;
      //	This is intended to be called repeatedly to step through
      //	the chain sequentially, similar to an iterator.  Before
      //	calling this to start a sequence, FIRST CALL openForRead
      //	Points to initialize things and set the IO marker at the
      //	first point in the chain.
      void readPoint (std::vector<Real>& chainVals) const;
      void calcStats (size_t iPar, Real& mean, Real& variance, size_t& nRepeats,
		      std::vector<std::pair<Real,Real> >& subIntervals,
		      RealArray& subMeans);
      void calcMeanVarValues (RealArray& meanParVals, RealArray& varParVals, 
			      Real& meanStatVal, Real& varStatVal);
      void findClosestPoint (RealArray& inputParVals, RealArray& parVals, Real& statVal);
      //        Find the best fit parameter values in the change
      void findBestPoint(size_t& lineNum, RealArray& parVals, Real& statVal);
      void findParsInChain (std::vector<Chain::ParamID>& parIDs, std::vector<size_t>& found) const;
      std::vector<Chain::ParamID> findParsInChain (size_t par1, const string& modName1, size_t par2, const string& modName2) const;
      static int FWIDTH ();
      //	This differs from the similar readPoint function in a
      //	couple of ways:  It will return the par values at a
      //	specified line number as measured from the start of the
      //	first par value line, whereas readPoint simply grabs
      //	from the current position.  Also it fills a valarray
      //	(which it ASSUMES is properly sized already) rather than
      //	a vector, and doesn't include the fit statistic value.
      //	This is to interface more easily with the random point
      //	retrieval required in certain error simulations.
      void readPointFromLine (size_t lineNum, RealArray& parVals) const;
      static int TEMPERPREC ();
      const string& format () const;
      size_t burnLength () const;
      size_t length () const;
      void length (size_t value);
      bool rand () const;
      size_t width () const;
      void width (size_t value);
      const std::vector<Chain::ParamID>& paramIDs () const;
      void paramIDs (const std::vector<Chain::ParamID>& value);
      const string& statistic () const;
      void statistic (const string& value);
      const Chain::TemperInfoContainer& tempering () const;
      void tempering (const Chain::TemperInfoContainer& value);
      size_t walkers () const;
      void walkers (size_t value);
      const string& chainType () const;
      void chainType (const string& value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      Chain(const Chain &right);
      Chain & operator=(const Chain &right);

      void cleanupRun (const RealArray& origPars);
      static bool checkForRepeat (const std::vector<Real>& prevPoint, const std::vector<Real>& point);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const string m_fileName;
      size_t m_burnLength;
      size_t m_length;
      bool m_rand;
      size_t m_width;
      std::vector<Chain::ParamID> m_paramIDs;
      string m_statistic;
      Chain::TemperInfoContainer m_tempering;
      size_t m_walkers;
      string m_chainType;

    // Data Members for Associations
      //	Opaque pointer to class performing Chain IO functions in
      //	a mixture of Strategy and Template patterns.
      ChainIO* m_IO;

    // Additional Implementation Declarations

};

// Class Chain::ChainError 

// Class Chain::ParamID 

inline int Chain::ParamID::operator==(const Chain::ParamID &right) const
{
   return modName==right.modName && parName==right.parName 
                && index==right.index && units==right.units;
}

inline int Chain::ParamID::operator!=(const Chain::ParamID &right) const
{
   return !(*this == right);
}


// Class Chain::ChainInterrupt 

// Class Chain 

inline const string& Chain::getFileName () const
{
  return m_fileName;
}

inline size_t Chain::burnLength () const
{
  return m_burnLength;
}

inline size_t Chain::length () const
{
  return m_length;
}

inline void Chain::length (size_t value)
{
  m_length = value;
}

inline bool Chain::rand () const
{
  return m_rand;
}

inline size_t Chain::width () const
{
  return m_width;
}

inline void Chain::width (size_t value)
{
  m_width = value;
}

inline const std::vector<Chain::ParamID>& Chain::paramIDs () const
{
  return m_paramIDs;
}

inline void Chain::paramIDs (const std::vector<Chain::ParamID>& value)
{
  m_paramIDs = value;
}

inline const string& Chain::statistic () const
{
  return m_statistic;
}

inline void Chain::statistic (const string& value)
{
  m_statistic = value;
}

inline const Chain::TemperInfoContainer& Chain::tempering () const
{
  return m_tempering;
}

inline void Chain::tempering (const Chain::TemperInfoContainer& value)
{
  m_tempering = value;
}

inline size_t Chain::walkers () const
{
  return m_walkers;
}

inline void Chain::walkers (size_t value)
{
  m_walkers = value;
}

inline const string& Chain::chainType () const
{
  return m_chainType;
}

inline void Chain::chainType (const string& value)
{
  m_chainType = value;
}


// This is a handy helper function to convert from a parameter label
// ([<model name>]:<parameter index> for model parameters and
// [source number]:r<parameter index> for response parameters
// to the internal modelName and index used by chains
bool convertParameterLabel(const string& label, string& modelName, size_t& index);



#endif
