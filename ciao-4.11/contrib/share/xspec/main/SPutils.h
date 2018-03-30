// Useful functions - mostly using CCfits

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPio
#include "SPio.h"
#endif

#define HAVE_SPutils 1

// Read the units associated with a column

void SPreadColUnits(ExtHDU&, string, string&);

// Write the units associated with a column

void SPwriteColUnits(Table&, string, string);

// returns the tform string for the longest string in the input vector.

string SPstringTform(const vector<string>& Data);

// copy from infile to outfile all HDUs which are not manipulated by this library 

Integer SPcopyHDUs(string infile, string outfile);

// copy non-critical columns from infile to outfile for the HDUnumber instance
// of the HDUname HDU.
// note that the SPcopyCols do not do anything yet since they are waiting for
// a change to CCfits

Integer SPcopyCols(string infile, string outfile, string HDUname, Integer HDUnumber);

// copy non-critical columns from infile to outfile from the HDUnumber instance
// of the HDUname HDU to the outHDUnumber instance of the outHDUname HDU.

Integer SPcopyCols(string infile, string outfile, string HDUname, string outHDUname,
		   Integer HDUnumber, Integer outHDUnumber);

// copy non-critical keywords from infile to outfile for the HDUnumber instance
// of the HDUname HDU.

Integer SPcopyKeys(string infile, string outfile, string HDUname, Integer HDUnumber);

// copy non-critical keywords from infile to outfile from the HDUnumber instance
// of the HDUname HDU to the outHDUnumber instance of the outHDUname HDU.

Integer SPcopyKeys(string infile, string outfile, string HDUname, string outHDUname,
		   Integer HDUnumber, Integer outHDUnumber);

// write the creating program and version id string into the CREATOR keyword in the
// specified file

Integer SPwriteCreator(string filename, string HDUname, string creator);
Integer SPwriteCreator(string filename, string HDUname, Integer HDUnumber, string creator);

// find the numbers of any extensions containing keyword keyname=keyvalue

vector<Integer> SPfindExtensions(string filename, string keyname, string value, Integer& Status);

// Check whether valid X units

bool isValidXUnits(string xUnits);

// Calculate the unit conversion factor for energy/wavelength

Integer calcXfactor(string xUnits, bool& isWave, Real& xFactor);

// Check whether valid Y units

bool isValidYUnits(string yUnits);

// Calculate the unit conversion factor for the flux

Integer calcYfactor(string yUnits, bool& isEnergy, bool& perWave, bool& perEnergy, Real& yFactor);

// Add to the error stack

void SPreportError(int errorNumber, string optionalString);

// Output error stack

string SPgetErrorStack();

// Clear error stack

void SPclearErrorStack();

// Read a text file and place each row into its own element of a vector<string>

vector<string> SPreadStrings(const string& filename);

// Divide a string into substrings delimited using delim

vector<string> SPtokenize(const string & str, const string & delim);

// Partial match a string from a vector of strings

string SPmatchString(const string& str, const vector<string>& strArray, int& nmatch);

// convert a string into a Real

bool SPstring2Real(const vector<string>& str, vector<Real>& value);
bool SPstring2Real(const string& str, Real& value);

// convert a string into a double

bool SPstring2double(const vector<string>& str, vector<double>& value);
bool SPstring2double(const string& str, double& value);

// convert a string into a float

bool SPstring2float(const vector<string>& str, vector<float>& value);
bool SPstring2float(const string& str, float& value);

// convert a string into an Integer

bool SPstring2Integer(const vector<string>& str, vector<Integer>& value);
bool SPstring2Integer(const string& str, Integer& value);

// convert a string of delimited range specifications of form n1"delim2"n2 
// meaning n1 to n2 inclusive or n3 meaning just n3. Ranges are delimited
// using delim1.

bool SPrangeString2IntegerList(const string& str, const string& delim1, 
			       const string& delim2, vector<Integer>& list);

// calculate factors for shifting an array

void SPcalcShift(const vector<Real>& Low, const vector<Real>& High, 
		 const vector<Integer>& vStart, const vector<Integer>& vEnd, 
		 const vector<Real>& vShift, const vector<Real>& vFactor, 
		 vector<vector<size_t> >& fromIndex, vector<vector<Real> >& Fraction);

// if array is increasing the index is the last element in array <= target; if 
// target < array[0] then index = -1; if target >= array[N-1] then index = N-1.
// if array is decreasing the index is the last element in array >= target; if
// target > array[0] then index = -1; if target <= array[N-1] then index = N-1.
// template class T can be either vector or valarray of Real or Integer

template <class T> void SPfind(const T& array, const Real& target, Integer& index);

// handy routine to do bisection search between indices lower and upper

template <class T> void SPbisect(Integer& lower, Integer& upper, const T& array,
				 const Real& target, bool increasing);
