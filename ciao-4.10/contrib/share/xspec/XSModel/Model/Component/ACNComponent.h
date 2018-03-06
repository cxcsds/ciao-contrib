//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ACNCOMPONENT_H
#define ACNCOMPONENT_H 1

// ConComponent
#include <XSModel/Model/Component/ConComponent.h>

class Response;


class ACNComponent : public ConComponent  //## Inherits: <unnamed>%3F60877B01AA
{

  public:
      ACNComponent(const ACNComponent &right);
      ACNComponent (ComponentGroup* p);
      virtual ~ACNComponent();

      virtual ACNComponent* clone (ComponentGroup* p) const;
      virtual SumComponent& operator * (SumComponent& right) const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      ACNComponent & operator=(const ACNComponent &right);

      virtual void copy (const Component& right);
      const Response* detector (size_t spectrumNumber) const;

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class ACNComponent 


#endif
