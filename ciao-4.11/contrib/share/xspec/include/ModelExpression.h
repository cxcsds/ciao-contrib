// C++
#ifndef MODELEXPRESSION_H
#define MODELEXPRESSION_H 1

#include <XSUtil/Error/Error.h>
#include <XSUtil/Parse/AbstractExpression.h>
#include <algorithm>
#include <sstream>
#include <utility>
#include <cstdio>

#include <xsTypes.h>

class ModelExpressionError : public YellowAlert  
{
  public:
      ModelExpressionError (const string& errMsg);

  protected:
  private:
  private: 
};

//	Template subclass of AbstractExpression.  This parses
//	with syntax rules that are particular to Xspec Model
//	expressions.  The template parameter Usage is determined
//	by usage of model expression: stand-alone or as a
//	sub-expression in a tree.

template <class Usage>
class ModelExpression : public AbstractExpression, 
                        	public Usage  
{

  public:



    //	This struct repeats string info from the base class Token
    //	Type struct, to which it adds the sequence data member
    //	convenient for dealing with nested groups.  It also
    //	exists for historical reasons, taking the place of the
    //	former Expression::Word nested struct.

      struct ComponentSpec 
      {
            ComponentSpec (size_t tok_idx, int seq, const string& name);

          // Data Members for Class Attributes
            size_t tokIdx;
            //	This is a 1-based index to keep track of overall
            //	component order, even from a lower-level sub-Model
            //	Expression.  A $GROUP placeholder is assigned the
            //	sequence number -1.  Primarily needed for add/delcomp
            //	and editmod operations.
            int sequence;
            string content;

        public:
        protected:
        private:
        private: 
      };

      ModelExpression();

      ModelExpression(const ModelExpression< Usage > &right);
      virtual ~ModelExpression();
      ModelExpression< Usage > & operator=(const ModelExpression< Usage > &right);

      virtual ModelExpression<Usage>* clone () const;
      bool operator == (const ModelExpression<Usage>& right) const;
      virtual void init (const string& exprString, bool removeWhitespace = true);
      void setComponentString (const string& str, size_t index);
      const string& getComponentString (size_t index) const;
      //	This returns the equivalent to the 1-based Component
      //	object index number.  It refers to the ComponentSpec's
      //	order in the FULL  ModelExpression even if this happens
      //	to be a sub expression.  The input index refers to the
      //	ComponentSpec's order in THIS ModelExpression.
      int getComponentSequence (size_t index) const;
      size_t getComponentLocation(size_t index) const;
      void replaceWordBySequence (int sequence, const string& newWord);
      //        Neither insertWordBySequence or deleteWordBySequence updates
      //        sequence numbers (since sub-expressions don't have access to the
      //        full tree).  Therefore one should assume sequence numbers are
      //        invalid immediately following one of these calls.  A new
      //        expression tree must be created (from a stand-alone expression)
      //        to restore proper sequence numbers.
      void insertWordBySequence (int index, const string& newWord, char op);
      void deleteWordBySequence (int seq);
      const std::vector<typename ModelExpression<Usage>::ComponentSpec>& compSpecs () const;
      //	Returns the tokenList array index for the operators
      //	immediately preceeding and following the component
      //	specified by the location.  This would be a relatively
      //	trivial function except that table components can be
      //	spread over many tokens.  If no operator, returns npos.
      std::pair<size_t,size_t> findPreAndPostOp (size_t location) const;

      static string makeGroupString (int position);
      static string starToParen (const string& input, size_t location);
      //	This ASSUMES the two input Expressions DO NOT differ in
      //	size by more than 1 word.  If they do not have the same
      //	number of words, the return values will always refer to
      //	the word positions in the larger.  Consecutively
      //	repeated words indicate a possible ambiguity, and so the
      //	return values will be their start and end positions
      //	(INCLUSIVE).  If the values are the same there is no
      //	ambiguity.  If no differences found, the return value is
      //	(0,0).
      static std::pair<int,int> findWordDifference (const ModelExpression<Usage>& oldExp, const ModelExpression<Usage>& newExp);
      //	Intended to work in tandem with findWordDifference.
      //	This performs a test to determine if an editmod
      //	operation makes one and only one component change.  No
      //	other structural and/or arithmetic operator changes will
      //	pass. The compIdx refers to the component which will be
      //	deleted from the larger expression in order to make the
      //	comparison.  If both expressions are of equal size, it
      //	will be deleted from both.
      static bool testEditOperation (const ModelExpression<Usage>& oldExp, const ModelExpression<Usage>& newExp, const int compIdx);
      // ASSUMES "pos" is the location of a '(' in inString.  
      // Returns the location of its matching ')' OR 
      // string::npos if no match is found.
      // If plusEnclosed is non-zero, its value will be set to 'true' if any '+' is
      // found at any depth between the parentheses.
      static string::size_type findMatchingRightParen (const string& inString, string::size_type pos, bool* plusEnclosed = 0);
      // Return the positions of all plus signs found in inString 
      // which are at the top level.  Any nested pluses are ignored. 
      static std::vector<string::size_type> findSameLevelPlus(const string& inString);
      static string flagNonGroupParens (const string& inString);
      static string restoreNonGroupParens (const string& inString);


  public:
    // Additional Public Declarations

  protected:
      void Swap (ModelExpression<Usage>& right);
      // The idea here is that only a Usage base class which also declares a
      // (perhaps empty) setComponentSequence function will be able to use
      // this, via runtime polymorphism.  Either way, this should remain
      // inaccessible to the rest of XSPEC.
      virtual void setComponentSequence(int seq, int index);

    // Additional Protected Declarations

  private:
      virtual const string& allValidChars () const;
      //	This is called during init.  The default (base class)
      //	version does nothing.  Leave the definition of
      //	redundancy to inheriting classes, assuming they want to
      //	do anything.
      virtual void killRedundantParen (const string::size_type startPos, const string::size_type endPos);
      char findPreParenType (const string::size_type leftParenPos) const;
      char findPostParenType (const string::size_type rightParenPos) const;
      int findPrecedenceLevel (string::size_type startPos, string::size_type endPos) const;
      //	Perform syntax checking beyond that in Abstract
      //	Expression's init function, and which is specific to
      //	model expressions.
      void modelSyntaxCheck () const;
      void createComponentSpecs ();
      void updateComponentStringChange(size_t iComp);

      static int determinePrecedence (char typeCode, bool isPre);
      static bool isArithmeticOperator (const Token& token);
      static bool multiplyingCGroups(const string& exprStr);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_allValidChars;
      std::vector<typename ModelExpression<Usage>::ComponentSpec> m_compSpecs;

    // Additional Implementation Declarations

};


