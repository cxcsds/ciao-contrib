// Class definitions for EffectiveArea object

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_grouping
#include "grouping.h"
#endif

#define HAVE_arf 1

class arf{
 public:

  // constructor

  arf();
  arf(const arf& a);
  arf(const string filename, const Integer ARFnumber = 1, const Integer RowNumber = 1);

  // destructor

  ~arf();

  // read file into object. Third parameter is to read from a row of a type II file

  Integer read(const string filename, const Integer ARFnumber = 1, const Integer RowNumber = 1);

  // Deep copy

  arf& copy(const arf&);
  arf& operator= (const arf&);

  // Display information about the arf - return as a string

  string disp() const;

  // Clear information from the arf

  void clear();

  // Check completeness and consistency of information in arf
  // if there is a problem then return diagnostic in string

  string check() const;

  // Rebin 

  Integer rebin(grouping&);

  // Write arf extension to file

  Integer write(const string filename) const;

  // Multiply by a constant

  arf& operator*=(const Real&);

  // Add arfs

  arf& operator+=(const arf&);

  Integer checkCompatibility(const arf&) const;

  Integer convertUnits();

  // Return information

  Integer NumberEnergyBins() const;            // size of RealArrays
  Integer getNumberEnergyBins() const;

  // methods to get and set internal data.

  const vector<Real>& getLowEnergy() const;
  Integer setLowEnergy(const vector<Real>& values);
  Real getLowEnergyElement(const Integer i) const;
  Integer setLowEnergyElement(const Integer i, const Real value);

  const vector<Real>& getHighEnergy() const;
  Integer setHighEnergy(const vector<Real>& values);
  Real getHighEnergyElement(const Integer i) const;
  Integer setHighEnergyElement(const Integer i, const Real value);

  const vector<Real>& getEffArea() const;
  Integer setEffArea(const vector<Real>& values);
  Real getEffAreaElement(const Integer i) const;
  Integer setEffAreaElement(const Integer i, const Real value);

  string getEnergyUnits() const;
  void setEnergyUnits(const string& value);

  string getEffAreaUnits() const;
  void setEffAreaUnits(const string& value);

  string getTelescope() const;
  void setTelescope(const string& value);

  string getInstrument() const;
  void setInstrument(const string& value);

  string getDetector() const;
  void setDetector(const string& value);

  string getFilter() const;
  void setFilter(const string& value);

  string getExtensionName() const;
  void setExtensionName(const string& value);


  
  // internal data
  
 private:

  vector<Real> m_LowEnergy;                   // Start energy of bin
  vector<Real> m_HighEnergy;                  // End energy of bin

  vector<Real> m_EffArea;                     // Effective areas

  string m_EnergyUnits;                     // Units for energies
  string m_EffAreaUnits;                        // Units for effective areas

  string m_Telescope;                             
  string m_Instrument;
  string m_Detector;
  string m_Filter;
  string m_ExtensionName;               // Value of EXTNAME keyword in SPECRESP extension

  
};

// define this outside the class

arf operator+ (const arf&, const arf&);
arf operator* (const arf&, const Real&);
arf operator* (const Real&, const arf&);

// Return the number of energy bins

inline Integer arf::NumberEnergyBins() const 
{
  return m_LowEnergy.size();
}
inline Integer arf::getNumberEnergyBins() const
{
  return m_LowEnergy.size();
}

// inline methods to get and set data

inline const vector<Real>& arf::getLowEnergy() const
{
  return m_LowEnergy;
}
inline Integer arf::setLowEnergy(const vector<Real>& values)
{
  m_LowEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_LowEnergy[i] = values[i];
  return OK;
}
inline Real arf::getLowEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_LowEnergy.size() ) {
    return m_LowEnergy[i];
  } else {
    return -999.;
  }
}
inline Integer arf::setLowEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_LowEnergy.size() ) {
    m_LowEnergy[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& arf::getHighEnergy() const
{
  return m_HighEnergy;
}
inline Integer arf::setHighEnergy(const vector<Real>& values)
{
  m_HighEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_HighEnergy[i] = values[i];
  return OK;
}
inline Real arf::getHighEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_HighEnergy.size() ) {
    return m_HighEnergy[i];
  } else {
    return -999.;
  }
}
inline Integer arf::setHighEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_HighEnergy.size() ) {
    m_HighEnergy[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& arf::getEffArea() const
{
  return m_EffArea;
}
inline Integer arf::setEffArea(const vector<Real>& values)
{
  m_EffArea.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_EffArea[i] = values[i];
  return OK;
}
inline Real arf::getEffAreaElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_EffArea.size() ) {
    return m_EffArea[i];
  } else {
    return -999.;
  }
}
inline Integer arf::setEffAreaElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_EffArea.size() ) {
    m_EffArea[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline string arf::getEnergyUnits() const
{
  return m_EnergyUnits;
}
inline void arf::setEnergyUnits(const string& value)
{
  m_EnergyUnits = value;
}

inline string arf::getEffAreaUnits() const
{
  return m_EffAreaUnits;
}
inline void arf::setEffAreaUnits(const string& value)
{
  m_EffAreaUnits = value;
}

inline string arf::getTelescope() const
{
  return m_Telescope;
}
inline void arf::setTelescope(const string& value)
{
  m_Telescope = value;
}

inline string arf::getInstrument() const
{
  return m_Instrument;
}
inline void arf::setInstrument(const string& value)
{
  m_Instrument = value;
}

inline string arf::getDetector() const
{
  return m_Detector;
}
inline void arf::setDetector(const string& value)
{
  m_Detector = value;
}

inline string arf::getFilter() const
{
  return m_Filter;
}
inline void arf::setFilter(const string& value)
{
  m_Filter = value;
}

inline string arf::getExtensionName() const
{
  return m_ExtensionName;
}
inline void arf::setExtensionName(const string& value)
{
  m_ExtensionName = value;
}

