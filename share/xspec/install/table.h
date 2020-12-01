// Class definition for table model object

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#define HAVE_table 1

// class definition for individual parameters within the table model

class tableParameter{
 public:

  //constructors

  tableParameter();
  tableParameter(const string name, const Integer interp, const Real initial,
    		 const Real delta, const Real min, const Real bot, const Real top,
    		 const Real max, const vector<Real>& values = vector<Real>());

  // destructor

  ~tableParameter();

  // load method
  
  void load(const string name, const Integer interp, const Real initial,
  	    const Real delta, const Real min, const Real bot, const Real top,
  	    const Real max, const vector<Real>& values = vector<Real>());

  // display information about the table parameter - return as a string

  string disp() const;

  // clear contents of the table parameter (mainly useful for Python)

  void clear();

  // return the number of tabulated values

  Integer NumberTabulatedValues() const;
  Integer getNumberTabulatedValues() const;

  // methods to get and set internal data
  
  string getName() const;
  void setName(const string value);
  Integer getInterpolationMethod() const;
  void setInterpolationMethod(const Integer value);
  Real getInitialValue() const;
  void setInitialValue(const Real value);
  Real getDelta() const;
  void setDelta(const Real value);
  Real getMinimum() const;
  void setMinimum(const Real value);
  Real getBottom() const;
  void setBottom(const Real value);
  Real getTop() const;
  void setTop(const Real value);
  Real getMaximum() const;
  void setMaximum(const Real value);
  const vector<Real>& getTabulatedValues() const;
  Integer setTabulatedValues(const vector<Real>& values);
  Real getTabulatedValuesElement(const Integer i) const;
  Integer setTabulatedValuesElement(const Integer i, const Real value);

  // internal data
 private:
  
  string m_Name;                  // Parameter name
  Integer m_InterpolationMethod;      // 0==linear, 1==log, -1==additional (non-interp)
  Real m_InitialValue;            // Initial value for fit
  Real m_Delta;                   // Delta for fit
  Real m_Minimum;                 // Hard lower-limit (should correspond to first tabulated value)
  Real m_Bottom;                  // Soft lower-limit
  Real m_Top;                     // Soft upper-limit
  Real m_Maximum;                 // Hard upper-limit (should correspond to last tabulated value)
  vector<Real> m_TabulatedValues; // Tabulated parameter values
  
};

// return the number of tabulated values

inline Integer tableParameter::NumberTabulatedValues() const
{
  return m_TabulatedValues.size();
}
inline Integer tableParameter::getNumberTabulatedValues() const
{
  return m_TabulatedValues.size();
}


