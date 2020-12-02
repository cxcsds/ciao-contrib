//C++
#ifndef PYFIT_H
#define PYFIT_H

#include <Python.h>

extern "C" {

   // Get the current fit settings.
   //
   // Return a PyTuple containing:
   //    [0] -- Stat method name
   //    [1] -- Fit method name
   //    [2] -- nIterations (int)
   //    [3] -- critical delta (float)
   //    [4] -- is Bayes on (bool)
   //    [5] -- Test stat name
   PyObject* _pyXspec_getFitSettings(PyObject *self, PyObject *args);

   // Get the fit statistic value
   //
   // Return a PyFloatObject
   PyObject* _pyXspec_getStatistic(PyObject *self, PyObject *args);

   // Get the test statistic value
   //
   // Return a PyFloatObject
   PyObject* _pyXspec_getTestStatistic(PyObject *self, PyObject *args);

   // Set the fit query value
   //
   //    Input args from Python:
   //       arg1 -- A pre-verified lower case char, 'o', 'y', or 'n'
   //                
   // Return PyIntObject = 0 if success, else NULL.
   PyObject* _pyXspec_setQuery(PyObject *self, PyObject *args);

   //  Call Xspec's "show fit" command.
   //  Returns PyIntObject = 0.
   PyObject* _pyXspec_showFit(PyObject *self, PyObject *args);
   
   // Get attributes of a currently loaded chain.
   //
   //    Input arg from Python:
   //       arg1 -- The 1-based chain index number in the container (int)
   //    This creates exception and returns NULL if index is out of range.
   //
   // Returns a PyTuple containing:
   //    [0] -- Chain filename (string)
   //    [1] -- Chain file format (string)
   //    [2] -- Current length (int)
   //    [3] -- Chain width (int)
   //
   PyObject* _pyXspec_getChainByIndex(PyObject *self, PyObject *args);
   
   // Get information from the C++ ChainManager container.
   //
   // Returns a PyTuple containing:
   //    [0] -- A PyList of loaded chain filename strings.
   //    [1] -- A PyList of current variable parameter labels.
   PyObject* _pyXspec_getChainManagerInfo(PyObject *self, PyObject *args);
   
   // Unload a Chain from the container, based on its filename.
   //
   //    This is needed for when the "chain unload <index>" command
   //    won't suffice.
   //
   //    Input arg from Python:
   //       arg1 -- The chain fileName string.
   //
   // Returns PyIntObject = 0 if removal took place, -1 if not.
   PyObject* _pyXspec_removeChainByName(PyObject *self, PyObject *args);
   
   // Display Python Chain object attributes.
   //
   // Note that this does NOT interface with a corresponding C++ chain
   // object.  It only looks at the Python object, and then sends the
   // results to tcout.  Therefore it can be called even when chain is
   // not loaded.
   //
   //    Input args from Python:
   //       arg1 -- The Python chain object
   //
   // Return PyIntObject = 0.
   PyObject* _pyXspec_showChain(PyObject *self, PyObject *args);
   
   // Display Python ChainContainer settings and loaded chain info.
   //
   // This function must be used in place of the "chain info" option.
   // The def<attribute> settings in ChainContainer are NOT the same
   // as the current default settings in the xsChain handler.
   //
   //   Input args from Python:
   //      arg1 -- The AllChains self pointer.
   //
   // Return PyIntObject = 0.
   PyObject* _pyXspec_showChainContainer(PyObject *self, PyObject *args);
   
}


#endif