// Class ModelExpression::ComponentSpec 

template <class Usage>
ModelExpression< Usage >::ComponentSpec::ComponentSpec (size_t tok_idx, int seq, const string& name)
   :tokIdx(tok_idx),
   sequence(seq),
   content(name)   
{
}

// Parameterized Class ModelExpression 

template <class Usage>
ModelExpression<Usage>::ModelExpression()
   :AbstractExpression(),
    Usage(),
   m_compSpecs()
{
}

template <class Usage>
ModelExpression<Usage>::ModelExpression(const ModelExpression<Usage> &right)
  : AbstractExpression(right),
    Usage(right), 
    m_compSpecs(right.m_compSpecs)
{
}


template <class Usage>
ModelExpression<Usage>::~ModelExpression()
{
}


template <class Usage>
ModelExpression<Usage> & ModelExpression<Usage>::operator=(const ModelExpression<Usage> &right)
{
   if (this != &right)
   {
      ModelExpression<Usage> tmp(right);
      Swap(tmp);
   }
   return *this;
}


template <class Usage>
ModelExpression<Usage>* ModelExpression<Usage>::clone () const
{
   return new ModelExpression<Usage>(*this);
}

template <class Usage>
bool ModelExpression<Usage>::operator == (const ModelExpression<Usage>& right) const
{
   // Define equality purely by comparison of tokens.  If this is a
   // sub-expression, it's tree position info is irrelevant.
   return AbstractExpression::operator==(right);
}

template <class Usage>
void ModelExpression<Usage>::init (const string& exprString, bool removeWhitespace)
{
   AbstractExpression::init(exprString,removeWhitespace);

   m_compSpecs.clear();
   modelSyntaxCheck();
   createComponentSpecs();

   Usage::contextSpecificInit(this);
}

template <class Usage>
void ModelExpression<Usage>::setComponentString (const string& str, size_t index)
{
   if (index < m_compSpecs.size())
   {
      m_compSpecs[index].content = str;
      updateComponentStringChange(index);
   }
   else
      throw RedAlert("Programmer error: ModelExpression::setComponentString");
}

template <class Usage>
const string& ModelExpression<Usage>::getComponentString (size_t index) const
{
   if (index >= m_compSpecs.size())
      throw RedAlert("Array access error: ModelExpression::getComponentString");

   return m_compSpecs[index].content;
}

template <class Usage>
int ModelExpression<Usage>::getComponentSequence (size_t index) const
{
   if (index >= m_compSpecs.size())
      throw RedAlert("Array access error: ModelExpression::getComponentSequence");

   return m_compSpecs[index].sequence;
}

template <class Usage>
size_t ModelExpression<Usage>::getComponentLocation(size_t index) const
{
   if (index >= m_compSpecs.size())
      throw RedAlert("Array access error: ModelExpression::getComponentLocation");

   return tokenList()[m_compSpecs[index].tokIdx].location;
}

