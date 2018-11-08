//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MIXCOMPONENT_H
#define MIXCOMPONENT_H 1

// xsTypes
#include <xsTypes.h>
// Component
#include <XSModel/Model/Component/Component.h>

//	A mixing model is a model that transcends data groups,
//	unlike other components that are specific to individual
//	data groups.
//
//	The syntax checker ensures that there is exactly one
//	Mixing model per Model.
//
//	Unlike other component types,
//	generated fit
//	parameters are unique, rather than multiplied by the
//	number of data groups.
//
//	Finally the mixing component depends on the data, not
//	just the response, in
//	a way that requires implementation.

class MixUtility;

class MixComponent : public Component  //## Inherits: <unnamed>%3687BAB18948
{

  public:
      MixComponent(const MixComponent &right);
      MixComponent (ComponentGroup* p);
      virtual ~MixComponent();

      virtual MixComponent* clone (ComponentGroup* p) const;
      //	ConComponent::calculate() does  nothing, because
      //	convolution is applied to previously calculated flux
      //	array.
      //	The convolution is performed at the combination stage.
      virtual void calculate (bool saveComponentFlux, bool frozen);
      void initialize (const IntegerArray& specNums);
      virtual void initializeForFit ();
      void operator () (const std::vector<SumComponent*>& sumComps);
      // Mix-models aren't obligated to have associated
      //  MixUtility classes.  If they don't, these functions will do nothing.
      void addMixUtility();
      void removeMixUtility();
      bool isBad() const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual void copy (const Component& right);
      static void makeBadFlux(GroupFluxContainer& allFluxes);

    // Additional Private Declarations

  private: //## implementation
      MixUtility* m_mixUtility;
      // This flag will be set 'true' whenever an exception is thrown
      //  during any of the initialization or data verfication stages.
      //  And when set to 'true', m_mixUtility (if any) should immediately
      //  be deleted.
      bool m_isBad;
    // Additional Implementation Declarations

};

inline bool MixComponent::isBad() const
{
   return m_isBad;
}

// Class MixComponent 


#endif
