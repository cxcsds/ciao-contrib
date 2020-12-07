// Class definitions for rmf object

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_arf
#include "arf.h"
#endif

#ifndef HAVE_pha
#include "pha.h"
#endif

#ifndef HAVE_grouping
#include "grouping.h"
#endif

#define HAVE_rmf 1

class rmf{
 public:


  // constructors

  rmf();
  rmf(const rmf& a);
  rmf(const string filename, const Integer RMFnumber = 1);
  rmf(const vector<Integer>& inNumberGroups,
      const vector<Integer>& inFirstChannelGroup,
      const vector<Integer>& inNumberChannelsGroup,
      const vector<Integer>& inOrderGroup,
      const vector<Real>& inLowEnergy, const vector<Real>& inHighEnergy,
      const vector<Real>& inMatrix, const vector<Real>& inChannelLowEnergy,
      const vector<Real>& inChannelHighEnergy,
      const Integer inFirstChannel, const Real inAreaScaling,
      const Real inResponseThreshold, const map<string,string>& inKeys);

  // destructor

  ~rmf();

  // read file into object. 

  Integer read(const string filename, const Integer RMFnumber = 1);
  Integer readMatrix(const string filename, const Integer RMFnumber = 1);
  Integer readChannelBounds(const string filename, const Integer RMFnumber = 1);

  // Load object from input information

  Integer load(const vector<Integer>& inNumberGroups,
	       const vector<Integer>& inFirstChannelGroup,
	       const vector<Integer>& inNumberChannelsGroup,
	       const vector<Integer>& inOrderGroup,
	       const vector<Real>& inLowEnergy, const vector<Real>& inHighEnergy,
	       const vector<Real>& inMatrix, const vector<Real>& inChannelLowEnergy,
	       const vector<Real>& inChannelHighEnergy,
	       const Integer inFirstChannel, const Real inAreaScaling,
	       const Real inResponseThreshold, const map<string,string>& inKeys);

  // update the FirstGroup and FirstElement arrays from NumberGroups and
  // NumberChannelsGroup, respectively.

  void update();

  // initialize from an arf object. Copies members in common between arfs and rmfs

  void initialize(const arf&);

  // load a diagonal response

  void loadDiagonalResponse(const vector<Real>& eLow, const vector<Real>& eHigh,
			    const vector<Real>& rspVals, const Integer firstChan);

  // Deep copy

  rmf& copy(const rmf&);
  rmf& operator= (const rmf&);

  // Return the value for a particular channel, energy bin and grating order. If
  // grating order is set to -999 it is ignored.
  
  Real ElementValue(const Integer ChannelNumber, const Integer EnergyBin,
		    const Integer GratingOrder = -999) const;

  // Return the row of values for a particular energy bin and grating order. If
  // grating order is set to -999 it is ignored.

  vector<Real> RowValues(const Integer EnergyBin, const Integer GratingOrder = -999) const;

  // Use the response matrix to generate random channel numbers for a photon 
  // of given energy or set of energies (and grating order).

  vector<Integer> RandomChannels(const Real energy, const Integer NumberPhotons,
				 const vector<Real>& RandomNumber,
				 const Integer GratingOrder = -999) const;
  vector<Integer> RandomChannels(const vector<Real>& energy,
				 const vector<Integer>& NumberPhotons,
				 const vector<vector<Real> >& RandomNumber,
				 const Integer GratingOrder = -999) const;

  // Display information about the response - return as a string

  string disp() const;

  // Clear information from the response

  void clear();

  // Clear only the matrix from the response

  void clearMatrix();

  // Check completeness and consistency of information in the rmf
  // if there is a problem then return diagnostic in string

  string check() const;

  // Normalize the rmf so it sums to 1.0 for each energy bin

  void normalize();

  // Compress the rmf to remove all elements below the threshold value

  void compress(const Real threshold);

  // Uncompress the rmf ie turn it into a full rectangular matrix

  void uncompress();

  // Rebin in either channel or energy space

  Integer rebinChannels(grouping&);
  Integer rebinEnergies(grouping&);

  // Remaps response up or down in channels or energies

  Integer shiftChannels(const Integer Start, const Integer End, const Real Shift, const Real Factor = 1.0, bool useEnergyBounds = false);
  Integer shiftChannels(const vector<Integer>& vStart, const vector<Integer>& vEnd, 
			const vector<Real>& vShift, const vector<Real>& vFactor, bool useEnergyBounds = false);

  Integer shiftEnergies(const Integer Start, const Integer End, const Real Shift, const Real Factor);
  Integer shiftEnergies(const vector<Integer>& vStart, const vector<Integer>& vEnd, 
			const vector<Real>& vShift, const vector<Real>& vFactor);

