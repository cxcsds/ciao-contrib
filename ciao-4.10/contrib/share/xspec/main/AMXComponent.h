//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef AMXCOMPONENT_H
#define AMXCOMPONENT_H 1

// xsTypes
#include <xsTypes.h>
// Component
#include <XSModel/Model/Component/Component.h>

//	A mixing model is a model that transcends data groups,
//	unlike other components that are specific to individual
//	data groups. This class is a modification of the mixing
//      model such that it operates on the flux multiplied by
//      the efficiency (the analog of the ACN model wrt the 
//      convolution model).
//
//	The syntax checker ensures that there is exactly one
//	AMX model per Model.
//
//	Unlike other component types,
//	generated fit
//	parameters are unique, rather than multiplied by the
//	number of data groups.
//
//	Finally the AMX component depends on the data, not
//	just the response, in a way that requires implementation.

class MixUtility;

class AMXComponent : public Component  //## Inherits: <unnamed>%3687BAB18948
{

  public:
      AMXComponent(const AMXComponent &right);
      AMXComponent (ComponentGroup* p);
      virtual ~AMXComponent();

      virtual AMXComponent* clone (ComponentGroup* p) const;
      //	ConComponent::calculate() does  nothing, because
      //	convolution is applied to previously calculated flux
      //	array.
      //	The convolution is performed at the combination stage.
      virtual void calculate (bool saveComponentFlux, bool frozen);
      void initialize ();
      void perform (const EnergyPointer& energy, GroupFluxContainer& flux, GroupFluxContainer& fluxError);
      virtual void initializeForFit ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual void copy (const Component& right);
      const Response* detector (size_t spectrumNumber) const;

    // Additional Private Declarations

  private: //## implementation
      MixUtility* m_mixUtility;
    // Additional Implementation Declarations

};

// Class AMXComponent 


#endif
