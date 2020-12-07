// Class definitions for ResponseMatrixTranspose object

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_rmf
#include "rmf.h"
#endif

#define HAVE_rmft 1

class rmft{
 public:

  // constructor

  rmft();

  // destructor

  ~rmft();

  // load object from a standard rmf

  void load(rmf&);

  // update the FirstGroup and FirstElement arrays from NumberGroups and
  // NumberEnergiesGroup, respectively.

  void update();

  // Deep copy

  rmft& operator= (const rmft&);

  // Return the value for a particular channel and energy

  Real ElementValue(Integer, Integer) const;

  // Return the array for a particular channel

  vector<Real> RowValues(Integer) const;

  // Display information about the object - return as a string

  string disp() const;

  // Clear information from the object

  void clear();

  // Return information

  Integer NumberChannels() const;               // Number of spectrum channels 
  Integer getNumberChannels() const;
  Integer NumberEnergyBins() const;             // Number of response energies 
  Integer getNumberEnergyBins() const;
  Integer NumberTotalGroups() const;            // Total number of response groups 
  Integer getNumberTotalGroups() const;
  Integer NumberTotalElements() const;          // Total number of response elements 
  Integer getNumberTotalElements() const;

  // methods to get and set internal data

  Integer getFirstChannel() const;
  void setFirstChannel(const Integer value);

  const vector<Integer>& getNumberGroups() const;
  Integer setNumberGroups(const vector<Integer>& values);
  Integer getNumberGroupsElement(const Integer i) const;
  Integer setNumberGroupsElement(const Integer i, const Integer value);

  const vector<Integer>& getFirstGroup() const;
  Integer setFirstGroup(const vector<Integer>& values);
  Integer getFirstGroupElement(const Integer i) const;
  Integer setFirstGroupElement(const Integer i, const Integer value);

  const vector<Integer>& getFirstEnergyGroup() const;
  Integer setFirstEnergyGroup(const vector<Integer>& values);
  Integer getFirstEnergyGroupElement(const Integer i) const;
  Integer setFirstEnergyGroupElement(const Integer i, const Integer value);

  const vector<Integer>& getNumberEnergiesGroup() const;
  Integer setNumberEnergiesGroup(const vector<Integer>& values);
  Integer getNumberEnergiesGroupElement(const Integer i) const;
  Integer setNumberEnergiesGroupElement(const Integer i, const Integer value);

  const vector<Integer>& getFirstElement() const;
  Integer setFirstElement(const vector<Integer>& values);
  Integer getFirstElementElement(const Integer i) const;
  Integer setFirstElementElement(const Integer i, const Integer value);

  const vector<Integer>& getOrderGroup() const;
  Integer setOrderGroup(const vector<Integer>& values);
  Integer getOrderGroupElement(const Integer i) const;
  Integer setOrderGroupElement(const Integer i, const Integer value);

  const vector<Real>& getLowEnergy() const;
  Integer setLowEnergy(const vector<Real>& values);
  Real getLowEnergyElement(const Integer i) const;
  Integer setLowEnergyElement(const Integer i, const Real value);

  const vector<Real>& getHighEnergy() const;
  Integer setHighEnergy(const vector<Real>& values);
  Real getHighEnergyElement(const Integer i) const;
  Integer setHighEnergyElement(const Integer i, const Real value);

  const vector<Real>& getMatrix() const;
  Integer setMatrix(const vector<Real>& values);
  Real getMatrixElement(const Integer i) const;
  Integer setMatrixElement(const Integer i, const Real value);
  
  const vector<Real>& getChannelLowEnergy() const;
  Integer setChannelLowEnergy(const vector<Real>& values);
  Real getChannelLowEnergyElement(const Integer i) const;
  Integer setChannelLowEnergyElement(const Integer i, const Real value);

  const vector<Real>& getChannelHighEnergy() const;
  Integer setChannelHighEnergy(const vector<Real>& values);
  Real getChannelHighEnergyElement(const Integer i) const;
  Integer setChannelHighEnergyElement(const Integer i, const Real value);

  Real getAreaScaling() const;
  void setAreaScaling(const Real value);
  Real getResponseThreshold() const;
  void setResponseThreshold(const Real value);

  string getEnergyUnits() const;
  void setEnergyUnits(const string value);
  string getRMFUnits() const;
  void setRMFUnits(const string value);

  string getChannelType() const;
  void setChannelType(const string value);
  string getTelescope() const;
  void setTelescope(const string value);
  string getInstrument() const;
  void setInstrument(const string value);
  string getDetector() const;
  void setDetector(const string value);
  string getFilter() const;
  void setFilter(const string value);
  string getRMFType() const;
  void setRMFType(const string value);
  string getRMFExtensionName() const;
  void setRMFExtensionName(const string value);
  string getEBDExtensionName() const;
  void setEBDExtensionName(const string value);


  // internal data

 private:

  Integer m_FirstChannel;              // First channel number 

  vector<Integer> m_NumberGroups;        // Number of response groups for this channel bin 
  vector<Integer> m_FirstGroup;          // First response group for this channel bin (counts from 0)

