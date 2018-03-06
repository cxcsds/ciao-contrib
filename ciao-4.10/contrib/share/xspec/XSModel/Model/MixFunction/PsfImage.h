//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PSFIMAGE_H
#define PSFIMAGE_H 1
#include "xsTypes.h"
#include <XSUtil/Utils/XSutility.h>

// Error
#include <XSUtil/Error/Error.h>




class PsfImage 
{

  public:



    class PsfImageError : public YellowAlert  //## Inherits: <unnamed>%3FCBBE6101AE
    {
      public:
          PsfImageError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      PsfImage (const string& fileName);
      ~PsfImage();

      void calcPsf (Real E, Real theta, Real phi, RealArray& psf);
      static size_t NDIM ();

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void readImage ();
      void initGoodArray ();
      static void rotSym (size_t i, size_t j, int irot, bool asym, size_t& ii, size_t& jj);
      static void getEnergyBracket (Real E, size_t& ie0, size_t& ie1, Real& fe);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_fileName;
      static const size_t s_NDIM;
      static const size_t s_NP;
      XSutility::auto_array_ptr<bool> m_pGood;
      XSutility::auto_array_ptr<Real> m_pAllPsf;

    // Additional Implementation Declarations
      static const Real s_energy[];
      static const size_t s_NE;
      static const Real s_thetas[];
      static const size_t s_nThetas;
      static const size_t s_nPhisMax;
      static const size_t s_nPhis[];
      static const Real s_phis[];
      static const size_t s_nPoint[];
      static const int s_iDetCent[];
};

// Class PsfImage::PsfImageError 

// Class PsfImage 


#endif
