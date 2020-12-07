// Class definitions for the Magzdiarz and Zdziarski Compton reflection models

#include <xsTypes.h>
#include <XSstreams.h>
#include <functionMap.h>
#include <XSFunctions/Utilities/FunctionUtility.h>
#include <XSFunctions/Utilities/xsFortran.h>
#include <XSUtil/Utils/XSutility.h>
#include <cfortran.h>

using namespace std;

//  ranges for different methods
#define XMIN 2.E-4                    // = 0.1022 keV
#define XTRANSL 0.01957               // = 10.00027 keV
#define XTRANSH 0.02348               // = 11.99828 keV
#define YMIN 0.03333                  // = 15,330 keV

#define XJL  log(XTRANSL)
#define XJD (log(XTRANSH) - XJL)

#define SQ3 1.732051

// class definition

class MZCompRefl{
 public:

  MZCompRefl();         // default constructor
  ~MZCompRefl();        // default destructor

  void CalcReflection(string RootName, Real cosIncl, Real xnor, Real Xmax,
		      RealArray& InputX, RealArray& InputSpec, RealArray& Spref);

  RealArray CalculateIntegrand(const RealArray& y0);

 private:

  RealArray X;               // Input energies (m_e c^2 units)
  RealArray Spinc;           // Input spectrum

  RealArray pm1;
  RealArray pmx;
  RealArray ap;

  Real pmymax;

  Real Xmax;
  Real Precision;
  Real ysource;              // (1/energy) of input photon

  void InterpolatedSpectrum(const RealArray& y, RealArray& sout);  // return array of spectra for given 1/X values
  void InterpolatedValue(const Real y, Real& sout);  // return single spectrum value for input 1/X.

  void WriteSpectrum(const string filename);  // for diagnostic purposes - write X, Spinc arrays to file

  void IntegrandSetup(const Real y);

};

// C++ functions used by these classes

void calcCompReflTotalFlux(string ModelName, Real Scale, Real cosIncl, Real Abund, 
			   Real FeAbund, Real Xi, Real Temp, Real inXmax, 
			   RealArray& X, RealArray& Spinc, RealArray& Sptot);
void calcCompReflTotalFluxOld(string ModelName, Real Scale, Real cosIncl, Real Abund, 
			      Real FeAbund, Real Xi, Real Temp, Real inXmax, Real Gamma,
			      RealArray& X, RealArray& Spinc, RealArray& Sptot);
void CalcNonRelComp(const Real cosIncl, const RealArray& X, const RealArray& opac, RealArray& NonRel);
void grxy(const RealArray& pm1, const RealArray& pmx, const Real y, const RealArray& y0, const RealArray& ap, RealArray& grout);
Real aic(const Real y0, const Real dy, const Real apc);
void pmxy(const Real Xm, RealArray& Pmx);
void pm1y(const Real Xm, RealArray& Pm1);
Real apf (const Real x);

// this is a wrapper routine for MZCompRefl::CalculateIntegrand with void *p
// being used to pass in the MZCompRefl object.

RealArray MZCompReflIntegrand(const RealArray& y0, void *p);
