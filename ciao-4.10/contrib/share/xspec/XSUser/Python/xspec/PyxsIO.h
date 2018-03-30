//C++

#ifndef PYXSIO_H
#define PYXSIO_H

#include <Python.h>
#include <XSUtil/Utils/XSstream.h>
#include <iostream>

extern "C" {

   // Enable/disable user prompting by toggling Xspec's internal
   //    executingScript flag.
   //
   //    Input args from Python:
   //       arg1 -- int: 0 = disable, 1= enable.
   //
   //    Return PyInt = 0
   PyObject* _pyXspec_allowPrompting(PyObject* self, PyObject *args);
   
   // Release Xspec's log file.
   //
   //    This merely decrements the (PyFile) log file reference count.
   //    fclose will be called only if that count drops to zero (ie.
   //    no outstanding references in the calling python script).
   //
   //    Return PyInt = 0
   PyObject* _pyXspec_closeLog(PyObject* self, PyObject *args);

   // Get the console or log chatter level.
   //
   //   Input args from Python:
   //      arg1 -- int: 0 = console, 1 = log.
   //
   //   Return a PyInt containing the level.
   PyObject* _pyXspec_getChatter(PyObject* self, PyObject *args);

   // Set the console or log chatter level.
   //
   //   Input args from Python:
   //      arg1 -- int: 0 = console, 1 = log.
   //      arg2 -- int: the chatter level.
   //
   //    Return a PyInt containing the new level.
   PyObject* _pyXspec_setChatter(PyObject* self, PyObject *args); 


   // Get the currently opened log file.
   //
   //   Return a PyFile* if a file exists, else PyNone.
   PyObject* _pyXspec_getLog(PyObject* self, PyObject *args);

   // Open a file and set it to be Xspec's log file.
   //
   //   Input args from Python:
   //      arg1 -- A filename string.
   //
   //   If there's already an Xspec log file, this will decrement
   //   its reference count and cease writing to it.
   //
   //   Return a PyFile* to the new file.
   PyObject* _pyXspec_setLog(PyObject* self, PyObject *args);

}


// This class is NOT intended to be part of the Python/C++ interface,
// rather it is the Python equivalent of the TclIO class: an XSchannel
// to be plugged into Xspec's streambuf classes.  Therefore nothing in
// here should be made accessible in _PyXspecMethods[].

class PyxsIO : public XSchannel
{
   public:
      PyxsIO(std::istream* in, std::ostream* out);
      virtual ~PyxsIO();

      // If a PyxsIO object's read function is to be called (ie. when
      // it's assigned to tcin), it MUST also have a valid m_outChannel
      // to output the prompting string.
      virtual std::streamsize read (char* s, std::streamsize n = 1);
      virtual void setPrompt (const string& ps);
      virtual const string& prompt () const;
      PyObject* logFile() const;


   private:
      PyxsIO(const PyxsIO& right);
      PyxsIO& operator=(const PyxsIO& right);

      virtual std::streamsize write (const char* s, std::streamsize n);
      // This does not close a previously opened log file, nor does it delete
      // the associated python object.  It will THROW a YellowAlert if unable
      // to open the new file.
      virtual void internalSetLogger (const std::string& name, bool isErr = false);
      virtual void internalCloseLog ();

      std::istream* m_inChannel;
      std::ostream* m_outChannel;
      // m_logFile should ALWAYS = 0 unless a log file is open.
      PyObject* m_logFile;

      string m_prompt;
};

inline const string& PyxsIO::prompt() const
{
   return m_prompt;
}

inline PyObject* PyxsIO::logFile() const
{
   return m_logFile;
}

#endif
