//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SFBACKGROUND_H
#define SFBACKGROUND_H 1

// Background
#include <XSModel/Data/BackCorr/Background.h>
// SfIO
#include <XSModel/DataFactory/SfIO.h>




class SfBackCorr : public BackCorr, //## Inherits: <unnamed>%39AD402C021D
                   	public SfIO  //## Inherits: <unnamed>%39AD40820085
{

  public:
      SfBackCorr();

      SfBackCorr(const SfBackCorr &right);
      virtual ~SfBackCorr();

      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      virtual SfBackCorr* clone () const;
      virtual size_t read (const string& fileName, bool readFlag = true);
      void closeSourceFiles ();
      virtual void initialize (DataSet* parentData, size_t row, const string& fileName, size_t backCorRow);

    // Additional Public Declarations

  protected:
      virtual void setDescription (size_t spectrumNumber = 1);
      virtual void scaleArrays (bool correction = false);
      virtual void setArrays (size_t backgrndRow, bool ignoreStats = false);

    // Additional Protected Declarations

  private:
      SfBackCorr & operator=(const SfBackCorr &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



typedef SfBackCorr SfBackground;



typedef SfBackCorr SfCorrection;

// Class SfBackCorr 


#endif
