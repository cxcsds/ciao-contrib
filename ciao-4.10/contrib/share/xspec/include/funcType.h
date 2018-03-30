//
//  XSPEC12  November 2003
//
//

#ifndef FUNCTYPE_H
#define FUNCTYPE_H

 // Created: Ben Dorman L-3 Com EER Systems LHEA-NASA/GSFC V2.0 Jan 2003

#include <xsTypes.h>
#include <map>

class XSModelFunction;
class MixUtility;

typedef  std::map<string,XSModelFunction*> ModelFunctionMap;


extern "C" {

// standard XSPEC11 fortran 77 calls
	typedef void (xsf77Call) (const float* energyArray, 
                                  const int& Nenergy, 
                                  const float* parameterValues, 
                                  const int& spectrumNumber, 
                                  float* flux, 
                                  float* fluxError); 
// double precision fortran 77 calls
	typedef void (xsF77Call) (const double* energyArray, 
                                  const int& Nenergy, 
                                  const double* parameterValues, 
                                  const int& spectrumNumber, 
                                  double* flux, 
                                  double* fluxError); 
// C language calls using C arrays
        typedef void (xsccCall)   (const Real* energyArray, 
                                   int Nenergy, 
                                   const Real* parameterValues, 
                                   int spectrumNumber,
                                   Real* flux, 
                                   Real* fluxError, 
                                   const char* initString);
// C++ call with initialization string passed.
        typedef void (XSCCall) (const RealArray& energyArray, 
                                const RealArray& parameterValues,
                                int spectrumNumber,
                                RealArray& flux, 
                                RealArray& fluxError,
                                const std::string& initString);

        typedef void (XSMixCCall) (const EnergyPointer& energyArray,
                                  const std::vector<Real>& parameterValues,
                                  GroupFluxContainer& flux,
                                  GroupFluxContainer& fluxError,
                                  MixUtility* mixGenerator,
                                  const std::string& modelName);

        typedef void (xsmixcall) ( const double** energyArray,
                                   const int* energyArraySize,
                                   const double* parameterValues,
                                   double** flux,
                                   double** fluxError,
                                   MixUtility* mixGenerator,
                                   const std::string& modelName);

//        typedef void (xsmixf77call) (const double* energyArray,
//                                     const int* arraySizes,
//                                     const double* parameterValues,
//                                     double* flux,
//                                     double* fluxError,
//                                     double* realWork,
//                                     int* integerWork);
}

#endif  // #ifndef FUNCTYPE_H
