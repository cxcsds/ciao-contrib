//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PARAMETERLINK_H
#define PARAMETERLINK_H 1

// Error
#include <XSUtil/Error/Error.h>
// map
#include <map>
// MathExpression
#include <XSUtil/Parse/MathExpression.h>
namespace XSContainer {
    class ModelContainer;

} // namespace XSContainer
#include <iosfwd>
class Parameter;

//	The ParameterLink class contains information needed to
//	express arbitrary links between parameters. its
//	attributes are
//
//	1) a std::map instance indexing parameter numbers
//	to parameter pointers.
//
//
//	2) an expression containing the relationship between
//	*this and the parameters in the map.



class ParameterLink 
{

  public:



    class InvalidInput : public YellowAlert  //## Inherits: <unnamed>%39172B907898
    {
      public:
          InvalidInput (const string& msg);

      protected:
      private:
      private: //## implementation
    };

  private:
    //	thrown if a link expression has slipped through all the
    //	checks with invalid syntax. RedAlert fatal.



    class ParseFailure : public RedAlert  //## Inherits: <unnamed>%3921695600F4
    {
      public:
          ParseFailure (const string& msg);

      protected:
      private:
      private: //## implementation
    };

  public:



    class DivideCheck : public YellowAlert  //## Inherits: <unnamed>%3921A58601FE
    {
      public:
          DivideCheck (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    class NoValidParametersInExpression : public YellowAlert  //## Inherits: <unnamed>%3AB8CE9E0092
    {
      public:
          NoValidParametersInExpression (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      ParameterLink(const ParameterLink &right);
      //	Constructor for parameter link class.
      //
      //	Arguments are a string, from which is constructed
      //	an Expression instance.
      //
      //	The isBoolean argument allows the code
      //	to flag when the link is applied to a SwitchParam that
      //	has a much more restrictive link syntax
      ParameterLink (const string& linkExpression, const Parameter* p, bool isBoolean = false);
      ~ParameterLink();
      ParameterLink & operator=(const ParameterLink &right);

      //	Return a pointer to the ith independent parameter
      //	in the link string.
      const Parameter* independentParameter (int i) const;
      Real linkValue () const;
      void putLink (std::ostream& s) const;
      ParameterLink* clone () const;
      bool findParam (const Parameter* param) const;
      string linkExpression (bool fullname) const;
      const MathExpression& linkString () const;
      void rerouteLink (const std::vector<Parameter*>& newPars);
      void regenerateExpression ();
      static const int& FLAGVALUE ();
      const std::vector<const Parameter*>& members () const;
      void members (const std::vector<const Parameter*>& value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void swap (ParameterLink& right);
      //	Interprets a "word" in the link expression as
      //	a parameter, and adds a map entry to the members list.
      bool wordToParam (const string& word);
      bool addPointer (int num, const string& modelName = string("_DEFAULT"));
      //	Interprets a "word" in the link expression as a response
      //	parameter, and adds pointer to the members list.
      bool wordToResponseParam (const string& word);
      const bool boolean () const;
      //	Current value of the link. Definitely useful for
      //	printing,
      //	and perhaps useful if the changed() flag is set and
      //	queried appropriately.
      //
      //	linkVal is set before exit of linkValue().
      const Real linkVal () const;
      void linkVal (Real value);
      const Parameter* parent () const;
      void parent (const Parameter* value);
      void linkString (MathExpression value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_boolean;
      Real m_linkVal;
      const Parameter* m_parent;
      static const int s_FLAGVALUE;
      std::vector<const Parameter*> m_members;

    // Data Members for Associations
      MathExpression m_linkString;

    // Additional Implementation Declarations

};

// Class ParameterLink::InvalidInput 

// Class ParameterLink::ParseFailure 

// Class ParameterLink::DivideCheck 

// Class ParameterLink::NoValidParametersInExpression 

// Class ParameterLink 

inline const Parameter* ParameterLink::independentParameter (int i) const
{
  return m_members[i];    
}

inline const MathExpression& ParameterLink::linkString () const
{
   return m_linkString;
}

inline const bool ParameterLink::boolean () const
{
  return m_boolean;
}

inline const Real ParameterLink::linkVal () const
{
  return m_linkVal;
}

inline void ParameterLink::linkVal (Real value)
{
  m_linkVal = value;
}

inline const Parameter* ParameterLink::parent () const
{
  return m_parent;
}

inline void ParameterLink::parent (const Parameter* value)
{
  m_parent = value;
}

inline const int& ParameterLink::FLAGVALUE ()
{
  return s_FLAGVALUE;
}

inline const std::vector<const Parameter*>& ParameterLink::members () const
{
  return m_members;
}

inline void ParameterLink::members (const std::vector<const Parameter*>& value)
{
  m_members = value;
}

inline void ParameterLink::linkString (MathExpression value)
{
  m_linkString = value;
}


#endif
