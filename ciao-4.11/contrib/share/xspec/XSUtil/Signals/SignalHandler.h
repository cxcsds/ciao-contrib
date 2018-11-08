//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SIGNALHANDLER_H
#define SIGNALHANDLER_H 1
#include <map>

// EventHandlers
#include <XSUtil/Signals/EventHandlers.h>




class SignalHandler 
{

  public:
      ~SignalHandler();

      static SignalHandler* instance ();
      EventHandler* registerHandler (int sigNum, EventHandler* eh);
      int removeHandler (int sigNum);
      static const EventHandler* getHandler (int sigNum);

    // Additional Public Declarations

  protected:
      SignalHandler();

      static void dispatcher (int sigNum);

    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static SignalHandler* s_instance;
      static std::map<int,EventHandler*> s_signalHandlers;

    // Additional Implementation Declarations

};

// Class SignalHandler 


#endif
