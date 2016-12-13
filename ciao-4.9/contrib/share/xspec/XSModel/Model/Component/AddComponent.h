//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ADDCOMPONENT_H
#define ADDCOMPONENT_H 1

// Component
#include <XSModel/Model/Component/Component.h>
class SumComponent;

//	Additive Component. Derived Class Component extended by
//	defining its combination operation.
//
//	The Additive component also extends the Component class
//	by the addition of a normalization parameter.



class AddComponent : public Component  //## Inherits: <unnamed>%3687BAA76668
{

  public:
      AddComponent(const AddComponent &right);
      AddComponent (ComponentGroup* p);
      virtual ~AddComponent();

      virtual AddComponent* clone (ComponentGroup* p) const;
      virtual Real norm () const;
      virtual void calculate (bool saveComponentFlux, bool frozen);

    // Additional Public Declarations

  protected:
      virtual void swap (Component& right);
      //	The number identifying the normalization parameter. The
      //	parameter itself can be retrieved from the parameterSet
      //	vector using the array operator
      //		(another way of doing this would be to store an
      //	iterator,
      //	(another way of doing this would be to store an iterator,
      //	but that seems less storage wise).
      const int normParNum () const;
      void normParNum (int value);

    // Additional Protected Declarations

  private:
      virtual int read ();
      virtual void copy (const Component& right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      int m_normParNum;

    // Additional Implementation Declarations

};

// Class AddComponent 

inline const int AddComponent::normParNum () const
{
  return m_normParNum;
}

inline void AddComponent::normParNum (int value)
{
  m_normParNum = value;
}


#endif
