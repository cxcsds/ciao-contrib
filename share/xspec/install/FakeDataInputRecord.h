//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef FAKEDATAINPUTRECORD_H
#define FAKEDATAINPUTRECORD_H 1

// utility
#include <utility>
// xsTypes
#include <xsTypes.h>
// DataInputRecord
#include <XSModel/Data/DataInputRecord.h>




class FakeDataInputRecord : public DataInputRecord  //## Inherits: <unnamed>%3E89C8750391
{

  public:
    //	Location of Back/Corr spectra given by <fileName,rowNum>
    //	where rowNum = 0 for type I file.



    typedef std::pair<string,size_t> BackLocator;
    //	Stores the response file name and its 0-based sourceNum



    typedef std::pair<string,size_t> ResponseID;



    typedef std::vector<ResponseID> Detectors;
    //	The BackLocator member stores Arf <fileName,rowNum> and
    //	the size_t member stores 0-based sourceNum.



    typedef std::pair<BackLocator,size_t> ArfID;



    typedef std::vector<ArfID> Arfs;
      FakeDataInputRecord (size_t nSpec);
      ~FakeDataInputRecord();

      void printDiagnostics () const;
      const string& backgndFile () const;
      void backgndFile (const string& value);
      bool useCountingStat () const;
      void useCountingStat (bool value);
      bool isType2 () const;
      void isType2 (bool value);
      Real exposureTime () const;
      void exposureTime (Real value);

      // This setting is entirely optional.  It should hold
      // a negative value if it is to be unused.
      Real backExposureTime() const;
      void backExposureTime (Real value);
      Real correctionNorm () const;
      void correctionNorm (Real value);
      bool enteredNone () const;
      void enteredNone (bool value);
      //	This is the total number of possible sources for the fake
      //	spectra to be created.  It is optional that they later
      //	be filled in with actual responses.
      size_t numSourcesForSpectra () const;
      void numSourcesForSpectra (size_t value);
      
      // This is only used for fake spectra NOT based on original spectra,
      // in which case the fakeit handler must pass the current default
      // stat down to the DataSet.  When there is an original spectrum, 
      // the statName and testStatName will simply be copied to the new one.
      const string& statName() const;
      void statName(const string& defaultStat);
      const string& testStatName() const;
      void testStatName(const string& defaultStat);
      