  // Multiply by a vector which may not have the same energy binning as the response

  Integer interpolateAndMultiply(const vector<Real>& energies, 
				 const vector<Real>& factors);

  // Write response

  Integer write(const string filename) const;
  Integer writeMatrix(const string filename) const;
  Integer writeChannelBounds(const string filename) const;

  // Merge ARF and rmf

  rmf& operator*=(const arf&);

  // multiply rmf by factor

  rmf& operator*=(const Real&);

  // add rmf's

  rmf& operator+=(const rmf&);

  // check compatibility with another rmf or ARF

  Integer checkCompatibility(const rmf&) const;
  Integer checkCompatibility(const arf&) const;

  // convert units. mainly useful if input energy/wavelengths are not in keV

  Integer convertUnits();

  // reverse the rows, required if they are not in increasing order of energy

  void reverseRows();

  // add a row to the response using an input response vector and energy range.

  void addRow(const vector<Real>& Response, const Real eLow, const Real eHigh);
  void addRow(const vector<vector<Real> >& Response, const Real eLow, const Real eHigh, const vector<Integer>& GratingOrder);

  // substitute a row into the response using an input response vector and energy range.

  void substituteRow(const Integer RowNumber, const vector<Real>& Response);
  void substituteRow(const Integer RowNumber, const vector<vector<Real> >& Response, const vector<Integer>& GratingOrder);

  // multiply a response by a vector and output a vector of pha values. The input
  // vector is assumed to be on the energy binning

  vector<Real> multiplyByModel(const vector<Real>& model);

  // return a vector containing the FWHM in channels for each energy. This does
  // assume that the response has a well-defined main peak

  vector<Real> estimatedFWHM() const;

  // return a vector containing the FWHM in channels for each channel. This does
  // assume that the response has a well-defined main peak

  vector<Real> estimatedFWHMperChannel() const;

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

  const vector<Integer>& getFirstChannelGroup() const;
  Integer setFirstChannelGroup(const vector<Integer>& values);
  Integer getFirstChannelGroupElement(const Integer i) const;
  Integer setFirstChannelGroupElement(const Integer i, const Integer value);

  const vector<Integer>& getNumberChannelsGroup() const;
  Integer setNumberChannelsGroup(const vector<Integer>& values);
  Integer getNumberChannelsGroupElement(const Integer i) const;
  Integer setNumberChannelsGroupElement(const Integer i, const Integer value);

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

  vector<Integer> m_NumberGroups;        // Number of response groups for this energy bin 
  vector<Integer> m_FirstGroup;          // First response group for this energy bin (counts from 0)

  vector<Integer> m_FirstChannelGroup;   // First channel number in this group 
  vector<Integer> m_NumberChannelsGroup; // Number of channels in this group 
  vector<Integer> m_FirstElement;        // First response element for this group (counts from 0)
  vector<Integer> m_OrderGroup;          // The grating order of this group 

  vector<Real> m_LowEnergy;              // Start energy of bin 
  vector<Real> m_HighEnergy;             // End energy of bin 

  vector<Real> m_Matrix;                 // Matrix elements 

  vector<Real> m_ChannelLowEnergy;       // Start energy of channel 
  vector<Real> m_ChannelHighEnergy;      // End energy of channel 

  Real m_AreaScaling;                 // Value of EFFAREA keyword 
  Real m_ResponseThreshold;           // Minimum value in response 

  string m_EnergyUnits;               // Energy units used
  string m_RMFUnits;                  // Units for RMF values

  string m_ChannelType;               // Value of CHANTYPE keyword 
  string m_Telescope;                             
  string m_Instrument;
  string m_Detector;
  string m_Filter;
  string m_RMFType;                   // Value of HDUCLAS3 keyword in MATRIX extension 
  string m_RMFExtensionName;          // Value of EXTNAME keyword in MATRIX extension 
  string m_EBDExtensionName;          // Value of EXTNAME keyword in EBOUNDS extension 
  
};

// define these outside the class

// binary operators 

rmf operator* (const rmf&, const arf&);
rmf operator* (const arf&, const rmf&);
rmf operator* (const rmf&, const Real&);
rmf operator* (const Real&, const rmf&);
rmf operator+ (const rmf&, const rmf&);

// calculate the response vector for some energy given a gaussian width
// the gaussian is assumed to be in the units of energyLow, energyHigh,
// ChannelLowEnergy and ChannelHighEnergy

