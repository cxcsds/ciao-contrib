//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIPTABLEDEFERREAD_H
#define OGIPTABLEDEFERREAD_H 1
#include <xsTypes.h>

// TableAccess
#include <XSModel/Model/Component/OGIPTable/TableAccess.h>
namespace CCfits {
   class ExtHDU;
}




class OGIPTableDeferRead : public TableAccess  //## Inherits: <unnamed>%46F4475D03C5
{

  public:
      OGIPTableDeferRead();
      virtual ~OGIPTableDeferRead();

      virtual OGIPTableDeferRead* clone ();
      virtual void initialRead (CCfits::ExtHDU& spectraExt, const size_t nEngs, const size_t nAddPars, const bool isSameAsPrev);
      virtual void initialAccessRows (const IntegerArray& rowNumbers, const size_t nAddPars);
      virtual void getSpectrumEntries (const size_t iEng, Real* values);
      virtual void getVarianceEntries (const size_t iEng, Real* values);
      virtual void getAddSpectra (const size_t iEng, const size_t iAdd, Real* values);
      virtual void getAddVariance (const size_t iEng, const size_t iAdd, Real* values);
      virtual bool isError () const;
      virtual const BoolArray& isAddParamError () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      OGIPTableDeferRead(const OGIPTableDeferRead &right);
      OGIPTableDeferRead & operator=(const OGIPTableDeferRead &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      TableValues m_tableVals;
      IntegerArray m_selectedRows;
      bool m_isError;
      BoolArray m_isAddParamError;
      //	It is necessary to store the table file location since
      //	this class will need to reopen the file each time
      //	readTableRows is called.
      string m_absPath;

    // Additional Implementation Declarations

};

// Class OGIPTableDeferRead 

inline bool OGIPTableDeferRead::isError () const
{
  return m_isError;
}

inline const BoolArray& OGIPTableDeferRead::isAddParamError () const
{
  return m_isAddParamError;
}


#endif
