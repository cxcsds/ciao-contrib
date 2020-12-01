// Class definitions for PHA object

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_grouping
#include "grouping.h"
#endif

#define HAVE_pha 1

class pha{
 public:

  // constructor

  pha();
  pha(const pha& a);
  pha(const string filename, const Integer PHAnumber = 1,
      const Integer SpectrumNumber = 1);
  pha(const vector<Real>& inPha, const vector<Real>& inStatError,
      const vector<Real>& inSysError, const vector<Integer>& inChannel,
      const vector<Integer>& inQuality, const vector<Integer>& inGroup,
      const vector<Real>& inAreaScaling, const vector<Real>& inBackScaling,
      const Integer inFirstChannel, const Real inExposure, const Real inCorrectionScaling,
      const Integer inDetChans, const bool inPoisserr,
      const map<string,string>& inKeys,
      const vector<string>& inXSPECFilter = vector<string>());

  // destructor

  ~pha();

  // read file into object. For a type I file SpectrumNumber should be set to 1

  Integer read(const string filename, const Integer PHAnumber = 1,
	       const Integer SpectrumNumber = 1);

  // Load object from input information

  Integer load(const vector<Real>& inPha, const vector<Real>& inStatError,
	       const vector<Real>& inSysError, const vector<Integer>& inChannel,
	       const vector<Integer>& inQuality, const vector<Integer>& inGroup,
	       const vector<Real>& inAreaScaling, const vector<Real>& inBackScaling,
	       const Integer inFirstChannel, const Real inExposure,
	       const Real inCorrectionScaling, const Integer inDetChans,
	       const bool inPoisserr, const map<string,string>& inKeys,
	       const vector<string>& inXSPECFilter = vector<string>());

  // Deep copy

  pha& copy(const pha&);
  pha& operator= (const pha&);

  // Display information about the spectrum - return as a string

  string disp() const;

  // Clear the information in the spectrum

  void clear();

  // Check completeness and consistency of information in spectrum
  // if there is a problem then return diagnostic in string

  string check() const;

  // Write spectrum as type I file

  Integer write(const string filename) const;

  // Multiply by a constant

  pha& operator*= (const Real);

  // Add to another pha

  pha& operator+= (const pha&);

  // Check compatibility with another pha

  Integer checkCompatibility(const pha&) const;

  // Select a subset of the channels

  Integer selectChannels(const vector<Integer>& Start, const vector<Integer>& End);

  // Set grouping array from grouping object

  Integer setGrouping(grouping&);

  // Get grouping object from the grouping array

  grouping getGrouping() const;

  // Get grouping (optionally between channels StartChannel and EndChannel) 
  // using a minimum number of counts per bin. If StartChannel=EndChannel=0 then
  // all channels are used

  grouping getMinCountsGrouping(const Integer MinCounts, const Integer StartChannel = 0,
				const Integer EndChannel = 0) const;

  // Get grouping (optionally between channels StartChannel and EndChannel) 
  // using a minimum S/N. Optionally includes a background file as well.
  // If StartChannel=EndChannel=0 then all channels are used. If Background is
  // set to the default constructor it is ignored.

  grouping getMinSNGrouping(const Real SignalToNoise, const pha& Background = pha(),
			    const Integer StartChannel = 0,
			    const Integer EndChannel = 0) const;

  // Rebin channels

  Integer rebinChannels(grouping& GroupInfo, const string errorType = "PROPAGATE");

  // Shift channels. Option to use channel energy bounds in which case Shift is
  // assumed to be in energies, otherwise in channel number.

  Integer shiftChannels(const Integer Start, const Integer End, const Real Shift,
			const Real Factor = 1.0);
  Integer shiftChannels(const vector<Integer>& Start, const vector<Integer>& End,
			const vector<Real>& Shift, const vector<Real>& Factor);
  Integer shiftChannels(const vector<Real>& ChannelLowEnergy,
			const vector<Real>& ChannelHighEnergy, 
			const Integer Start, const Integer End, const Real Shift,
			const Real Factor = 1.0);
  Integer shiftChannels(const vector<Real>& ChannelLowEnergy,
			const vector<Real>& ChannelHighEnergy, 
			const vector<Integer>& Start, const vector<Integer>& End,
			const vector<Real>& Shift, const vector<Real>& Factor);

