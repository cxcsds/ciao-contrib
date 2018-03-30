//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OGIPTABLE_H
#define OGIPTABLE_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// TableComponent
#include <XSModel/Model/Component/TableComponent.h>

class UniqueEnergy;
class TableAccess;
struct TableValues;
class ModParam;
class TableModParam;




class OGIPTable : public TableComponent  //## Inherits: <unnamed>%3D2EE1AB030B
{

  public:
      OGIPTable (const string& nameString, Component* p = 0);
      virtual ~OGIPTable();

      //	If p is a valid Component pointer, isAddRequest argument
      //	is irrelevant.  It only needs to be filled to verify Add
      //	or Mult type when TableComponent is used in isolation,
      //	and there is no owning Component.
      virtual void read (bool readSpectralData, Component* p, bool isAddRequest = true);
      virtual OGIPTable* clone (Component* parent) const;
      virtual bool formatCheck (const string& fileName);
      virtual void energyWeights (const UniqueEnergy* uniqueEng);
      virtual void clearArrays (const std::set<UniqueEnergy*>& currentEngs);
      //	Interpolation tables with fewer elements than this will
      //	be read in their entirety and saved in RAM.  For larger
      //	tables only the necessary rows will be read, on the fly.
      static long MEM_THRESHOLD ();

    // Additional Public Declarations

  protected:
      virtual void getInterpolantIndices ();
      virtual std::pair<Real,Real> energyPoint (size_t energyIndex, const RealArray& fraction, TableValues& workspace);
      virtual void getInterpolant (RealArray& spectrum, RealArray& variance);
      //	rebin model component fluxes using weighting array.
      virtual void rebinComponent (const UniqueEnergy* uniqueEng, const RealArray& inputArray, RealArray& outputArray, bool variance);
      //	rebin model component fluxes using weighting array.
      virtual void interpolateComponent (const UniqueEnergy* uniqueEng, const RealArray& inputArray, RealArray& outputArray, bool exponential);
      virtual void setParamPointersFromCopy ();
      static const string& MODLNAME ();
      static const string& MODLUNIT ();
      static const string& REDSHIFT ();
      static const string& ADDMODEL ();
      static const string& HDUCLASS ();
      static const string& HDUCLAS1 ();
      static const string& HDUVERS ();
      static const string& NINTPARM ();
      static const string& NADDPARM ();
      static const string& NAME ();
      static const string& METHOD ();
      static const string& INITIAL ();
      static const string& DELTA ();
      static const string& MINIMUM ();
      static const string& BOTTOM ();
      static const string& TOP ();
      static const string& MAXIMUM ();
      static const string& NUMBVALS ();
      static const string& VALUE ();
      static const string& HDUCLAS2 ();
      static const string& ENERG_LO ();
      static const string& ENERG_HI ();
      static const string& PARAMVAL ();
      static const string& INTPSPEC ();
      static const string& UNITS ();
      static const string& HDUVERS1 ();
      static const string& LOWELIMIT ();
      static const string& HIGHELIMIT ();
      const std::vector<TableModParam*>& interParam () const;
      void interParam (const std::vector<TableModParam*>& value);
      const BoolArray& exact () const;
      void setExact (const BoolArray& value);
      const IntegerArray& recordNumbers () const;
      void setRecordNumbers (const IntegerArray& value);
      const IntegerArray& bracket () const;
      void setBracket (const IntegerArray& value);
      const std::vector<ModParam*>& addParam () const;
      void addParam (const std::vector<ModParam*>& value);
      const Real lowELim () const;
      void setLowELim (const Real value);
      const Real highELim () const;
      void setHighELim (const Real value);

    // Additional Protected Declarations

  private:
      OGIPTable(const OGIPTable &right);
      OGIPTable & operator=(const OGIPTable &right);
      RealArray& startWeight (const UniqueEnergy* uniqueEng);
      RealArray& endWeight (const UniqueEnergy* uniqueEng);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_MODLNAME;
      static const string s_MODLUNIT;
      static const string s_REDSHIFT;
      static const string s_ADDMODEL;
      static const string s_HDUCLASS;
      static const string s_HDUCLAS1;
      static const string s_HDUVERS;
      static const string s_NINTPARM;
      static const string s_NADDPARM;
      static const string s_NAME;
      static const string s_METHOD;
      static const string s_INITIAL;
      static const string s_DELTA;
      static const string s_MINIMUM;
      static const string s_BOTTOM;
      static const string s_TOP;
      static const string s_MAXIMUM;
      static const string s_NUMBVALS;
      static const string s_VALUE;
      static const string s_HDUCLAS2;
      static const string s_ENERG_LO;
      static const string s_ENERG_HI;
      static const string s_PARAMVAL;
      static const string s_INTPSPEC;
      static bool s_init;
      static const string s_UNITS;
      static const string s_HDUVERS1;
      static const Real FUZZY;
      static const long s_MEM_THRESHOLD;
      static const string s_LOWELIMIT;
      static const string s_HIGHELIMIT;
      //	Absolute path to the most recently opened table model
      //	file.
      static string s_prevFile;

