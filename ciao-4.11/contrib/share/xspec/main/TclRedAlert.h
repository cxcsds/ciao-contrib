//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TCL_REDALERT_H
#define TCL_REDALERT_H 1

// Error
#include <XSUtil/Error/Error.h>




class TclRedAlert : public RedAlert  //## Inherits: <unnamed>%407EB18401D7
{
  public:
      TclRedAlert (const std::string& message, int returnCode);

  protected:
      virtual void reportAndExit (const std::string& message = "Unspecified Fatal Error", const int returnCode = -1);

  private:
  private: //## implementation
};



class TclInitErr : public TclRedAlert  //## Inherits: <unnamed>%407EBA3A0270
{
  public:
      TclInitErr (const string& message = "Fatal: Cannot initialize tcl command interface", const int returnCode = -1);

  protected:
  private:
  private: //## implementation
};

// Class TclRedAlert 

// Class TclInitErr 


#endif