template <class Usage>
void ModelExpression<Usage>::replaceWordBySequence (int sequence, const string& newWord)
{
   // ONLY replaces a word, makes no changes to operators on either side.
   bool isFound = false;
   typename std::vector<ComponentSpec>::iterator itWord = m_compSpecs.begin();
   typename std::vector<ComponentSpec>::iterator itWordEnd = m_compSpecs.end();
   size_t iComp=0;
   while (itWord != itWordEnd && !isFound)
   {
      if (itWord->sequence == sequence)
         isFound = true;
      else
         ++itWord, ++iComp;
   }
   if (!isFound)
   {
      std::ostringstream oss;
      oss << "Error searching for sequence number " << sequence 
         << " in ModelExpression::replaceWordBySequence\n";
      throw RedAlert(oss.str());
   }
   itWord->content = newWord;
   updateComponentStringChange(iComp);
}

template <class Usage>
void ModelExpression<Usage>::insertWordBySequence (int index, const string& newWord, char op)
{
  // Find the insert point. By the time this is called we must know that the
  // word given by index lies in this expression.
  typename std::vector<ComponentSpec>::const_iterator itW = m_compSpecs.begin();
  typename std::vector<ComponentSpec>::const_iterator itWEnd = m_compSpecs.end();
  while ( itW != itWEnd && itW->sequence != index ) ++itW;
  string  newInsert(newWord);

  string opStr("   ");
  opStr[1] = op;
  bool previousOperationWasCombine (false);
  size_t insertLocation=0;
  // insertion before the end
  if (itW != itWEnd )  
  {
     size_t idx = itW->tokIdx;
     insertLocation = tokenList()[idx].location;
     while ((idx != 0) && !previousOperationWasCombine )
     {
        --idx;       
        const TokenType& tok = tokenList()[idx];
        if ( tok.type == Plus || 
             tok.type == Lbrace || 
             tok.type == Rbrace ) break;
        previousOperationWasCombine = ( tok.type == Star);
     }
     newInsert  = newWord + opStr;
  }
  // insertion at the end.
  else
  {
     insertLocation = exprString().size();       
     newInsert  = opStr + newWord;       
  }
  string newExprStr(exprString());
  switch ( op )
  {
     case '+':
        {
           // case where we have something like A*B -> A(<new>+B)
           if ( previousOperationWasCombine )
           {
              newExprStr = starToParen(exprString(),insertLocation);
           }
           newExprStr.insert(insertLocation,newInsert);
           init(newExprStr,false); 
           // The init call rebuilds the m_compSpecs vector, which is rather
           // important.  
           break;
        }
     default:
        {        
           newExprStr.insert(insertLocation,newInsert);
           init(newExprStr,false);       
           break;
        }       

  }
}

template <class Usage>
void ModelExpression<Usage>::deleteWordBySequence (int seq)
{
   // Should already have checked that component with seq number is in 
   // this expression.  This will reconstruct the expression string with
   // the appropriate component removed (and a neighboring operator if
   // necessary).  The new string will be sent back to the init function to
   // reconstruct the rest of the data members.  No assumptions regarding
   // whitespace.
   typename std::vector<ComponentSpec>::const_iterator itComp = m_compSpecs.begin();
   typename std::vector<ComponentSpec>::const_iterator itCompEnd = m_compSpecs.end();
   bool isFound = false;
   while (!isFound && itComp != itCompEnd)
   {
      if (itComp->sequence == seq)
         isFound = true;
      else
         ++itComp;
   }
   if (!isFound)
      throw RedAlert("Component not found in ModelExpression::deleteWordBySequence");

   // Simple case of deletion of last remaining component. 
   if (m_compSpecs.size() == 1)
   {
      init(string(""),false);
   } 
   else
   {  

      const ComponentSpec& doomedComp = *itComp;

      const std::vector<TokenType>& tokens = tokenList();  
      std::pair<size_t,size_t> ops(findPreAndPostOp(tokens[doomedComp.tokIdx].location));
      Token prevType = (ops.first == string::npos) ? 
                   Null : tokens[ops.first].type;
      Token nextType = (ops.second == string::npos) ? 
                   Null : tokens[ops.second].type;
      string::size_type startSkip=0;
      string::size_type nSkip=0;
      if ( ((prevType == Plus || prevType == Star) && 
            (nextType == Null || nextType == Rbrace || prevType == nextType)) ||
            (prevType == Star && nextType == Plus))
      {
         // Cases where the previous operator MUST be removed:
         //  [+|*]d, [+|*]d), a*d+b.  Also handles cases where EITHER previous 
         // OR next must be removed: a+d+b, a*d*c.
         startSkip = tokens[ops.first].location;
         nSkip = (nextType == Null) ? string::npos : 
                   tokens[ops.second].location - startSkip;
      }
      else if (((prevType == Null || prevType == Lbrace) && 
               (nextType == Plus || nextType == Star)) ||
               (prevType == Plus && nextType == Star))
      {
         // Cases where the next operator MUST be removed:
         // d[+|*], (d[+|*], a+d*b. 
         startSkip = tokens[doomedComp.tokIdx].location;
         // A plus or star can't be the last token, so it's safe
         // to go one beyond.
         nSkip = tokens[ops.second+1].location - startSkip;
      }
      else
      {
         // All other cases, just remove the component itself.
         startSkip = tokens[doomedComp.tokIdx].location;
         nSkip = (nextType == Null) ? string::npos : 
                   tokens[ops.second].location - startSkip;
      }

      string newExprStr(exprString().substr(0,startSkip));
      if (nSkip != string::npos)
         newExprStr += exprString().substr(startSkip+nSkip);
      init(newExprStr,false);
   } // end if not deleting the last component.
}

