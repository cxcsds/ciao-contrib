//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ABSTRACTEXPRESSION_H
#define ABSTRACTEXPRESSION_H 1
#include <xsTypes.h>

// Error
#include <XSUtil/Error/Error.h>

//	Abstract base class for Expression subclasses.  This
//	is meant to take care of only the most generic and
//	context-free parsing tasks (a category somewhat open to
//	interpretation).  For example it makes no distinction
//	between numbers and letters.  Both are grouped under the
//	WordExp token type.  It is also unaware that some words
//	may be mathematical functions, or that Xspec model
//	expressions may have more limiting rules.  One exception
//	to the generality is for "{}" chars, for which it uses
//	some knowledge of table model expression syntax.



class AbstractExpression 
{

  public:



    class AbstractExpressionError : public YellowAlert  //## Inherits: <unnamed>%47EAB3C8021A
    {
      public:
          AbstractExpressionError (const string& errMsg);

      protected:
      private:
      private: //## implementation
    };



    typedef enum {Null, WordExp, Lbrace, Rbrace, Plus, Minus, Star, Slash, Exp, Lcurl, Rcurl, Comma} Token;
    //	Token class that gives information of the type and
    //	location of the various elements in the Abstract
    //	Expression
    //
    //	type  - Token enum value
    //	location - location in the string
    //	tokenString - corresponding char symbol(s)
    //
    //	Thus if the string is:
    //	a(b+c*d)
    //	01234567
    //	the Token entry for the character c is (WordExp,4,"c")



    struct TokenType 
    {
          TokenType (AbstractExpression::Token type_, size_t loc, string charToken);

        // Data Members for Class Attributes
          AbstractExpression::Token type;
          size_t location;
          string tokenString;

      public:
      protected:
      private:
      private: //## implementation
    };
      virtual ~AbstractExpression();

      virtual void init (const string& exprString, bool removeWhitespace = true);
      virtual AbstractExpression* clone () const = 0;
      static const string& WS ();
      const string& exprString () const;
      const std::vector<AbstractExpression::TokenType>& tokenList () const;

  public:
    // Additional Public Declarations

  protected:
      AbstractExpression();

      AbstractExpression(const AbstractExpression &right);

      bool operator == (const AbstractExpression& right) const;
      void Swap (AbstractExpression& right);
      void setExprString (const string& exprString);
      void tokenList (const std::vector<AbstractExpression::TokenType>& value);
      //	OK, this does make a distinction between letters and
      //	numbers, but its results aren't stored in this base
      //	class.  This is a helper function for inheriting classes
      //	which need to recognize when an 'e' and a Minus token
      //	may be part of a number.   Its two vector arguments are
      //	filled in with 1: the indices of all Tokens which are
      //	NOT part of a number, and 2: the values of all the found
      //	numbers in left to right order.
      void findTheNumbers (std::vector<size_t>& remainingNonNumbers, std::vector<Real>& values) const;

    // Additional Protected Declarations

  private:
      AbstractExpression & operator=(const AbstractExpression &right);

      //	This function is non-static in order to make it virtual.
      virtual const string& allValidChars () const = 0;
      //	Should this be virtual?  A subclass may want to change
      //	the way symbols are categorized into Tokens.
      virtual AbstractExpression::Token determineToken (string::size_type* pPos) const;
      void standardizeExponentOp ();
      void checkBalance () const;
      void removeStarParenCombo ();
      //	Meant to be one of the very first parsing stages, this
      //	will throw if it finds any char not among those in all
      //	ValidChars
      void verifyAllChars () const;
      void makeTokenList ();
      void checkTokenSequence () const;
      void removeAllWhitespace ();
      //	This is called during init.  The default (base class)
      //	version does nothing.  Leave the definition of
      //	redundancy to inheriting classes, assuming they want to
      //	do anything.
      virtual void killRedundantParen (const string::size_type startPos, const string::size_type endPos);
      //	Needed by findTheNumbers, determine whether testStr
      //	consists only of digits, with an optional single decimal
      //	point at an arbitrary place.  If function returns false,
      //	*value will not be modified.
      static bool isNonExpFloat (const string& testStr, Real* value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_WS;
      string m_exprString;
      std::vector<AbstractExpression::TokenType> m_tokenList;

    // Additional Implementation Declarations
      static const bool s_legalTokenSequences[][11];
};

// Class AbstractExpression::AbstractExpressionError 

// Class AbstractExpression::TokenType 

// Class AbstractExpression 

inline void AbstractExpression::setExprString (const string& exprString)
{
  m_exprString = exprString;
}

inline void AbstractExpression::tokenList (const std::vector<AbstractExpression::TokenType>& value)
{
  m_tokenList = value;
}

inline const string& AbstractExpression::WS ()
{
  return s_WS;
}

inline const string& AbstractExpression::exprString () const
{
  return m_exprString;
}

inline const std::vector<AbstractExpression::TokenType>& AbstractExpression::tokenList () const
{
  return m_tokenList;
}


#endif