inline string tableParameter::getName() const
{
  return m_Name;
}
inline void tableParameter::setName(const string value)
{
  m_Name = value;
}
inline Integer tableParameter::getInterpolationMethod() const
{
  return m_InterpolationMethod;
}
inline void tableParameter::setInterpolationMethod(const Integer value)
{
  m_InterpolationMethod = value;
}
inline Real tableParameter::getInitialValue() const
{
  return m_InitialValue;
}
inline void tableParameter::setInitialValue(const Real value)
{
  m_InitialValue = value;
}
inline Real tableParameter::getDelta() const
{
  return m_Delta;
}
inline void tableParameter::setDelta(const Real value)
{
  m_Delta = value;
}
inline Real tableParameter::getMinimum() const
{
  return m_Minimum;
}
inline void tableParameter::setMinimum(const Real value)
{
  m_Minimum = value;
}
inline Real tableParameter::getBottom() const
{
  return m_Bottom;
}
inline void tableParameter::setBottom(const Real value)
{
  m_Bottom = value;
}
inline Real tableParameter::getTop() const
{
  return m_Top;
}
inline void tableParameter::setTop(const Real value)
{
  m_Top = value;
}
inline Real tableParameter::getMaximum() const
{
  return m_Maximum;
}
inline void tableParameter::setMaximum(const Real value)
{
  m_Maximum = value;
}
inline const vector<Real>& tableParameter::getTabulatedValues() const
{
  return m_TabulatedValues;
}
inline Integer tableParameter::setTabulatedValues(const vector<Real>& values)
{
  m_TabulatedValues.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_TabulatedValues[i] = values[i];
  return OK;
}
inline Real tableParameter::getTabulatedValuesElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_TabulatedValues.size() ) {
    return m_TabulatedValues[i];
  } else {
    return -999.;
  }
}
inline Integer tableParameter::setTabulatedValuesElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_TabulatedValues.size() ) {
    m_TabulatedValues[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}


// class definition for individual spectra (and additional spectra) within the table model

class tableSpectrum{
 public:

  // constructors

  tableSpectrum();
  tableSpectrum(const vector<Real>& parVals, const vector<Real>& flux,
  		const vector<vector<Real> >& addFlux = vector<vector<Real> >(),
  		const vector<Real>& fluxErr = vector<Real>(),
  		const vector<vector<Real> >& addFluxErr = vector<vector<Real> >());

  // destructor

  ~tableSpectrum();

  // load method
  
  void load(const vector<Real>& parVals, const vector<Real>& flux,
  	    const vector<vector<Real> >& addFlux = vector<vector<Real> >(),
  	    const vector<Real>& fluxErr = vector<Real>(),
  	    const vector<vector<Real> >& addFluxErr = vector<vector<Real> >());
	    
  // push an additional parameter spectrum

  void pushaddFlux(vector<Real>);

  // display information about the table spectrum - return as a string

  string disp() const;

  // clear contents of the table spectrum (mainly useful for Python)

  void clear();

  // routines to return some useful sizes

  Integer NumberFluxes() const;
  Integer getNumberFluxes() const;
  Integer NumberFluxErrors() const;
  Integer getNumberFluxErrors() const;
  Integer NumberParameterValues() const;
  Integer getNumberParameterValues() const;
  Integer NumberAdditiveParameters() const;
  Integer getNumberAdditiveParameters() const;
  Integer NumberAdditiveFluxes(const Integer iaddParam) const;
  Integer getNumberAdditiveFluxes(const Integer iaddParam) const;
  Integer NumberAdditiveFluxErrors(const Integer iaddParam) const;
  Integer getNumberAdditiveFluxErrors(const Integer iaddParam) const;

  // get and set methods for internal data
  
  const vector<Real>& getFlux() const;
  Integer setFlux(const vector<Real>& values);
  Real getFluxElement(const Integer i) const;
  Integer setFluxElement(const Integer i, const Real value);
  const vector<Real>& getFluxError() const;
  Integer setFluxError(const vector<Real>& values);
  Real getFluxErrorElement(const Integer i) const;
  Integer setFluxErrorElement(const Integer i, const Real value);
  const vector<Real>& getParameterValues() const;
  Integer setParameterValues(const vector<Real>& values);
  Real getParameterValuesElement(const Integer i) const;
  Integer setParameterValuesElement(const Integer i, const Real value);
  const vector<vector<Real> >& getaddFlux() const;
  Integer setaddFlux(const vector<vector<Real> >& values);
  const vector<Real>& getaddFluxElement(const Integer iparam) const;
  Integer setaddFluxElement(const Integer iparam, const vector<Real>& valueparam);
  Real getaddFluxElementElement(const Integer iparam, const Integer i) const;
  Integer setaddFluxElementElement(const Integer iparam, const Integer i, const Real value);
  const vector<vector<Real> >& getaddFluxError() const;
  Integer setaddFluxError(const vector<vector<Real> >& values);
  const vector<Real>& getaddFluxErrorElement(const Integer iparam) const;
  Integer setaddFluxErrorElement(const Integer iparam, const vector<Real>& valueparam);
  Real getaddFluxErrorElementElement(const Integer iparam, const Integer i) const;
  Integer setaddFluxErrorElementElement(const Integer iparam, const Integer i, const Real value);

  // internal data
 private:
  
  vector<Real> m_Flux;
  vector<Real> m_FluxError;
  vector<Real> m_ParameterValues;
  vector<vector<Real> > m_addFlux;
  vector<vector<Real> > m_addFluxError;

};

// routines to return some useful sizes

inline Integer tableSpectrum::NumberFluxes() const
{
  return m_Flux.size();
}
inline Integer tableSpectrum::getNumberFluxes() const
{
  return m_Flux.size();
}
inline Integer tableSpectrum::NumberFluxErrors() const
{
  return m_FluxError.size();
}
inline Integer tableSpectrum::getNumberFluxErrors() const
{
  return m_FluxError.size();
}
inline Integer tableSpectrum::NumberParameterValues() const
{
  return m_ParameterValues.size();
}
inline Integer tableSpectrum::getNumberParameterValues() const
{
  return m_ParameterValues.size();
}
inline Integer tableSpectrum::NumberAdditiveParameters() const
{
  return m_addFlux.size();
}
inline Integer tableSpectrum::getNumberAdditiveParameters() const
{
  return m_addFlux.size();
}
inline Integer tableSpectrum::NumberAdditiveFluxes(const Integer iaddParam) const
{
  return m_addFlux[iaddParam].size();
}
inline Integer tableSpectrum::getNumberAdditiveFluxes(const Integer iaddParam) const
{
  return m_addFlux[iaddParam].size();
}
inline Integer tableSpectrum::NumberAdditiveFluxErrors(const Integer iaddParam) const
{
  return m_addFluxError[iaddParam].size();
}
inline Integer tableSpectrum::getNumberAdditiveFluxErrors(const Integer iaddParam) const
{
  return m_addFluxError[iaddParam].size();
}



inline const vector<Real>& tableSpectrum::getFlux() const
{
  return m_Flux;
}
inline Integer tableSpectrum::setFlux(const vector<Real>& values)
{
  m_Flux.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Flux[i] = values[i];
  return OK;
}
inline Real tableSpectrum::getFluxElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Flux.size() ) {
    return m_Flux[i];
  } else {
    return -999.;
  }
}
inline Integer tableSpectrum::setFluxElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_Flux.size() ) {
    m_Flux[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline const vector<Real>& tableSpectrum::getFluxError() const
{
  return m_FluxError;
}
inline Integer tableSpectrum::setFluxError(const vector<Real>& values)
{
  m_FluxError.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_FluxError[i] = values[i];
  return OK;
}
inline Real tableSpectrum::getFluxErrorElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_FluxError.size() ) {
    return m_FluxError[i];
  } else {
    return -999.;
  }
}
inline Integer tableSpectrum::setFluxErrorElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_FluxError.size() ) {
    m_FluxError[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline const vector<Real>& tableSpectrum::getParameterValues() const
{
  return m_ParameterValues;
}
inline Integer tableSpectrum::setParameterValues(const vector<Real>& values)
{
  m_ParameterValues.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_ParameterValues[i] = values[i];
  return OK;
}
inline Real tableSpectrum::getParameterValuesElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_ParameterValues.size() ) {
    return m_ParameterValues[i];
  } else {
    return -999.;
  }
}
inline Integer tableSpectrum::setParameterValuesElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_ParameterValues.size() ) {
    m_ParameterValues[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline const vector<vector<Real> >& tableSpectrum::getaddFlux() const
{
  return m_addFlux;
}
inline Integer tableSpectrum::setaddFlux(const vector<vector<Real> >& values)
{
  m_addFlux.resize(values.size());
  for (size_t i=0; i<values.size(); i++) {
    m_addFlux[i].resize(values[i].size());
    for (size_t j=0; j<values[i].size(); j++) {
      m_addFlux[i][j] = values[i][j];
    }
  }
  return OK;
}
inline const vector<Real>& tableSpectrum::getaddFluxElement(const Integer iparam) const
{
  if ( iparam >= 0 && iparam < (Integer)m_addFlux.size() ) {
    return m_addFlux[iparam];
  } else {
    if ( iparam < 0 ) {
      return m_addFlux[0];
    } else {
      return m_addFlux[m_addFlux.size()-1];
    }
  }
}
inline Integer tableSpectrum::setaddFluxElement(const Integer iparam, const vector<Real>& values)
{
  if ( iparam >= 0 && iparam < (Integer)m_addFlux.size() ) {
    m_addFlux[iparam].resize(values.size());
    for (size_t j=0; j<values.size(); j++) m_addFlux[iparam][j] = values[j];
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline Real tableSpectrum::getaddFluxElementElement(const Integer iparam, const Integer i) const
{
  if ( iparam >= 0 && iparam < (Integer)m_addFlux.size() &&
       i >= 0 && i < (Integer)m_addFlux[iparam].size() ) {
    return m_addFlux[iparam][i];
  } else {
    return -999.;
  }
}
inline Integer tableSpectrum::setaddFluxElementElement(const Integer iparam, const Integer i, const Real value)
{
  if ( iparam >= 0 && iparam < (Integer)m_addFlux.size() &&
       i >= 0 && i < (Integer)m_addFlux[iparam].size() ) {
    m_addFlux[iparam][i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline const vector<vector<Real> >& tableSpectrum::getaddFluxError() const
{
  return m_addFluxError;
}
inline Integer tableSpectrum::setaddFluxError(const vector<vector<Real> >& values)
{
  m_addFluxError.resize(values.size());
  for (size_t i=0; i<values.size(); i++) {
    m_addFluxError[i].resize(values[i].size());
    for (size_t j=0; j<values[i].size(); j++) {
      m_addFluxError[i][j] = values[i][j];
    }
  }
  return OK;
}
inline const vector<Real>& tableSpectrum::getaddFluxErrorElement(const Integer iparam) const
{
  if ( iparam >= 0 && iparam < (Integer)m_addFluxError.size() ) {
    return m_addFluxError[iparam];
  } else {
    if ( iparam < 0 ) {
      return m_addFluxError[iparam];
    } else {
      return m_addFluxError[m_addFluxError.size()-1];
    }
  }
}
inline Integer tableSpectrum::setaddFluxErrorElement(const Integer iparam, const vector<Real>& values)
{
  if ( iparam >= 0 && iparam < (Integer)m_addFluxError.size() ) {
    m_addFluxError[iparam].resize(values.size());
    for (size_t j=0; j<values.size(); j++) m_addFluxError[iparam][j] = values[j];
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

inline Real tableSpectrum::getaddFluxErrorElementElement(const Integer iparam, const Integer i) const
{
  if ( iparam >= 0 && iparam < (Integer)m_addFluxError.size() &&
       i >= 0 && i < (Integer)m_addFluxError[iparam].size() ) {
    return m_addFluxError[iparam][i];
  } else {
    return -999.;
  }
}
inline Integer tableSpectrum::setaddFluxErrorElementElement(const Integer iparam, const Integer i, const Real value)
{
  if ( iparam >= 0 && iparam < (Integer)m_addFluxError.size() &&
       i >= 0 && i < (Integer)m_addFluxError[iparam].size() ) {
    m_addFluxError[iparam][i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}


// class definition for table

class table{
 public:

  // constructors

  table();
  table(const table& a);
  table(const string infilename, bool loadAll = true);
  table(const string modName, const string modUnits, const Integer nInt,
  	const Integer nAdd, const bool isz, const bool isAdd,
  	const string eUnits, const Real lowElim, const Real highElim,
  	const string filename, const vector<Real>& energies = vector<Real>(),
  	const vector<tableParameter>& paramObjects = vector<tableParameter>(),
  	const vector<tableSpectrum>& spectrumObjects = vector<tableSpectrum>(),
  	const bool isErr = false);

  // destructor

  ~table();

  // load method
  
  void load(const string modName, const string modUnits, const Integer nInt,
  	    const Integer nAdd, const bool isz, const bool isAdd,
  	    const string eUnits, const Real lowElim, const Real highElim,
  	    const string filename, const vector<Real>& energies = vector<Real>(),
  	    const vector<tableParameter>& paramObjects = vector<tableParameter>(),
  	    const vector<tableSpectrum>& spectrumObjects = vector<tableSpectrum>(),
  	    const bool isErr = false);

  // read the table from a FITS file. if loadAll is false then don't actually
  // read in the Spectra but set up the objects

  Integer read(const string infilename, bool loadAll = true);

  // read the listed Spectra

  template <class T> Integer readSpectra(T& spectrumList); 

  // Push table Parameter object

  void pushParameter(const tableParameter& paramObject);

  // Push table Spectrum object

  void pushSpectrum(const tableSpectrum& spectrumObject);

  // Get table Parameter object (counts from zero)

  tableParameter getParameter(const Integer number) const;

  // get table Spectrum object (counts from zero)

  tableSpectrum getSpectrum(const Integer number) const;

  // deep copy

  table& copy(const table& a);
  table& operator= (const table& a);

  // display information about the table - return as a string

  string disp(const bool headerOnly) const;

  // clear contents of table object (mainly useful for Python)

  void clear();

  // check for completeness and consistency of information in the table
  // if there is a problem then return diagnostic in string

  string check() const;

  // convert to standard units (keV and ph/cm^2/s).

  Integer convertUnits();

  // reverse the rows if energies are not increasing (as can occur eg after
  // converting from wavelength)

  void reverseRows();

  // write to a FITS file

  Integer write(string outfilename) const;

  // get values from table for input parameters using interpolation.

  template <class T> Integer getValues(const T& parameterValues, const Real minEnergy,
				       const Real maxEnergy, T& tableEnergyBins, 
				       T& tableValues, T& tableErrors);

  // useful routines to return sizes

  Integer NumberParameters() const;
  Integer getNumberParameters() const;
  Integer NumberSpectra() const;
  Integer getNumberSpectra() const;
  Integer NumberEnergies() const;
  Integer getNumberEnergies() const;

  // methods to set and get internal data
  
  const vector<tableParameter>& getParameters() const;
  Integer setParameters(const vector<tableParameter>& values);
  tableParameter getParametersElement(const Integer i) const;
  Integer setParametersElement(const Integer i, const tableParameter& value);
  const vector<tableSpectrum>& getSpectra() const;
  Integer setSpectra(const vector<tableSpectrum>& values);
  tableSpectrum getSpectraElement(const Integer i) const;
  Integer setSpectraElement(const Integer i, const tableSpectrum& value);
  string getModelName() const;
  void setModelName(const string value);
  string getModelUnits() const;
  void setModelUnits(const string value);
  Integer getNumIntParams() const;
  void setNumIntParams(const Integer value);
  Integer getNumAddParams() const;
  void setNumAddParams(const Integer value);
  bool getisError() const;
  void setisError(const bool value);
  bool getisRedshift() const;
  void setisRedshift(const bool value);
  bool getisAdditive() const;
  void setisAdditive(const bool value);
  const vector<Real>& getEnergies() const;
  Integer setEnergies(const vector<Real>& values);
  Real getEnergiesElement(const Integer i) const;
  Integer setEnergiesElement(const Integer i, const Real value);
  string getEnergyUnits() const;
  void setEnergyUnits(const string value);
  Real getLowEnergyLimit() const;
  void setLowEnergyLimit(const Real value);
  Real getHighEnergyLimit() const;
  void setHighEnergyLimit(const Real value);
  string getFilename() const;
  void setFilename(const string value);

  // internal data
 private:
  
  vector<tableParameter> m_Parameters;
  vector<tableSpectrum> m_Spectra;
  string m_ModelName;
  string m_ModelUnits;
  Integer m_NumIntParams;
  Integer m_NumAddParams;
  bool m_isError;
  bool m_isRedshift;
  bool m_isAdditive;
  vector<Real> m_Energies;
  string m_EnergyUnits;
  Real m_LowEnergyLimit;
  Real m_HighEnergyLimit;
  string m_Filename;
  
};

// useful routines to return sizes

inline Integer table::NumberParameters() const
{
  return m_Parameters.size();
}
inline Integer table::getNumberParameters() const
{
  return m_Parameters.size();
}
inline Integer table::NumberSpectra() const 
{
  return m_Spectra.size();
}
inline Integer table::getNumberSpectra() const 
{
  return m_Spectra.size();
}
inline Integer table::NumberEnergies() const 
{
  return m_Energies.size();
}
inline Integer table::getNumberEnergies() const 
{
  return m_Energies.size();
}


inline const vector<tableParameter>& table::getParameters() const
{
  return m_Parameters;
}
inline Integer table::setParameters(const vector<tableParameter>& values)
{
  m_Parameters.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Parameters[i] = values[i];
  return OK;
}
inline tableParameter table::getParametersElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Parameters.size() ) {
    return m_Parameters[i];
  } else {
    tableParameter nothing;
    return nothing;
  }
}
inline Integer table::setParametersElement(const Integer i, const tableParameter& value)
{
  if ( i >= 0 && i < (Integer)m_Parameters.size() ) {
    m_Parameters[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline const vector<tableSpectrum>& table::getSpectra() const
{
  return m_Spectra;
}
inline Integer table::setSpectra(const vector<tableSpectrum>& values)
{
  m_Spectra.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Spectra[i] = values[i];
  return OK;
}
inline tableSpectrum table::getSpectraElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Spectra.size() ) {
    return m_Spectra[i];
  } else {
    tableSpectrum nothing;
    return nothing;
  }
}
inline Integer table::setSpectraElement(const Integer i, const tableSpectrum& value)
{
  if ( i >= 0 && i < (Integer)m_Spectra.size() ) {
    m_Spectra[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline string table::getModelName() const
{
  return m_ModelName;
}
inline void table::setModelName(const string value)
{
  m_ModelName = value;
}
inline string table::getModelUnits() const
{
  return m_ModelUnits;
}
inline void table::setModelUnits(const string value)
{
  m_ModelUnits = value;
}
inline Integer table::getNumIntParams() const
{
  return m_NumIntParams;
}
inline void table::setNumIntParams(const Integer value)
{
  m_NumIntParams = value;
}
inline Integer table::getNumAddParams() const
{
  return m_NumAddParams;
}
inline void table::setNumAddParams(const Integer value)
{
  m_NumAddParams = value;
}
inline bool table::getisError() const
{
  return m_isError;
}
inline void table::setisError(const bool value)
{
  m_isError = value;
}
inline bool table::getisRedshift() const
{
  return m_isRedshift;
}
inline void table::setisRedshift(const bool value)
{
  m_isRedshift = value;
}
inline bool table::getisAdditive() const
{
  return m_isAdditive;
}
inline void table::setisAdditive(const bool value)
{
  m_isAdditive = value;
}
inline const vector<Real>& table::getEnergies() const
{
  return m_Energies;
}
inline Integer table::setEnergies(const vector<Real>& values)
{
  m_Energies.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_Energies[i] = values[i];
  return OK;
}
inline Real table::getEnergiesElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_Energies.size() ) {
    return m_Energies[i];
  } else {
    return -999.;
  }
}
inline Integer table::setEnergiesElement(const Integer i, const Real value)
{
  if ( i >= 0 && i < (Integer)m_Energies.size() ) {
    m_Energies[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
inline string table::getEnergyUnits() const
{
  return m_EnergyUnits;
}
inline void table::setEnergyUnits(const string value)
{
  m_EnergyUnits = value;
}
inline Real table::getLowEnergyLimit() const
{
  return m_LowEnergyLimit;
}
inline void table::setLowEnergyLimit(const Real value)
{
  m_LowEnergyLimit = value;
}
inline Real table::getHighEnergyLimit() const
{
  return m_HighEnergyLimit;
}
inline void table::setHighEnergyLimit(const Real value)
{
  m_HighEnergyLimit = value;
}
inline string table::getFilename() const
{
  return m_Filename;
}
inline void table::setFilename(const string value)
{
  m_Filename = value;
}
