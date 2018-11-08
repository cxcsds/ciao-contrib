//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SUMCOMPONENT_H
#define SUMCOMPONENT_H 1

// xsTypes
#include <xsTypes.h>
// Component
#include <XSModel/Model/Component/Component.h>

class AddComponent;
class ComponentGroup;
class ConComponent;
class MixComponent;
class MulComponent;

//	SumComponent is a component type which represents the
//	sum of a component group. It differs from AddComponent
//	in that
//	1) the count is not updated
//	2) the normalization parameter is 1, and is ignored.
//	3) model arithmetic (+=, +, *=, *) is defined on Sum
//	Components and between multiplicative types and Sum
//	Components and not on AddComponents



class SumComponent : public Component  //## Inherits: <unnamed>%3DD148960348
{

  public:
      SumComponent(const SumComponent &right);
      SumComponent (ComponentGroup* p);
      SumComponent (const AddComponent& right);
      SumComponent (const MulComponent& right);
      virtual ~SumComponent();

      virtual SumComponent* clone (ComponentGroup* p) const;
      virtual void calculate (bool saveComponentFlux, bool frozen);
      //	+= operator for addition of two additives.
      //
      //	N.B. expects left hand expression to be pre-normalized.
      //
      SumComponent& operator += (const SumComponent& right);
      //	Additional Public Declarations
      virtual bool isNested () const;
      void normalize ();
      virtual Real norm () const;
      virtual void savePhotonArray (bool setSaveFlag);
      virtual void restorePhotonArray ();
      virtual void registerSelf () const;
      virtual void saveUniquePhotonArray (bool setSaveFlag = true);
      virtual void restoreUniquePhotonArray ();
      void fillPhotonArrays ();
      void clearPhotonArrays ();
      //	Provides an alternative to dynamic_cast.
      virtual SumComponent* toSumComponent ();
      SumComponent& operator *= (const Component& right);
      virtual SumComponent& operator * (SumComponent& right) const;
      //	Non-const version is used by Model when folding its
      //	source components and calling its alignFluxForFold
      //	function.
      ArrayContainer& photonArray ();
      //	Non-const version is used by Model when folding its
      //	source components and calling its alignFluxForFold
      //	function.
      ArrayContainer& photonErrArray ();
      const ArrayContainer& foldedPhotonFlux () const;
      RealArray& foldedPhotonFlux (size_t spectrumNumber);
      const ArrayContainer& foldedPhotonFluxErr () const;
      RealArray& foldedPhotonFluxErr (size_t spectrumNumber);
      const ArrayContainer& photonArray () const;
      const RealArray& photonArray (size_t spectrumNumber) const;
      const ArrayContainer& photonErrArray () const;
      const RealArray& photonErrArray (size_t spectrumNumber) const;

    // Additional Public Declarations
      friend class MixComponent;
      friend class ConComponent;
      friend class MulComponent;
      friend class ACNComponent;
      friend class AddComponent;
  protected:
    // Additional Protected Declarations

  private:
      void copy (const Component& right);
      virtual void swap (Component& right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string NORM;

    // Data Members for Associations
      ArrayContainer m_foldedPhotonFlux;
      ArrayContainer m_foldedPhotonFluxErr;
      ArrayContainer m_photonArray;
      ArrayContainer m_photonErrArray;

    // Additional Implementation Declarations

};

// Class SumComponent 

inline SumComponent* SumComponent::toSumComponent ()
{
   return this;
}

inline ArrayContainer& SumComponent::photonArray ()
{
   return m_photonArray;
}

inline ArrayContainer& SumComponent::photonErrArray ()
{
   return m_photonErrArray;
}

inline const ArrayContainer& SumComponent::foldedPhotonFlux () const
{
  return m_foldedPhotonFlux;
}

inline RealArray& SumComponent::foldedPhotonFlux (size_t spectrumNumber)
{
  return m_foldedPhotonFlux[spectrumNumber];
}

inline const ArrayContainer& SumComponent::foldedPhotonFluxErr () const
{
  return m_foldedPhotonFluxErr;
}

inline RealArray& SumComponent::foldedPhotonFluxErr (size_t spectrumNumber)
{
  return m_foldedPhotonFluxErr[spectrumNumber];
}

inline const ArrayContainer& SumComponent::photonArray () const
{
  return m_photonArray;
}

inline const ArrayContainer& SumComponent::photonErrArray () const
{
  return m_photonErrArray;
}


#endif