  // Convert flux units from whatever they are currently to ph/cm^2/s. 
  // This requires as input the channel energy arrays from the rmf object and
  // the string specifying their units.

  Integer convertUnits(const vector<Real>& ChannelLowEnergy,
		       const vector<Real>& ChannelHighEnergy, const string EnergyUnits);

  // Return information

  Integer NumberChannels() const;            // size of internal Arrays
  Integer getNumberChannels() const;

  // methods to get and set internal data

  Integer getFirstChannel() const;
  void setFirstChannel(const Integer value);

  const vector<Real>& getPha() const;
  Integer setPha(const vector<Real>& values);
  Real getPhaElement(const Integer i) const;
  Integer setPhaElement(const Integer i, const Real value);

  const vector<Real>& getStatError() const;
  Integer setStatError(const vector<Real>& values);
  Real getStatErrorElement(const Integer i) const;
  Integer setStatErrorElement(const Integer i, const Real value);

  const vector<Real>& getSysError() const;
  Integer setSysError(const vector<Real>& values);
  Real getSysErrorElement(const Integer i) const;
  Integer setSysErrorElement(const Integer i, const Real value);

  const vector<Integer>& getChannel() const;
  Integer setChannel(const vector<Integer>& values);
  Integer getChannelElement(const Integer i) const;
  Integer setChannelElement(const Integer i, const Integer value);

  const vector<Integer>& getQuality() const;
  Integer setQuality(const vector<Integer>& values);
  Integer getQualityElement(const Integer i) const;
  Integer setQualityElement(const Integer i, const Integer value);

  const vector<Integer>& getGroup() const;
  Integer setGroup(const vector<Integer>& values);
  Integer getGroupElement(const Integer i) const;
  Integer setGroupElement(const Integer i, const Integer value);

  const vector<Real>& getAreaScaling() const;
  Integer setAreaScaling(const vector<Real>& values);
  Real getAreaScalingElement(const Integer i) const;
  Integer setAreaScalingElement(const Integer i, const Real value);

  const vector<Real>& getBackScaling() const;
  Integer setBackScaling(const vector<Real>& values);
  Real getBackScalingElement(const Integer i) const;
  Integer setBackScalingElement(const Integer i, const Real value);

  Real getExposure() const;
  void setExposure(const Real value);
  
  Real getCorrectionScaling() const;
  void setCorrectionScaling(const Real value);

  Integer getDetChans() const;
  void setDetChans(const Integer value);

  bool getPoisserr() const;
  void setPoisserr(const bool value);

  string getDatatype() const;
  void setDatatype(const string value);
  
  string getSpectrumtype() const;
  void setSpectrumtype(const string value);

  string getResponseFile() const;
  void setResponseFile(const string value);

  string getAncillaryFile() const;
  void setAncillaryFile(const string value);

  string getBackgroundFile() const;
  void setBackgroundFile(const string value);

  string getCorrectionFile() const;
  void setCorrectionFile(const string value);
  
  string getFluxUnits() const;
  void setFluxUnits(const string value);
  
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

  string getDatamode() const;
  void setDatamode(const string value);

  const vector<string>& getXSPECFilter() const;
  Integer setXSPECFilter(const vector<string>& values);
  string getXSPECFilterElement(const Integer i) const;
  Integer setXSPECFilterElement(const Integer i, const string value);

  // internal data

 private:
  
  Integer m_FirstChannel;                 // First legal channel number

  vector<Real> m_Pha;                     // PHA data
  vector<Real> m_StatError;               // Statistical error 
  vector<Real> m_SysError;                // Systematic error 

  vector<Integer> m_Channel;              // Channel number
  vector<Integer> m_Quality;              // Data quality (0=good, 1=bad, 2=dubious, 
                                          //               5=set bad by user)
  vector<Integer> m_Group;                // Data grouping ( 1=start of bin, 
                                        //                -1=continuation of bin)

  vector<Real> m_AreaScaling;             // Area scaling factor 
  vector<Real> m_BackScaling;             // Background scaling factor 

  Real m_Exposure;                        // Exposure time 
  Real m_CorrectionScaling;               // Correction file scale factor 

  Integer m_DetChans;                     // Total legal number of channels
  bool m_Poisserr;                        // If true, errors are Poisson 
  string m_Datatype;                      // "COUNT" for count data and "RATE" for count/sec 
  string m_Spectrumtype;                  // "TOTAL", "NET", or "BKG" 