void calcGaussResp(const Real width, const Real energy, const Real threshold, 
		   const vector<Real>& ChannelLowEnergy, 
		   const vector<Real>& ChannelHighEnergy, 
		   vector<Real>& ResponseVector);

size_t binarySearch(const Real energy, const vector<Real>& lowEnergy,
		    const vector<Real>& highEnergy);

// Return information

inline Integer rmf::NumberChannels() const
{
  return m_ChannelLowEnergy.size();
}
inline Integer rmf::getNumberChannels() const
{
  return m_ChannelLowEnergy.size();
}
inline Integer rmf::NumberEnergyBins() const
{
  return m_LowEnergy.size();
}
inline Integer rmf::getNumberEnergyBins() const
{
  return m_LowEnergy.size();
}
inline Integer rmf::NumberTotalGroups() const
{
  return m_FirstChannelGroup.size();
}
inline Integer rmf::getNumberTotalGroups() const
{
  return m_FirstChannelGroup.size();
}
inline Integer rmf::NumberTotalElements() const
{
  return m_Matrix.size();
}
inline Integer rmf::getNumberTotalElements() const
{
  return m_Matrix.size();
}


// methods to get and set internal data

inline Integer rmf::getFirstChannel() const
{
  return m_FirstChannel;
}
inline void rmf::setFirstChannel(const Integer value)
{
  m_FirstChannel = value;
}

