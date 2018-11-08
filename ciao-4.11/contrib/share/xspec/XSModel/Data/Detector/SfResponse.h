//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SFRESPONSE_H
#define SFRESPONSE_H 1

// RealResponse
#include <XSModel/Data/Detector/RealResponse.h>
// SfIO
#include <XSModel/DataFactory/SfIO.h>




class SfResponse : public RealResponse, //## Inherits: <unnamed>%376A61B603F0
                   	public SfIO  //## Inherits: <unnamed>%39A3ED4E00A2
{

  public:
      SfResponse();

      SfResponse(const SfResponse &right);
      virtual ~SfResponse();

      virtual size_t read (const string& fileName, bool readFlag = true);
      virtual SfResponse* clone () const;
      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      void closeSourceFiles ();

    // Additional Public Declarations

  protected:
      virtual void setArrays ();
      virtual void setDescription (size_t spectrumNumber = 1, size_t groupNumber = 1);

    // Additional Protected Declarations

  private:
      SfResponse & operator=(const SfResponse &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class SfResponse 


#endif