  string m_ResponseFile;                  // Response filename 
  string m_AncillaryFile;                 // Ancillary filename 
  string m_BackgroundFile;                // Background filename 
  string m_CorrectionFile;                // Correction filename 

  string m_FluxUnits;                     // Units for Pha and StatError

  string m_ChannelType;                   // Value of CHANTYPE keyword 
  string m_Telescope;                                          
  string m_Instrument;
  string m_Detector;
  string m_Filter;
  string m_Datamode;

  vector<string> m_XSPECFilter;           // Filter keywords 

};

// Binary operation

pha operator+ (const pha& a, const pha& b);

// Utility routines

// return the type of a PHA extension

Integer PHAtype(const string filename, const Integer PHAnumber); 
Integer PHAtype(const string filename, const Integer PHAnumber, Integer& Status); 

// return true if COUNTS column exists and is integer

bool IsPHAcounts(const string filename, const Integer PHAnumber); 
bool IsPHAcounts(const string filename, const Integer PHAnumber, Integer& Status); 

// return the number of spectra in a type II PHA extension

Integer NumberofSpectra(const string filename, const Integer PHAnumber); 
Integer NumberofSpectra(const string filename, const Integer PHAnumber, Integer& Status); 

// return the numbers of any spectrum extensions

vector<Integer> SpectrumExtensions(const string filename);
vector<Integer> SpectrumExtensions(const string filename, Integer& Status);

// return the number of channels

inline Integer pha::NumberChannels() const
{
  return m_Pha.size();
}
inline Integer pha::getNumberChannels() const
{
  return m_Pha.size();
}

// inline methods to get and set internal data

inline Integer pha::getFirstChannel() const
{
  return m_FirstChannel;
}
inline void pha::setFirstChannel(const Integer value)
{
  m_FirstChannel = value;
}

