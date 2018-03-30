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

  vector<Real> LowEnergy;                   // Start energy of bin
  vector<Real> HighEnergy;                  // End energy of bin

  vector<Real> EffArea;                     // Effective areas

  string EnergyUnits;                     // Units for energies
  string arfUnits;                        // Units for effective areas

  string Version;                        // SPECRESP extension format version
  string Telescope;                             
  string Instrument;
  string Detector;
  string Filter;
  string ExtensionName;               // Value of EXTNAME keyword in SPECRESP extension

  // constructor

  arf();

  // destructor

  ~arf();

  // read file into object. Third option is to read from a row of a type II file

  Integer read(string filename);
  Integer read(string filename, Integer ARFnumber);
  Integer read(string filename, Integer ARFnumber, Integer RowNumber);

  // Deep copy

  arf& operator= (const arf&);

  // Return information

  Integer NumberEnergyBins();            // size of RealArrays

  // Display information about the arf - return as a string

  string disp();

  // Clear information from the arf

  void clear();

  // Check completeness and consistency of information in arf
  // if there is a problem then return diagnostic in string

  string check();

  // Rebin 

  Integer rebin(grouping&);

  // Write arf

  Integer write(string filename);
  Integer write(string filename, string copyfilename);
  Integer write(string filename, string copyfilename, Integer HDUnumber);

  // Multiply by a constant

  arf& operator*=(const Real&);

  // Add arfs

  arf& operator+=(const arf&);

  Integer checkCompatibility(const arf&);

  Integer convertUnits();

};

// define this outside the class

arf operator+ (const arf&, const arf&);
arf operator* (const arf&, const Real&);
arf operator* (const Real&, const arf&);
