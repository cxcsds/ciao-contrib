//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PSFTRAITS_H
#define PSFTRAITS_H 1
#include <xsTypes.h>
#include <string>


template <typename T> class Psf;
template <typename T> class PsfRegion;

//	These are essentially combined traits and policy
//	classes, since it's difficult to imagine a future case
//	where one would want these uncoupled (ie. XMM string
//	labels with Suzaku psf calculation method).



class XMM 
{

  public:
      static void pointSpreadFunction (Psf<XMM>& psf, size_t iObs, size_t iReg, int ixb, int iyb, size_t iEng);
      static void readSpecificMapKeys (PsfRegion<XMM>& region);

    // Data Members for Class Attributes
      static const string keywordRoot;

    // Additional Public Declarations
      static const size_t NE;
      static const Real psfEnergy[];
  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



class Suzaku 
{

  public:
      static void pointSpreadFunction (Psf<Suzaku>& psf, size_t iObs, size_t iReg, int ixb, int iyb, size_t iEng);
      static void readSpecificMapKeys (PsfRegion<Suzaku>& region);

    // Data Members for Class Attributes
      static const string keywordRoot;

    // Additional Public Declarations
      static const size_t NE;
      static const Real psfEnergy[];
  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class XMM 

// Class Suzaku 


#endif
