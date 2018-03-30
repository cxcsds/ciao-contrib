//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIP_92ARESPONSE_H
#define OGIP_92ARESPONSE_H 1

// RealResponse
#include <XSModel/Data/Detector/RealResponse.h>
// OGIP-92aIO
#include <XSModel/DataFactory/OGIP-92aIO.h>




class OGIP_92aResponse : public RealResponse, //## Inherits: <unnamed>%376A619EBE20
                         	public OGIP_92aIO  //## Inherits: <unnamed>%39A3ED4701A4
{

  public:
      OGIP_92aResponse();

      OGIP_92aResponse(const OGIP_92aResponse &right);
      virtual ~OGIP_92aResponse();

      virtual size_t read (const string& fileName, bool readFlag = true);
      virtual OGIP_92aResponse* clone () const;
      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      void closeSourceFiles ();
      virtual bool readAuxResponse (int rowNum = -1);

    // Additional Public Declarations

  protected:
      virtual void setArrays ();
      virtual void setDescription (size_t specNum = 1, size_t groupNum = 1);

    // Additional Protected Declarations

  private:
      OGIP_92aResponse & operator=(const OGIP_92aResponse &right);

      void groupEbounds ();

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class OGIP_92aResponse 


#endif
