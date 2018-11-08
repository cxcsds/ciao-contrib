//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EINSTEINRESPONSE_H
#define EINSTEINRESPONSE_H 1

// RealResponse
#include <XSModel/Data/Detector/RealResponse.h>
// EinsteinIO
#include <XSModel/DataFactory/EinsteinIO.h>




class EinsteinResponse : public RealResponse, //## Inherits: <unnamed>%376A617AE310
                         	public EinsteinIO  //## Inherits: <unnamed>%39A3ED4A0291
{

  public:
      EinsteinResponse();

      EinsteinResponse(const EinsteinResponse &right);
      virtual ~EinsteinResponse();

      virtual EinsteinResponse* clone () const;
      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      size_t read (const string& fileName, bool readFlag = true);
      void closeSourceFiles ();

    // Additional Public Declarations

  protected:
      virtual void groupQuality ();
      virtual void setArrays ();
      virtual void setDescription (size_t spectrumNumber = 1, size_t groupNumber = 1);

    // Additional Protected Declarations

  private:
      EinsteinResponse & operator=(const EinsteinResponse &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class EinsteinResponse 


#endif
