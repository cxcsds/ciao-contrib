//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CHAINIO_H
#define CHAINIO_H 1

// Error
#include <XSUtil/Error/Error.h>
class Chain;

#include <xsTypes.h>




class ChainIO 
{

  public:



    class ChainIOError : public YellowAlert  //## Inherits: <unnamed>%46DD738A00DE
    {
      public:
          ChainIOError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      virtual ~ChainIO();

      virtual void doOpenForReadPoints () const = 0;
      virtual void doCloseFile () const = 0;
      virtual void doOpenForWrite () = 0;
      virtual void doReadPoint (std::vector<Real>& chainVals) const = 0;
      virtual void doReadPointFromLine (size_t lineNum, RealArray& parVals) const = 0;
      virtual void doReadPointFromLine (size_t lineNum, RealArray& parVals, Real& statVal) const = 0;
      virtual const string& getFormatName () const = 0;
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
      static const int& TEMPERPREC ();
      static const int FWIDTH ();

  public:
    // Additional Public Declarations

  protected:
      ChainIO();
      static const string& LENGTHLABEL ();
      static const string& WIDTHLABEL ();
      static const int& PRECISION ();
      static const string& TEMPERLABEL ();

    // Additional Protected Declarations

  private:
      ChainIO(const ChainIO &right);
      ChainIO & operator=(const ChainIO &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_LENGTHLABEL;
      static const string s_WIDTHLABEL;
      static const int s_PRECISION;
      static const string s_TEMPERLABEL;
      static const int s_TEMPERPREC;
      static const int s_FWIDTH;

    // Additional Implementation Declarations

};

// Class ChainIO::ChainIOError 

// Class ChainIO 

inline ChainIO::ChainIO()
{
}


inline ChainIO::~ChainIO()
{
}


inline const string& ChainIO::LENGTHLABEL ()
{
  return s_LENGTHLABEL;
}

inline const string& ChainIO::WIDTHLABEL ()
{
  return s_WIDTHLABEL;
}

inline const int& ChainIO::PRECISION ()
{
  return s_PRECISION;
}

inline const string& ChainIO::TEMPERLABEL ()
{
  return s_TEMPERLABEL;
}

inline const int& ChainIO::TEMPERPREC ()
{
  return s_TEMPERPREC;
}

inline const int ChainIO::FWIDTH ()
{
  return s_FWIDTH;
}


#endif
