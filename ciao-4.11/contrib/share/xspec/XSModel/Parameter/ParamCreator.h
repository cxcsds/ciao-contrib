//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PARAMCREATOR_H
#define PARAMCREATOR_H 1

// string
#include <string>

class Component;


struct ParamCreator 
{

      static Parameter* MakeParameter (std::string initString, Component* p, size_t paramIndex = 0);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class Utility ParamCreator 


#endif
