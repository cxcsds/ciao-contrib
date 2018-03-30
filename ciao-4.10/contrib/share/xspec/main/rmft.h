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

  Integer FirstChannel;              // First channel number 

  vector<Integer> NumberGroups;        // Number of response groups for this channel bin 
  vector<Integer> FirstGroup;          // First response group for this channel bin (counts from 0)

  vector<Integer> FirstEnergyGroup;    // First energy bin in this group 
  vector<Integer> NumberEnergiesGroup; // Number of energy bins in this group 
  vector<Integer> FirstElement;        // First response element for this group (counts from 0)
  vector<Integer> OrderGroup;          // The grating order of this group 

  vector<Real> LowEnergy;              // Start energy of bin 
  vector<Real> HighEnergy;             // End energy of bin 

  vector<Real> Matrix;                 // Matrix elements 

  vector<Real> ChannelLowEnergy;       // Start energy of channel 
  vector<Real> ChannelHighEnergy;      // End energy of channel 

  Real AreaScaling;                 // Value of EFFAREA keyword 
  Real ResponseThreshold;           // Minimum value in response 

  string EnergyUnits;               // Energy units
  string RMFUnits;                  // RMF units

  string ChannelType;               // Value of CHANTYPE keyword 
  string RMFVersion;                // MATRIX extension format version 
  string EBDVersion;                // EBOUNDS extension format version 
  string Telescope;                             
  string Instrument;
  string Detector;
  string Filter;
  string RMFType;                   // Value of HDUCLAS3 keyword in MATRIX extension 
  string RMFExtensionName;          // Value of EXTNAME keyword in MATRIX extension 
  string EBDExtensionName;          // Value of EXTNAME keyword in EBOUNDS extension 

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

  // Return information

  Integer NumberChannels();               // Number of spectrum channels 
  Integer NumberEnergyBins();             // Number of response energies 
  Integer NumberTotalGroups();            // Total number of response groups 
  Integer NumberTotalElements();          // Total number of response elements 

  Real ElementValue(Integer, Integer);    // Return the value for a particular channel
                                          // and energy

  vector<Real> RowValues(Integer);          // Return the array for a particular channel

  // Display information about the object - return as a string

  string disp();

  // Clear information from the object

  void clear();

};

