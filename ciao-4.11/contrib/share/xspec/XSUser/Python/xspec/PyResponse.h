//C++
#ifndef PYRESPONSE_H
#define PYRESPONSE_H

#include <Python.h>

extern "C" {

   // Get Arf for response
   //
   //   Input args from Python:
   //      arg1 -- The Response object's handle.
   //
   //   Return a PyString containing the Arf filename.
   //      If no Arf, returns NULL.
   PyObject* _pyXspec_getArf(PyObject* self, PyObject *args);
   
   // Get the channel energies from the Spectrum's first found Response.
   //
   //   Input args from Python:
   //      arg1 -- The Spectrum's index.
   //
   //   Return PyTuple containing the channel energies.  If no response
   //      is found, or using dummy resp without defined channels, this
   //      returns NULL and sets a PyException.
   PyObject* _pyXspec_getChannelEnergies(PyObject *self, PyObject *args);

   // Get a response for a given spectrum and 0-based source number.
   //
   //   Input args from Python:
   //      arg1 -- Spectrum handle
   //      arg2 -- 0-based source number (int)
   //
   //   If a valid response exists in slot, returns a response tuple 
   //     containing the invariants:
   //        [0] -- Response file name, or "dummy".
   //        [1] -- Channel energies EBOUNDS array
   //        [2] -- Photon energies array
   //        [3] -- Response handle
   //        [4] -- Source number
   //
   //   If sourceNum is in range but detector slot is empty, return Py_None.
   //   All other conditions (including out-of-bounds sourceNum) will
   //     raise an error and return NULL.
   //   
   PyObject* _pyXspec_getResponse(PyObject *self, PyObject *args);
   
   // Return a bool indicating whether the C++ Response object has any
   //  gain parameters attached.
   //
   //   Input args from Python:
   //     arg1 -- The Response objects's handle.
   //
   PyObject* _pyXspec_hasGainPars(PyObject *self, PyObject *args);
   
   // Set or remove a Response's Arf.
   //
   //   Input args from Python:
   //      arg1 -- The Response object's handle.
   //      arg2 -- Arf filename string. If None, remove Arf.
   //      
   PyObject* _pyXspec_setArf(PyObject *self, PyObject *args);

   // Set a response for spectrum and source number.
   //
   //   Input args from Python:
   //      arg1 -- The spectrum handle
   //      arg2 -- The source number (0-based)
   //      arg3 -- Response filename string.  If None, current
   //              response will be removed.
   PyObject* _pyXspec_setResponse(PyObject* self, PyObject *args);
   
   PyObject* _pyXspec_showResponse(PyObject* self, PyObject *args);
  
}

#endif
