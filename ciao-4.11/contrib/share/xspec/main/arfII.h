// Definition of the arfII object. Just a wrap-up for a vector array of arf objects

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_arf
#include "arf.h"
#endif

#define HAVE_arfII 1

class arfII{
 public:

  vector<arf> arfs;           // vector of arf objects

  // constructor

  arfII();

  // destructor

  ~arfII();

  // read file into object. 

  Integer read(string filename);
  Integer read(string filename, Integer ARFnumber);
  Integer read(string filename, Integer ARFnumber, vector<Integer> RowNumber);

  // Deep copy

  arfII& operator= (const arfII&);

  // Get arf object (counts from zero).

  arf get(Integer number);

  // Push arf object into arfII object

  void push(arf ea);

  // Return information

  Integer NumberARFs();          // Number of ARFs in the object

  // Display information about the ARFs - return as a string

  string disp();

  // Clear information from the ARFs

  void clear();

  // Check completeness and consistency of information in arfs
  // if there is a problem then return diagnostic in string

  string check();

  // Write ARFs as type II file

  Integer write(string filename);
  Integer write(string filename, string copyfilename);
  Integer write(string filename, string copyfilename, Integer HDUnumber);

};

// return the number of ARFs in a type II ARF extension

Integer NumberofARFs(string filename, Integer HDUnumber);
Integer NumberofARFs(string filename, Integer HDUnumber, Integer& Status);
