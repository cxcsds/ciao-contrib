//C++
#ifndef PYMODEL_H
#define PYMODEL_H

#include <Python.h>

extern "C" {
   // All get/create functions return NULL if a failure occurs.

   // Create an Xspec Model object from an expression string.
   //
   //    Input args from Python:
   //       arg1 -- An expression string of xspec components (ie. "wa*po")
   //       arg2 -- The optional model name string.  Python should pass an
   //                  empty string if model has no name.
   //       arg3 -- The source number (int)
   //    Return:
   //       A PyTuple with: [0] -- A handle for the Model's C++ pointer
   //                       [1] -- A list of the FULL component name strings.
   //                       [2] -- Data group number
   //                       [3] -- Source number
   //                       [4] -- 1-based index of the first parameter in model
   //                       [5] -- Number of parameters in model
   //                       [6] -- The full model expression string
   //    
   //    If succeeds:  The model is completely constructed (ie. with  
   //       Components, Parameters) and inserted into Xspec's ModelContainer.
   //    If fails:  Nothing inserted into ModelContainer, returns NULL.
   PyObject* _pyXspec_createModel(PyObject *self, PyObject *args);

   //  Wrapper for Xspec's flux command handler.
   //
   //    Input args from Python:
   //       arg1 -- An int flag,  0 = lumin, else = flux.
   //       arg2 -- A list of strings constructed from the user's
   //                 single input string, split by whitespace.
   //                 The list may be empty.
   //
   //    Return PyIntObject = 0 if success.
   PyObject* _pyXspec_fluxCmd(PyObject *self, PyObject *args);

   // Return the model's flux or folded array for a given spectrum.
   //
   //   Input args from Python:
   //      arg1 -- The model object handle
   //      arg2 -- The spectrum number (should be 0 for inactive models)
   //      arg3 -- Bool as int, 0 = get flux, else = get folded
   //   Return:
   //      A PyList containing the flux or folded elements
   //
   //   This will throw if the model has no array corresponding to the
   //   user-entered spectrum number.
   PyObject* _pyXspec_getArray(PyObject *self, PyObject *args);

   // Retrieve the parameter names for a Component.
   //
   //   Input args from Python:
   //      arg1 -- The name of the Model to which the Component belongs. 
   //      arg2 -- The 1-based Component index number (int).
   //   Return:
   //      A PyList of parameter names
   //
   //   Input args are expected to have been validated by the time
   //   this is called, so any failure is NOT due to user input.
   //   Information is collected from the lowest dg model copy.
   PyObject* _pyXspec_getComponentPars(PyObject *self, PyObject *args);

   // Display and retrieve the emission lines as selected from the "identify" command.
   //
   //   Input args from Python:
   //      arg1 -- A list of strings (some may be empty) corresponding
   //                to the 6 args of the "identify" command.
   //
   //   Return a PyString containing the formatted output of all emission
   //     lines meeting the search criteria.
   //     
   PyObject* _pyXspec_getLines(PyObject *self, PyObject *args);
   
   // Get the results of the most recent flux calculation for a model.
   //
   //   Input args from Python:
   //       arg1 -- The model object handle.
   //       arg2 -- An int flag, 0 = lumin, else = flux.
   //
   //   Return a PyTuple containing (value, errLow, errHigh (in ergs/cm^2),
   //      value, errLow, errHigh (in photons)).
   PyObject* _pyXspec_getModelFluxLuminCalc(PyObject *self, PyObject *args);

   // Return a handle for a currently existing Xspec Model object.
   //
   //   Input args from Python:
   //      arg1 -- The model name string, empty if default.
   //      arg2 -- The data group number.
   //   Return:
   //      PyCObject handle.
   //   
   PyObject* _pyXspec_getModelFromNameAndGroup(PyObject *self, PyObject *args);

   // Return a dictionary of all active <sourceNum>:<modName> key,val pairs.
   //
   //   Input args from Python:
   //      None
   //
   //   Only the designated ACTIVE model for the source will be entered
   //     in the dictionary (whether active/on or active/off).
   //     The sourceNum is 1-based.  The modName for unnamed models
   //     will be an empty string.
   //
   PyObject* _pyXspec_getModelSourceAssignments(PyObject *self, PyObject *args);
   
   // Get info from a currently existing Xspec Model object.
   //
   //   Input args from Python:
   //      arg1 -- The model object handle
   //   Return:
   //      A PyTuple containing the same info as described in createModel.
   PyObject* _pyXspec_getModelTuple(PyObject *self, PyObject *args);

   // Get the spectrum numbers for which the Model object has a flux
   //    and energies array.
   //
   //   Input args from Python:
   //      arg1 -- The model object handle
   //   Return:
   //      A PyTuple of spectrum numbers, in the same order as the keys
   //      in the C++ modelFlux map.  (Note that PySet doesn't exist
   //      prior to Python 2.5, else that might be preferred return type.)
   PyObject* _pyXspec_getSpectraForModel(PyObject *self, PyObject *args);

   // Load a local model library
   //
   //   Input args from Python:
   //     arg1 -- The name of the Tcl local model package.
   //               If name string is empty, the function will
   //               treat this as a request to use the Tcl 'load'
   //               mechanism and will bypass the call to lmod.
   //     arg2 -- Directory path.  This should be an empty string
   //                if the user didn't enter any.
   //
   // Return PyIntObject = 0 if success, else NULL.
   PyObject* _pyXspec_localModel(PyObject *self, PyObject *args);

   
   // Remove one or all models.
   //
   //   Input args from Python:
   //      arg1 -- The name of the model to be removed.  If trying
   //                 to remove the default model, this should be
   //                 set to "unnamed".  If this string is empty,
   //                 ALL models will be removed.
   //   This will throw if string is not empty and the corresponding
   //   model is not in the container.
   //
   //   Return: 1 if success
   PyObject* _pyXspec_removeModels(PyObject *self, PyObject *args);

   // Display information for a single Model object.
   //
   //   Input args from Python:
   //      arg1 -- The Model object's handle.
   PyObject* _pyXspec_showModel(PyObject *self, PyObject *args);

}


#endif
