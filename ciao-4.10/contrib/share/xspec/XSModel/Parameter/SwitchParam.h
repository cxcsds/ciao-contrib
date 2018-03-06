//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SWITCHPARAM_H
#define SWITCHPARAM_H 1

// Parameter
#include <XSModel/Parameter/Parameter.h>

class Component;


class SwitchParam : public Parameter  //## Inherits: <unnamed>%38EB53F2AD48
{

  public:
      SwitchParam(const SwitchParam &right);
      SwitchParam (const string& initString = "", Component* p = 0	// Token for parent component instance for grabbing
      	// initialization data etc. Since there are (gain)
      	// parameters that do not have a component parent this is
      	// a pointer rather than a reference as used for the same
      	// concept for ComponentGroup and Component.
      );
      virtual ~SwitchParam();

      virtual SwitchParam* clone (Component* p) const;
      virtual std::ostream& put (std::ostream& s) const;
      virtual Real value () const;
      //	Operation supporting the XSPEC tclout command which
      //	simply writes the data members of the parameter to a
      //	string.
      virtual string stringVal () const;
      virtual string parameterSetting () const;

    // Additional Public Declarations

  protected:
      virtual bool compare (const Parameter& right) const;
      virtual void link (const string& toLink);

    // Additional Protected Declarations

  private:
      SwitchParam & operator=(const SwitchParam &right);

      virtual void init (const string& initString);
      virtual void changeValue (const string& parString);
      void setValue (int state);
      virtual void doPreserve ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      int m_state;

    // Additional Implementation Declarations

};

// Class SwitchParam 


#endif
