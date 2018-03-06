//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef LINKEXPRESSION_H
#define LINKEXPRESSION_H 1

// Error
#include <XSUtil/Error/Error.h>
// AbstractExpression
#include <XSUtil/Parse/AbstractExpression.h>
#include <xsTypes.h>
#include <list>
#include <utility>

//	Concrete subclass of AbstractExpression.  This parses
//	and evaluates mathematical expressions with constraints
//	specific to Xspec's rules of parameter linking, as
//	defined by the newpar command.  Note that this is
//	unaware of Parameter objects as it is at a lower library
//	level.



class LinkExpression : public AbstractExpression  //## Inherits: <unnamed>%485116C90245
{

  public:



    class LinkExpressionError : public YellowAlert  //## Inherits: <unnamed>%485118DF024F
    {
      public:
          LinkExpressionError (const string& errMsg);

      protected:
      private:
      private: //## implementation
    };

  private:



    typedef enum {NUM, PARAM, OPER, LPAREN, RPAREN} ElementType;

  public:
    //	Each pair contains the [<modName>:]n string identifier
    //	and its index number in the tokenList.



    typedef std::list<std::pair<string,size_t> > ParamInfo;
      LinkExpression();

      LinkExpression(const LinkExpression &right);
      virtual ~LinkExpression();
      LinkExpression & operator=(const LinkExpression &right);

      //	This can only perform the first stage of initialization
      //	since it has no information about actually existing
      //	Parameter objects (this class can't even know what a
      //	Parameter object is).  Once the higher level client
      //	class has determined which parameter strings are valid,
      //	it must perform the second stage of initialization by
      //	calling resetParamInfo.
      virtual void init (const string& exprString, bool removeWhitespace = true);
      virtual LinkExpression* clone () const;
      Real evaluate (const RealArray& parVals) const;
      //	This performs the second stage of initialization and
      //	ultimately builds the postfix expression array.  The
      //	input array indicates which of the strings initially
      //	placed in m_parIDs are actually found to match up with
      //	existing Parameter objects.
      void resetParamInfo (const std::vector<bool>& isParFound);
      //	Each pair contains the [<modName>:]n string identifier
      //	and its index number in the tokenList.
      const LinkExpression::ParamInfo& parIDs () const;

  public:
    // Additional Public Declarations

  protected:
      void Swap (LinkExpression& right);

    // Additional Protected Declarations

  private:
      virtual const string& allValidChars () const;
      void convertToInfix ();
      void convertToPostfix ();
      void findParIDs ();
      void verifyWordExprs (const std::vector<size_t>& numberedTokens) const;
      void connectParsAndInts (const std::vector<size_t>& numberTokens);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      //	This allows some special chars since they may exist as
      //	part of a model name (though unlikely).
      static const string s_allValidChars;
      static std::map<string,int> s_precedenceMap;
      std::list<Real> m_numericalConsts;
      //	Originally to be filled in infix order, then rearranged
      //	to postfix before initialization is complete.
      std::vector<string> m_mathOperators;
      std::vector<LinkExpression::ElementType> m_postfixElems;
      std::vector<LinkExpression::ElementType> m_infixElems;
      LinkExpression::ParamInfo m_parIDs;
      //	Private bookkeeping array used to match up elements in
      //	the parIDs list with their corresponding entry in the
      //	numericalConsts list, if any (and which indicates the
      //	need for removal from one or the other).  If no match,
      //	the value will be set to npos.
      std::vector<size_t> m_parToNum;
      //	Private bookkeeping array, these are indices of tokens
      //	which are NOT detected to be parts of numerical
      //	constants as according to the AbstractExpression base
      //	class.  Therefore gaps in this sequence correspond to
      //	either genuine numerical constants OR parameter indices
      //	disguised as integers.
      std::vector<size_t> m_nonNumberTokens;

    // Additional Implementation Declarations

};

// Class LinkExpression::LinkExpressionError 

// Class LinkExpression 

inline const LinkExpression::ParamInfo& LinkExpression::parIDs () const
{
  return m_parIDs;
}


#endif
