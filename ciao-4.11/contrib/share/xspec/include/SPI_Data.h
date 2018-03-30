//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SPI_DATA_H
#define SPI_DATA_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// OGIP-92aData
#include <XSModel/Data/OGIP-92aData.h>




class SPI_Data : public OGIP_92aData  //## Inherits: <unnamed>%3AA67FD10216
{

  public:
      SPI_Data();

      SPI_Data(const SPI_Data &right);
      virtual ~SPI_Data();

      virtual SPI_Data* clone () const;
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      void closeSourceFiles ();
      //	setData processes the input file for a single source
      //	spectrum into a data object (e.g. SpectrumData,
      //	ResponseData). For files with multiple sources,
      //	e.g. OGIP type II files, setData will be called once for
      //	each data row to be read.
      virtual void setResponse (size_t spectrumNumber, size_t row = 0);
      virtual size_t read (const string& fileName, bool readFlag);
      virtual void reportResponse (size_t row) const;
      virtual bool setResponse (SpectralData* sourceSpectrum, size_t spectrumNumber, size_t specNum, const string& responseName, const string& arfName);
      virtual void initialize (DataPrototype* proto, DataInputRecord& record);
      virtual void reportAll ();
      virtual void report (size_t row) const;
      virtual void initializeFake (DataPrototype* proto, FakeDataInputRecord& record);
      virtual FakeDataInputRecord::Arfs getAncillaryLocation (size_t rowNum, const FakeDataInputRecord::Detectors& respInfo) const;
      virtual std::pair<string,size_t>  getBackCorrLocation (size_t rowNum, bool isCorr = false) const;
      virtual bool isMultiple () const;
      virtual void outputData ();
      virtual bool isModular () const;
      virtual FakeDataInputRecord::Detectors getResponseName (size_t rowNum) const;
      const StringArray& rmfNames () const;
      void rmfNames (const StringArray& value);
      const StringArray& arfNames () const;
      void arfNames (const StringArray& value);

    // Additional Public Declarations

  protected:
      int getRespdbInfo (CCfits::FITS* openFile);
      int getRespdbInfo (const string& fileName);
      virtual void getNChansForFake (FakeDataInputRecord& record, const size_t index, SpectralData::ChannelInfo& chanInfo);
      virtual void writeCommonKeys (CCfits::Table* tbl);
      static const string& RESPONSEDB ();
      static const string& NRMF ();
      static const string& ISDCTYPE ();
      static const string& RESPFILEDB ();
      static std::vector<std::string> SPIspectrumKeys ();

    // Additional Protected Declarations

  private:

      SPI_Data& operator=(const SPI_Data &right);
      CCfits::Table* makeSpectraTable (string& hduName, size_t nChans, const BoolArray& optCols);
      CCfits::Table* makeRespdbTable (string& hduName);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_RESPONSEDB;
      static const string s_NRMF;
      static const string s_ISDCTYPE;
      static const string s_RESPFILEDB;
      bool m_isFirstSpectrum;

    // Data Members for Associations
      static std::vector<std::string> s_SPIspectrumKeys;
      StringArray m_rmfNames;
      StringArray m_arfNames;

    // Additional Implementation Declarations

};

// Class SPI_Data 

inline bool SPI_Data::isMultiple () const
{
  return true;
}

inline bool SPI_Data::isModular () const
{
  return true;
}

inline const string& SPI_Data::RESPONSEDB ()
{
  return s_RESPONSEDB;
}

inline const string& SPI_Data::NRMF ()
{
  return s_NRMF;
}

inline const string& SPI_Data::ISDCTYPE ()
{
  return s_ISDCTYPE;
}

inline const string& SPI_Data::RESPFILEDB ()
{
  return s_RESPFILEDB;
}

inline std::vector<std::string> SPI_Data::SPIspectrumKeys ()
{
  return s_SPIspectrumKeys;
}

inline const StringArray& SPI_Data::rmfNames () const
{
  return m_rmfNames;
}

inline void SPI_Data::rmfNames (const StringArray& value)
{
  m_rmfNames = value;
}

inline const StringArray& SPI_Data::arfNames () const
{
  return m_arfNames;
}

inline void SPI_Data::arfNames (const StringArray& value)
{
  m_arfNames = value;
}


#endif
