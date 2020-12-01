//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIP_92ADATA_H
#define OGIP_92ADATA_H 1

// DataSet
#include <XSModel/Data/DataSet.h>
// OGIP-92aIO
#include <XSModel/DataFactory/OGIP-92aIO.h>
#include <XSModel/Data/SpectralData.h>

//	Implementation for OGIP 1992a standard data.
//	This class will handle the OGIP Type I format



class OGIP_92aData : public DataSet, //## Inherits: <unnamed>%3AA906AA00C3
                     	public OGIP_92aIO  //## Inherits: <unnamed>%3BF52E41004A
{

  private:



    class OutputInfo 
    {

      public:
          OutputInfo (const string& fileName, const SpectralData* sd, const std::vector<string>& respNames, const std::vector<string>& arfNames, const string& bckName, const string& corrName, const RealArray& bckScaleRatio, const Real corrScale, const std::vector<string>& modelNames, bool aScaleIsKeyword, bool bScaleIsKeyword);
          const string& fileName () const;
          const SpectralData* sd () const;
          const std::vector<string>& respNames () const;
          const std::vector<string>& arfNames () const;
          const string& bckName () const;
          const string& corrName () const;
          const RealArray& bckScaleRatio () const;
          const Real corrScale () const;
          const std::vector<string>& modelNames () const;
          bool isAScaleKeyword () const;
          bool isBScaleKeyword () const;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          const string& m_fileName;
          const SpectralData* m_sd;
          const std::vector<string> m_respNames;
          const std::vector<string> m_arfNames;
          const string& m_bckName;
          const string& m_corrName;
          const RealArray& m_bckScaleRatio;
          const Real m_corrScale;
          const std::vector<string>& m_modelNames;
          bool m_isAScaleKeyword;
          bool m_isBScaleKeyword;

        // Additional Implementation Declarations

    };

  public:
      OGIP_92aData();

      OGIP_92aData(const OGIP_92aData &right);
      virtual ~OGIP_92aData();

      virtual OGIP_92aData* clone () const;
      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      virtual void initialize (DataPrototype* proto, DataInputRecord& record);
      void closeSourceFiles ();
      //	setData processes the input file for a single source
      //	spectrum into a data object (e.g. SpectrumData,
      //	ResponseData). For files with multiple sources,
      //	e.g. OGIP type II files, setData will be called once for
      //	each data row to be read.
      virtual void setResponse (size_t spectrumNumber, size_t row = 0);
      virtual void reportResponse (size_t row) const;
      virtual bool setResponse (SpectralData* sourceSpectrum, size_t spectrumNumber, size_t sourceNum, const string& responseName, const string& arfName);
      virtual bool setBackgroundData (size_t row = 0, int bckRow = -1);
      virtual bool setCorrectionData (size_t row = 0, int corRow = -1);
      virtual void initializeFake (DataPrototype* proto, FakeDataInputRecord& record);
      virtual void outputData ();
      virtual FakeDataInputRecord::Arfs getAncillaryLocation (size_t rowNum, const FakeDataInputRecord::Detectors& respInfo) const;
      virtual std::pair<string,size_t> getBackCorrLocation (size_t rowNum, bool isCorr = false) const;
      virtual FakeDataInputRecord::Detectors getResponseName (size_t rowNum) const;

    // Additional Public Declarations

  protected:
      virtual void setArrays (size_t row = 0);
      virtual void setDescription (size_t spectrumNumber = 1, size_t row = 0);
      virtual void groupArrays (size_t row = 0);
      //	This is the equivalent of fpauxf
      void setAncillaryFileName (string& outFileName, const string& matchName, const string& key, const string& suffix, size_t row = 0);
      //	Abstract function to be called by setData.
      //
      //	Invokes methods that instantiate ancilliary
      //	datasets in the case of DataSet and Response
      //	classes.
      //
      //	Default implementation is to do nothing.
      virtual bool setAncillaryData (size_t row = 0, int ancRow = -1);
      virtual bool isCounts () const;
      bool match (const IntegerVector& srcValue, const IntegerVector& value);
      virtual void getNChansForFake (FakeDataInputRecord& record, const size_t index, SpectralData::ChannelInfo& chanInfo);
      virtual void writeCommonKeys (CCfits::Table* tbl);
      //	OGIP files can have a NET indicator that the file is
      //	background subtracted. This is used in groupArrays.
      virtual bool isNet (const RealArray& spectrum);

    // Additional Protected Declarations

  private:
      OGIP_92aData & operator=(const OGIP_92aData &right);

      void outputType1Table ();
      void outputType2Table ();
      void outputTable1Common (const OutputInfo& info);
      void outputTable2Common (const OutputInfo& info, size_t row, const BoolArray& optCols);
      void setFilterKeys (size_t row);
      RealArray scaleVector (const string& key, int row, int first, int last);
      static void fakeitModRespHistory (CCfits::Table* tbl, const OutputInfo& info, size_t rowNum);
      static void collectRespArfNames (const std::vector<Response*>& detectors, std::vector<string>& respNames, std::vector<string>& arfNames);
      static void type2FakeitHistoryCols (CCfits::Table* tbl, size_t nSources);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_fkModRoot;
      static const string s_fkRspRoot;
      static const string s_fkArfRoot;
      //	Should equal FLEN_VALUE - 3, where FLEN_VALUE is defined
      //	in CFITSIO.  The 3 comes from spaces for quotes in the
      //	fits header, and a trailing null.
      static const size_t s_fkKeyValLen;

    // Additional Implementation Declarations

};

// Class OGIP_92aData::OutputInfo 

inline const string& OGIP_92aData::OutputInfo::fileName () const
{
  return m_fileName;
}

inline const SpectralData* OGIP_92aData::OutputInfo::sd () const
{
  return m_sd;
}

inline const std::vector<string>& OGIP_92aData::OutputInfo::respNames () const
{
  return m_respNames;
}

inline const std::vector<string>& OGIP_92aData::OutputInfo::arfNames () const
{
  return m_arfNames;
}

inline const string& OGIP_92aData::OutputInfo::bckName () const
{
  return m_bckName;
}

inline const string& OGIP_92aData::OutputInfo::corrName () const
{
  return m_corrName;
}

inline const RealArray& OGIP_92aData::OutputInfo::bckScaleRatio () const
{
  return m_bckScaleRatio;
}

inline const Real OGIP_92aData::OutputInfo::corrScale () const
{
  return m_corrScale;
}

inline const std::vector<string>& OGIP_92aData::OutputInfo::modelNames () const
{
  return m_modelNames;
}

inline bool OGIP_92aData::OutputInfo::isAScaleKeyword () const
{
  return m_isAScaleKeyword;
}

inline bool OGIP_92aData::OutputInfo::isBScaleKeyword () const
{
  return m_isBScaleKeyword;
}

// Class OGIP_92aData 


#endif
