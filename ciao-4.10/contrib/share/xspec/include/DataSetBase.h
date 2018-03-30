//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATASETBASE_H
#define DATASETBASE_H 1

// Error
#include <XSUtil/Error/Error.h>
// string
#include <string>
// map
#include <map>
// SpectralData
#include <XSModel/Data/SpectralData.h>

class DataPrototype;




class DataSetBase 
{

  public:



    class NoSuchSpectrum : public YellowAlert  //## Inherits: <unnamed>%3A2BD4AA0354
    {
      public:
          NoSuchSpectrum (const string& diag);

      protected:
      private:
      private: //## implementation
    };
      DataSetBase(const DataSetBase &right);
      DataSetBase (const string& name, size_t index, DataPrototype* proto);
      ~DataSetBase();

      void destroy () throw ();
      void closeFiles ();
      std::map<size_t,SpectralData*>& multiSpectralData ();
      SpectralData* spectralData ();
      const string& dataName () const;
      void dataName (const string& value);
      const size_t legalStartChan () const;
      void legalStartChan (size_t value);
      const size_t legalEndChan () const;
      void legalEndChan (size_t value);
      size_t dataGroup () const;
      void dataGroup (size_t value);
      const size_t index () const;
      void index (size_t value);
      const int origNumSources () const;
      void origNumSources (int value);
      const string& outputFileName () const;
      void outputFileName (const string& value);
      const string& outputBckFileName () const;
      void outputBckFileName (const string& value);
      bool aScaleIsKeyword () const;
      void aScaleIsKeyword (bool value);
      bool bScaleIsKeyword () const;
      void bScaleIsKeyword (bool value);
      const string& runPath () const;
      void runPath (const string& value);
      const SpectralData* spectralData () const;
      void spectralData (SpectralData* value);
      const DataPrototype* protoType () const;
      void setProtoType (DataPrototype* value);
      const std::map<size_t, SpectralData*>& multiSpectralData () const;
      void multiSpectralData (const std::map<size_t, SpectralData*>& value);
      SpectralData*& multiSpectralData (size_t index);
      const std::vector<std::string>& modelNamesForFake () const;
      void setModelNamesForFake (const std::vector<std::string>& value);
      const std::string& modelNamesForFake (size_t index) const;
      void modelNamesForFake (size_t index, const std::string& value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      DataSetBase & operator=(const DataSetBase &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_dataName;
      size_t m_legalStartChan;
      size_t m_legalEndChan;
      size_t m_dataGroup;
      size_t m_index;
      int m_origNumSources;
      string m_outputFileName;
      string m_outputBckFileName;
      bool m_aScaleIsKeyword;
      bool m_bScaleIsKeyword;
      string m_runPath;

    // Data Members for Associations
      SpectralData* m_spectralData;
      DataPrototype* m_protoType;
      std::map<size_t, SpectralData*> m_multiSpectralData;
      std::vector<std::string> m_modelNamesForFake;

    // Additional Implementation Declarations

};

// Class DataSetBase::NoSuchSpectrum 

// Class DataSetBase 

inline const string& DataSetBase::dataName () const
{
  return m_dataName;
}

inline void DataSetBase::dataName (const string& value)
{
  m_dataName = value;
}

inline const size_t DataSetBase::legalStartChan () const
{
  return m_legalStartChan;
}

inline void DataSetBase::legalStartChan (size_t value)
{
  m_legalStartChan = value;
}

inline const size_t DataSetBase::legalEndChan () const
{
  return m_legalEndChan;
}

inline void DataSetBase::legalEndChan (size_t value)
{
  m_legalEndChan = value;
}

inline size_t DataSetBase::dataGroup () const
{
  return m_dataGroup;
}

inline const size_t DataSetBase::index () const
{
  return m_index;
}

inline void DataSetBase::index (size_t value)
{
  m_index = value;
}

inline const int DataSetBase::origNumSources () const
{
  return m_origNumSources;
}

inline void DataSetBase::origNumSources (int value)
{
  m_origNumSources = value;
}

inline const string& DataSetBase::outputFileName () const
{
  return m_outputFileName;
}

inline void DataSetBase::outputFileName (const string& value)
{
  m_outputFileName = value;
}

inline const string& DataSetBase::outputBckFileName () const
{
  return m_outputBckFileName;
}

inline void DataSetBase::outputBckFileName (const string& value)
{
  m_outputBckFileName = value;
}

inline bool DataSetBase::aScaleIsKeyword () const
{
  return m_aScaleIsKeyword;
}

inline void DataSetBase::aScaleIsKeyword (bool value)
{
  m_aScaleIsKeyword = value;
}

inline bool DataSetBase::bScaleIsKeyword () const
{
  return m_bScaleIsKeyword;
}

inline void DataSetBase::bScaleIsKeyword (bool value)
{
  m_bScaleIsKeyword = value;
}

inline const string& DataSetBase::runPath () const
{
  return m_runPath;
}

inline void DataSetBase::runPath (const string& value)
{
  m_runPath = value;
}

inline const SpectralData* DataSetBase::spectralData () const
{
  return m_spectralData;
}

inline void DataSetBase::spectralData (SpectralData* value)
{
  m_spectralData = value;
}

inline const DataPrototype* DataSetBase::protoType () const
{
  return m_protoType;
}

inline void DataSetBase::setProtoType (DataPrototype* value)
{
  m_protoType = value;
}

inline const std::map<size_t, SpectralData*>& DataSetBase::multiSpectralData () const
{
  return m_multiSpectralData;
}

inline void DataSetBase::multiSpectralData (const std::map<size_t, SpectralData*>& value)
{
  m_multiSpectralData = value;
}

inline const std::vector<std::string>& DataSetBase::modelNamesForFake () const
{
  return m_modelNamesForFake;
}

inline void DataSetBase::setModelNamesForFake (const std::vector<std::string>& value)
{
  m_modelNamesForFake = value;
}

inline const std::string& DataSetBase::modelNamesForFake (size_t index) const
{
  return m_modelNamesForFake[index];
}

inline void DataSetBase::modelNamesForFake (size_t index, const std::string& value)
{
  m_modelNamesForFake[index] = value;
}


#endif
