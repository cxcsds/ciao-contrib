//C++
#ifndef PYPARAMETER_H
#define PYPARAMETER_H

#include <Python.h>

extern "C" {

   // Retrieve the parameter settings from the specified Parameteter object.
   //
   //   Input args from Python:
   //      arg1 -- The Parameter's parent Model or Response handle.
   //      arg2 -- The 1-based parameter index number, relative
   //                to the Model/Response object's start (int).
   //      arg3 -- Flag: 0 = ModPar, 1 = RespPar (int).
   //   Return:
   //      A tuple of size 11 with members:
   //         1st -- List of doubles containing val, and optional
   //                del, min, bot, top, max.
   //         2nd -- sigma (double), set to -1.0 if N/A
   //         3rd -- frozen flag (bool)
   //         4th -- link expression string (empty if not linked)
   //         5th -- optional units string
   //         6th -- parameter name string
   //         7th -- Low bound of last error calculation.  0.0 if none
   //                    or if parameter is not a ModParam.
   //         8th -- High bound of last error calculation.
   //         9th -- Status code string from last error calculation.
   //                   All 'F's if ModParam with no calculation, empty
   //                   string if not a ModParam.
   //        10th -- Bayesian prior type string (empty if not a ModPar).
   //        11th -- List of doubles containing optional Bayes hyper params.
   //   
   PyObject* _pyXspec_getParTuple(PyObject *self, PyObject *args);

   // Wrapper for making a direct call to Xspec's doNewpar handler.
   //
   //   This is intended for usage by Xset.restore(), which may need
   //   to process a direct call to 'newpar' (a non-standard interface
   //   not accessible from _doXspecCmd).  Other contexts can use one
   //   of the various _setPar functions.
   //
   //   Input args from Python:
   //      arg1 -- Single string containing everything to the right
   //                 of the 'newpar' or 'rnewpar' command.
   //      arg2 -- Flag: 0 = 'newpar', 1 = 'rnewpar' (int).
   //    Return PyIntObject = 0 if success, else NULL.   
   PyObject* _pyXspec_newparCmd(PyObject *self, PyObject *args);
   
   // Set a Bayesian prior for the parameter.
   //
   //   Input args from Python:
   //      arg1 -- The Parameter's parent Model handle.
   //      arg2 -- The 1-based parameter index number, relative
   //                to the Model object's start (int).
   //      arg3 -- The prior type (string).
   //      arg4 -- List of hyper params, converted to strings in Python.
   //      arg5 -- Flag: 0 = resp par, 1 = mod par (int).
   //   Return:
   //      1 if success
   PyObject* _pyXspec_setParBayes(PyObject *self, PyObject *args);
   
   // Freeze or thaw a single parameter.
   //
   //   Input args from Python: 
   //      arg1 -- The Parameter's parent Model handle.
   //      arg2 -- The 1-based parameter index number, relative
   //                to the Model object's start (int).
   //      arg3 -- Flag: 0 = thaw, 1 = freeze (int).
   //      arg4 -- Flag: 0 = resp par, 1 = mod par (int).
   //   Return:
   //      NULL if error
   //      0 if input does not cause freeze/thaw status to change
   //      1 if input changes freeze/thaw status
   PyObject* _pyXspec_setParFreeze(PyObject *self, PyObject *args);
   
   // Set or remove a parameter link.
   //
   //   Input args from Python: 
   //      arg1 -- The Parameter's parent Model handle.
   //      arg2 -- The 1-based parameter index number, relative
   //                to the Model object's start (int).
   //      arg3 -- The input in string format.
   //      arg4 -- Flag: 0 = resp par, 1 = mod par (int).
   //   Return:
   //      NULL if error
   //      1 if success
   PyObject* _pyXspec_setParLink(PyObject *self, PyObject *args);

   // Set multiple parameters, then do recalculation.  Linking not
   //   supported.
   //
   //   Input args from Python:
   //      arg1 -- The Parameter's parent Model handle.
   //      arg2 -- A tuple of the 1-based index numbers of the parameters
   //                to modify.  These are relative to the Model object's
   //                start (ie. higher data group models still begin at 1).
   //      arg3 -- A tuple of strings for the new value settings.  This
   //                should be the same size as the tuple in arg2.  String
   //                is allowed to be empty or blank, which will just leave
   //                the settings unchanged.
   //      arg4 -- An int flag where 1 indicates input indices are local
   //                and 0 indicates they are global.   
   PyObject* _pyXspec_setPars(PyObject *self, PyObject *args);
   
   // Set multiple parameters from global AllModels container rather
   //    than from individual Model objects.
   //
   //   Input args from Python:
   //      Tuples for arg1,2,3 must all be the same size.
   //      arg1 -- A tuple of model name strings (use empty string for
   //                unnamed).  1 string for each parameter.
   //      arg2 -- Tuple of the global 1-based parameter indices.
   //      arg3 -- Tuple of strings for new value settings.  These can
   //                be empty or blank.
   PyObject* _pyXspec_setParsGlobal(PyObject *self, PyObject *args);
   
   // Set multiple response parameters.
   //
   //   Input args from Python:
   //      arg1 -- The response par's parent Response handle.
   //      arg2 -- A tuple of the 1-based resp par indices.
   //                Until more than 'gain' is implemented, this ASSUMES
   //                size is either 1 or 2.
   //      arg3 -- A tuple of strings for the new value settings.
   PyObject* _pyXspec_setRespPars(PyObject *self, PyObject *args);
   
   // Show all or a subset of parameters.
   //
   //    Input args from Python:
   //       arg1 -- A list of strings constructed from the user's
   //                single input string, split by whitespace.
   //                The list may be empty.
   PyObject* _pyXspec_showPar(PyObject *self, PyObject *args);

}


#endif
