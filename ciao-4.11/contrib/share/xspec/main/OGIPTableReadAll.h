//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIPTABLEREADALL_H
#define OGIPTABLEREADALL_H 1

// TableAccess
#include <XSModel/Model/Component/OGIPTable/TableAccess.h>




class OGIPTableReadAll : public TableAccess  //## Inherits: <unnamed>%46F4463F016B
{

  public:
      OGIPTableReadAll();
      virtual ~OGIPTableReadAll();

      virtual OGIPTableReadAll* clone ();
      virtual void initialRead (CCfits::ExtHDU& spectraExt, const size_t nEngs, const size_t nAddPars, const bool isSameAsPrev);
      virtual void initialAccessRows (const IntegerArray& rowNumbers, const size_t nAddPars);
      virtual void getSpectrumEntries (const size_t iEng, Real* values);
      virtual void getVarianceEntries (const size_t iEng, Real* values);
      virtual void getAddSpectra (const size_t iEng, const size_t iAdd, Real* values);
      virtual void getAddVariance (const size_t iEng, const size_t iAdd, Real* values);
      virtual bool isError () const;
      virtual const BoolArray& isAddParamError () const;
      const TableValues& tableVals () const;
      void tableVals (const TableValues& value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      OGIPTableReadAll(const OGIPTableReadAll &right);
      OGIPTableReadAll & operator=(const OGIPTableReadAll &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      IntegerArray m_selectedRows;
      bool m_isError;
      BoolArray m_isAddParamError;
      TableValues m_tableVals;
      static TableValues s_prevTable;

    // Additional Implementation Declarations

};

// Class OGIPTableReadAll 

inline bool OGIPTableReadAll::isError () const
{
  return m_isError;
}

inline const BoolArray& OGIPTableReadAll::isAddParamError () const
{
  return m_isAddParamError;
}

inline const TableValues& OGIPTableReadAll::tableVals () const
{
  return m_tableVals;
}

inline void OGIPTableReadAll::tableVals (const TableValues& value)
{
  m_tableVals = value;
}


#endif