    // Data Members for Associations
      static std::vector<std::string> s_paramStrings;
      static std::vector<std::string> s_energyStrings;
      static std::vector<std::string> s_spectrumStrings;
      static std::vector<std::string> s_hduPrimary;
      static std::vector<std::string> s_hduNames;
      std::vector<TableModParam*> m_interParam;
      BoolArray m_exact;
      std::map<const UniqueEnergy*,RealArray> m_startWeight;
      std::map<const UniqueEnergy*,RealArray> m_endWeight;
      std::map<const UniqueEnergy*,IntegerArray> m_startWeightBin;
      std::map<const UniqueEnergy*,IntegerArray> m_endWeightBin;
      IntegerArray m_recordNumbers;
      IntegerArray m_bracket;
      std::vector<ModParam*> m_addParam;
      Real m_lowELim;
      Real m_highELim;
      //	Opaque pointer to strategy for interp table reading
      TableAccess* m_readStrategy;

    // Additional Implementation Declarations

};

// Class OGIPTable 

inline const string& OGIPTable::MODLNAME ()
{
  return s_MODLNAME;
}

inline const string& OGIPTable::MODLUNIT ()
{
  return s_MODLUNIT;
}

inline const string& OGIPTable::REDSHIFT ()
{
  return s_REDSHIFT;
}

inline const string& OGIPTable::ADDMODEL ()
{
  return s_ADDMODEL;
}

inline const string& OGIPTable::HDUCLASS ()
{
  return s_HDUCLASS;
}

inline const string& OGIPTable::HDUCLAS1 ()
{
  return s_HDUCLAS1;
}

inline const string& OGIPTable::HDUVERS ()
{
  return s_HDUVERS;
}

inline const string& OGIPTable::NINTPARM ()
{
  return s_NINTPARM;
}

inline const string& OGIPTable::NADDPARM ()
{
  return s_NADDPARM;
}

inline const string& OGIPTable::NAME ()
{
  return s_NAME;
}

inline const string& OGIPTable::METHOD ()
{
  return s_METHOD;
}

inline const string& OGIPTable::INITIAL ()
{
  return s_INITIAL;
}

inline const string& OGIPTable::DELTA ()
{
  return s_DELTA;
}

inline const string& OGIPTable::MINIMUM ()
{
  return s_MINIMUM;
}

inline const string& OGIPTable::BOTTOM ()
{
  return s_BOTTOM;
}

inline const string& OGIPTable::TOP ()
{
  return s_TOP;
}

inline const string& OGIPTable::MAXIMUM ()
{
  return s_MAXIMUM;
}

inline const string& OGIPTable::NUMBVALS ()
{
  return s_NUMBVALS;
}

inline const string& OGIPTable::VALUE ()
{
  return s_VALUE;
}

inline const string& OGIPTable::HDUCLAS2 ()
{
  return s_HDUCLAS2;
}

inline const string& OGIPTable::ENERG_LO ()
{
  return s_ENERG_LO;
}

inline const string& OGIPTable::ENERG_HI ()
{
  return s_ENERG_HI;
}

inline const string& OGIPTable::PARAMVAL ()
{
  return s_PARAMVAL;
}

inline const string& OGIPTable::INTPSPEC ()
{
  return s_INTPSPEC;
}

inline const string& OGIPTable::UNITS ()
{
  return s_UNITS;
}

inline const string& OGIPTable::HDUVERS1 ()
{
  return s_HDUVERS1;
}

inline const string& OGIPTable::LOWELIMIT ()
{
  return s_LOWELIMIT;
}

inline const string& OGIPTable::HIGHELIMIT ()
{
  return s_HIGHELIMIT;
}

inline long OGIPTable::MEM_THRESHOLD ()
{
  return s_MEM_THRESHOLD;
}

inline const std::vector<TableModParam*>& OGIPTable::interParam () const
{
  return m_interParam;
}

inline void OGIPTable::interParam (const std::vector<TableModParam*>& value)
{
  m_interParam = value;
}

inline const BoolArray& OGIPTable::exact () const
{
  return m_exact;
}

inline void OGIPTable::setExact (const BoolArray& value)
{
  m_exact = value;
}

inline RealArray& OGIPTable::startWeight (const UniqueEnergy* uniqueEng)
{
  return m_startWeight[uniqueEng];
}

inline RealArray& OGIPTable::endWeight (const UniqueEnergy* uniqueEng)
{
  return m_endWeight[uniqueEng];
}

inline const IntegerArray& OGIPTable::recordNumbers () const
{
  return m_recordNumbers;
}

inline void OGIPTable::setRecordNumbers (const IntegerArray& value)
{
  m_recordNumbers = value;
}

inline const IntegerArray& OGIPTable::bracket () const
{
  return m_bracket;
}

inline void OGIPTable::setBracket (const IntegerArray& value)
{
  m_bracket = value;
}

inline const std::vector<ModParam*>& OGIPTable::addParam () const
{
  return m_addParam;
}

inline void OGIPTable::addParam (const std::vector<ModParam*>& value)
{
  m_addParam = value;
}

inline const Real OGIPTable::lowELim () const
{
  return m_lowELim;
}

inline void OGIPTable::setLowELim (const Real value)
{
  m_lowELim = value;
}

inline const Real OGIPTable::highELim () const
{
  return m_highELim;
}

inline void OGIPTable::setHighELim (const Real value)
{
  m_highELim = value;
}



#endif