template <class Usage>
inline const std::vector<typename ModelExpression<Usage>::ComponentSpec>& ModelExpression<Usage>::compSpecs () const
{
  return m_compSpecs;
}

template <class Usage>
std::pair<size_t,size_t> ModelExpression<Usage>::findPreAndPostOp (size_t location) const
{
   // Unlike the findPre|PostParenType functions, this can make use of the
   // tokenList.  It is useful when removing a component from the expression.
   // ASSUME location is the position of a component. 
   bool isFound = false; 
   size_t preIdx = string::npos;
   size_t curIdx = 0;
   std::vector<TokenType>::const_iterator itTok = tokenList().begin();
   std::vector<TokenType>::const_iterator itTokEnd = tokenList().end();
   while (!isFound && itTok != itTokEnd)
   {
      if (itTok->location == location)
         isFound = true;
      else
         preIdx = curIdx;
      ++curIdx;
      ++itTok;
   } 
   if (!isFound)
      throw RedAlert("Token not found in ModelExpression::findPreAndPostOp");
   size_t postIdx = string::npos;
   if (itTok != itTokEnd)
   {
      if (itTok->type == Lcurl)
      {
         // There MUST also be an Rcurl or we couldn't get in here.
         while (itTok != itTokEnd && itTok->type != Rcurl)
            ++itTok, ++curIdx;
         if (itTok == itTokEnd)
            throw RedAlert("Missing '}' in ModelExpression::findPreAndPostOp");
         ++itTok, ++curIdx;
         if (itTok != itTokEnd)
             postIdx = curIdx;
      }
      else
         postIdx = curIdx;
   }

   return std::pair<size_t,size_t>(preIdx,postIdx);
}

template <class Usage>
string ModelExpression<Usage>::makeGroupString (int position)
{
   const char* flag = "$GROUP";
   // This fixes upper limit of 99 nested groups, which seems
   // high enough for any conceivable usage.
   const int nDigits = 2;
   if (position < 0)
   {
      throw RedAlert("Negitive position in ModelExpression<Usage>::makeGroupString");
   }
   if (static_cast<double>(position) >= pow(10.0,nDigits))
   {
      string msg("Number of nested expressions exceeds current implementation's limit.");
      throw ModelExpressionError(msg);
   }
   char* rString = new char[7 + nDigits];
   sprintf(rString, "%s%.2d", flag, position);
   string groupString(rString);
   delete [] rString;
   return groupString;
}

template <class Usage>
string ModelExpression<Usage>::starToParen (const string& input, size_t location)
{
  // ASSUMES that it is dealing with an input
  // string that has already been fully verified and used
  // during the construction of a model.  Furthermore, it assumes 
  // that 'location' points to the start of an AddComponent string.
  // It only places parentheses around that particular AddComponent,
  // and then only as necessary.  
  const string delim(")(+*/-");
  string output = input;
  string::size_type acLoc = location;
  string::size_type rdLoc = input.find_first_of(delim, acLoc);
  string::size_type ldLoc = input.find_last_of(delim, acLoc);

  // The rule to follow:  if a '*' is the first delimiter to the
  // left OR right of addComp, it is removed and replaced by
  // a set of parentheses immediately around addComp

  if(ldLoc != string::npos || rdLoc != string::npos) {
      if(ldLoc != string::npos && output[ldLoc] == '*')
	  output[ldLoc] = '(';
      else
	  output.insert(acLoc, 1, '(');

      if(rdLoc != string::npos)
	  if(output[ldLoc] == '*')
	      output[rdLoc] = ')';
	  else
	      output.insert(rdLoc, 1, ')');
      else
	  output += ')';
  }
  return output;
}

