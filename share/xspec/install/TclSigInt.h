//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TCLSIGINT_H
#define TCLSIGINT_H 1
#include <xstcl.h>

// EventHandlers
#include <XSUtil/Signals/EventHandlers.h>




class TclSigInt : public SIGINT_Handler  //## Inherits: <unnamed>%40AE762B0065
{

  public:
      TclSigInt();
      virtual ~TclSigInt();

      virtual int handleSignal (int sigNum);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      static int handleTclSafe (ClientData cdata, Tcl_Interp* xsInterp, int code);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Tcl_AsyncHandler m_sig_Token;

    // Additional Implementation Declarations

};

// Class TclSigInt 


#endif
