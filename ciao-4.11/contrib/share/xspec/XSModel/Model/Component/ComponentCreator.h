//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef COMPONENT_CREATOR_H
#define COMPONENT_CREATOR_H 1

// Component
class Component;
class ComponentGroup;

//	Instantiates Components: virtual constructor
//	using Factory Method



class ComponentCreator 
{

  public:
      ComponentCreator();
      virtual ~ComponentCreator();

      Component* GetComponent (const string& name, ComponentGroup* group);
      Component* GetComponent (const string& id, ComponentGroup* group, const string& type, int table = false);
      //	Additional Public Declarations
      void reset ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual Component* Make (const string& name, ComponentGroup* group);
      virtual Component* Make (const string& idstring, ComponentGroup* group, const string& type, int table = false);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      Component* m_component;

    // Additional Implementation Declarations

};

// Class ComponentCreator 

inline void ComponentCreator::reset ()
{
  m_component = 0;



}


#endif
