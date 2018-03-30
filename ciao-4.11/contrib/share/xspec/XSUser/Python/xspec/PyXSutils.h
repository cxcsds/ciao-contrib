//C++
#ifndef PYXSUTILS_H
#define PYXSUTILS_H

#include <Python.h>

#include <xsTypes.h>

#if XS_PYTHON_VERSION >= 25
 typedef Py_ssize_t PY_SZ_TYPE;
#else
 typedef int PY_SZ_TYPE;
#endif

#if PY_MAJOR_VERSION >= 3
 #define PYXSPEC3
 #define PYXSSTRING_FROMSTRING PyUnicode_FromString
 #define PYXSSTRING_ASSTRING PyUnicode_AsUTF8
 #define PYXSINT_FROMLONG PyLong_FromLong
 #define PYXSINT_ASLONG PyLong_AsLong
 #define PYXSCOBJECT_FROMVOIDPTR(pointer, name, destructor) \
      (PyCapsule_New(pointer, name, destructor))
 #define PYXSCOBJECT_ASVOIDPTR(pointer, name) \
      (PyCapsule_GetPointer(pointer, name))
#else
 #define PYXSSTRING_FROMSTRING PyString_FromString
 #define PYXSSTRING_ASSTRING PyString_AsString
 #define PYXSINT_FROMLONG PyInt_FromLong
 #define PYXSINT_ASLONG PyInt_AsLong
 #define PYXSCOBJECT_FROMVOIDPTR(pointer, name, destructor) \
      (PyCObject_FromVoidPtr(pointer, destructor))
 #define PYXSCOBJECT_ASVOIDPTR(pointer, name) \
      (PyCObject_AsVoidPtr(pointer))
#endif

class Model;
class Response;
class SpectralData;

extern "C" {

   // Generic xspec handler function wrapper.
   //
   //   Input args from Python:
   //      arg1 -- A list of strings. No whitespace should exist
   //                 within an individual string.  The first
   //                 string in the list must be the handler name.
   //
   //   Return PyIntObject = 0 if success, else NULL.
   PyObject* _pyXspec_doXspecCmd(PyObject* self, PyObject* args);
}

namespace PyXSutils {
// This namespace is for functions that are only accessed from within
// other Py/Xspec C++ code files.  They are NOT added to the _pyXspec 
// module for use in Python code.

// rawArgs need not be empty upon input.  All arguments found in
// PyList object (extracted from args tuple) will be added to rawArgs 
// via push_back operations.
// Returns 0 if failure, else 1.
int PyListToXSArgs(PyObject* args, StringArray& rawArgs);

// If handle no longer points to an existing C++ Model,
// this will set the PyErr string and return NULL.
Model* verifyModelHandle(PyObject* handle);
// Same as above, but for C++ Response.
Response* verifyResponseHandle(PyObject* handle);   
// Same as above, but for C++ SpectralData.
SpectralData* verifySpectrumHandle(PyObject* handle);
}

#endif