inline const vector<Real>& pha::getPha() const
{
  return m_Pha;
}
inline Integer pha::setPha(const vector<Real>& values)
{
  m_Pha.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Pha[i] = values[i];
  return OK;
}
inline Real pha::getPhaElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Pha.size() ) {
    return m_Pha[i];
  } else {
    return -999.;
  }
}
inline Integer pha::setPhaElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_Pha.size() ) {
    m_Pha[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& pha::getStatError() const
{
  return m_StatError;
}
inline Integer pha::setStatError(const vector<Real>& values)
{
  m_StatError.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_StatError[i] = values[i];
  return OK;
}
inline Real pha::getStatErrorElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_StatError.size() ) {
    return m_StatError[i];
  } else {
    return -999.;
  }
}
inline Integer pha::setStatErrorElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_StatError.size() ) {
    m_StatError[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& pha::getSysError() const
{
  return m_SysError;
}
inline Integer pha::setSysError(const vector<Real>& values)
{
  m_SysError.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_SysError[i] = values[i];
  return OK;
}
inline Real pha::getSysErrorElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_SysError.size() ) {
    return m_SysError[i];
  } else {
    return -999.;
  }
}
inline Integer pha::setSysErrorElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_SysError.size() ) {
    m_SysError[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& pha::getChannel() const
{
  return m_Channel;
}
inline Integer pha::setChannel(const vector<Integer>& values)
{
  m_Channel.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Channel[i] = values[i];
  return OK;
}
inline Integer pha::getChannelElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Channel.size() ) {
    return m_Channel[i];
  } else {
    return -999;
  }
}
inline Integer pha::setChannelElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_Channel.size() ) {
    m_Channel[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& pha::getQuality() const
{
  return m_Quality;
}
inline Integer pha::setQuality(const vector<Integer>& values)
{
  m_Quality.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Quality[i] = values[i];
  return OK;
}
inline Integer pha::getQualityElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Quality.size() ) {
    return m_Quality[i];
  } else {
    return -999;
  }
}
inline Integer pha::setQualityElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_Quality.size() ) {
    m_Quality[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Integer>& pha::getGroup() const
{
  return m_Group;
}
inline Integer pha::setGroup(const vector<Integer>& values)
{
  m_Group.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Group[i] = values[i];
  return OK;
}
inline Integer pha::getGroupElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Group.size() ) {
    return m_Group[i];
  } else {
    return -999;
  }
}
inline Integer pha::setGroupElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_Group.size() ) {
    m_Group[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& pha::getAreaScaling() const
{
  return m_AreaScaling;
}
inline Integer pha::setAreaScaling(const vector<Real>& values)
{
  m_AreaScaling.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_AreaScaling[i] = values[i];
  return OK;
}
inline Real pha::getAreaScalingElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_AreaScaling.size() ) {
    return m_AreaScaling[i];
  } else {
    return -999.;
  }
}
inline Integer pha::setAreaScalingElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_AreaScaling.size() ) {
    m_AreaScaling[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline const vector<Real>& pha::getBackScaling() const
{
  return m_BackScaling;
}
inline Integer pha::setBackScaling(const vector<Real>& values)
{
  m_BackScaling.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_BackScaling[i] = values[i];
  return OK;
}
inline Real pha::getBackScalingElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_BackScaling.size() ) {
    return m_BackScaling[i];
  } else {
    return -999.;
  }
}
inline Integer pha::setBackScalingElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_BackScaling.size() ) {
    m_BackScaling[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline Real pha::getExposure() const
{
  return m_Exposure;
}
inline void pha::setExposure(const Real value)
{
  m_Exposure = value;
}
  
inline Real pha::getCorrectionScaling() const
{
  return m_CorrectionScaling;
}
inline void pha::setCorrectionScaling(const Real value)
{
  m_CorrectionScaling = value;
}

inline Integer pha::getDetChans() const
{
  return m_DetChans;
}
inline void pha::setDetChans(const Integer value)
{
  m_DetChans = value;
}

inline bool pha::getPoisserr() const
{
  return m_Poisserr;
}
inline void pha::setPoisserr(const bool value)
{
  m_Poisserr = value;
}

inline string pha::getDatatype() const
{
  return m_Datatype;
}
inline void pha::setDatatype(const string value)
{
  m_Datatype = value;
}
  
inline string pha::getSpectrumtype() const
{
  return m_Spectrumtype;
}
inline void pha::setSpectrumtype(const string value)
{
  m_Spectrumtype = value;
}

inline string pha::getResponseFile() const
{
  return m_ResponseFile;
}
inline void pha::setResponseFile(const string value)
{
  m_ResponseFile = value;
}

inline string pha::getAncillaryFile() const
{
  return m_AncillaryFile;
}
inline void pha::setAncillaryFile(const string value)
{
  m_AncillaryFile = value;
}

inline string pha::getBackgroundFile() const
{
  return m_BackgroundFile;
}
inline void pha::setBackgroundFile(const string value)
{
  m_BackgroundFile = value;
}

inline string pha::getCorrectionFile() const
{
  return m_CorrectionFile;
}
inline void pha::setCorrectionFile(const string value)
{
  m_CorrectionFile = value;
}
  
inline string pha::getFluxUnits() const
{
  return m_FluxUnits;
}
inline void pha::setFluxUnits(const string value)
{
  m_FluxUnits = value;
}

inline string pha::getChannelType() const
{
  return m_ChannelType;
}
inline void pha::setChannelType(const string value)
{
  m_ChannelType = value;
}

inline string pha::getTelescope() const
{
  return m_Telescope;
}
inline void pha::setTelescope(const string value)
{
  m_Telescope = value;
}

inline string pha::getInstrument() const
{
  return m_Instrument;
}
inline void pha::setInstrument(const string value)
{
  m_Instrument = value;
}

inline string pha::getDetector() const
{
  return m_Detector;
}
inline void pha::setDetector(const string value)
{
  m_Detector = value;
}

inline string pha::getFilter() const
{
  return m_Filter;
}
inline void pha::setFilter(const string value)
{
  m_Filter = value;
}

inline string pha::getDatamode() const
{
  return m_Datamode;
}
inline void pha::setDatamode(const string value)
{
  m_Datamode = value;
}

inline const vector<string>& pha::getXSPECFilter() const
{
  return m_XSPECFilter;
}
inline Integer pha::setXSPECFilter(const vector<string>& values)
{
  m_XSPECFilter.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_XSPECFilter[i] = values[i];
  return OK;
}
inline string pha::getXSPECFilterElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_XSPECFilter.size() ) {
    return m_XSPECFilter[i];
  } else {
    return "";
  }
}
inline Integer pha::setXSPECFilterElement(const Integer i, const string value)
{
  if ( i >= 0 && i < (Integer)m_XSPECFilter.size() ) {
    m_XSPECFilter[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

