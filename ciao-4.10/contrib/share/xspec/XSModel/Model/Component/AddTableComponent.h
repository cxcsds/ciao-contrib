//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ADDTABLECOMPONENT_H
#define ADDTABLECOMPONENT_H 1
class UniqueEnergy;

// AddComponent
#include <XSModel/Model/Component/AddComponent.h>

class TableComponent;




class AddTableComponent : public AddComponent  //## Inherits: <unnamed>%36C456F7EC48
{

  public:
      AddTableComponent(const AddTableComponent &right);
      AddTableComponent (ComponentGroup* p);
      virtual ~AddTableComponent();

      virtual void calculate (bool saveComponentFlux, bool frozen);
      virtual AddTableComponent* clone (ComponentGroup* p) const;
      virtual void clearArrays (const std::set<UniqueEnergy*>& currentEngs);
      virtual void initializeForFit ();
      const string& tableFile () const;
      void tableFile (const string& value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual void swap (Component& right);
      virtual int read ();
      virtual void copy (const Component& right);
      const string tableType () const;
      void tableType (string value);
      const TableComponent* table () const;
      void table (TableComponent* value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_tableFile;
      string m_tableType;

    // Data Members for Associations
      TableComponent* m_table;

    // Additional Implementation Declarations

};

// Class AddTableComponent 

inline const string& AddTableComponent::tableFile () const
{
  return m_tableFile;
}

inline void AddTableComponent::tableFile (const string& value)
{
  m_tableFile = value;
}

inline const string AddTableComponent::tableType () const
{
  return m_tableType;
}

inline void AddTableComponent::tableType (string value)
{
  m_tableType = value;
}

inline const TableComponent* AddTableComponent::table () const
{
  return m_table;
}

inline void AddTableComponent::table (TableComponent* value)
{
  m_table = value;
}


#endif
