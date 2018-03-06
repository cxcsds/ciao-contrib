//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef BACKGROUND_H
#define BACKGROUND_H 1

// Error
#include <XSUtil/Error/Error.h>
// XspecRegistry
#include <XSModel/DataFactory/XspecRegistry.h>

class SpectralData;
class DataSet;
#include "xsTypes.h"

//	Class representing the background for the dataset



class BackCorr : public RegisteredFormat  //## Inherits: <unnamed>%39A3D80F022E
{

  public:



    class IncorrectGrouping : public YellowAlert  //## Inherits: <unnamed>%39F8706F02EC
    {
      public:
          IncorrectGrouping (const string& message = string());

      protected:
      private:
      private: //## implementation
    };
      BackCorr();
      virtual ~BackCorr();

      void destroy () throw ();
      virtual BackCorr* clone () const = 0;
      void setData (size_t spectrumNumber, size_t backgrndRow, bool correction = false);
      virtual size_t read (const string& fileName, bool readFlag = true) = 0;
      const SpectralData* data () const;
      virtual void closeSourceFiles () = 0;
      void renumber (size_t newIndex);
      void weightVariance (const RealArray& norm, bool correction);
      virtual void initialize (DataSet* parentData, size_t parentRow, const string& fileName, size_t backCorRow) = 0;
      const RealArray& spectrum () const;
      const RealArray& variance () const;
      void setSpectrum (const RealArray& value);
      void setVariance (const RealArray& value);
      void setRawVariance (const RealArray& value);
      bool aScaleIsKeyword () const;
      void aScaleIsKeyword (bool value);
      bool bScaleIsKeyword () const;
      void bScaleIsKeyword (bool value);
      const string& runPath () const;
      void runPath (const string& value);
      SpectralData* data ();
      void data (SpectralData* value);

  public:
    // Additional Public Declarations

  protected:
      BackCorr(const BackCorr &right);

      virtual void setArrays (size_t backgrndRow, bool ignoreStats = false) = 0;
      virtual void setDescription (size_t spectrumNumber) = 0;
      virtual void scaleArrays (bool correction = false);
      virtual bool isCounts () const;
      virtual void groupArrays (bool correction);
      size_t sourceRow ();
      void sourceRow (size_t value);
      DataSet* source ();
      void source (DataSet* value);

    // Additional Protected Declarations

  private:
      BackCorr & operator=(const BackCorr &right);
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      size_t m_sourceRow;
      bool m_aScaleIsKeyword;
      bool m_bScaleIsKeyword;
      string m_runPath;

    // Data Members for Associations
      SpectralData* m_data;
      DataSet* m_source;

    // Additional Implementation Declarations

};



typedef BackCorr Background;



typedef BackCorr Correction;

// Class BackCorr::IncorrectGrouping 

// Class BackCorr 

inline const SpectralData* BackCorr::data () const
{
  return m_data;
}

inline size_t BackCorr::sourceRow ()
{
  return m_sourceRow;
}

inline void BackCorr::sourceRow (size_t value)
{
  m_sourceRow = value;
}

inline bool BackCorr::aScaleIsKeyword () const
{
  return m_aScaleIsKeyword;
}

inline void BackCorr::aScaleIsKeyword (bool value)
{
  m_aScaleIsKeyword = value;
}

inline bool BackCorr::bScaleIsKeyword () const
{
  return m_bScaleIsKeyword;
}

inline void BackCorr::bScaleIsKeyword (bool value)
{
  m_bScaleIsKeyword = value;
}

inline const string& BackCorr::runPath () const
{
  return m_runPath;
}

inline void BackCorr::runPath (const string& value)
{
  m_runPath = value;
}

inline SpectralData* BackCorr::data ()
{
  return m_data;
}

inline void BackCorr::data (SpectralData* value)
{
  m_data = value;
}

inline DataSet* BackCorr::source ()
{
  return m_source;
}

inline void BackCorr::source (DataSet* value)
{
  m_source = value;
}


#endif
