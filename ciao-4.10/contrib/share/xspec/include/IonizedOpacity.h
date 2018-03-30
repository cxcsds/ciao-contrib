// Class for ionized opacity

#include <xsTypes.h>
#include <XSstreams.h>
#include <functionMap.h>
#include <FunctionUtility.h>
#include <XSUtil/FunctionUtils/xsFortran.h>
#include <XSUtil/Utils/XSutility.h>
#include <cfortran.h>
#include <fstream>
#include <iostream>

using namespace std;

class IonizedOpacity{
 public:

  IntegerArray AtomicNumber;
  vector<string> ElementName;

  RealArray Energy;

  RealArray **ion;
  RealArray **sigma;
  RealArray *num;

  IonizedOpacity();     // default constructor
  ~IonizedOpacity();    // destructor

  void LoadFiles();     // internal routine to load model data files
  void Setup(Real Xi, Real Temp, RealArray inputEnergy, RealArray inputSpectrum);   // set up opacities
  void Get(RealArray inputEnergy, Real Abundance, Real IronAbundance, bool IncludeHHe, RealArray& Opacity);  // return opacities 
  void GetValue(Real inputEnergy, Real Abundance, Real IronAbundance, bool IncludeHHe, Real& Opacity);  // return single opacity 

};
