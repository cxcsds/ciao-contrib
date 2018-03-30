// definitions for heasp library

// all the includes

#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstdlib>
#include <cmath>
#include <cstdio>
#include <sstream>
#include <string>
#include <stdexcept>
#include <ctime>
#include <valarray>
#include <vector>
#include <algorithm>

#include <CCfits/CCfits>

// use the std and CCfits namespaces

using namespace std;
using namespace CCfits;

// define Integer and Real

typedef int Integer;
typedef double Real;

// and helpful to have definitions for some internal routines
// note this matches to xspec definitions

typedef vector<Integer> IntegerArray;
typedef valarray<Real> RealArray;

#define HAVE_HEASP 1

// set up error statuses

enum{OK, 
     NoSuchFile, NoData, NoChannelData, NoStatError, CannotCreate,
     NoEnergLo, NoEnergHi, NoSpecresp, NoEboundsExt, NoEmin, 
     NoEmax, NoMatrixExt, NoNgrp, NoFchan, NoNchan, 
     NoMatrix, CannotCreateMatrixExt, CannotCreateEboundsExt, InconsistentGrouping, InconsistentEnergies,
     InconsistentChannels, InconsistentUnits, UnknownXUnits, UnknownYUnits, InconsistentNumelt, 
     InconsistentNumgrp, InconsistentNumTableParams, TableParamValueOutsideRange};

const string SPerrorNames[] = 
  {"OK", "NoSuchFile", "NoData", "NoChannelData", "NoStatError", "CannotCreate",
   "NoEnergLo", "NoEnergHi", "NoSpecresp", "NoEboundsExt", "NoEmin", "NoEmax",
   "NoMatrixExt", "NoNgrp", "NoFchan", "NoNchan", "NoMatrix", "CannotCreateMatrixExt",
   "CannotCreateEboundsExt", "InconsistentGrouping", "InconsistentEnergies",
   "InconsistentChannels", "InconsistentUnits", "UnknownXUnits", "UnknownYUnits",
   "InconsistentNumelt", "InconsistentNumgrp", "InconsistentNumTableParams",
   "TableParamValueOutsideRange"};

// the error message stack

static vector<string> SPerrorStack;

// some useful conversion factors

#define KEVTOA 12.3984191
#define KEVTOHZ 2.4179884076620228e17
#define KEVTOERG 1.60217733e-9
#define KEVTOJY 1.60217733e14

static const Real FUZZY(1.0e-6);
