//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATASET_H
#define DATASET_H 1
#include "xsTypes.h"

// Error
#include <XSUtil/Error/Error.h>
// iosfwd
#include <iosfwd>
// FakeDataInputRecord
#include <XSModel/Data/FakeDataInputRecord.h>
// XspecRegistry
#include <XSModel/DataFactory/XspecRegistry.h>

class DataSetBase;
namespace XSContainer {
    class DataContainer;

} // namespace XSContainer
class DataInputRecord;

//	A data set is the basic data unit consisting of a
//	spectrum expressed in counts per energy bin
//	The data set "uses" a response file, an  efficiency file,
//	an optional correction file and an optional background
//	file
//	The plan is to implement as data members raw i.e. as read
//	data sets to speed up the ignore/notice commands etc.
//	This superclass provides the general interface of the
//	data to the rest of the program. The subclasses are
//	different formats that overload the read() function.



class DataSet : public RegisteredFormat  //## Inherits: <unnamed>%399967380180
{

  public:
    //	Exception to be thrown on receiving an abort sequence,
    //	usually via user entry of the "none" or "/*" sequence.



    class AbortDataLoop : public YellowAlert  //## Inherits: <unnamed>%3A5CCB7A03AF
    {
      public:
          AbortDataLoop (const string& msg = "Terminated at user request\n");

      protected:
      private:
      private: //## implementation
    };



    class ResponseIsNeeded : public YellowAlert  //## Inherits: <unnamed>%3E94745E015E
    {
      public:
          ResponseIsNeeded (const string& msg = "");

      protected:
      private:
      private: //## implementation
    };
      DataSet();

      DataSet(const DataSet &right);
      virtual ~DataSet();

      void plot (const string& args);
      virtual DataSet* clone () const = 0;
      const std::vector<int>& groupingInfo (size_t row) const;
      const std::vector<int>& qualityInfo (size_t row) const;
      size_t channels (size_t row) const;
      const string& dataName () const;
      SpectralData*& sourceData (size_t row);
      virtual void initialize (DataPrototype* proto, DataInputRecord& record) = 0;
      //	setData processes the input file for a single source
      //	spectrum into a data object (e.g. SpectrumData,
      //	ResponseData). For files with multiple sources,
      //	e.g. OGIP type II files, setData will be called once for
      //	each data row to be read.
      void setData (size_t spectrumNumber, size_t row = 0);
      //	setData processes the input file for a single source
      //	spectrum into a data object (e.g. SpectrumData,
      //	ResponseData). For files with multiple sources,
      //	e.g. OGIP type II files, setData will be called once for
      //	each data row to be read.
      virtual void setResponse (size_t spectrumNumber, size_t row = 0);
      void ignoreBadChannels ();
      virtual void report (size_t row) const;
      void destroy () throw ();
      virtual void reportAll ();
      const SpectralData* sourceData (size_t row) const;
      virtual void closeSourceFiles () = 0;
      virtual bool isMultiple () const;
      int numSpectra () const;
      //	return TLMINn, TLMAXn for the file, which are the start
      //	and end range of rows in which  the response data may be
      //	contained.
      void legalChannelBounds (int& startChan, int& endChan) const;
      bool groupingSet (size_t row);
      bool qualitySet (size_t row);
      size_t dataGroup () const;
      void dataGroup (size_t group);
      size_t index () const;
      int removeNumberedSpectrum (size_t index, bool remove = false);
      void setChannels (bool value, IntegerArray& channelRange);
      void setChannels (bool value, std::pair<Real,Real>& realRange	// for setting energy or wavelength range ignore/notice
      	// status
      );
      virtual void reportResponse (size_t row) const = 0;
      SpectralData* spectralData () const;
      const std::map<size_t,SpectralData*>& multiSpectralData () const;
      int origNumSources () const;
      void origNumSources (int value);
      virtual bool setResponse (SpectralData* sourceSpectrum, size_t spectrumNumber, size_t sourceNum, const string& responseName, const string& arfName);
      virtual bool setBackgroundData (size_t row, int bckRow);
      virtual bool setCorrectionData (size_t row, int corRow);
      bool resetAllDetectors ();
      virtual void initializeFake (DataPrototype* proto, FakeDataInputRecord& record) = 0;
      virtual void outputData () = 0;
      void nullBackPointers (const IntegerArray& rows);
      bool specNumOrder (IntegerArray& rows) const;
      virtual FakeDataInputRecord::Detectors getResponseName (size_t rowNum) const = 0;
      virtual FakeDataInputRecord::Arfs getAncillaryLocation (size_t rowNum, const FakeDataInputRecord::Detectors& respInfo) const = 0;
      virtual std::pair<string,size_t> getBackCorrLocation (size_t rowNum, bool isCorr = false) const = 0;
      virtual void generateFake ();
      const string& outputFileName () const;
      void outputFileName (const string& fileName);
      const string& outputBckFileName () const;
      void outputBckFileName (const string& fileName);
      size_t getMaxChannels () const;
      virtual bool isModular () const;
      void setModelNamesForFake (const string& name, size_t index);
      void setModelNamesForFake (const StringArray& names);
      bool anyQuality () const;
      bool anyGrouping () const;
      bool aScaleIsKeyword () const;
      bool bScaleIsKeyword () const;
      string getFullPathName () const;
      void setRunPath ();
      const string& getRunPath () const;
      static size_t STD_FIRST_CHAN ();
      void insertSpectrum (SpectralData* s);
      static bool useFakeCountingStat ();
      static void useFakeCountingStat (bool value);
      static const string& xspecVersion ();
      static void xspecVersion (const string& value);

  public:
    // Additional Public Declarations

  protected:
      virtual bool setAncillaryData (size_t row, int ancRow = -1) = 0;
      virtual void setArrays (size_t row = 0) = 0;
      virtual void scaleArrays (size_t row = 0);
      virtual void setDescription (size_t spectrumNum = 1, size_t row = 0) = 0;
      virtual bool isCounts () const;
      virtual void computeTotals (size_t row);
      const DataSetBase* dataSetBase () const;
      virtual void groupArrays (size_t row);
      virtual bool isNet (const RealArray& spectrum);
      static const int count ();
      DataSetBase*& dataSetBase ();

    // Additional Protected Declarations

  private:
      DataSet & operator=(const DataSet &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static int s_count;
      static bool s_useFakeCountingStat;
      static string s_xspecVersion;
      static const size_t s_STD_FIRST_CHAN;

    // Data Members for Associations
      DataSetBase* m_dataSetBase;

    // Additional Implementation Declarations
      friend class DataContainer;
};

// Class DataSet::AbortDataLoop 

// Class DataSet::ResponseIsNeeded 

// Class DataSet 

inline const DataSetBase* DataSet::dataSetBase () const
{

  return m_dataSetBase;
}

inline bool DataSet::isModular () const
{
  return false;
}

inline size_t DataSet::STD_FIRST_CHAN ()
{
  return s_STD_FIRST_CHAN;
}

inline const int DataSet::count ()
{
  return s_count;
}

inline bool DataSet::useFakeCountingStat ()
{
  return s_useFakeCountingStat;
}

inline void DataSet::useFakeCountingStat (bool value)
{
  s_useFakeCountingStat = value;
}

inline const string& DataSet::xspecVersion ()
{
  return s_xspecVersion;
}

inline void DataSet::xspecVersion (const string& value)
{
  s_xspecVersion = value;
}

inline DataSetBase*& DataSet::dataSetBase ()
{
  return m_dataSetBase;
}


#endif
