//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef IOSHOLDER_H
#define IOSHOLDER_H 1

#include <iostream>



class IosHolder 
{

  public:
      static void setStreams (std::istream* inStream, std::ostream* outStream, std::ostream* errStream);
      static std::istream* inHolder ();
      static std::ostream* outHolder ();
      static std::ostream* errHolder ();
      static const char* xsPrompt ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static std::istream* s_inHolder;
      static std::ostream* s_outHolder;
      static std::ostream* s_errHolder;
      static const char* s_xsPrompt;

    // Additional Implementation Declarations

};

// Class IosHolder 

inline std::istream* IosHolder::inHolder ()
{
  return s_inHolder;
}

inline std::ostream* IosHolder::outHolder ()
{
  return s_outHolder;
}

inline std::ostream* IosHolder::errHolder ()
{
  return s_errHolder;
}

inline const char* IosHolder::xsPrompt ()
{
  return s_xsPrompt;
}


#endif