  vector<Integer> m_FirstEnergyGroup;    // First energy bin in this group 
  vector<Integer> m_NumberEnergiesGroup; // Number of energy bins in this group 
  vector<Integer> m_FirstElement;        // First response element for this group (counts from 0)
  vector<Integer> m_OrderGroup;          // The grating order of this group 

  vector<Real> m_LowEnergy;              // Start energy of bin 
  vector<Real> m_HighEnergy;             // End energy of bin 

  vector<Real> m_Matrix;                 // Matrix elements 

  vector<Real> m_ChannelLowEnergy;       // Start energy of channel 
  vector<Real> m_ChannelHighEnergy;      // End energy of channel 

  Real m_AreaScaling;                 // Value of EFFAREA keyword 
  Real m_ResponseThreshold;           // Minimum value in response 

  string m_EnergyUnits;               // Energy units
  string m_RMFUnits;                  // RMF units

  string m_ChannelType;               // Value of CHANTYPE keyword 
  string m_Telescope;                             
  string m_Instrument;
  string m_Detector;
  string m_Filter;
  string m_RMFType;                   // Value of HDUCLAS3 keyword in MATRIX extension 
  string m_RMFExtensionName;          // Value of EXTNAME keyword in MATRIX extension 
  string m_EBDExtensionName;          // Value of EXTNAME keyword in EBOUNDS extension 

};

// Return information

inline Integer rmft::NumberChannels() const
{
  return m_ChannelLowEnergy.size();
}
inline Integer rmft::getNumberChannels() const
{
  return m_ChannelLowEnergy.size();
}
inline Integer rmft::NumberEnergyBins() const
{
  return m_LowEnergy.size();
}
inline Integer rmft::getNumberEnergyBins() const
{
  return m_LowEnergy.size();
}
inline Integer rmft::NumberTotalGroups() const
{
  return m_FirstEnergyGroup.size();
}
inline Integer rmft::getNumberTotalGroups() const
{
  return m_FirstEnergyGroup.size();
}
inline Integer rmft::NumberTotalElements() const
{
  return m_Matrix.size();
}
inline Integer rmft::getNumberTotalElements() const
{
  return m_Matrix.size();
}

// rmft::methods to get and set internal data

inline Integer rmft::getFirstChannel() const
{
  return m_FirstChannel;
}
inline void rmft::setFirstChannel(const Integer value)
{
  m_FirstChannel = value;
}