      const IntegerVector& origRowNums () const;
      void setOrigRowNums (const IntegerVector& value);
      int origRowNums (size_t index) const;
      void origRowNums (size_t index, int value);
      const std::vector<BackLocator>& inputCorrFiles () const;
      void setInputCorrFiles (const std::vector<BackLocator>& value);
      const BackLocator& inputCorrFiles (size_t index) const;
      void inputCorrFiles (size_t index, const BackLocator& value);
      const std::vector<BackLocator>& inputBackgrounds () const;
      void setInputBackgrounds (const std::vector<BackLocator>& value);
      const BackLocator& inputBackgrounds (size_t index) const;
      void inputBackgrounds (size_t index, const BackLocator& value);
      const std::vector<Detectors>& inputResponses () const;
      void setInputResponses (const std::vector<Detectors>& value);
      const Detectors& inputResponses (size_t index) const;
      void inputResponses (size_t index, const Detectors& value);
      const std::vector<Arfs>& inputArfs () const;
      void setInputArfs (const std::vector<Arfs>& value);
      const Arfs& inputArfs (size_t index) const;
      void inputArfs (size_t index, const Arfs& value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_backgndFile;
      bool m_useCountingStat;
      bool m_isType2;
      Real m_exposureTime;

      Real m_backExposureTime;

      Real m_correctionNorm;
      bool m_enteredNone;
      size_t m_numSourcesForSpectra;
      
      string m_statName;
      string m_testStatName;

    // Data Members for Associations
      IntegerVector m_origRowNums;
      std::vector<BackLocator> m_inputCorrFiles;
      std::vector<BackLocator> m_inputBackgrounds;
      std::vector<Detectors> m_inputResponses;
      std::vector<Arfs> m_inputArfs;

    // Additional Implementation Declarations

};

// Class FakeDataInputRecord 

inline const string& FakeDataInputRecord::backgndFile () const
{
  return m_backgndFile;
}

inline void FakeDataInputRecord::backgndFile (const string& value)
{
  m_backgndFile = value;
}

inline bool FakeDataInputRecord::useCountingStat () const
{
  return m_useCountingStat;
}

inline void FakeDataInputRecord::useCountingStat (bool value)
{
  m_useCountingStat = value;
}

inline bool FakeDataInputRecord::isType2 () const
{
  return m_isType2;
}

inline void FakeDataInputRecord::isType2 (bool value)
{
  m_isType2 = value;
}

inline Real FakeDataInputRecord::exposureTime () const
{
  return m_exposureTime;
}

inline void FakeDataInputRecord::exposureTime (Real value)
{
  m_exposureTime = value;
}

inline Real FakeDataInputRecord::backExposureTime () const
{
  return m_backExposureTime;
}

inline void FakeDataInputRecord::backExposureTime (Real value)
{
  m_backExposureTime = value;
}

inline Real FakeDataInputRecord::correctionNorm () const
{
  return m_correctionNorm;
}

inline void FakeDataInputRecord::correctionNorm (Real value)
{
  m_correctionNorm = value;
}

inline bool FakeDataInputRecord::enteredNone () const
{
  return m_enteredNone;
}

inline void FakeDataInputRecord::enteredNone (bool value)
{
  m_enteredNone = value;
}

inline size_t FakeDataInputRecord::numSourcesForSpectra () const
{
  return m_numSourcesForSpectra;
}

inline void FakeDataInputRecord::numSourcesForSpectra (size_t value)
{
  m_numSourcesForSpectra = value;
}

inline const string& FakeDataInputRecord::statName () const
{
   return m_statName;
}

inline void FakeDataInputRecord::statName(const string& defaultStat)
{
   m_statName = defaultStat;
}

inline const string& FakeDataInputRecord::testStatName () const
{
   return m_testStatName;
}

inline void FakeDataInputRecord::testStatName(const string& defaultStat)
{
   m_testStatName = defaultStat;
}

inline const IntegerVector& FakeDataInputRecord::origRowNums () const
{
  return m_origRowNums;
}

inline void FakeDataInputRecord::setOrigRowNums (const IntegerVector& value)
{
  m_origRowNums = value;
}

inline int FakeDataInputRecord::origRowNums (size_t index) const
{
  return m_origRowNums[index];
}

inline void FakeDataInputRecord::origRowNums (size_t index, int value)
{
  m_origRowNums[index] = value;
}

inline const std::vector<FakeDataInputRecord::BackLocator>& FakeDataInputRecord::inputCorrFiles () const
{
  return m_inputCorrFiles;
}

inline void FakeDataInputRecord::setInputCorrFiles (const std::vector<FakeDataInputRecord::BackLocator>& value)
{
  m_inputCorrFiles = value;
}

inline const FakeDataInputRecord::BackLocator& FakeDataInputRecord::inputCorrFiles (size_t index) const
{
  return m_inputCorrFiles[index];
}

inline void FakeDataInputRecord::inputCorrFiles (size_t index, const FakeDataInputRecord::BackLocator& value)
{
  m_inputCorrFiles[index] = value;
}

inline const std::vector<FakeDataInputRecord::BackLocator>& FakeDataInputRecord::inputBackgrounds () const
{
  return m_inputBackgrounds;
}

inline void FakeDataInputRecord::setInputBackgrounds (const std::vector<FakeDataInputRecord::BackLocator>& value)
{
  m_inputBackgrounds = value;
}

inline const FakeDataInputRecord::BackLocator& FakeDataInputRecord::inputBackgrounds (size_t index) const
{
  return m_inputBackgrounds[index];
}

inline void FakeDataInputRecord::inputBackgrounds (size_t index, const FakeDataInputRecord::BackLocator& value)
{
  m_inputBackgrounds[index] = value;
}

inline const std::vector<FakeDataInputRecord::Detectors>& FakeDataInputRecord::inputResponses () const
{
  return m_inputResponses;
}

inline void FakeDataInputRecord::setInputResponses (const std::vector<FakeDataInputRecord::Detectors>& value)
{
  m_inputResponses = value;
}

inline const FakeDataInputRecord::Detectors& FakeDataInputRecord::inputResponses (size_t index) const
{
  return m_inputResponses[index];
}

inline void FakeDataInputRecord::inputResponses (size_t index, const FakeDataInputRecord::Detectors& value)
{
  m_inputResponses[index] = value;
}

inline const std::vector<FakeDataInputRecord::Arfs>& FakeDataInputRecord::inputArfs () const
{
  return m_inputArfs;
}

inline void FakeDataInputRecord::setInputArfs (const std::vector<FakeDataInputRecord::Arfs>& value)
{
  m_inputArfs = value;
}

inline const FakeDataInputRecord::Arfs& FakeDataInputRecord::inputArfs (size_t index) const
{
  return m_inputArfs[index];
}

inline void FakeDataInputRecord::inputArfs (size_t index, const FakeDataInputRecord::Arfs& value)
{
  m_inputArfs[index] = value;
}


#endif
