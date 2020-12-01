//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MULCOMPONENT_H
#define MULCOMPONENT_H 1

// Component
#include <XSModel/Model/Component/Component.h>

class SumComponent;

//	Multiplicative Component. ComponentGroup must contain
//	one or more of MulComponent and ConComponent



class MulComponent : public Component  //## Inherits: <unnamed>%3687BAB623D0
{

  public:
      MulComponent(const MulComponent &right);
      MulComponent (ComponentGroup* p);
      virtual ~MulComponent();

      virtual SumComponent& operator * (SumComponent& right) const;
      virtual MulComponent* clone (ComponentGroup* p) const;
      virtual void calculate (bool saveComponentFlux, bool frozen);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual void copy (const Component& right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class MulComponent 


#endif
