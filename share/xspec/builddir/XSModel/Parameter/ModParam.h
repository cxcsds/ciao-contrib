//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MODPARAM_H
#define MODPARAM_H 1

// ParamData
#include <XSModel/Parameter/ParamData.h>
// Parameter
#include <XSModel/Parameter/Parameter.h>
#include "XSsymbol.h"

class Component;

class ModParam : public Parameter  //## Inherits: <unnamed>%38EB4EDCF508
{

  public:



  typedef enum {CONS, EXP, JEFFREYS, GAUSS} PriorType;
      ModParam(const ModParam &right);
      //	Custom Constructor
      ModParam (const string& inputName, Component* p, Real val, Real delta = 0., Real high = LARGE, Real low = -LARGE, Real top = LARGE, Real bot = -LARGE, const string& unit = string(), bool isPeriodic = false);
      virtual ~ModParam();

      virtual int setValue (Real val, const char key = 'v');
      virtual ModParam* clone (Component* p = 0) const;
      virtual void freeze ();
      virtual void thaw ();
      bool limitsInvalid ();
      virtual Real value () const;
      bool limitsInvalid () const;
      Real adjustedValue () const;
      Real value (const char key) const;
      //	reset parameter value to its initial values.
      //
      //	This is a virtual function whose default implementation
      //	is to assume that the parameter is defined in XSPEC's
      //	model.{version} file.
      virtual void reset ();
      //	Operation supporting the XSPEC tclout command which
      //	simply writes the data members of the parameter to a
      //	string.
      virtual string stringVal () const;
      virtual string parameterSetting () const;
      static void parseModParamString (const string& fullLine, string& parName, Real* pVal, Real* pDelta, Real* pHigh, Real* pLow, Real* pTop, Real* pBot, string& unit, bool* pIsPeriodic);
      //	Constructs a string from the model name and parameter
      //	index, useful for Fit output column headings.
      virtual string getParameterLabel () const;
      //	]
      const string& unit () const;
      virtual bool isFrozen () const;
      Real epo () const;
      Real emn () const;
      Real epe () const;
      Real gcc () const;
      Real sigma () const;
      ModParam::PriorType priorType () const;
      void priorType (ModParam::PriorType value);
      const RealArray& hyperParam () const;
      void hyperParam (const RealArray& value);
      Real hyperParam (size_t index) const;
      void hyperParam (size_t index, Real value);
      const string& lastErrorStatus () const;
      void lastErrorStatus (const string& value);
      bool isPeriodic () const;

  public:
    // Additional Public Declarations

  protected:
      //	Originally intended for use by ResponseParam subclass.
      //	Unit string and isPeriodic flag are fixed at their
      //	defaults, and Component parent pointer is fixed at
      //	NULL.
      ModParam (const string& initString);

      virtual bool compare (const Parameter& right) const;
      virtual std::ostream& put (std::ostream& s) const;
      virtual void changeValue (const string& parString);
      virtual void doPreserve ();
      virtual bool processValues (const string& parString);
      virtual void rePrompt (string& newString) const;
      Real checkDeltaForFrozen (Real delta);
      virtual void init (const string& initStr);
      Real applyPeriodicity (Real value) const;
      const ParamData values () const;
      void values (ParamData value);

    // Additional Protected Declarations

  private:
      ModParam();
      ModParam & operator=(const ModParam &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const string m_unit;
      bool m_isFrozen;
      Real m_epo;
      Real m_emn;
      Real m_epe;
      Real m_gcc;
      Real m_sigma;
      ModParam::PriorType m_priorType;
      RealArray m_hyperParam;
      string m_lastErrorStatus;
      const bool m_isPeriodic;

    // Data Members for Associations
      ParamData m_values;

    // Additional Implementation Declarations

};

// Class ModParam 

inline void ModParam::thaw ()
{
  m_isFrozen = false;
}

inline bool ModParam::limitsInvalid () const
{
  return ( m_values.bot() > m_values.top() || 
           m_values.top() > m_values.max() ||
           m_values.min() > m_values.max() ); 
}

inline const string& ModParam::unit () const
{
  return m_unit;
}

inline bool ModParam::isFrozen () const
{
  return m_isFrozen;
}

inline Real ModParam::epo () const
{
  return m_epo;
}

inline Real ModParam::emn () const
{
  return m_emn;
}

inline Real ModParam::epe () const
{
  return m_epe;
}

inline Real ModParam::gcc () const
{
  return m_gcc;
}

inline Real ModParam::sigma () const
{
  return m_sigma;
}

inline ModParam::PriorType ModParam::priorType () const
{
  return m_priorType;
}

inline void ModParam::priorType (ModParam::PriorType value)
{
  m_priorType = value;
}

inline const RealArray& ModParam::hyperParam () const
{
  return m_hyperParam;
}

inline void ModParam::hyperParam (const RealArray& value)
{
  m_hyperParam.resize(value.size());
  m_hyperParam = value;
}

inline Real ModParam::hyperParam (size_t index) const
{
  if (index < m_hyperParam.size() ) {
    return m_hyperParam[index];
  } else {
    return 0.0;
  }
}

inline void ModParam::hyperParam (size_t index, Real value)
{
  if (index < m_hyperParam.size() ) {
    m_hyperParam[index] = value;
  }
}

inline const string& ModParam::lastErrorStatus () const
{
  return m_lastErrorStatus;
}

inline void ModParam::lastErrorStatus (const string& value)
{
  m_lastErrorStatus = value;
}

inline bool ModParam::isPeriodic () const
{
  return m_isPeriodic;
}

inline const ParamData ModParam::values () const
{
  return m_values;
}

inline void ModParam::values (ParamData value)
{
  m_values = value;
}


#endif
