//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIP_92ABACKGROUND_H
#define OGIP_92ABACKGROUND_H 1

// SpectralData
#include <XSModel/Data/SpectralData.h>
// Background
#include <XSModel/Data/BackCorr/Background.h>
// OGIP-92aIO
#include <XSModel/DataFactory/OGIP-92aIO.h>




class OGIP_92aBackCorr : public BackCorr, //## Inherits: <unnamed>%39AD400F029A
                         	public OGIP_92aIO  //## Inherits: a%39AD4068021A
{

  public:
      OGIP_92aBackCorr();

      OGIP_92aBackCorr(const OGIP_92aBackCorr &right);
      virtual ~OGIP_92aBackCorr();

      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      virtual OGIP_92aBackCorr* clone () const;
      virtual size_t read (const string& fileName, bool readFlag = true);
      void closeSourceFiles ();
      virtual void initialize (DataSet* parentData, size_t row, const string& fileName, size_t backCorRow);

    // Additional Public Declarations

  protected:
      virtual void setDescription (size_t spectrumNumber);
      //	source() != 0
      virtual void setArrays (size_t backgrndRow, bool correction = false);
      virtual void groupArrays (bool correction = false);
      virtual bool isCounts () const;

    // Additional Protected Declarations

  private:
      OGIP_92aBackCorr & operator=(const OGIP_92aBackCorr &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



typedef OGIP_92aBackCorr OGIP_92aBackground;



typedef OGIP_92aBackCorr OGIP_92aCorrection;

// Class OGIP_92aBackCorr 

inline bool OGIP_92aBackCorr::isCounts () const
{

  return OGIP_92aIO::isCounts();
}


#endif
