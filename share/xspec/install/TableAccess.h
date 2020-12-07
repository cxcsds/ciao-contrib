//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TABLEACCESS_H
#define TABLEACCESS_H 1
#include <xsTypes.h>
namespace CCfits {
   class ExtHDU;
}

//	Abstract Strategy pattern interface for performing table
//	model reads.



class TableAccess 
{

  public:
      virtual ~TableAccess();

      virtual TableAccess* clone () = 0;
      virtual void initialRead (CCfits::ExtHDU& spectraExt, const size_t nEngs, const size_t nAddPars, const bool isSameAsPrev) = 0;
      virtual bool isError () const = 0;
      virtual const BoolArray& isAddParamError () const = 0;
      virtual void initialAccessRows (const IntegerVector& rowNumbers, const size_t nAddPars) = 0;
      virtual void getSpectrumEntries (const size_t iEng, Real* values) = 0;
      virtual void getVarianceEntries (const size_t iEng, Real* values) = 0;
      virtual void getAddSpectra (const size_t iEng, const size_t iAdd, Real* values) = 0;
      virtual void getAddVariance (const size_t iEng, const size_t iAdd, Real* values) = 0;

    // Additional Public Declarations

  protected:
      TableAccess();

      TableAccess(const TableAccess &right);

    // Additional Protected Declarations

  private:
      TableAccess & operator=(const TableAccess &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};
//	This class is meant to simply bundle the various
//	INTPSPEC  arrays into one convenient place.  It is
//	designed for SPEED and NOT SAFETY.  Hence the use of
//	C-style arrays and no bounds checking.  It is left up to
//	the user to allocate arrays of precisely size nSpecRows
//	if and when a particular member array is needed.



struct TableValues 
{
      TableValues();

      TableValues(const TableValues &right);
      ~TableValues();
      TableValues & operator=(const TableValues &right);

      void clearAll ();

    // Data Members for Class Attributes
      std::vector<Real*> m_interpValues;
      std::vector<Real*> m_interpValueError;
      std::vector<std::vector<Real*> > m_addSpectra;
      std::vector<std::vector<Real*> > m_addSpectraError;
      size_t m_nSpecRows;

  public:
  protected:
  private:
      void copy (const TableValues& right);
      void swap (TableValues& right);

  private: //## implementation
};

// Class TableAccess 

// Class TableValues 


#endif
