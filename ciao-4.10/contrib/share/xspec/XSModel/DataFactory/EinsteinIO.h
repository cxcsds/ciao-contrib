//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EINSTEINIO_H
#define EINSTEINIO_H 1
#include "XspecDataIO.h"
namespace CCfits
{
        class FITS;
        class ExtHDU;       
}

//	See XspecDataIO for details.



class EinsteinIO : public XspecDataIO  //## Inherits: <unnamed>%3AACF9920105
{

  public:
      virtual ~EinsteinIO();

      virtual void write (const string& fileName);
      virtual size_t read (const string& fileName, bool readFlag = true);
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);

    // Additional Public Declarations

  protected:
      EinsteinIO();

      EinsteinIO(const EinsteinIO &right);

      virtual void channelBounds (int& startChannel, int& endChannel, size_t row = 0) const;
      void closeFile ();
      const CCfits::FITS* dataSource () const;
      void dataSource (CCfits::FITS* value);

    // Additional Protected Declarations

  private:
      EinsteinIO & operator=(const EinsteinIO &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      CCfits::FITS* m_dataSource;

    // Additional Implementation Declarations

};

// Class EinsteinIO 

inline const CCfits::FITS* EinsteinIO::dataSource () const
{
  return m_dataSource;
}

inline void EinsteinIO::dataSource (CCfits::FITS* value)
{
  m_dataSource = value;
}


#endif
