//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SPI_RESPONSE_H
#define SPI_RESPONSE_H 1

// xsTypes
#include "xsTypes.h"
// MultiResponse
#include "XSModel/Data/Detector/MultiResponse.h"
// OGIP-92aIO
#include "XSModel/DataFactory/OGIP-92aIO.h"




class SPI_Response : public MultiResponse, //## Inherits: <unnamed>%3AA3A60E00B0
                     	public OGIP_92aIO  //## Inherits: <unnamed>%3AA7EE1F0290
{

  public:
      SPI_Response();

      SPI_Response(const SPI_Response &right);
      virtual ~SPI_Response();

      virtual size_t read (const string& fileName, bool readFlag = true);
      virtual SPI_Response* clone () const;
      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      virtual void closeSourceFiles (size_t index = 0);
      virtual bool readAuxResponse ();
      virtual const RealArray& efficiency () const;

    // Additional Public Declarations

  protected:
      virtual void setArrays ();
      virtual void setDescription (size_t specNum = 1, size_t groupNum = 1);

    // Additional Protected Declarations

  private:
      SPI_Response & operator=(const SPI_Response &right);

      void groupEbounds ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      RealArray m_efficiency;

    // Additional Implementation Declarations

};

// Class SPI_Response 

inline const RealArray& SPI_Response::efficiency () const
{
  return m_efficiency;
}


#endif
