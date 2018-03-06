//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SCALEPARAM_H
#define SCALEPARAM_H 1

// Parameter
#include <XSModel/Parameter/Parameter.h>

class Component;


class ScaleParam : public Parameter  //## Inherits: <unnamed>%38EB53F7E248
{

  public:
      ScaleParam(const ScaleParam &right);
      ScaleParam (const string& initString = "", Component* p = 0	// Token for parent component instance for grabbing
      	// initialization data etc. Since there are (gain)
      	// parameters that do not have a component parent this is
      	// a pointer rather than a reference as used for the same
      	// concept for ComponentGroup and Component.
      );
      ScaleParam (const string& inputName, Real initial, Component* p = 0	// Token for parent component instance for grabbing
      	// initialization data etc. Since there are (gain)
      	// parameters that do not have a component parent this is
      	// a pointer rather than a reference as used for the same
      	// concept for ComponentGroup and Component.
      );
      virtual ~ScaleParam();

      virtual ScaleParam* clone (Component* p) const;
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

    // Additional Protected Declarations

  private:
      ScaleParam & operator=(const ScaleParam &right);

      virtual void init (const string& initString);
      virtual void changeValue (const string& parString);
      virtual void setValue (Real& val);
      virtual void doPreserve ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_factor;

    // Additional Implementation Declarations

};

// Class ScaleParam 


#endif
