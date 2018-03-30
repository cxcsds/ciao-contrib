// Definition of the SpectrumII object. Just a wrap-up for a vector array of Spectrum objects

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_pha
#include "pha.h"
#endif

#define HAVE_phaII 1

class phaII{
 public:

  vector<pha> phas;           // vector of pha objects

  // constructor

  phaII();

  // destructor

  ~phaII();

  // read file into object. 

  Integer read(string filename);
  Integer read(string filename, Integer PHAnumber);
  Integer read(string filename, Integer PHAnumber, vector<Integer> SpectrumNumber);

  // Deep copy

  phaII& operator= (const phaII&);

  // Get pha object (counts from zero).

  pha get(Integer number);

  // Push pha object into phaII object

  void push(pha spectrum);

  // Return information

  Integer NumberSpectra();          // Number of Spectra in the object

  // Display information about the spectra - return as a string

  string disp();

  // Clear information about the spectra

  void clear();

  // Check completeness and consistency of information in spectrum
  // if there is a problem then return diagnostic in string

  string check();

  // Write spectra as type II file

  Integer write(string filename);
  Integer write(string filename, string copyfilename);
  Integer write(string filename, string copyfilename, Integer HDUnumber);

};


