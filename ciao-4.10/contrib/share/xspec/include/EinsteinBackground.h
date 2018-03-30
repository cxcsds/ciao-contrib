//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EINSTEINBACKGROUND_H
#define EINSTEINBACKGROUND_H 1

// SpectralData
#include <XSModel/Data/SpectralData.h>
// Background
#include <XSModel/Data/BackCorr/Background.h>
// EinsteinIO
#include <XSModel/DataFactory/EinsteinIO.h>




class EinsteinBackCorr : public BackCorr, //## Inherits: <unnamed>%39AD404503B7
                         	public EinsteinIO  //## Inherits: <unnamed>%39AD4074015A
{

  public:
      EinsteinBackCorr();

      EinsteinBackCorr(const EinsteinBackCorr &right);
      virtual ~EinsteinBackCorr();

      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      virtual EinsteinBackCorr* clone () const;
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
      EinsteinBackCorr & operator=(const EinsteinBackCorr &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



typedef EinsteinBackCorr EinsteinBackground;



typedef EinsteinBackCorr EinsteinCorrection;

// Class EinsteinBackCorr 


#endif
