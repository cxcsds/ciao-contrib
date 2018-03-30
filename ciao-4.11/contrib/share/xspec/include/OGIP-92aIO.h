//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIP_92AIO_H
#define OGIP_92AIO_H 1
#include <XSModel/DataFactory/XspecDataIO.h>
#include <XSModel/Data/DataUtility.h>
namespace CCfits
{
  class FITS;
  class ExtHDU;
}

//	See XspecDataIO for details.



class OGIP_92aIO : public XspecDataIO  //## Inherits: <unnamed>%3AACF98E00CE
{

  public:



    class IncorrectDataType : public YellowAlert  //## Inherits: <unnamed>%3F7349720357
    {
      public:
          IncorrectDataType (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    typedef enum {COUNTS_COL,STATERR_COL,QUAL_COL,GROUP_COL,ASCALE_COL,BSCALE_COL,NOPTCOLS} OptCols;



    typedef enum {NO_STORE, KEYSTORE, COLSTORE} StorageType;

      virtual size_t read (const string& fileName, bool readFlag = true);
      virtual void write (const string& fileName);
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      const CCfits::FITS* dataSource (size_t index = 0) const;
      void setDataSource (CCfits::FITS* fitsObject, size_t index = 0);
      CCfits::FITS* dataSource (size_t index = 0);
      static int getKeyIntValue (CCfits::FITS* fitsFile, const string& keyWord);
      //	If fileName does not contain extended syntax or curly
      //	brackets, return the first extension that matches the
      //	keyword criteria given by the type, throw if none.  If
      //	using extended syntax OR curly bracket extver specifier,
      //	return the specific HDU only if it also has the proper
      //	keywords, otherwise throw. This will throw  if extended
      //	syntax and curly brackets are used together.  NOTE: this
      //	function always interprets curly brackets to mean extver
      //	and NOT row numbers.  Row number specifier should not be
      //	part of the fileName sent to this function.
      static std::auto_ptr<CCfits::FITS> openFitsExtension (const string& fileName, XspecDataIO::DataType type);
      OGIP_92aIO::StorageType  qualityStorage () const;
      OGIP_92aIO::StorageType groupingStorage () const;
      static std::pair<int,int> getChanInfoFromResponse (const string& fileName);
      int extVers () const;
      void extVers (int value);
      static const std::vector<std::string>& AuxResponseKeys ();
      static void AuxResponseKeys (const std::vector<std::string>& value);

  public:
    // Additional Public Declarations

  protected:
      OGIP_92aIO();

      OGIP_92aIO(const OGIP_92aIO &right);
      virtual ~OGIP_92aIO();

      virtual void channelBounds (int& startChannel, int& endChannel, size_t row = 0) const;
      int verifyQualGroup (const int startChan, const int endChan, IntegerArray& qual, IntegerArray& group, size_t row = 0);
      //	OGIP files have PHA array stored as counts or rate.
      //	This function returns true if it's counts.
      bool isCounts () const;
      bool specNum (CCfits::ExtHDU& hdu) const;
      void closeFile (size_t  index = 0);
      CCfits::Table* makeType1Table (string& hduName, size_t nChans, const BoolArray& optCols);
      CCfits::Table* makeType2Table (string& hduName, size_t nSpec, size_t nChans, const BoolArray& optCols);
      void getNetType ();
      //	Type of file can be TOTAL, NET, BKG. This returns true
      //	if it's NET.
      bool isNet () const;
      void getDataType ();
      void getQualGroupStorage (const string& keyword);
      void channelLimits (const size_t lowDefault, size_t& legalStart, size_t& legalEnd) const;
      static void readChannelBounds (CCfits::ExtHDU& ext, int& startChannel, int& endChannel, const size_t row);
      static void readChannelLimits (CCfits::ExtHDU& ext, const size_t lowDefault, size_t& legalStart, size_t& legalEnd);
      static const string& HDUCLASS ();
      //	Store the FITS header name. Set by fileFormat: avoids the
      //	need to open the file at the read stage.
      //
      //	NOTE: still need to find HDU for files which contain
      //	more than one extension of interest (e.g. responses
      //	which need MATRIX or its variants and EBOUNDS).
      const string& extensionName () const;
      void setExtensionName (const string& value);
      static const string& HDUVERS ();
      static const string& PHAVERSN ();
      static const string& VERSKEY ();
      static const string& SPECTYPE ();
      static const string& HDUCLAS1 ();
      static const string& RMFVERSN ();
      static const string& ARFVERSN ();
      static const string& OGIPVERS ();
      static const string& RESPTYPE ();
      static const string& SPECRESPTYPE ();
      static const string& HDUCLAS2 ();
      static const string& OGIPTYPE ();
      static const string& NUMKEY ();
      static const string& CHANNEL ();
      static const string& TELESCOPE ();
      static const string& INSTRUMENT ();
      static const string& BACKFILE ();
      static const string& RESPFILE ();
      static const string& CORRFILE ();
      static const string& ANCRFILE ();
      static const string& AREASCALE ();
      static const string& BACKSCALE ();
      static const string& CORRSCALE ();
      static const string& EXPOSURE ();
      static const string& FILTER ();
      static const string& GROUPING ();
      static const string& QUALITY ();
      static const size_t& MAXFILTER ();
      static const string& CHANNELTYPE ();
      static const string& COUNTS ();
      static const string& RATE ();
      static const string& SYSTEMATIC ();
      static const string& STATISTICAL ();
      static const string& POISSERR ();
      static const string& MINENERGY ();
      static const string& MAXENERGY ();
      static const string& ENERGYLO ();
      static const string& ENERGYHI ();
      static const string& NGROUP ();
      static const string& NCHANNEL ();
      static const string& FCHANNEL ();
      static const string& MATRIX ();
      static const string& DETNAM ();
      static const string& DETCHANS ();
      static const string& RSPVERSN ();
      static const string& EBOUNDS ();
      static const string& RSPMATRIXTYPE ();
      static const string& HDUCLAS3 ();
      static const string& GSLOP_MIN ();
      static const string& GSLOP_MAX ();
      static const string& GOFFS_MIN ();
      static const string& GOFFS_MAX ();
      void net (bool value);
      bool netIsSet () const;
      void netIsSet (bool value);
      void qualityStorage (OGIP_92aIO::StorageType value);
      void groupingStorage (OGIP_92aIO::StorageType value);
      static const std::vector<std::string>& ResponseKeys ();
      const std::vector<CCfits::FITS*>& getDataSource () const;
      void setDataSource (const std::vector<CCfits::FITS*>& value);
      static const std::vector<std::string>& typeIColNames ();
      static const std::vector<std::string>& typeIColForms ();
      static const std::vector<std::string>& typeIColUnits ();

    // Additional Protected Declarations

  private:
      OGIP_92aIO & operator=(const OGIP_92aIO &right);

      //	A private utility function used by openFitsExtension,
      //	this calls the appropriate FITS constructor based on
      //	whether there's extended syntax in the filename, and
      //	also verifies the search key values.  This may throw Fits
      //	Exceptions.  If using extended syntax and the indicated
      //	HDU is found but doesn't have the proper search keys, a
      //	null pointer is returned.
      //
      //	When using extended syntax, extVers will be modified to
      //	match the value in the HDU given by the extended name.
      //	For regular filenames, extVers is read-only and will be
      //	used along with the searchKeys to pinpoint the specific
      //	HDU.
      static CCfits::FITS* callFITSctor (const string& filename, const StringArray& searchKeys, const StringArray& searchVals, const bool isExtended, int& extVers);
      static std::vector<std::string>& SpectrumKeys ();
      static void SpectrumKeys (const std::vector<std::string>& value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_HDUCLASS;
      string m_extensionName;
      static const string s_HDUVERS;
      static const string s_PHAVERSN;
      static const string s_VERSKEY;
      static const string s_SPECTYPE;
      static const string s_HDUCLAS1;
      static const string s_RMFVERSN;
      static const string s_ARFVERSN;
      static const string s_OGIPVERS;
      static const string s_RESPTYPE;
      static const string s_SPECRESPTYPE;
      static const string s_HDUCLAS2;
      static const string s_OGIPTYPE;
      static const string s_NUMKEY;
      static const string s_CHANNEL;
      static const string s_TELESCOPE;
      static const string s_INSTRUMENT;
      static const string s_BACKFILE;
      static const string s_RESPFILE;
      static const string s_CORRFILE;
      static const string s_ANCRFILE;
      static const string s_AREASCALE;
      static const string s_BACKSCALE;
      static const string s_CORRSCALE;
      static const string s_EXPOSURE;
      static const string s_FILTER;
      static const string s_GROUPING;
      static const string s_QUALITY;
      static const size_t s_MAXFILTER;
      static const string s_CHANNELTYPE;
      static const string s_COUNTS;
      static const string s_RATE;
      static const string s_SYSTEMATIC;
      static const string s_STATISTICAL;
      static const string s_POISSERR;
      static const string s_MINENERGY;
      static const string s_MAXENERGY;
      static const string s_ENERGYLO;
      static const string s_ENERGYHI;
      static const string s_NGROUP;
      static const string s_NCHANNEL;
      static const string s_FCHANNEL;
      static const string s_MATRIX;
      static const string s_DETNAM;
      static const string s_DETCHANS;
      static const string s_RSPVERSN;
      static const string s_EBOUNDS;
      static const string s_RSPMATRIXTYPE;
      static const string s_HDUCLAS3;
      static const string s_GSLOP_MIN;
      static const string s_GSLOP_MAX;
      static const string s_GOFFS_MIN;
      static const string s_GOFFS_MAX;
      bool m_net;
      bool m_counts;
      bool m_netIsSet;
      OGIP_92aIO::StorageType m_qualityStorage;
      OGIP_92aIO::StorageType m_groupingStorage;
      int m_extVers;

    // Data Members for Associations
      static std::vector<std::string> s_SpectrumKeys;
      static std::vector<std::string> s_ResponseKeys;
      std::vector<CCfits::FITS*> m_dataSource;
      static std::vector<std::string> s_AuxResponseKeys;
      static std::vector<std::string> s_typeIColNames;
      static std::vector<std::string> s_typeIColForms;
      static std::vector<std::string> s_typeIColUnits;

    // Additional Implementation Declarations
    friend class DataUtility;
};

// Class OGIP_92aIO::IncorrectDataType 

// Class OGIP_92aIO 

inline OGIP_92aIO::StorageType  OGIP_92aIO::qualityStorage () const
{
  return m_qualityStorage;
}

inline OGIP_92aIO::StorageType OGIP_92aIO::groupingStorage () const
{
  return m_groupingStorage;
}

inline const string& OGIP_92aIO::HDUCLASS ()
{
  return s_HDUCLASS;
}

inline const string& OGIP_92aIO::extensionName () const
{
  return m_extensionName;
}

inline void OGIP_92aIO::setExtensionName (const string& value)
{
  m_extensionName = value;
}

inline const string& OGIP_92aIO::HDUVERS ()
{
  return s_HDUVERS;
}

inline const string& OGIP_92aIO::PHAVERSN ()
{
  return s_PHAVERSN;
}

inline const string& OGIP_92aIO::VERSKEY ()
{
  return s_VERSKEY;
}

inline const string& OGIP_92aIO::SPECTYPE ()
{
  return s_SPECTYPE;
}

inline const string& OGIP_92aIO::HDUCLAS1 ()
{
  return s_HDUCLAS1;
}

inline const string& OGIP_92aIO::RMFVERSN ()
{
  return s_RMFVERSN;
}

inline const string& OGIP_92aIO::ARFVERSN ()
{
  return s_ARFVERSN;
}

inline const string& OGIP_92aIO::OGIPVERS ()
{
  return s_OGIPVERS;
}

inline const string& OGIP_92aIO::RESPTYPE ()
{
  return s_RESPTYPE;
}

inline const string& OGIP_92aIO::SPECRESPTYPE ()
{
  return s_SPECRESPTYPE;
}

inline const string& OGIP_92aIO::HDUCLAS2 ()
{
  return s_HDUCLAS2;
}

inline const string& OGIP_92aIO::OGIPTYPE ()
{
  return s_OGIPTYPE;
}

inline const string& OGIP_92aIO::NUMKEY ()
{
  return s_NUMKEY;
}

inline const string& OGIP_92aIO::CHANNEL ()
{
  return s_CHANNEL;
}

inline const string& OGIP_92aIO::TELESCOPE ()
{
  return s_TELESCOPE;
}

inline const string& OGIP_92aIO::INSTRUMENT ()
{
  return s_INSTRUMENT;
}

inline const string& OGIP_92aIO::BACKFILE ()
{
  return s_BACKFILE;
}

inline const string& OGIP_92aIO::RESPFILE ()
{
  return s_RESPFILE;
}

inline const string& OGIP_92aIO::CORRFILE ()
{
  return s_CORRFILE;
}

inline const string& OGIP_92aIO::ANCRFILE ()
{
  return s_ANCRFILE;
}

inline const string& OGIP_92aIO::AREASCALE ()
{
  return s_AREASCALE;
}

inline const string& OGIP_92aIO::BACKSCALE ()
{
  return s_BACKSCALE;
}

inline const string& OGIP_92aIO::CORRSCALE ()
{
  return s_CORRSCALE;
}

inline const string& OGIP_92aIO::EXPOSURE ()
{
  return s_EXPOSURE;
}

inline const string& OGIP_92aIO::FILTER ()
{
  return s_FILTER;
}

inline const string& OGIP_92aIO::GROUPING ()
{
  return s_GROUPING;
}

inline const string& OGIP_92aIO::QUALITY ()
{
  return s_QUALITY;
}

inline const size_t& OGIP_92aIO::MAXFILTER ()
{
  return s_MAXFILTER;
}

inline const string& OGIP_92aIO::CHANNELTYPE ()
{
  return s_CHANNELTYPE;
}

inline const string& OGIP_92aIO::COUNTS ()
{
  return s_COUNTS;
}

inline const string& OGIP_92aIO::RATE ()
{
  return s_RATE;
}

inline const string& OGIP_92aIO::SYSTEMATIC ()
{
  return s_SYSTEMATIC;
}

inline const string& OGIP_92aIO::STATISTICAL ()
{
  return s_STATISTICAL;
}

inline const string& OGIP_92aIO::POISSERR ()
{
  return s_POISSERR;
}

inline const string& OGIP_92aIO::MINENERGY ()
{
  return s_MINENERGY;
}

inline const string& OGIP_92aIO::MAXENERGY ()
{
  return s_MAXENERGY;
}

inline const string& OGIP_92aIO::ENERGYLO ()
{
  return s_ENERGYLO;
}

inline const string& OGIP_92aIO::ENERGYHI ()
{
  return s_ENERGYHI;
}

inline const string& OGIP_92aIO::NGROUP ()
{
  return s_NGROUP;
}

inline const string& OGIP_92aIO::NCHANNEL ()
{
  return s_NCHANNEL;
}

inline const string& OGIP_92aIO::FCHANNEL ()
{
  return s_FCHANNEL;
}

inline const string& OGIP_92aIO::MATRIX ()
{
  return s_MATRIX;
}

inline const string& OGIP_92aIO::DETNAM ()
{
  return s_DETNAM;
}

inline const string& OGIP_92aIO::DETCHANS ()
{
  return s_DETCHANS;
}

inline const string& OGIP_92aIO::RSPVERSN ()
{
  return s_RSPVERSN;
}

inline const string& OGIP_92aIO::EBOUNDS ()
{
  return s_EBOUNDS;
}

inline const string& OGIP_92aIO::RSPMATRIXTYPE ()
{
  return s_RSPMATRIXTYPE;
}

inline const string& OGIP_92aIO::HDUCLAS3 ()
{
  return s_HDUCLAS3;
}

inline const string& OGIP_92aIO::GSLOP_MIN ()
{
  return s_GSLOP_MIN;
}

inline const string& OGIP_92aIO::GSLOP_MAX ()
{
  return s_GSLOP_MAX;
}

inline const string& OGIP_92aIO::GOFFS_MIN ()
{
  return s_GOFFS_MIN;
}

inline const string& OGIP_92aIO::GOFFS_MAX ()
{
  return s_GOFFS_MAX;
}

inline void OGIP_92aIO::net (bool value)
{
  m_net = value;
}

inline bool OGIP_92aIO::netIsSet () const
{
  return m_netIsSet;
}

inline void OGIP_92aIO::netIsSet (bool value)
{
  m_netIsSet = value;
}

inline void OGIP_92aIO::qualityStorage (OGIP_92aIO::StorageType value)
{
  m_qualityStorage = value;
}

inline void OGIP_92aIO::groupingStorage (OGIP_92aIO::StorageType value)
{
  m_groupingStorage = value;
}

inline int OGIP_92aIO::extVers () const
{
  return m_extVers;
}

inline void OGIP_92aIO::extVers (int value)
{
  m_extVers = value;
}

inline std::vector<std::string>& OGIP_92aIO::SpectrumKeys ()
{
  return s_SpectrumKeys;
}

inline void OGIP_92aIO::SpectrumKeys (const std::vector<std::string>& value)
{
  s_SpectrumKeys = value;
}

inline const std::vector<std::string>& OGIP_92aIO::ResponseKeys ()
{
  return s_ResponseKeys;
}

inline const std::vector<CCfits::FITS*>& OGIP_92aIO::getDataSource () const
{
  return m_dataSource;
}

inline void OGIP_92aIO::setDataSource (const std::vector<CCfits::FITS*>& value)
{
  m_dataSource = value;
}

inline const std::vector<std::string>& OGIP_92aIO::AuxResponseKeys ()
{
  return s_AuxResponseKeys;
}

inline void OGIP_92aIO::AuxResponseKeys (const std::vector<std::string>& value)
{
  s_AuxResponseKeys = value;
}

inline const std::vector<std::string>& OGIP_92aIO::typeIColNames ()
{
  return s_typeIColNames;
}

inline const std::vector<std::string>& OGIP_92aIO::typeIColForms ()
{
  return s_typeIColForms;
}

inline const std::vector<std::string>& OGIP_92aIO::typeIColUnits ()
{
  return s_typeIColUnits;
}


#endif
