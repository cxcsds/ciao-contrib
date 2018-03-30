//C++
#ifndef PYPYMOD_H
#define PYPYMOD_H

#include <Python.h>

#include <XSUtil/FunctionUtils/funcType.h>
#include <XSUtil/FunctionUtils/XSModelFunction.h>

extern ModelFunctionMap XSFunctionMap;

// Internal wrapper function for performing the C++->Python array conversions,
//  and the reverse Python->C++ upon return of the model function.
//
// Given an input energyArray of size = nE and params of size nPar,
// this will send to Python model function the following args:
//    1) energy tuple of size nE
//    2) param tuple of size nPar
//    3) flux list of size nE-1.  
//       - If incoming fluxArray is already size nE-1, it's values will be
//         copied into the flux list before sending to Python.
//       - If incoming fluxArray is size 0, the flux list will be filled 
//         with 0.0 before sending to Python.
//       - Any other size of the incoming fluxArrays will trigger a RedAlert.
//  Optional args:
//    4) If Python model function has a 4th arg, an empty fluxerr
//       list will be sent from here to Python.  If the function,
//       chooses to expand and fill it, it will be copied to fluxErrArray
//       upon return.
//    5) If Python model has a 5th arg, an int containing the spectrum number
//       will be sent to Python.
//
//  If any status error occurs in return from Python call, or Python model
//    function improperly resizes any of the list arguments, this will
//    issue message and fill fluxArray with all NaNs.
template <>
void XSCall<PyObject>::operator() (const RealArray& energyArray, const RealArray& params,
                        int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, 
                        const string& initString) const;


extern "C" {

   // Add a user-defined Python function to XSPEC's models library.
   //
   //    Input args from Python:
   //        arg1 -- The Python model function (Python type = 'function').
   //        arg2 -- A tuple containing parInfo strings, 1 string for
   //                  each parameter in model.
   //        arg3 -- String indicating the component's type (ie. 'add' etc)
   //        arg4 -- Bool flag indicating whether flux errors will be calculated.
   //        arg5 -- Bool flag indicating whether model explicitly depends on spectrum.
   //        arg6 -- String containing the function name.  This will also become
   //                   the name of the component within XSPEC's library.
   //
   //    Returns PyInt = 0 if success.  Otherwise throws exception and returns NULL.
   
   PyObject* _pyXspec_addPyComp(PyObject *self, PyObject *args);

}

#endif
