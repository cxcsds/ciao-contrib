//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SFIO_H
#define SFIO_H 1

// XspecDataIO
#include <XSModel/DataFactory/XspecDataIO.h>

//	See XspecDataIO for details.



class SfIO : public XspecDataIO  //## Inherits: <unnamed>%3AACF9890222
{

  public:
      virtual ~SfIO();

      virtual size_t read (const string& fileName, bool readFlag = true);
      virtual void write (const string& fileName);
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);

    // Additional Public Declarations

  protected:
      SfIO();

      virtual void channelBounds (int& startChannel, int& endChannel, size_t row = 0) const;
      void closeFile ();

    // Additional Protected Declarations

  private:
      SfIO & operator=(const SfIO &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class SfIO 

inline SfIO::~SfIO()
{
}



#endif
