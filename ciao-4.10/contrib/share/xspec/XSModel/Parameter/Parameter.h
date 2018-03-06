//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PARAMETER_H
#define PARAMETER_H 1
#include <xsTypes.h>
#include <set>

// Error
#include <XSUtil/Error/Error.h>
// map
#include <map>
// ParamLinkList
#include <XSModel/Parameter/ParamLinkList.h>

class Component;
class ParameterLink;




class Parameter 
{

  public:



    class ResetFailure : public RedAlert  //## Inherits: <unnamed>%3919B2AA033C
    {
      public:
          ResetFailure();

      protected:
      private:
      private: //## implementation
    };



    class InvalidInput : public YellowAlert  //## Inherits: <unnamed>%3911DD3EADD0
    {
      public:
          InvalidInput (const string& name);

      protected:
      private:
      private: //## implementation
    };



    class CantFreeze : public YellowAlert  //## Inherits: <unnamed>%3C110D9C0141
    {
      public:
          CantFreeze (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      Parameter(const Parameter &right);
      Parameter (Component* p = 0	// Token for parent component instance for grabbing
      	// initialization data etc. Since there are (gain)
      	// parameters that do not have a component parent this is
      	// a pointer rather than a reference as used for the same
      	// concept for ComponentGroup and Component.
      );
      virtual ~Parameter();
      int operator<(const Parameter &right) const;

      int operator>(const Parameter &right) const;

      int operator<=(const Parameter &right) const;

      int operator>=(const Parameter &right) const;

      virtual Parameter* clone (Component* p) const = 0;
      //	This is the main call that modifies parameter
      //	values and constitutes the public part of the interface.
      //
      //	It is implemented as a "Template Method": that is,
      //	it calls overload functions changeValue() and link()
      //
      //	Link's default implementation, which links the numerical
      //	value of one parameter to one or more others
      //	should work for ModParams and ScaleParams.
      //
      //	it is overloaded for SwitchParam which is true or false.
      //
      //
      //	returns true if the parameter has been changed.
      void modify (const string& input);
      //	freeze and thaw  have self explanatory names.
      //
      //	The one point is that they don't apply to anything
      //	other than ModParam subclass. The default implementation
      //	therefore does nothing and is not overridden by Switch
      //	Param or ScaleParam.
      virtual void freeze ();
      //	See "freeze" for details.
      virtual void thaw ();
      //	reset parameter value to its initial values.
      //
      //	This is a virtual function whose default implementation
      //	is to assume that the parameter is defined in XSPEC's
      //	model.{version} file.
      virtual void reset () throw (Parameter::ResetFailure);
      ParameterLink* thisLink ();
      const ParameterLink* thisLink () const;
      virtual Real value () const = 0;
      friend std::ostream& operator << (std::ostream& s, const Parameter& right);
      friend std::istream& operator >> (std::istream& s, Parameter& right);
      static void initializeLinks ();
      size_t dataGroup () const;
      //	untie unlinks parameters preserving the current value if
      //	preserve is set to true.
      void untie (bool preserve = false);
      void reindex (int offset);
      Parameter* lookupCoParameter (size_t i) const;
      virtual bool isFrozen () const;
      virtual void setCompute (bool flag) const;
      //	Operation supporting the XSPEC tclout command which
      //	simply writes the data members of the parameter to a
      //	string.
      virtual string stringVal () const = 0;
      string linkString () const;
      //	for calling from TableComponents. Does a check to see
      //	whether the component base pointer has been previously
      //	set and exits without action if so.
      void setParent (Component* p);
      virtual string parameterSetting () const = 0;
      const string& modelName () const;
      const Component* parent () const;
      static void findPersistentLink (Parameter* par, std::set<Parameter*>& parsToProcess, std::map<Parameter*,Parameter*>& processedPars);
      static bool isLinkedToFrozen (const Parameter* par);
      size_t index () const;
      void index (size_t value);
      const string& name () const;
      void name (const string& value);
      bool isLinked () const;
      void isLinked (bool value);
      bool isModelDoomed () const;
      void isModelDoomed (bool value);
      //	If set to true, output stream operator function will
      //	only print for variable parameters.  Otherwise it will
      //	do nothing.
      static bool onlyPrintFree ();
      static void onlyPrintFree (bool value);

  public:
    // Additional Public Declarations

  protected:
      virtual std::istream& get (std::istream& s) throw (YellowAlert&);
      virtual std::ostream& put (std::ostream& s) const = 0;
      virtual void changeValue (const string& parString) = 0;
      virtual void link (const string& toLink);
      bool compare (const Parameter& right) const;
      void setComputeForLinks (bool flag = true) const;
      static ParamLinkList* links ();
      static void links (ParamLinkList* value);
      bool changed () const;
      void changed (bool value);
      Component* parent ();
      void parent (Component* value);
      void thisLink (ParameterLink* value);

    // Additional Protected Declarations
      friend void ParamLinkList::unlink(Parameter* p);
      friend void ParamLinkList::removeDependentParameterLinks(Parameter* p);
  private:
      Parameter & operator=(const Parameter &right);

      void unlink ();
      virtual void doPreserve () = 0;
      virtual void init (const string& initString) = 0;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      size_t m_index;
      string m_name;
      static ParamLinkList* s_links;
      bool m_isLinked;
      bool m_changed;
      bool m_isModelDoomed;
      static bool s_onlyPrintFree;

    // Data Members for Associations
      Component* m_parent;
      ParameterLink* m_thisLink;

    // Additional Implementation Declarations

};

// Class Parameter::ResetFailure 

// Class Parameter::InvalidInput 

// Class Parameter::CantFreeze 

// Class Parameter 

inline int Parameter::operator<(const Parameter &right) const
{
   return m_index < right.m_index;
}

inline int Parameter::operator>(const Parameter &right) const
{
   return m_index > right.m_index;
}

inline int Parameter::operator<=(const Parameter &right) const
{
   return m_index <= right.m_index;
}

inline int Parameter::operator>=(const Parameter &right) const
{
   return m_index >= right.m_index;
}


inline void Parameter::thaw ()
{
  // do nothing. Since a parameter that is linked cannot be frozen
  // it doesn't need to be thawed either.
}

inline ParameterLink* Parameter::thisLink ()
{

  return m_thisLink;
}

inline const Component* Parameter::parent () const
{
  return m_parent;
}

inline size_t Parameter::index () const
{
  return m_index;
}

inline void Parameter::index (size_t value)
{
  m_index = value;
}

inline const string& Parameter::name () const
{
  return m_name;
}

inline void Parameter::name (const string& value)
{
  m_name = value;
}

inline ParamLinkList* Parameter::links ()
{
  return s_links;
}

inline void Parameter::links (ParamLinkList* value)
{
  s_links = value;
}

inline bool Parameter::isLinked () const
{
  return m_isLinked;
}

inline void Parameter::isLinked (bool value)
{
  m_isLinked = value;
}

inline bool Parameter::changed () const
{
  return m_changed;
}

inline void Parameter::changed (bool value)
{
  m_changed = value;
}

inline bool Parameter::isModelDoomed () const
{
  return m_isModelDoomed;
}

inline void Parameter::isModelDoomed (bool value)
{
  m_isModelDoomed = value;
}

inline bool Parameter::onlyPrintFree ()
{
  return s_onlyPrintFree;
}

inline void Parameter::onlyPrintFree (bool value)
{
  s_onlyPrintFree = value;
}

inline Component* Parameter::parent ()
{
  return m_parent;
}

inline void Parameter::parent (Component* value)
{
  m_parent = value;
}

inline const ParameterLink* Parameter::thisLink () const
{
  return m_thisLink;
}

inline void Parameter::thisLink (ParameterLink* value)
{
  m_thisLink = value;
}


#endif
