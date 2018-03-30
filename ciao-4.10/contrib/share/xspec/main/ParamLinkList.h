//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PARAMLINKLIST_H
#define PARAMLINKLIST_H 1
class ResponseParam;
#include <map>


class ParameterLink;
class Parameter;




class ParamLinkList 
{

  public:
      ~ParamLinkList();

      //	Additional Public Declarations
      void unlink (Parameter* p);
      static ParamLinkList* Instance ();
      void setCompute (const Parameter* param, bool flag) const;
      void removeDependentParameterLinks (Parameter* p);
      //	Tell all ResponseParams which link to respPar that resp
      //	Par has changed.
      void updateResponseParamLinkers (const ResponseParam* respPar) const;
      const std::map<Parameter*,ParameterLink*>& linkList () const;
      const ParameterLink* linkList (Parameter* key) const;
      void linkList (Parameter* key, ParameterLink* value);
      // On input, parsWithZeroNorms should be the FULL indices of all
      // VARIABLE parameters in component groups with a zero norm.  This 
      // function will remove those which can still affect the model due to 
      // being linked to from parameters in non-zero norm component groups.
      void checkLinksToZeroNorms(std::set<int>& parsWithZeroNorms) const;

    // Additional Public Declarations

  protected:
      ParamLinkList();

    // Additional Protected Declarations

  private:
     void recursiveCheckZeroLinks(const Parameter* par, std::set<int>& parsWithZeroNorms) const;
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static ParamLinkList* s_instance;

    // Data Members for Associations
      std::map<Parameter*,ParameterLink*> m_linkList;

    // Additional Implementation Declarations

};

// Class ParamLinkList 

inline const std::map<Parameter*,ParameterLink*>& ParamLinkList::linkList () const
{
  return m_linkList;
}

inline const ParameterLink* ParamLinkList::linkList (Parameter* key) const
{
  std::map<Parameter*,ParameterLink*>::const_iterator f(m_linkList.find(key));
  return (f != m_linkList.end() ?  f->second : 0 );
}

inline void ParamLinkList::linkList (Parameter* key, ParameterLink* value)
{
  m_linkList[key] = value;
}


#endif
