//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CONCOMPONENT_H
#define CONCOMPONENT_H 1

// Component
#include <XSModel/Model/Component/Component.h>

class SumComponent;




class ConComponent : public Component  //## Inherits: <unnamed>%3687BAAB0098
{

  public:
      ConComponent(const ConComponent &right);
      ConComponent (ComponentGroup* p);
      virtual ~ConComponent();

      virtual ConComponent* clone (ComponentGroup* p) const;
      virtual SumComponent& operator * (SumComponent& right) const;
      //	ConComponent::calculate() does  nothing, because
      //	convolution is applied to previously calculated flux
      //	array.
      //	The convolution is performed at the combination stage.
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

// Class ConComponent 


#endif
