//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TABLEMODPARAM_H
#define TABLEMODPARAM_H 1

// xsTypes
#include <xsTypes.h>
// ModParam
#include <XSModel/Parameter/ModParam.h>




class TableModParam : public ModParam  //## Inherits: <unnamed>%37179FA02BC0
{

  public:
      TableModParam(const TableModParam &right);
      TableModParam (const string& inputName, Component* p, Real val, Real delta = 0., Real high = LARGE, Real low = -LARGE, Real top = LARGE, Real bot = -LARGE, const string& unit = "");
      virtual ~TableModParam();

      virtual TableModParam* clone (Component* p) const;
      //	The value of the Method Keyword in the Table model file.
      //	logInterp = 0 -> linear interpolation as opposed to
      //	logarithmic (the specifics of "linear" interpolation are
      //	not clear -- could this mean any technique in which the
      //	abscissa is linear rather than logarithmic?)
      const bool logInterp () const;
      void logInterp (bool value);
      const int numVals () const;
      void numVals (int value);
      const RealArray& tabValue () const;
      void setTabValue (const RealArray& value);
      Real tabValue (size_t index) const;
      void tabValue (size_t index, Real value);

    // Additional Public Declarations

  protected:
      //	Additional Protected Declarations
      virtual bool compare (const Parameter& right) const;

    // Additional Protected Declarations

  private:
      TableModParam();
      TableModParam & operator=(const TableModParam &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_logInterp;
      int m_numVals;

    // Data Members for Associations
      RealArray m_tabValue;

    // Additional Implementation Declarations

};

// Class TableModParam 

inline const bool TableModParam::logInterp () const
{
  return m_logInterp;
}

inline void TableModParam::logInterp (bool value)
{
  m_logInterp = value;
}

inline const int TableModParam::numVals () const
{
  return m_numVals;
}

inline void TableModParam::numVals (int value)
{
  m_numVals = value;
}

inline const RealArray& TableModParam::tabValue () const
{
  return m_tabValue;
}

inline void TableModParam::setTabValue (const RealArray& value)
{
  m_tabValue.resize(value.size());
  m_tabValue = value;
}

inline Real TableModParam::tabValue (size_t index) const
{
  return m_tabValue[index];
}

inline void TableModParam::tabValue (size_t index, Real value)
{
  m_tabValue[index] = value;
}


#endif
