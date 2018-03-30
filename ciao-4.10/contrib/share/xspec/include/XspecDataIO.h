//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSPECDATAIO_H
#define XSPECDATAIO_H 1

// Error
#include <XSUtil/Error/Error.h>

class SpectralData;

//	XspecIO is an interface to be attached to Data classes
//	requiring that they define a read() and write()
//	operation.
//
//	The subclasses, which are data format specific, supply a
//	default implementation for each type, which will
//	read/write the spectrum information for each data
//	format. This will take care of the DataSet, Background,
//	and Correction file read/writes. They will then be
//	overridden in the Response read/write operations.
//
//	Also, OGIP2 may override the default implementation for
//	OGIP. Both read/write operations must be virtual.
//
//	In Xspec 11-, write() operations are scarce. It is
//	intended that the write() operation for SfIO produces
//	OGIP format output. The OGIP write() operation can also
//	be reused for writing FakeData. Einstein SSS data could
//	also be EOLed by writing the data as OGIP.



class XspecDataIO 
{
  public:



    class CannotOpen : public YellowAlert  //## Inherits: <unnamed>%39A3F55D025C
    {
      public:
          CannotOpen();
          CannotOpen (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    typedef enum {SpectrumType,ResponseType,AuxResponseType} DataType;



    class RequiredDataNotPresent : public YellowAlert  //## Inherits: <unnamed>%3A2D33350307
    {
      public:
          RequiredDataNotPresent (const string& diag);

      protected:
      private:
      private: //## implementation
    };
    //	Exception to be thrown if the user tried to specify
    //	spectrum numbers to read from a file containing a single
    //	spectrum.
    //	This exception will be absorbed silently (spectrum
    //	number ignored): its function is to halt the loop after
    //	the spectrum is read in the case that the user specified
    //	multiple spectra
    //	from the file.



    class SingleSpectrumOnly : public YellowAlert  //## Inherits: <unnamed>%3A02EA0900A9
    {
      public:
          SingleSpectrumOnly (const string& diag);

      protected:
      private:
      private: //## implementation
    };
    //	Exception to be thrown if the data file contains multiple
    //	spectra and the user did not specify which is to be read.



    class UnspecifiedSpectrumNumber : public YellowAlert  //## Inherits: <unnamed>%3A02EA1602D1
    {
      public:
          UnspecifiedSpectrumNumber (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class CatchAllIO : public YellowAlert  //## Inherits: <unnamed>%3EA40A710299
    {
      public:
          CatchAllIO (const string& msg);

      protected:
      private:
      private: //## implementation
    };

      virtual size_t read (const string& fileName, bool readFlag = true) = 0;
      virtual void write (const string& fileName) = 0;
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType) = 0;

  public:
  protected:
      XspecDataIO();
      virtual ~XspecDataIO() = 0;

      //	Function to find the channel bounds in the analysis
      //	version of the data
      //	read from the source file.
      //
      //	The array size is modified from the total number of
      //	data lines read by possible start/end channel keywords
      //	(TLMINn, TLMAXn in OGIP files, where n is the
      //	number of the column with the channel numbers).
      virtual void channelBounds (int& startChannel, int& endChannel, size_t row = 0) const = 0;

  private:
      XspecDataIO & operator=(const XspecDataIO &right);

  private: //## implementation
};

// Class XspecDataIO::CannotOpen 

// Class XspecDataIO::RequiredDataNotPresent 

// Class XspecDataIO::SingleSpectrumOnly 

// Class XspecDataIO::UnspecifiedSpectrumNumber 

// Class XspecDataIO::CatchAllIO 

// Class XspecDataIO 


#endif
