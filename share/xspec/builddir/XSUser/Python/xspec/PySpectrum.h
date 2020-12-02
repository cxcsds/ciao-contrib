//C++
#ifndef PYSPECTRUM_H
#define PYSPECTRUM_H


#include <Python.h>

extern "C" {

   // Unless stated otherwise, all functions will create a Python
   //    Exception object and return NULL upon failure.

   // Pass a string directly to Xspec's xsData command handler.
   //
   //   Input args from Python:
   //       arg1 -- A list of strings constructed from the user's
   //                single input string, split by whitespace.
   //                The list may be empty.
   //
   //   Return PyIntObject = 1 if success,
   PyObject* _pyXspec_dataCmd(PyObject *self, PyObject* args);

   // Package fakeit arguments from python interface, pass to standard
   //   Xspec fakeit handler.
   //
   //   Input args from Python:
   //       arg1 -- List of FakeitSetting objects, 1 for each fake
   //                spectrum that is to be created.
   //       arg2 -- Flag indicating whether to apply randomization (int).
   //       arg3 -- Optional file prefix string.
   //       arg4 -- Flag indicating whether to pass 'nowrite' (int).
   //
   //   Return PyInt Object = 1 if success
   //
   //   Note that this ASSUMES there is exactly 1 FakeitSetting object
   //     for each fake spectrum.  It DOES NOT check.
   PyObject* _pyXspec_doFakeit(PyObject *self, PyObject* args);

   // Return background or correction information for a given spectrum.
   //
   //   Input args from Python:
   //       arg1 -- The spectrum's index number.
   //       arg2 -- int:  0 = back, 1 = corr
   //
   //   Return PyTuple containing the same information as listed in
   //      getSpectrumInvariants
   PyObject* _pyXspec_getBackgrnd(PyObject *self, PyObject *args);

   // Get the correction scale setting for a spectrum.
   //
   //   Input args from Python:
   //      arg1 -- The Spectrum's C++ handle
   //  
   //   Return PyFloat containing correction scale.
   PyObject* _pyXspec_getCornorm(PyObject *self, PyObject *args);

   // Get the results of the most recent flux calculation for the spectrum.
   //
   //   Input args from Python:
   //       arg1 -- The spectrum's index number.
   //       arg2 -- An int flag, 0 = lumin, else = flux.
   //
   //   Return a PyTuple containing (value, errLow, errHigh (in ergs/cm^2),
   //      value, errLow, errHigh (in photons)) for each model associated
   //      with spectrum.
   PyObject* _pyXspec_getFluxLuminCalc(PyObject *self, PyObject *args);

   // Get an array of the currently ignored 1-BASED channel numbers.
   //
   //    Input args from Python:
   //       arg1 -- The Spectrum's index.
   //
   //   Return a PyListObject
   PyObject* _pyXspec_getIgnoredChannels(PyObject *self, PyObject *args);

   // Get a spectrum's index number from its handle.
   //   Algorithm is O(N) where N is the number of loaded spectra.
   //
   //   Input args from Python:
   //      arg1 -- The object's handle, should be a SpectralData*
   //              converted to a void* upon storage.
   //
   //   Return PyInt object = iSpec if success.
   PyObject* _pyXspec_getIndexFromHandle(PyObject *self, PyObject* args);

   // Get an array of the currently noticed 1-BASED channel numbers.
   //
   //    Input args from Python:
   //       arg1 -- The Spectrum's index.
   //
   //   Return a PyListObject
   PyObject* _pyXspec_getNoticedChannels(PyObject *self, PyObject *args);

   // Get the number of currently loaded spectra.
   //
   //   Return a PyInt
   PyObject* _pyXspec_getNSpectra(PyObject *self, PyObject *args);

   // Get the rate values from a single spectrum.
   //
   //   Input args from Python:
   //      arg1 -- The Spectrum's index.
   //     
   //   Return a PyTuple containing (net rate(cts/sec), net variance, 
   //       total rate, predicted model rate).
   PyObject* _pyXspec_getRate(PyObject *self, PyObject *args);

   // Get a single spectrum from spectrum index number.
   //
   //   Input args from Python:
   //      arg1 -- Spectrum index number, from 1 to nAllSpectra.
   //   
   //   Returns a PyCObject handle created from the SpectralData pointer.
   PyObject* _pyXspec_getSpectrum(PyObject *self, PyObject *args);

   // Get the spectrum array of values.
   //
   //   Input args from Python:
   //      arg1 -- Spectrum index number.
   //
   //   Returns a PyTuple containing:
   //      [0] -- Spectrum filename
   //      [1] -- A PyTuple of floats containing the spectrum array.
   //      [2] -- A PyTuple of floats containing the variance array.
   //      [3] -- The isPoisson flag, Py_True or Py_False.
   //      [4] -- Exposure time (float).
   //      [5] -- Areascale, a single float if file has keyword, 
   //                else a PyTuple of floats.
   //      [6] -- Backscale, a single float if file has keyword, 
   //                else a PyTuple of floats.
   PyObject* _pyXspec_getSpectrumInvariants(PyObject *self, PyObject *args);

   // Create a single Xspec SpectralData object and insert it into
   // the DataContainer.
   //
   //   Input args from Python:
   //      arg1 -- Data filename string.
   //
   //   Return PyCObject = handle created from (void*) pointer to
   //      the newly created SpectralData object. 
   PyObject* _pyXspec_readSpectrum(PyObject *self, PyObject *args);


   // Set a Spectrum object's background or correction.
   //
   //   Input args from Python:
   //      arg1 -- The owning spectrum's index number.
   //      arg2 -- Back/Cor filename string.  If None, current 
   //              Back/Cor (if any) will be removed.
   //      arg3 -- int:  0 = back, 1 = corr
   //
   //   Return a PyTuple containing spectrum information for the
   //      newly set back/cor.  If none, return Py_None.
   PyObject* _pyXspec_setBackgrnd(PyObject *self, PyObject *args);

   // Show all loaded spectra
   PyObject* _pyXspec_showAllData(PyObject *self, PyObject *args);

   // Show a single Spectrum object
   //
   //   Input args from Python:
   //      arg1 -- A handle to the C++ SpectralData object
   PyObject* _pyXspec_showData(PyObject *self, PyObject *args);
}

#endif
