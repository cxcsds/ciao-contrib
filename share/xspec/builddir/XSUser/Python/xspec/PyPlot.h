//C++
#ifndef PYPLOT_H
#define PYPLOT_H

#include <Python.h>

extern "C" {

   // Remove all user-entered custom plot commands.
   //
   PyObject* _pyXspec_clearCommands(PyObject *self, PyObject *args);

   // Call Xspec's commonPlotHandler function to make the plot.
   //
   //   Input args from Python:
   //      arg1 -- A list of plot command string arguments.  Strings
   //               should contain no whitespace by this point.
   //               example:  For plotting data and a model named "m1",
   //                         list should be ["data","model","m1"].
   //     
   //              To call in IPLOT MODE, the last string should be
   //               the arbitrarily mangled "iplot" string, as defined
   //               in the doPlot function body.
   //
   //   Return: PyIntObject = 0
   PyObject* _pyXspec_doPlot(PyObject *self, PyObject *args);

   // Get a particular setplot attribute.
   //
   //   Input args from Python:
   //      arg1 -- A string specifying the setplot attribute.
   //
   //   Return: The setplot value(s), may be of several different types, 
   //           ie. string, bool, tuple of floats, etc.
   PyObject* _pyXspec_getplotSettings(PyObject *self, PyObject *args);

   // Return an array of X or Y plot values for a given plot group.
   //
   //   Input args from Python:
   //     arg1 -- A 0-based int for plot group number (irrelevant for X values).
   //     arg2 -- A 0-based int for plot pane number.
   //     arg3 -- Array identifier string (ie. "x", "xerr", "y", "yerr",
   //               "model", "background")
   //
   //   Return: A PyList of floating-point values.  Returns NULL if
   //           requested array isn't part of the plot (either due to
   //           out-of-range plot group number, or array type not
   //           relevant to the particular plot).
   PyObject* _pyXspec_getplotValues(PyObject *self, PyObject *args);

   // Determine whether a user-input units string matches available
   //   energy units, wavelength units, or neither.
   //
   //   Input args from Python:
   //      arg1 -- A case-insensitive units string (ie. "kev", "nm")
   //                 Abbreviations are accepted.
   //
   //   Return PyIntObject = 0: energy units
   //                      = 1: wavelength units
   //                      = -1: neither
   PyObject* _pyXspec_identifyUnits(PyObject *self, PyObject *args);

   // Set the isWavePerHz flag for y-axis display.  Xspec's "setplot
   // wave perhz" command can do this, but has the unwanted side effect
   // of automatically switching things to wave mode.  This function sets
   // the flag and does nothing else.
   //
   //   Input args from Python:
   //      arg1 -- True|False
   // 
   //   Return PyIntObject = 0
   PyObject* _pyXspec_setPerHz(PyObject *self, PyObject *args);

   // Wrapper for Xspec's setplot command.
   //
   //   Input args from Python:
   //      arg1 -- A list of strings containing the args for setplot,
   //                 including the option string as first arg.  These
   //                 strings should contain no whitespace.
   //
   //   Return PyIntObject = 0 if success.
   PyObject* _pyXspec_setplotCmd(PyObject *self, PyObject *args);

   // Wrapper for "show plot"
   //
   PyObject* _pyXspec_showPlot(PyObject *self, PyObject *args);

}


#endif