inline const vector<Integer>& rmf::getNumberGroups() const
{
  return m_NumberGroups;
}
inline Integer rmf::setNumberGroups(const vector<Integer>& values)
{
  m_NumberGroups.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_NumberGroups[i] = values[i];
  return OK;
}
inline Integer rmf::getNumberGroupsElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_NumberGroups.size() ) {
    return m_NumberGroups[i];
  } else {
    return -999;
  }
}
inline Integer rmf::setNumberGroupsElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_NumberGroups.size() ) {
    m_NumberGroups[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& rmf::getFirstGroup() const
{
  return m_FirstGroup;
}
inline Integer rmf::setFirstGroup(const vector<Integer>& values)
{
  m_FirstGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FirstGroup[i] = values[i];
  return OK;
}
inline Integer rmf::getFirstGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FirstGroup.size() ) {
    return m_FirstGroup[i];
  } else {
    return -999;
  }
}
inline Integer rmf::setFirstGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_FirstGroup.size() ) {
    m_FirstGroup[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& rmf::getFirstChannelGroup() const
{
  return m_FirstChannelGroup;
}
inline Integer rmf::setFirstChannelGroup(const vector<Integer>& values)
{
  m_FirstChannelGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FirstChannelGroup[i] = values[i];
  return OK;
}
inline Integer rmf::getFirstChannelGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FirstChannelGroup.size() ) {
    return m_FirstChannelGroup[i];
  } else {
    return -999;
  }
}
inline Integer rmf::setFirstChannelGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_FirstChannelGroup.size() ) {
    m_FirstChannelGroup[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& rmf::getNumberChannelsGroup() const
{
  return m_NumberChannelsGroup;
}
inline Integer rmf::setNumberChannelsGroup(const vector<Integer>& values)
{
  m_NumberChannelsGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_NumberChannelsGroup[i] = values[i];
  return OK;
}
inline Integer rmf::getNumberChannelsGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_NumberChannelsGroup.size() ) {
    return m_NumberChannelsGroup[i];
  } else {
    return -999;
  }
}
inline Integer rmf::setNumberChannelsGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_NumberChannelsGroup.size() ) {
    m_NumberChannelsGroup[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& rmf::getFirstElement() const
{
  return m_FirstElement;
}
inline Integer rmf::setFirstElement(const vector<Integer>& values)
{
  m_FirstElement.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FirstElement[i] = values[i];
  return OK;
}
inline Integer rmf::getFirstElementElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FirstElement.size() ) {
    return m_FirstElement[i];
  } else {
    return -999;
  }
}
inline Integer rmf::setFirstElementElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_FirstElement.size() ) {
    m_FirstElement[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& rmf::getOrderGroup() const
{
  return m_OrderGroup;
}
inline Integer rmf::setOrderGroup(const vector<Integer>& values)
{
  m_OrderGroup.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_OrderGroup[i] = values[i];
  return OK;
}
inline Integer rmf::getOrderGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_OrderGroup.size() ) {
    return m_OrderGroup[i];
  } else {
    return -999;
  }
}
inline Integer rmf::setOrderGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_OrderGroup.size() ) {
    m_OrderGroup[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& rmf::getLowEnergy() const
{
  return m_LowEnergy;
}
inline Integer rmf::setLowEnergy(const vector<Real>& values)
{
  m_LowEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_LowEnergy[i] = values[i];
  return OK;
}
inline Real rmf::getLowEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_LowEnergy.size() ) {
    return m_LowEnergy[i];
  } else {
    return -999.;
  }
}
inline Integer rmf::setLowEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_LowEnergy.size() ) {
    m_LowEnergy[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& rmf::getHighEnergy() const
{
  return m_HighEnergy;
}
inline Integer rmf::setHighEnergy(const vector<Real>& values)
{
  m_HighEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_HighEnergy[i] = values[i];
  return OK;
}
inline Real rmf::getHighEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_HighEnergy.size() ) {
    return m_HighEnergy[i];
  } else {
    return -999.;
  }
}
inline Integer rmf::setHighEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_HighEnergy.size() ) {
    m_HighEnergy[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& rmf::getMatrix() const
{
  return m_Matrix;
}
inline Integer rmf::setMatrix(const vector<Real>& values)
{
  m_Matrix.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Matrix[i] = values[i];
  return OK;
}
inline Real rmf::getMatrixElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Matrix.size() ) {
    return m_Matrix[i];
  } else {
    return -999.;
  }
}
inline Integer rmf::setMatrixElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_Matrix.size() ) {
    m_Matrix[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
  
inline const vector<Real>& rmf::getChannelLowEnergy() const
{
  return m_ChannelLowEnergy;
}
inline Integer rmf::setChannelLowEnergy(const vector<Real>& values)
{
  m_ChannelLowEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_ChannelLowEnergy[i] = values[i];
  return OK;
}
inline Real rmf::getChannelLowEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_ChannelLowEnergy.size() ) {
    return m_ChannelLowEnergy[i];
  } else {
    return -999.;
  }
}
inline Integer rmf::setChannelLowEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_ChannelLowEnergy.size() ) {
    m_ChannelLowEnergy[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& rmf::getChannelHighEnergy() const
{
  return m_ChannelHighEnergy;
}
inline Integer rmf::setChannelHighEnergy(const vector<Real>& values)
{
  m_ChannelHighEnergy.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_ChannelHighEnergy[i] = values[i];
  return OK;
}
inline Real rmf::getChannelHighEnergyElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_ChannelHighEnergy.size() ) {
    return m_ChannelHighEnergy[i];
  } else {
    return -999.;
  }
}
inline Integer rmf::setChannelHighEnergyElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_ChannelHighEnergy.size() ) {
    m_ChannelHighEnergy[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline Real rmf::getAreaScaling() const
{
  return m_AreaScaling;
}
inline void rmf::setAreaScaling(const Real value)
{
  m_AreaScaling = value;
}
inline Real rmf::getResponseThreshold() const
{
  return m_ResponseThreshold;
}
inline void rmf::setResponseThreshold(const Real value)
{
  m_ResponseThreshold = value;
}

inline string rmf::getEnergyUnits() const
{
  return m_EnergyUnits;
}
inline void rmf::setEnergyUnits(const string value)
{
  m_EnergyUnits = value;
}
inline string rmf::getRMFUnits() const
{
  return m_RMFUnits;
}
inline void rmf::setRMFUnits(const string value)
{
  m_RMFUnits = value;
}

inline string rmf::getChannelType() const
{
  return m_ChannelType;
}
inline void rmf::setChannelType(const string value)
{
  m_ChannelType = value;
}
inline string rmf::getTelescope() const
{
  return m_Telescope;
}
inline void rmf::setTelescope(const string value)
{
  m_Telescope = value;
}
inline string rmf::getInstrument() const
{
  return m_Instrument;
}
inline void rmf::setInstrument(const string value)
{
  m_Instrument = value;
}
inline string rmf::getDetector() const
{
  return m_Detector;
}
inline void rmf::setDetector(const string value)
{
  m_Detector = value;
}
inline string rmf::getFilter() const
{
  return m_Filter;
}
inline void rmf::setFilter(const string value)
{
  m_Filter = value;
}
inline string rmf::getRMFType() const
{
  return m_RMFType;
}
inline void rmf::setRMFType(const string value)
{
  m_RMFType = value;
}
inline string rmf::getRMFExtensionName() const
{
  return m_RMFExtensionName;
}
inline void rmf::setRMFExtensionName(const string value)
{
  m_RMFExtensionName = value;
}
inline string rmf::getEBDExtensionName() const
{
  return m_EBDExtensionName;
}
inline void rmf::setEBDExtensionName(const string value)
{
  m_EBDExtensionName = value;
}