inline const vector<Integer>& rmft::getNumberGroups() const
{
  return m_NumberGroups;
}
inline Integer rmft::setNumberGroups(const vector<Integer>& values)
{
  m_NumberGroups.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_NumberGroups[i] = values[i];
  return OK;
}
inline Integer rmft::getNumberGroupsElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_NumberGroups.size() ) {
    return m_NumberGroups[i];
  }
  return -999;
}
inline Integer rmft::setNumberGroupsElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_NumberGroups.size() ) {
    m_NumberGroups[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Integer>& rmft::getFirstGroup() const
{
  return m_FirstGroup;
}
inline Integer rmft::setFirstGroup(const vector<Integer>& values)
{
  m_FirstGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FirstGroup[i] = values[i];
  return OK;
}
inline Integer rmft::getFirstGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FirstGroup.size() ) {
    return m_FirstGroup[i];
  }
  return -999;
}
inline Integer rmft::setFirstGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_FirstGroup.size() ) {
    m_FirstGroup[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Integer>& rmft::getFirstEnergyGroup() const
{
  return m_FirstEnergyGroup;
}
inline Integer rmft::setFirstEnergyGroup(const vector<Integer>& values)
{
  m_FirstEnergyGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FirstEnergyGroup[i] = values[i];
  return OK;
}
inline Integer rmft::getFirstEnergyGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FirstEnergyGroup.size() ) {
    return m_FirstEnergyGroup[i];
  }
  return -999;
}
inline Integer rmft::setFirstEnergyGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_FirstEnergyGroup.size() ) {
    m_FirstEnergyGroup[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Integer>& rmft::getNumberEnergiesGroup() const
{
  return m_NumberEnergiesGroup;
}
inline Integer rmft::setNumberEnergiesGroup(const vector<Integer>& values)
{
  m_NumberEnergiesGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_NumberEnergiesGroup[i] = values[i];
  return OK;
}
inline Integer rmft::getNumberEnergiesGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_NumberEnergiesGroup.size() ) {
    return m_NumberEnergiesGroup[i];
  }
  return -999;
}
inline Integer rmft::setNumberEnergiesGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_NumberEnergiesGroup.size() ) {
    m_NumberEnergiesGroup[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Integer>& rmft::getFirstElement() const
{
  return m_FirstElement;
}
inline Integer rmft::setFirstElement(const vector<Integer>& values)
{
  m_FirstElement.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FirstElement[i] = values[i];
  return OK;
}
inline Integer rmft::getFirstElementElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FirstElement.size() ) {
    return m_FirstElement[i];
  }
  return -999;
}
inline Integer rmft::setFirstElementElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_FirstElement.size() ) {
    m_FirstElement[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Integer>& rmft::getOrderGroup() const
{
  return m_OrderGroup;
}
inline Integer rmft::setOrderGroup(const vector<Integer>& values)
{
  m_OrderGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_OrderGroup[i] = values[i];
  return OK;
}
inline Integer rmft::getOrderGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_OrderGroup.size() ) {
    return m_OrderGroup[i];
  }
  return -999;
}
inline Integer rmft::setOrderGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_OrderGroup.size() ) {
    m_OrderGroup[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Real>& rmft::getLowEnergy() const
{
  return m_LowEnergy;
}
inline Integer rmft::setLowEnergy(const vector<Real>& values)
{
  m_LowEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_LowEnergy[i] = values[i];
  return OK;
}
inline Real rmft::getLowEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_LowEnergy.size() ) {
    return m_LowEnergy[i];
  }
  return -999.;
}
inline Integer rmft::setLowEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_LowEnergy.size() ) {
    m_LowEnergy[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Real>& rmft::getHighEnergy() const
{
  return m_HighEnergy;
}
inline Integer rmft::setHighEnergy(const vector<Real>& values)
{
  m_HighEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_HighEnergy[i] = values[i];
  return OK;
}
inline Real rmft::getHighEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_HighEnergy.size() ) {
    return m_HighEnergy[i];
  }
  return -999.;
}
inline Integer rmft::setHighEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_HighEnergy.size() ) {
    m_HighEnergy[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Real>& rmft::getMatrix() const
{
  return m_Matrix;
}
inline Integer rmft::setMatrix(const vector<Real>& values)
{
  m_Matrix.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Matrix[i] = values[i];
  return OK;
}
inline Real rmft::getMatrixElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Matrix.size() ) {
    return m_Matrix[i];
  }
  return -999.;
}
inline Integer rmft::setMatrixElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_Matrix.size() ) {
    m_Matrix[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}
  
inline const vector<Real>& rmft::getChannelLowEnergy() const
{
  return m_ChannelLowEnergy;
}
inline Integer rmft::setChannelLowEnergy(const vector<Real>& values)
{
  m_ChannelLowEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_ChannelLowEnergy[i] = values[i];
  return OK;
}
inline Real rmft::getChannelLowEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_ChannelLowEnergy.size() ) {
    return m_ChannelLowEnergy[i];
  }
  return -999.;
}
inline Integer rmft::setChannelLowEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_ChannelLowEnergy.size() ) {
    m_ChannelLowEnergy[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline const vector<Real>& rmft::getChannelHighEnergy() const
{
  return m_ChannelHighEnergy;
}
inline Integer rmft::setChannelHighEnergy(const vector<Real>& values)
{
  m_ChannelHighEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_ChannelHighEnergy[i] = values[i];
  return OK;
}
inline Real rmft::getChannelHighEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_ChannelHighEnergy.size() ) {
    return m_ChannelHighEnergy[i];
  }
  return -999.;
}
inline Integer rmft::setChannelHighEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_ChannelHighEnergy.size() ) {
    m_ChannelHighEnergy[i] = value;
    return OK;
  }
  return VectorIndexOutsideRange;
}

inline Real rmft::getAreaScaling() const
{
  return m_AreaScaling;
}
inline void rmft::setAreaScaling(const Real value)
{
  m_AreaScaling = value;
}
inline Real rmft::getResponseThreshold() const
{
  return m_ResponseThreshold;
}
inline void rmft::setResponseThreshold(const Real value)
{
  m_ResponseThreshold = value;
}

inline string rmft::getEnergyUnits() const
{
  return m_EnergyUnits;
}
inline void rmft::setEnergyUnits(const string value)
{
  m_EnergyUnits = value;
}
inline string rmft::getRMFUnits() const
{
  return m_RMFUnits;
}
inline void rmft::setRMFUnits(const string value)
{
  m_RMFUnits = value;
}

inline string rmft::getChannelType() const
{
  return m_ChannelType;
}
inline void rmft::setChannelType(const string value)
{
  m_ChannelType = value;
}
inline string rmft::getTelescope() const
{
  return m_Telescope;
}
inline void rmft::setTelescope(const string value)
{
  m_Telescope = value;
}
inline string rmft::getInstrument() const
{
  return m_Instrument;
}
inline void rmft::setInstrument(const string value)
{
  m_Instrument = value;
}
inline string rmft::getDetector() const
{
  return m_Detector;
}
inline void rmft::setDetector(const string value)
{
  m_Detector = value;
}
inline string rmft::getFilter() const
{
  return m_Filter;
}
inline void rmft::setFilter(const string value)
{
  m_Filter = value;
}
inline string rmft::getRMFType() const
{
  return m_RMFType;
}
inline void rmft::setRMFType(const string value)
{
  m_RMFType = value;
}
inline string rmft::getRMFExtensionName() const
{
  return m_RMFExtensionName;
}
inline void rmft::setRMFExtensionName(const string value)
{
  m_RMFExtensionName = value;
}
inline string rmft::getEBDExtensionName() const
{
  return m_EBDExtensionName;
}
inline void rmft::setEBDExtensionName(const string value)
{
  m_EBDExtensionName = value;
}


