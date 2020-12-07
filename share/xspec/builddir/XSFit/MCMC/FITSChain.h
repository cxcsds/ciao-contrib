//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef FITSCHAIN_H
#define FITSCHAIN_H 1

// ChainIO
#include <XSFit/MCMC/ChainIO.h>

namespace CCfits {
    class FITS;
} // namespace CCfits

class Chain;
namespace CCfits {
   class Table;
}




class FITSChain : public ChainIO  //## Inherits: <unnamed>%46DD852400C2
{

  public:
      FITSChain (string fileName = string(""));
      virtual ~FITSChain();

      virtual void doOpenForReadPoints () const;
      virtual void doCloseFile () const;
      virtual void doOpenForWrite ();
      virtual void doReadPoint (std::vector<Real>& chainVals) const;
      virtual void doReadPointFromLine (size_t lineNum, RealArray& parVals) const;
      virtual void doReadPointFromLine (size_t lineNum, RealArray& parVals, Real& statVal) const;
      virtual const string& getFormatName () const;
      virtual void readFileInfo ();
      virtual void createFile ();
      virtual void writePoint ();
      virtual void writePoint (RealArray& paramVals, Real& statVal);
      virtual void writeFileInfo ();
      virtual void appendFile (RealArray& startingVals);
      virtual void appendFile (RealArray& startingVals, Real& startingStatVal);
      virtual void adjustTemperInfo ();
      virtual bool checkTemperField (const Real temperature) const;
      virtual void setParent (Chain* chain);
      static const string& FORMATNAME ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      FITSChain(const FITSChain &right);
      FITSChain & operator=(const FITSChain &right);

      static string intToKeyIndex (int iEntry);
      void readTemperInfo (CCfits::Table* table);
      void readParamInfo (CCfits::Table* table);
      void writeHistory (bool isAppend) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_FORMATNAME;
      static const string s_EXTNAME;
      static const string s_TEMPERKEY;
      static const string s_ROWKEY;
      static const string s_FLOATTYPE;
      static const string s_STATCOL;
      static const size_t s_TEMPERDIGITS;
      static const string s_COLNAMEDELIM;
      static const string s_CHAINTYP;
      static const string s_NWALKERS;
      //	Pointer to the Chain object which owns this object.
      //	This obviously must be a non-owning pointer or else it
      //	will be a circular dependency.
      Chain* m_chain;
      mutable long m_iRow;
      bool m_doFileFlush;

    // Data Members for Associations
      //	Opaque pointer to FITS object
      mutable CCfits::FITS* m_fits;

    // Additional Implementation Declarations

};

// Class FITSChain 

inline const string& FITSChain::FORMATNAME ()
{
  return s_FORMATNAME;
}


#endif