template <class Usage>
std::pair<int,int> ModelExpression<Usage>::findWordDifference (const ModelExpression<Usage>& oldExp, const ModelExpression<Usage>& newExp)
{
   std::pair<int,int> diffIndices(0,0);
   // This ASSUMES the old and new nWords DO NOT differ by more than 1,
   // else it wouldn't get in here.

   // Return values should refer to the 1-based word position of the
   // first detected difference.  If no ambiguity, the 2 values will be
   // the same.  Else, they will be the start and end pos (inclusive)
   // of consecutive repeated words.  If two expressions are of 
   // different size, values refer to positions in the larger.  If no 
   // difference found return (0,0).  
   const int nOldWords = static_cast<int>(oldExp.m_compSpecs.size());
   const int nNewWords = static_cast<int>(newExp.m_compSpecs.size());
   const std::vector<ComponentSpec>& larger = (nOldWords >= nNewWords) ?
                oldExp.compSpecs() : newExp.compSpecs();
   const std::vector<ComponentSpec>& smaller = (nOldWords >= nNewWords) ?
                newExp.compSpecs() : oldExp.compSpecs();
   const size_t nWords = smaller.size();

   ComponentSpec prevWord(-1,-1,string(""));
   size_t start=0, stop=0;
   bool diffFound = false;
   for (size_t i=0; !diffFound && i<nWords; ++i)
   {
      const ComponentSpec& currWord = larger[i];
      if (currWord.content != prevWord.content)
      {
         start = i+1;  // 1-based
         prevWord = currWord;
      }
      stop = i+1;
      if (currWord.content != smaller[i].content)
      {
         diffFound = true;
      }
   }

   if (!diffFound)
   {
      // We've reached the end of the smaller array without
      // finding a difference.
      // If any additional word in larger, that becomes
      // the difference (but it still could have repeated
      // preceeding words of which we'll need to keep track).
      if (larger.size() > nWords)
      {
         // Remember, we're ASSUMING larger only has 1 more element.
         if (larger[nWords].content != prevWord.content)
            start = nWords+1;
         stop = nWords+1;
         diffFound = true;   
      }
   }
   else
   {
      // A difference was found, keep checking in larger for trailing 
      // repeated words.
      for (size_t i=stop; i<larger.size(); ++i)
      {
         if (larger[i].content == prevWord.content)
            stop = i+1;
         else
            break;
      }
   }

   if (diffFound)
   {
      diffIndices.first = static_cast<int>(start);
      diffIndices.second = static_cast<int>(stop);
   }
   return diffIndices;
}

template <class Usage>
bool ModelExpression<Usage>::testEditOperation (const ModelExpression<Usage>& oldExp, const ModelExpression<Usage>& newExp, const int compIdx)
{
   // ASSUME sizeDiff has already been verified to be -1, 0, or +1
   // by this point.

   ModelExpression<Usage> oldExpression(oldExp);
   ModelExpression<Usage> newExpression(newExp);

   const int sizeDiff = static_cast<int>(newExpression.m_compSpecs.size())
                         - static_cast<int>(oldExpression.m_compSpecs.size());
   switch (sizeDiff)
   {
      case -1: 
         oldExpression.deleteWordBySequence(compIdx);
         break;
      case 0:
         oldExpression.deleteWordBySequence(compIdx);
         newExpression.deleteWordBySequence(compIdx);
         break;
      case 1:
         newExpression.deleteWordBySequence(compIdx);
         break;
      default:
         throw RedAlert("Edit expression size diff not equal to -1, 0, or 1.");         
   }
   return (oldExpression == newExpression);
}

template <class Usage>
string::size_type ModelExpression<Usage>::findMatchingRightParen (const string& inString, string::size_type pos, bool* plusEnclosed)
{
     // ASSUMES "pos" is the location of a '(' in inString.  
     // Returns the location of its matching ')' OR 
     // string::npos if no match is found.
     // If plusEnclosed pointer is non-zero, will set to
     // 'true' if a '+' is found ANYWHERE between the parentheses.
    int count = 0;
    const string::size_type len = inString.length();
    bool plusFound = false;
    string::size_type i = pos;

    do {
        const char c = inString[i];
	switch(c) 
	{
	case '(':
	    ++count;
	    break;
	case ')':
	    --count;
	    break;
	}
        if (c == '+')
           plusFound = true;
    } while(count && ++i < len);
    if (i == len)
       i = string::npos;

    if (plusEnclosed)
       *plusEnclosed = plusFound;
    return i;
}

template <class Usage>
void ModelExpression<Usage>::Swap (ModelExpression<Usage>& right)
{
   AbstractExpression::Swap(right);
   Usage::Swap(right);
   std::swap(m_compSpecs,right.m_compSpecs);
}

template <class Usage>
void ModelExpression<Usage>::setComponentSequence(int seq, int index)
{
   if (index >= static_cast<int>(m_compSpecs.size()))
      throw RedAlert("Array access error: ModelExpression::setComponentSequence");

   m_compSpecs[index].sequence = seq;
}

template <class Usage>
const string& ModelExpression<Usage>::allValidChars () const
{
   return s_allValidChars;
}

