//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MODELEXPRCONTEXTS_H
#define MODELEXPRCONTEXTS_H 1
#include <xsTypes.h>
#include <XSUtil/Parse/XSModExpTree.h>
#include <utility>

template <typename T>
class ModelExpression;
class ModExprTreeMember;




typedef XSModExpTree<ModelExpression<ModExprTreeMember> > ModelExprTree;
//	This implements functionality specific to Model
//	Expressions when they are used as sub-expressions in an
//	expression tree.  The major distinction between this and
//	a stand-alone context is that it ASSUMES the expression
//	string corresponds to an Xspec ComponentGroup, ie. at
//	most 1 pair of parentheses and no plus signs outside of
//	parentheses.  It also contains additional data members
//	for storing tree position information.



class ModExprTreeMember 
{
   friend class ModExprStandAlone;

  public:



    typedef ModelExpression<ModExprTreeMember> HostClass;
      virtual ~ModExprTreeMember();
      //	This is the expression's 0-based post-order tree
      //	position.
      int location () const;
      //	The group number is the location number of the top-level
      //	component group which contains this sub-expression.  A
      //	distinguishing feature of top-level expressions is that
      //	their group and location numbers are equal.
      int group () const;
      //	The location in the expression string of the one allowed
      //	pair of parentheses.  If there is no pair, the values
      //	will be set to npos.
      std::pair<size_t,size_t> parenLocs () const;
      const std::vector<size_t>& plusLocs () const;

  public:
    // Additional Public Declarations

  protected:
      ModExprTreeMember();

      //	Store locations of parentheses and plus signs, if any.
      void contextSpecificInit (HostClass* host);
      //	This exists merely to provide this class with
      //	polymorphic access to the inhereting HostClass's version
      //	of the function.
      virtual void setComponentSequence (int seq, int index) = 0;
      void Swap (ModExprTreeMember& right);

    // Additional Protected Declarations

  private:
      ModExprTreeMember & operator=(const ModExprTreeMember &right);

      static void sequenceSubExpressions (ModelExprTree::iterator& itExp, int& wordStart);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      int m_location;
      int m_group;
      std::pair<size_t,size_t> m_parenLocs;
      std::vector<size_t> m_plusLocs;

    // Additional Implementation Declarations

};
//	This implements functionality that is specific to Model
//	Expressions when they exist as a single stand-alone
//	object rather than parts of tree.  It assumes the
//	expression strings can have all of the complexity
//	allowed under Xspec's model command, including
//	parentheses nested to arbitrary depth.  It can also
//	create a tree of sub-expressions from itself.



class ModExprStandAlone 
{

  public:



    typedef ModelExpression<ModExprStandAlone> HostClass;
      virtual ~ModExprStandAlone() = 0;

      void createExpTree (ModelExprTree& expTree) const;

  public:
    // Additional Public Declarations

  protected:
      ModExprStandAlone();

      void contextSpecificInit (HostClass* host);
      void Swap (ModExprStandAlone& right);

    // Additional Protected Declarations

  private:
      ModExprStandAlone & operator=(const ModExprStandAlone &right);

      static std::vector<string::size_type> findGroups (const string& inString);
      static void makeSubExpressions (const string& inString, ModelExprTree& expTree);
      static std::vector<string::size_type> findNests (const string& inString);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      //	This is just a local copy of the Host class m_expr
      //	String.  Needed for createExpTree.
      string m_fullExprString;

    // Additional Implementation Declarations

};

// Class ModExprTreeMember 

inline ModExprTreeMember::~ModExprTreeMember()
{
}


inline int ModExprTreeMember::location () const
{
  return m_location;
}

inline int ModExprTreeMember::group () const
{
  return m_group;
}

inline std::pair<size_t,size_t> ModExprTreeMember::parenLocs () const
{
  return m_parenLocs;
}

inline const std::vector<size_t>& ModExprTreeMember::plusLocs () const
{
  return m_plusLocs;
}

// Class ModExprStandAlone 
inline ModExprStandAlone::~ModExprStandAlone() {}


#endif
