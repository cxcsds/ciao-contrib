//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef COMPONENTGROUP_H
#define COMPONENTGROUP_H 1
#include "xsTypes.h"

// xsTypes
#include <xsTypes.h>
// Error
#include <XSUtil/Error/Error.h>
// ComponentListTypes
#include <XSModel/Model/Component/ComponentListTypes.h>
#include <set>

class ModelBase;
class SumComponent;
class Component;
class Parameter;
class ModParam;
class UniqueEnergy;
class ModExprTreeMember;
template <typename T> class ModelExpression;
template <typename T> class XSModExpTree;

//	Component Group Contains one or many components that are
//	combined together, for example a number of additive
//	models that are all combined by a single multiplicative
//	or convolution component.
//
//
//	It is a concrete class which has also one derivation,
//	the background Component Group. This is distinguished by
//	having a unit efficiency matrix (auxiliary response file)
//	     rather than the auxiliary response supplied by the
//	dataset
//	     to be modelled.



class ComponentGroup 
{

  public:



    class NoSuchComponent : public YellowAlert  //## Inherits: <unnamed>%3A8D4AE6022A
    {
      public:
          NoSuchComponent (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      ComponentGroup(const ComponentGroup &right);
      ComponentGroup (ModelExpression<ModExprTreeMember>& gs, ModelBase* parent, bool nested = false);
      ~ComponentGroup();
      ComponentGroup & operator=(const ComponentGroup &right);

      //	Additional Public Declarations
      void calculate (bool saveComponentFlux = false, bool frozen = false);
      friend std::ostream& operator << (std::ostream& s, const ComponentGroup& right);
      ComponentGroup* clone () const;
      const ComponentList& elements () const;
      const Component* getElements (const string& componentName) const;
      void setElements (const string& componentName, const Component* newElement);
      void resetComponentFlux () const;
      SumComponent* groupFlux ();
      void registerParameters () const;
      Parameter* getLocalParameter (size_t i) const;
      Parameter* localParameter (size_t i) const;
      bool isNested () const;
      size_t dataGroup () const;
      size_t parameterIndexBase () const;
      //	Add one to component count and paramIncrement to
      //	parameter count for the containing model.
      size_t incrementModelParameterCount ();
      //	Add one to component count and paramIncrement to
      //	parameter count for the containing model.
      size_t incrementModelComponentCount ();
      size_t modelIndex () const;
      const ArrayContainer& energyArray () const;
      const SumComponent* sum () const;
      void allButNorms (IntegerVector& paramsToFreeze) const;
      void checkZeroNorms (std::set<int>& parsWithZeroNorms);
      void setComputeFlag (bool value);
      std::list<ModParam*> normParams () const;
      void clearArrays (const std::set<UniqueEnergy*>& currentEngs);
      std::vector<ModParam*> getVariableParameters () const;
      const string& parentName () const;
      void saveComponentFlux (bool setSaveFlux = false) const;
      void deleteComponent (int sequenceNumber, int index);
      void setNestedElement (const string& componentName, Component* newElement);
      void resetElement (XSModExpTree<ComponentGroup*>& newGroups, const std::vector<Component*>& existingComponents);
      Component* componentByNumber (int index) const;
      void insertComponent (int location, int index, const string& name, char op);
      void exchangeComponent (int location, Component* newComponent);
      Component* createComponent (string& name);
      void deregisterParameters () const;
      Component* firstComponent ();
      void addToElements (int componentOffset, Component* newComponent);
      const ModelBase* parent () const;
      const ModelExpression<ModExprTreeMember>* componentInfo () const;
      const std::set<UniqueEnergy*>& uniqueEnergyArray () const;
      static const string& GROUPTEST ();
      
      std::list<SumComponent*>& individualSources();

  public:
    // Additional Public Declarations
      friend class ModelBase;
      void setComponentInfo(ModelExpression<ModExprTreeMember>* expr);
  protected:
    // Additional Protected Declarations

  private:
      void setElement (XSModExpTree<ComponentGroup*>& componentGroups);
      void swap (ComponentGroup& right) throw ();
      void resizeElements (size_t n);
      void updateExpression (Component* newComponent, const string& oldName, size_t wordIdx);
      std::vector<size_t> postfixOperatorLocs (size_t endIdx, size_t nComps, size_t skipIdx, size_t nSkip) const;
      void parent(ModelBase* mod);
      // Upon return, parBeg will be the iterator to the left-most component
      //  inside the parentheses, parEnd will be one PAST the right-most.
      //  The return values are the indices of the 2 components. 
      //  Calling function must first verify that parentheses exist.
      std::pair<size_t,size_t> compsInsideParentheses(ComponentListIterator& parBeg, ComponentListIterator& parEnd);
      void getParsWithZeroNorms(std::set<int>& parsWithZeroNorms) const;
      static string checkCurrentTableModelExpr (const Component* component, const string& prevExprString);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_GROUPTEST;
      static int s_count;

      int m_index;
      bool m_nested;
      ModelExpression<ModExprTreeMember>* m_componentInfo;
      SumComponent* m_groupFlux;
      ModelBase* m_parent;
      ComponentList m_elements;

      // This is a temporary holder of the individual additive
      // contributions for the associated ComponentGroup.  It will
      // remain empty at all times except during the CompCombiner
      // combination process when storeSources=true (ie. during
      // plots with add components and for 'eqwidth'). Its results
      // will ultimately be transfered to ModelBase::m_componentSource.
      std::list<SumComponent*> m_individualSources;

    // Additional Implementation Declarations

};

// Class ComponentGroup::NoSuchComponent 

// Class ComponentGroup 

inline const string& ComponentGroup::GROUPTEST ()
{
  return s_GROUPTEST;
}

inline bool ComponentGroup::isNested () const
{
  return m_nested;
}

inline const ModelExpression<ModExprTreeMember>* ComponentGroup::componentInfo () const
{
    return m_componentInfo;
}

inline SumComponent* ComponentGroup::groupFlux ()
{
  return m_groupFlux;
}

inline const ModelBase* ComponentGroup::parent () const
{
  return m_parent;
}

inline void ComponentGroup::parent(ModelBase* mod)
{
   m_parent = mod;
}

inline const ComponentList& ComponentGroup::elements () const
{
 return m_elements;
}

inline std::list<SumComponent*>& ComponentGroup::individualSources ()
{
   return m_individualSources;
}

#endif
