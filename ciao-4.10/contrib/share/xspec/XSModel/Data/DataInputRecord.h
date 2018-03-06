//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATAINPUTRECORD_H
#define DATAINPUTRECORD_H 1

// xsTypes
#include "xsTypes.h"

class DataSet;
class BackCorr;
class Response;




class DataInputRecord 
{

  public:
      DataInputRecord(const DataInputRecord &right);
      DataInputRecord (const string& fName, const IntegerArray& specNums = IntegerArray(), std::size_t groupNum = 1, const IntegerArray& specRange = IntegerArray(1,0), size_t nCommas = 0);
      ~DataInputRecord();
      DataInputRecord & operator=(const DataInputRecord &right);

      void updateSpectrumCounts (size_t numberOfSpectra);
      void report ();
      const string& fileName () const;
      void renumber (size_t newIndex);
      friend bool operator < (const DataInputRecord& left, const DataInputRecord& right);
      string& fileName ();
      void fileName (const string& value);
      size_t groupNumber () const;
      void groupNumber (size_t value);
      size_t numTrailCommas () const;
      void numTrailCommas (size_t value);
      const IntegerArray& spectrumNumber () const;
      void setSpectrumNumber (const IntegerArray& value);
      int spectrumNumber (int index) const;
      void spectrumNumber (int index, int value);
      const IntegerArray& spectrumRange () const;
      void setSpectrumRange (const IntegerArray& value);
      int spectrumRange (int index) const;
      void spectrumRange (int index, int value);
      const Response* response () const;
      void response (Response* value);
      const BackCorr* backcorr () const;
      void backcorr (BackCorr* value);
      DataSet* data () const;
      void data (DataSet* value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void correctSpectraRows (size_t numberOfSpectra);

    // Additional Private Declarations

  private: //## implementation
      void swap (DataInputRecord& right);

    // Data Members for Class Attributes
      string m_fileName;
      size_t m_groupNumber;
      size_t m_numTrailCommas;

    // Data Members for Associations
      IntegerArray m_spectrumNumber;
      IntegerArray m_spectrumRange;
      Response* m_response;
      BackCorr* m_backcorr;
      DataSet* m_data;

    // Additional Implementation Declarations

};

// Class DataInputRecord 

inline string& DataInputRecord::fileName ()
{
  return m_fileName;
}

inline void DataInputRecord::fileName (const string& value)
{
  m_fileName = value;
}

inline size_t DataInputRecord::groupNumber () const
{
  return m_groupNumber;
}

inline void DataInputRecord::groupNumber (size_t value)
{
  m_groupNumber = value;
}

inline size_t DataInputRecord::numTrailCommas () const
{
  return m_numTrailCommas;
}

inline void DataInputRecord::numTrailCommas (size_t value)
{
  m_numTrailCommas = value;
}

inline const IntegerArray& DataInputRecord::spectrumNumber () const
{
  return m_spectrumNumber;
}

inline void DataInputRecord::setSpectrumNumber (const IntegerArray& value)
{
  m_spectrumNumber = value;
}

inline int DataInputRecord::spectrumNumber (int index) const
{
  return m_spectrumNumber[index];
}

inline void DataInputRecord::spectrumNumber (int index, int value)
{
  m_spectrumNumber[index] = value;
}

inline const IntegerArray& DataInputRecord::spectrumRange () const
{
  return m_spectrumRange;
}

inline void DataInputRecord::setSpectrumRange (const IntegerArray& value)
{
  m_spectrumRange = value;
}

inline int DataInputRecord::spectrumRange (int index) const
{
  return m_spectrumRange[index];
}

inline void DataInputRecord::spectrumRange (int index, int value)
{
  m_spectrumRange[index] = value;
}

inline const Response* DataInputRecord::response () const
{
  return m_response;
}

inline void DataInputRecord::response (Response* value)
{
  m_response = value;
}

inline const BackCorr* DataInputRecord::backcorr () const
{
  return m_backcorr;
}

inline void DataInputRecord::backcorr (BackCorr* value)
{
  m_backcorr = value;
}

inline DataSet* DataInputRecord::data () const
{
  return m_data;
}

inline void DataInputRecord::data (DataSet* value)
{
  m_data = value;
}


#endif
