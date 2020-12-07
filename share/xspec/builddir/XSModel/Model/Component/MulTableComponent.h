//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MULTABLECOMPONENT_H
#define MULTABLECOMPONENT_H 1
class UniqueEnergy;

// MulComponent
#include <XSModel/Model/Component/MulComponent.h>

class TableComponent;




class MulTableComponent : public MulComponent  //## Inherits: <unnamed>%36C456F11640
{

  public:
      MulTableComponent(const MulTableComponent &right);
      MulTableComponent (ComponentGroup* p);
      virtual ~MulTableComponent();

      void calculate (bool saveComponentFlux, bool frozen);
      virtual int read ();
      virtual MulTableComponent* clone (ComponentGroup* p) const;
      virtual void clearArrays (const std::set<UniqueEnergy*>& currentEngs);
      virtual void initializeForFit ();
      const string& tableFile () const;
      void tableFile (const string& value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual void swap (Component& right);
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
      bool m_expTable;
};

// Class MulTableComponent 

inline const string& MulTableComponent::tableFile () const
{
  return m_tableFile;
}

inline void MulTableComponent::tableFile (const string& value)
{
  m_tableFile = value;
}

inline const string MulTableComponent::tableType () const
{
  return m_tableType;
}

inline void MulTableComponent::tableType (string value)
{
  m_tableType = value;
}

inline const TableComponent* MulTableComponent::table () const
{
  return m_table;
}

inline void MulTableComponent::table (TableComponent* value)
{
  m_table = value;
}


#endif
