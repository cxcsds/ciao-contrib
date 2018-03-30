// Class definition for table model object

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#define HAVE_table 1

// class definition for individual parameters within the table model

class tableParameter{
 public:

  string Name;                  // Parameter name
  int InterpolationMethod;      // 0==linear, 1==log, -1==additional (non-interp)
  Real InitialValue;            // Initial value for fit
  Real Delta;                   // Delta for fit
  Real Minimum;                 // Hard lower-limit (should correspond to first tabulated value)
  Real Bottom;                  // Soft lower-limit
  Real Top;                     // Soft upper-limit
  Real Maximum;                 // Hard upper-limit (should correspond to last tabulated value)
  vector<Real> TabulatedValues; // Tabulated parameter values

  //constructor

  tableParameter();

  // destructor

  ~tableParameter();

  // display information about the table parameter - return as a string

  string disp();

  // clear contents of the table parameter (mainly useful for Python)

  void clear();

};

// class definition for individual spectra (and additional spectra) within the table model

class tableSpectrum{
 public:

  vector<Real> Flux;
  vector<Real> FluxError;
  vector<Real> ParameterValues;
  vector<vector<Real> > addFlux;
  vector<vector<Real> > addFluxError;

  //constructor

  tableSpectrum();

  // destructor

  ~tableSpectrum();

  // push an additional parameter spectrum

  void pushaddFlux(vector<Real>);

  // get an additional parameter spectrum

  vector<Real> getaddFlux(Integer Number);

  // display information about the table spectrum - return as a string

  string disp();

  // clear contents of the table spectrum (mainly useful for Python)

  void clear();

};

// class definition for table

class table{
 public:

  vector<tableParameter> Parameters;
  vector<tableSpectrum> Spectra;
  string ModelName;
  string ModelUnits;
  int NumIntParams;
  int NumAddParams;
  bool isError;
  bool isRedshift;
  bool isAdditive;
  vector<Real> Energies;
  string EnergyUnits;
  Real LowEnergyLimit;
  Real HighEnergyLimit;
  string Filename;
  
  // constructor

  table();

  // destructor

  ~table();

  // read the table from a FITS file. if loadAll is false then don't actually
  // read in the Spectra but set up the objects

  Integer read(string infilename);
  Integer read(string infilename, bool loadAll);

  // read the listed Spectra

  template <class T> Integer readSpectra(T& spectrumList); 

  // Push table Parameter object

  void pushParameter(const tableParameter& paramObject);

  // Push table Spectrum object

  void pushSpectrum(const tableSpectrum& spectrumObject);

  // Get table Parameter object (counts from zero)

  tableParameter getParameter(Integer number);

  // get table Spectrum object (counts from zero)

  tableSpectrum getSpectrum(Integer number);

  // display information about the table - return as a string

  string disp(const bool headerOnly);

  // clear contents of table object (mainly useful for Python)

  void clear();

  // check for completeness and consistency of information in the table
  // if there is a problem then return diagnostic in string

  string check();

  // convert to standard units (keV and ph/cm^2/s).

  Integer convertUnits();

  // reverse the rows if energies are not increasing (as can occur eg after
  // converting from wavelength)

  void reverseRows();

  // write to a FITS file

  Integer write(string outfilename);

  // get values from table for input parameters using interpolation.

  template <class T> Integer getValues(const T& parameterValues, const Real minEnergy,
				       const Real maxEnergy, T& tableEnergyBins, 
				       T& tableValues, T& tableErrors);

};
