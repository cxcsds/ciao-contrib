//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ASCIICHAIN_H
#define ASCIICHAIN_H 1

// ChainIO
#include <XSFit/MCMC/ChainIO.h>

class Chain;
#include <fstream>




class AsciiChain : public ChainIO  //## Inherits: <unnamed>%46DD7C75006B
{

  public:
      AsciiChain (string fileName = string(""));
      virtual ~AsciiChain();

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
      virtual void adjustLengthInfo ();
      virtual void appendFile (RealArray& startingVals);
      virtual void appendFile (RealArray& startingVals, Real& startingStatVal);
      virtual void adjustTemperInfo ();
      virtual bool checkTemperField (const Real temperature) const;
      virtual void setParent (Chain* chain);
      virtual bool allowsTemper () const;
      static const string& FORMATNAME ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      AsciiChain(const AsciiChain &right);
      AsciiChain & operator=(const AsciiChain &right);

      void moveToLine (const size_t lineNum) const;
      string readTemperInfo ();
      void testFile (const string& fileName) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const size_t s_LENGTHFIELDWIDTH;
      static const int s_TEMPERFIELDWIDTH;
      static const string s_FORMATNAME;
      static const string s_CHAINTYPE;
      static const string s_NWALKERS;
      mutable std::fstream m_file;
      std::fstream::pos_type m_lengthInfoPos;
      std::fstream::pos_type m_pointsStartPos;
      std::fstream::pos_type m_temperInfoPos;
      //	Pointer to the Chain object which owns this object.
      //	This obviously must be a non-owning pointer or else it
      //	will be a circular dependency.
      Chain* m_chain;

    // Additional Implementation Declarations

};

// Class AsciiChain 

inline const string& AsciiChain::FORMATNAME ()
{
  return s_FORMATNAME;
}


#endif
