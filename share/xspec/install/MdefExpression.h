//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MDEFEXPRESSION_H
#define MDEFEXPRESSION_H 1

// AbstractExpression
#include <XSUtil/Parse/AbstractExpression.h>
// Error
#include <XSUtil/Error/Error.h>
// Model functions
#include <XSFunctions/Utilities/funcType.h>

namespace Numerics {
   class MathOperator;
}


//	Concrete subclass of AbstractExpression.  This parses
//	and evaluates general mathematical expressions, used by
//	Xspec's mdefine command.



class MdefExpression : public AbstractExpression  //## Inherits: <unnamed>%47F12AF502CF
{

  public:

    class MdefExpressionError : public YellowAlert  //## Inherits: <unnamed>%47F298660166
    {
      public:
          MdefExpressionError (const string& errMsg);

      protected:
      private:
      private: //## implementation
    };

  private:



    typedef std::map<string,Numerics::MathOperator*> MathOpContainer;


    typedef enum {ENG, ENGC, NUM, PARAM, OPER, UFUNC, BFUNC, LPAREN, RPAREN, 
		  COMMA, XSMODEL, CONXSMODEL} ElementType;

  public:
      MdefExpression(const MdefExpression &right);
      MdefExpression (std::pair<Real,Real> eLimits, const string& compType);
      virtual ~MdefExpression();
      MdefExpression & operator=(const MdefExpression &right);

      virtual void init (const string& exprString, bool removeWhitespace = true);
      virtual MdefExpression* clone () const;
      static void clearOperatorsMap ();
      void evaluate (const RealArray& energies, const RealArray& parameters, RealArray& flux, RealArray& fluxErr) const;
      //	This will be the size of number of unique parameter
      //	names found in the expression.  The names will be stored
      //	in order of first left-to-right appearance, and should
      //	be the same order as the user prompts, and the order of
      //	the parameter values array sent to the evaluate function.
      const std::vector<string>& distinctParNames () const;
      //        This will be the size of the number of appearances of a
      //        parameter name in the expression. It returns the index in
      //        the AbstractExpression tokenList of each appearance of a
      //        parameter name.
      const std::vector<size_t>& paramTokenIndex () const;
      Real eLow () const;
      void eLow (Real value);
      Real eHigh () const;
      void eHigh (Real value);

    // Additional Public Declarations

  protected:
      void Swap (MdefExpression& right);

    // Additional Protected Declarations

  private:
      virtual const string& allValidChars () const;
      static void buildOperatorsMap ();
      void convertToInfix ();
      void fixConvolutionComponents();
      void convertToPostfix ();
      MdefExpression::ElementType classifyWords (const string& wordStr);
      void verifyInfix () const;
      //	Internal recursive function for validating commas in
      //	binary function calls.
      void verifyBFunc (size_t* idxElem) const;
      //        Internal function to check the correct number of arguments
      //        have been given for an xspec model function
      size_t verifyXSmodelFunc(const size_t idxElem, const size_t opPos) const;
      void convolveEvaluate (const RealArray& energies, const RealArray& parameters, RealArray& flux, RealArray& fluxErr) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_allValidChars;
      static MdefExpression::MathOpContainer s_operatorsMap;
      static std::map<string,int> s_precedenceMap;
      std::vector<string> m_distinctParNames;
      //	Maintains an index for each appearance of a PARAM in
      //	expression, in left-to-right order.  The index refers to
      //	which element of the user's input parameter array, and
      //	is equivalent to the ordering in the distinctParNames
      //	array.
      std::vector<size_t> m_paramsToGet;
      //        Maintains an index for each appearance of a PARAM of its
      //        position in the AbstractExpression tokenList.
      std::vector<size_t> m_paramTokenIndex;
      std::vector<Real> m_numericalConsts;
      //	This holds the ordered list of names of ALL operators, the built-in kind,
      //        function calls and xspec models, in the expression. It is originally
      //	filled in infix order, then re-arranged to postfix order
      //	before object construction is complete.
      std::vector<string> m_operators;

      //	This holds iterators to ALL mathematical operators, both
      //	the built-in kind and function calls.  It is originally
      //	filled in infix order, then re-arranged to postfix order
      //	before object construction is complete.
      //      std::vector<MdefExpression::MathOpContainer::const_iterator> m_mathOperators;
      //	This holds iterators to xspec models. It is originally
      //	filled in infix order, then re-arranged to postfix order
      //	before object construction is complete.
      //      std::vector<ModelFunctionMap::const_iterator> m_xspecModels;

      std::vector<MdefExpression::ElementType> m_postfixElems;
      std::vector<MdefExpression::ElementType> m_infixElems;
      Real m_eLow;
      Real m_eHigh;
      string m_compType;

    // Additional Implementation Declarations

};

// Class MdefExpression::MdefExpressionError 

// Class MdefExpression 

inline const std::vector<string>& MdefExpression::distinctParNames () const
{
  return m_distinctParNames;
}

inline const std::vector<size_t>& MdefExpression::paramTokenIndex () const
{
  return m_paramTokenIndex;
}

inline Real MdefExpression::eLow () const
{
  return m_eLow;
}

inline void MdefExpression::eLow (Real value)
{
  m_eLow = value;
}

inline Real MdefExpression::eHigh () const
{
  return m_eHigh;
}

inline void MdefExpression::eHigh (Real value)
{
  m_eHigh = value;
}


#endif