template <class Usage>
void ModelExpression<Usage>::killRedundantParen (const string::size_type startPos, const string::size_type endPos)
{
   // ASSUMES that parentheses balance has already been checked
   //  in range determined by startPos, endPos inclusive,
   //  that 0 <= startPos, endPos < exprString.length(),
   //  and that startPos <= endPos. If redundancy is found parentheses 
   //  will be replaced with blanks.

   // Definition of redundancy: No Pre or post components applied to 
   // parentheses at its own depth level, OR only one component within
   // parentheses.

   // If redundancy is found parentheses will be replaced with
   // blanks, UNLESS there is no non-nested '+' or '-' inside
   // and pre or post operator is a word.  In this case a '*' will
   // be inserted pre or post.

   // This will find any outer pairs of parentheses starting from 
   // startPos, and determine if they are redundant.  Any nested
   // parentheses within these will be handled with a recursive call.
   string newExprStr(exprString());
   string::size_type leftPos = newExprStr.find('(',startPos);
   while (leftPos != string::npos && leftPos < endPos)
   {
      string::size_type rightPos = findMatchingRightParen(newExprStr,leftPos);
      // rightPos must be valid and <= endPos based on our input 
      // assumption of balanced parentheses.
      char preType = findPreParenType(leftPos);
      char postType = findPostParenType(rightPos);
      killRedundantParen(leftPos+1, rightPos-1);
      newExprStr = exprString();

      // OK, we now know our pre and post operator types, and we
      // know that any nested parentheses have already been 
      // converted to their standardized form. 
      if (findPrecedenceLevel(leftPos+1,rightPos-1) == 3)
      {
         // This is the case of only one component between parentheses.
         newExprStr[leftPos] = (preType == 'w') ? '*' : ' ';
         newExprStr[rightPos] = (postType == 'w') ? '*' : ' ';
      } 
      else if (preType != 'w' && preType != ')' &&
                postType != 'w' && postType != '(')
      {
        newExprStr[leftPos] = ' ';
        newExprStr[rightPos] = ' '; 
      }
      leftPos = newExprStr.find('(', rightPos+1);
      setExprString(newExprStr);
   }
}

template <class Usage>
char ModelExpression<Usage>::findPreParenType (const string::size_type leftParenPos) const
{
  // Parsing helper function used early in ModelExpression
  // initialization, and therefore can't make use of Token object
  // information.
  // ASSUMES ONLY that leftParenPos is the location of a '(' in
  // m_parseString.
  const string WS(" \t");
  const string allowedOPS("*/+-()");
  char preType = ' ';
  if (leftParenPos > 0)
  {
     string::size_type prePos = 
        exprString().find_last_not_of(WS, leftParenPos - 1);
     if (prePos != string::npos)
     {
        preType = exprString()[prePos];
        // If not one of the allowed ops, assume it is 
        // the last character in a word.
        if (allowedOPS.find(preType) == string::npos)
           preType = 'w';
     }
  }
  return preType;
}

template <class Usage>
char ModelExpression<Usage>::findPostParenType (const string::size_type rightParenPos) const
{
  // Parsing helper function used very early on in ModelExpression
  // initialization, and therefore can't make use of Token object
  // information.
  // ASSUMES ONLY that rightParenPos is the location of a ')' in
  // m_parseString.
  char postType = ' ';
  const string WS(" \t");
  const string allowedOPS("*/+-()");
  if (rightParenPos < exprString().length()-1)
  {
     string::size_type postPos = 
        exprString().find_first_not_of(WS, rightParenPos + 1);
     if (postPos != string::npos)
     {
        postType = exprString()[postPos];
        // If not one of the allowed ops, assume it is 
        // the first character in a word.
        if (allowedOPS.find(postType) == string::npos)
           postType = 'w';
     }
  }
  return postType;
}

template <class Usage>
int ModelExpression<Usage>::findPrecedenceLevel (string::size_type startPos, string::size_type endPos) const
{
   // Private helper function used during initialization routines.
   // ASSUMES parentheses balance between startPos and endPos, and that
   // startPos and endPos represent the entire range between a pair of
   // outer parentheses.  Also assumes any nested parentheses have already
   // been checked for redundancy.

   // Looks for the lowest precedence operator between startPos and endPos
   // inclusive, ignoring operators inside nested paretheses.  (It assumes 
   // startPos and endPos are the entire range within a pair of outer 
   // parentheses.)  In this context, we're determining if an operator makes
   // its enclosing parentheses "necessary".  The lower the operator precedence,
   // the more necessary the parentheses.  Therefore, if only a word ( or  
   // consecutive words -- table models) exists, give it "very high" precedence
   // since it's not making the parentheses necessary.

   // Start with a default higher than anything determinePrecedence gives out.
   int level = 3;
   bool nestFound = false;
   string nonNestedParts;
   while (startPos != string::npos && startPos <= endPos) 
   {
      string::size_type nestedLeft = exprString().find('(', startPos);
      string::size_type nestedRight = string::npos;
      if (nestedLeft < endPos)
      {
         nestFound = true;
         nestedRight = findMatchingRightParen(exprString(), nestedLeft);
         // begin next search 1 after ')'
         ++nestedRight;
      }
      string::size_type len = std::min(nestedLeft, endPos+1) - startPos;
      nonNestedParts += exprString().substr(startPos, len);
      startPos = nestedRight;
   }
   if (nonNestedParts.find_first_of("+-") != string::npos)
      level = 1;
   else if (nestFound || nonNestedParts.find_first_of("*/") != string::npos)
      level = 2;
   return level;
}

