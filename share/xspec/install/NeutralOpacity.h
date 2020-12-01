// Class for neutral opacity

#include <xsTypes.h>
#include <XSFunctions/Utilities/FunctionUtility.h>
#include <XSstreams.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;

#define LYLIMIT 0.0135984      // Lyman limit in keV

class NeutralOpacity{
 public:

  IntegerVector AtomicNumber;
  vector<string> ElementName;

  string CrossSectionSource;

  NeutralOpacity();     // default constructor
  ~NeutralOpacity();    // destructor

  void Setup();   // set up opacities
  void Get(RealArray inputEnergy, Real Abundance, Real IronAbundance, bool IncludeHHe, RealArray& Opacity);  // return opacities 
  void GetValue(Real inputEnergy, Real Abundance, Real IronAbundance, bool IncludeHHe, Real& Opacity);  // return single opacity 

};
