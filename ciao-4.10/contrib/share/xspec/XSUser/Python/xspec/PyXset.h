//C++
#ifndef PYXSET_H
#define PYXSET_H

#include <Python.h>

extern "C" {

   // Use the tclout handler for retrieving information.
   //
   //   Input args from Python:
   //      arg1 -- A list of string arguments (no whitespace).
   //
   //   Return: A PyStringObject containing the tclout results.
   PyObject* _pyXspec_doTclout(PyObject *self, PyObject *args);

   // Get the name of the current abundance table.
   //
   //   Returns a PyString containing the name.
   PyObject* _pyXspec_getAbund(PyObject *self, PyObject *args);

   // Get the entire model string database.
   //
   //   Returns a PyDict.
   PyObject* _pyXspec_getModelStringValues(PyObject *self, PyObject *args);
   
   // Get the current parallel process setting for a particular context.
   //
   //   Input args from Python:
   //      arg1 -- A string containing the parallel context name.
   //
   //   Returns a PyIntObject.
   PyObject* _pyXspec_getParallel(PyObject *self, PyObject *args);
   
   // Get the proportional fit delta value.
   //
   //   Return: A PyFloat.  If the value stored in Xspec is <= 0.0
   //      (indicating proportional deltas are not in use), this
   //      will return 0.0.   
   PyObject* _pyXspec_getPropDelta(PyObject *self, PyObject *args);

   // Get the name of the photoelectric absorption cross-section in use.
   //
   //   Return: A PyString.
   PyObject* _pyXspec_getXsect(PyObject *self, PyObject *args);

   // Remove any existing model string settings, replace with new database.
   //
   //   Input args from Python:
   //     arg1 -- A dictionary of key/value string pairs.  This ASSUMES
   //                types have been validated and whitespace removed.
   //
   //  Returns PyInt=0
   PyObject* _pyXspec_setModelStringValues(PyObject *self, PyObject *args);
   
   PyObject* _pyXspec_showXset(PyObject *self, PyObject *args);

}

#endif