template <class Usage>
void ModelExpression<Usage>::modelSyntaxCheck () const
{
   // Checks additional rules applicable only to model expressions:
   // 1.  No '-' or '/' exists anywhere except between curly brackets
   //     (where they could be part of a file path and name).
   // 2.  Only words, '-', and '/' can exist inside curly brackets.
   // 3.  Don't allow ")(" if both groups contain a '+' inside,
   //     unless a  '+' exists somewhere in between the parens.
   //     This is to prevent multiplication of Component groups. 
   //
   // By this point we know that parentheses and curly brackets are
   // properly balanced, and that curly brackets are not nested.

   const std::vector<TokenType>& tokens = tokenList();
   bool betweenCurls = false;
   for (size_t i=0; i<tokens.size(); ++i)
   {
      const Token type = tokens[i].type;
      if (betweenCurls && (type != WordExp && type != Minus && type != Slash
                && type != Rcurl))
      {
         throw ModelExpressionError("Invalid table model file specifier");
      }
      switch (type)
      {
         case Lcurl:
            betweenCurls = true;
            break;
         case Rcurl:
            betweenCurls = false;
            break;
         case Slash:
            if (!betweenCurls)
            {
               string errMsg("No '/' operator allowed in model expressions");
               throw ModelExpressionError(errMsg);
            }
            break;
         case Minus:
            if (!betweenCurls)
            {
               string errMsg("No '-' operator allowed in model expressions");
               throw ModelExpressionError(errMsg);
            }
            break;
         default:
            break;
      }
   }

   if (multiplyingCGroups(exprString()))
   {
      string errMsg("Cannot multiply add component groups.");
      throw ModelExpressionError(errMsg);
   }
}

template <class Usage>
void ModelExpression<Usage>::createComponentSpecs ()
{
   // The big challenge here is recognizing and assembling table model 
   // component specs.  These are comprised of an undetermined amount of 
   // WordExp,/,-,{, and } tokens. Proper ordering of tokens should already 
   // have been checked.

   // If Usage is a tree member, the expression will be re-sequenced
   // once all tree sub-expressions are built.  At this early stage
   // it can't know its place in the tree.

   const std::vector<TokenType>& tokens = tokenList();
   const size_t nTok = tokens.size();
   size_t seqCount = 1;
   for (size_t i=0; i<nTok; ++i)
   {
      const TokenType& tok = tokens[i];
      if (tok.type == WordExp)
      {
         if (i < nTok-1 && tokens[i+1].type == Lcurl)
         {
            string tableComp(tok.tokenString);
            size_t startTok = i;
            tableComp += "{";
            i+=2;
            // Unbalanced or nested curly brackets would already have
            // been caught.  
            while (i<nTok && tokens[i].type != Rcurl)
            {
               tableComp += tokens[i].tokenString;
               ++i;
            }
            tableComp += "}";
            m_compSpecs.push_back(ComponentSpec(startTok,seqCount,tableComp));
            ++seqCount;
         }
         else
         {
            // The simple case where WordExp is 1-to-1 with ComponentSpec.
            m_compSpecs.push_back(ComponentSpec(i,seqCount,tok.tokenString));
            ++seqCount;
         }
      }
   }
}

template <class Usage>
void ModelExpression<Usage>::updateComponentStringChange(size_t iComp)
{
   // This ASSUMES that the only change made was to a component name at index
   // in a previously validated expression.  Therefore, it only need update
   // the tokenList, exprString, and m_compSpecs.tokIdx.  The size of
   // m_compSpecs will stay the same, but not necessarily tokenList if
   // we're dealing with a table model (either before or after).  
   // Sequence numbers will stay the same.
  string SPACE(" ");
  const ComponentSpec& changedComp = m_compSpecs[iComp];
  const size_t nOrigToks = tokenList().size();
  size_t iPostTok = findPreAndPostOp(tokenList()[changedComp.tokIdx].location).second;
  const size_t origNToksForComp = (iPostTok == string::npos) ? 
                  nOrigToks - changedComp.tokIdx : iPostTok - changedComp.tokIdx;
  size_t iTok=0;
  string updatedExpr;
  while (iTok < changedComp.tokIdx)
  {
     if (tokenList()[iTok].type == Plus)
        updatedExpr += SPACE;
     updatedExpr += tokenList()[iTok].tokenString;
     if (tokenList()[iTok].type == Plus)
        updatedExpr += SPACE;
     ++iTok;
  }
  updatedExpr += changedComp.content;
  iTok = iPostTok;
  while (iTok < nOrigToks)
  {
     if (tokenList()[iTok].type == Plus)
        updatedExpr += SPACE;
     updatedExpr += tokenList()[iTok].tokenString;
     if (tokenList()[iTok].type == Plus)
        updatedExpr += SPACE;
     ++iTok;
  }

  // This modifies the token list.
  AbstractExpression::init(updatedExpr,false);
  const size_t nNewToks = tokenList().size();
  // At this point all CompSpec.tokIdx members after changedComp may be invalid,
  // but that doesn't matter to findPreAndPostOp.
  iPostTok = findPreAndPostOp(tokenList()[changedComp.tokIdx].location).second;
  const size_t newNToksForComp = (iPostTok == string::npos) ? 
                  nNewToks - changedComp.tokIdx : iPostTok - changedComp.tokIdx;
  int diff = static_cast<int>(newNToksForComp - origNToksForComp);
  if (diff != 0)
  {
     ++iComp;
     while (iComp < m_compSpecs.size())
     {
        m_compSpecs[iComp].tokIdx += diff;
     }
  }

  Usage::contextSpecificInit(this);
}

