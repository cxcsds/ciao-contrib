//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EVENTHANDLERS_H
#define EVENTHANDLERS_H 1
#include <signal.h>




class EventHandler 
{

  public:
      virtual ~EventHandler();

      virtual int handleSignal (int sigNum) = 0;

    // Additional Public Declarations

  protected:
      EventHandler();

    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



class SIGINT_Handler : public EventHandler  //## Inherits: <unnamed>%40AE3F630017
{

  public:
      SIGINT_Handler();
      virtual ~SIGINT_Handler();

      virtual int handleSignal (int sigNum);
      sig_atomic_t interrupted () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      sig_atomic_t m_interrupted;

    // Additional Implementation Declarations

};

// Class EventHandler 

// Class SIGINT_Handler 

inline sig_atomic_t SIGINT_Handler::interrupted () const
{
  return m_interrupted;
}


#endif