template <class Usage>
int ModelExpression<Usage>::determinePrecedence (char typeCode, bool isPre)
{
   // Private function used during initialization routines.
   int level = 0;  
   switch (typeCode)
   {
      case 'w':
         // When pre or post operator is a word, treat as if '*'.
         level = 2;
         break;
      case '*':
      case '/':
         level = 2;
         break;
      case '(':
         level = isPre ? 0 : 2;
         break;
      case ')':
         level = isPre ? 2 : 0;
         break;
      case '+':
      case '-':
         level = 1;
         break;
      case ' ':
         level = 0;
         break;   
      default: 
         break;
   }
   return level;   
}

template <class Usage>
bool ModelExpression<Usage>::isArithmeticOperator (const Token& token)
{
   return ( token == Plus || token == Minus || token == Star || token == Slash );
}

template <class Usage>
bool ModelExpression<Usage>::multiplyingCGroups(const string& exprStr)
{
   // This is a recursive function
   bool isMultViolation = false;
   bool plusParenFound = false;
   bool plusSeparator = false;
   string::size_type curPos = exprStr.find('(');
   while (curPos != string::npos)
   {
      bool isPlus = false;
      string::size_type rPos = findMatchingRightParen(exprStr,curPos,&isPlus);
      if (isPlus)
      {
         if (plusParenFound && !plusSeparator)
         {
            isMultViolation = true;
            break;
         }
         plusParenFound = true;
         // There may be all sorts of nests.  Handle recursively.
         if(multiplyingCGroups(exprStr.substr(curPos+1,rPos-curPos-1)))
         {
            isMultViolation = true;
            break;
         }
      }
      string::size_type nextPlus = exprStr.find('+',rPos);
      string::size_type nextLpar = exprStr.find('(',rPos);
      plusSeparator = (nextPlus < nextLpar);
      curPos = nextLpar;

   }

   return isMultViolation;
}

template <class Usage>
std::vector<string::size_type> ModelExpression<Usage>::findSameLevelPlus(const string& inString)
{
   std::vector<string::size_type> pluses;
   string::size_type curPos = 0;
   const string::size_type len = inString.length();
   while (curPos != string::npos && curPos < len)
   {
      if (inString[curPos] == '(')
         curPos = findMatchingRightParen(inString,curPos);
      else if (inString[curPos] == '+')
         pluses.push_back(curPos);
      ++curPos;         
   }

   return pluses;
}

template <class Usage>
string ModelExpression<Usage>::flagNonGroupParens (const string& inString)
{
   // Find non-group parentheses (ie. not enclosing a non-nested '+'),
   // and replace left and right with '@' and '!' respectively.  This is
   // to simplify the findNests and set parLocs algorithms.
   string outString(inString);
   string::size_type curPos = outString.find('(');
   // Find each '(' in left-to-right order, non-recursive.
   while (curPos != string::npos)
   {
      bool isAnyPlus = false;
      string::size_type rPos = findMatchingRightParen(outString,
                                curPos, &isAnyPlus);
      if (isAnyPlus)
      {
         // isAnyPlus could be a nested plus, so we need to check further.
         if (rPos > curPos+1)
         {
            if (!findSameLevelPlus(outString.substr(curPos+1,
                        rPos-curPos-1)).size())
            {
               outString[curPos] = '@';
               outString[rPos] = '!';
            }
         }
         else if (rPos == curPos+1)
         {
            // Case of empty ().  If this should be allowed one day,
            // certainly don't want to mistake it for a component group.
            outString[curPos] = '@';
            outString[rPos] = '!';
         }         
      }
      else
      {
         outString[curPos] = '@';
         outString[rPos] = '!';
      }
      curPos = outString.find('(',curPos+1);
   }

   return outString;
}

template <class Usage>
string ModelExpression<Usage>::restoreNonGroupParens (const string& inString)
{
   // Restore the parentheses which were modified by flagNonGroupParens.
   string outString(inString);
   const string::size_type len = outString.length();
   for (string::size_type i=0; i<len; ++i)
   {
      char c = outString[i];
      if (c == '@')
         outString[i] = '(';
      else if (c == '!')
         outString[i] = ')';
   }

   return outString;
}


template <class Usage>
const string ModelExpression<Usage>::s_allValidChars = string("_$#.(){}+-*/~abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\r\n");




#endif
