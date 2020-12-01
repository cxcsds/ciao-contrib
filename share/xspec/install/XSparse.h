//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSPARSE_H
#define XSPARSE_H 1

// Error
#include <XSUtil/Error/Error.h>
#include <XSUtil/Utils/XSstream.h>
#include <XSUtil/Utils/IosHolder.h>

#include <XSUtil/Utils/XSutility.h>
#include <deque>
#include <stack>




class XSparse 
{

  public:



    class SkipThis : public YellowAlert  //## Inherits: <unnamed>%3A65FC6F016E
    {
      public:
          SkipThis (const std::string& diag = "... skipped\n");

      protected:
      private:
      private: //## implementation
    };



    class AbortLoop : public YellowAlert  //## Inherits: <unnamed>%3A65FC6B02E8
    {
      public:
          AbortLoop (const std::string& diag = "terminated at user request\n");

      protected:
      private:
      private: //## implementation
    };



    class SyntaxError : public YellowAlert  //## Inherits: <unnamed>%3BAB4A170318
    {
      public:
          SyntaxError (const std::string& diag);

      protected:
      private:
      private: //## implementation
    };



    class InputError : public YellowAlert  //## Inherits: <unnamed>%3BB4C0CD0072
    {
      public:
          InputError (const std::string& diag);

      protected:
      private:
      private: //## implementation
    };



    class InvalidRange : public YellowAlert  //## Inherits: <unnamed>%3BB4C09E0249
    {
      public:
          InvalidRange();
          InvalidRange (const std::string& diag);

      protected:
      private:
      private: //## implementation
    };

      //	Takes a set of Tcl_Objs and finds where the command ends
      //	and the subsequent input ("batch") begins.
      //
      //	Returns the command truncated by the subsequent
      //	batch strings, and a vector of strings representing the
      //	batch information.
      static void findBatchString (const string& cmdLine, string& command, std::deque<string>& batch);
      //	getRanges takes a string and outputs an integer array of
      //	indices in the range.
      //
      //	In XSPEC 11 this was done using tcl's Regexp machinery,
      //	but this won't be used here to keep tcl and xspec's
      //	innards separate.
      //
      //	The range should have the following forms:
      //
      //	a) * : all the indices that are relevant. For this it
      //	needs to be supplied the total number of relevant indices
      //
      //	b) n  : single number
      //
      //	c) n - m : a simple range
      //
      //	d) n1-m1,n2,n3-m3,...  a comma delimited set of ranges
      //
      //	e) n:*    from index n to the last index.
      //
      //	lastIndex = -1,  is used to denote the presence of wild
      //	cards in the range string.
      //
      //	Remember C++ uses zero-based indices!
      static IntegerVector getRanges (const string& rangeString, int lastIndex);
      //	For an input string representing a "range", returns the
      //	beginning and ending numbers in that range.
      //
      //	endRange is returned as -1 if there is a wildcard
      //	character. If the range corresponds to just a '*',  begin
      //	Range is set to 1.
      //
      //	a string xsdelimiters represents the delimiters used in
      //	expressing the range, defaults to - and :
      static void oneRange (const string& inputRange, int& beginRange, int& endRange);
      //	function for cutting a string at a delimiter. Returns a
      //	newly constructed string containing the next delimited
      //	argument and the input string, truncated to the remainder
      //	after the first delimited argument is split off.
      static string returnDelimitedArgument (string& inString, const string& xsdelim);
      //	function for cutting a string into substrings at delimiters.
      //        Makes repeated use of returnDelimitedArgument.
      static void returnAllDelimitedArguments (const string& inString, const string& xsdelim, StringArray& allArgs);
      //	Function for getting next line from file, with
      //	leading/trailing blanks/tabs removed.
      //
      //	Also, ignores lines that contain the '#' from that mark
      //	forward (this is a little more generous than tcl,
      //	functions like comment processing in make).
      static string getNextLine (std::ifstream& stream);
      //	function for parsing XSPEC model commands. It processes
      //	a string of the form
      //
      //	model <stringPar>:<intPar>  <commandString>
      //
      //	[The commandString, an XSPEC model string, is processed
      //	by the Expression class].
      static void parseInputModelString (const string& inputString, string& stringPar, size_t& intPar, string& commandString);
      //	Returns true if input is one of the following forms:
      //	<n> <n>: :<m> <n>:<m>, else returns false.
      //
      //	 If it returns true and the string contains only one
      //	integer and no colon, the second argument is set to -1.
      //
      //	If only one integer and there is a colon, the missing
      //	integer's argument is set to 1.
      //
      //	If it returns false, both arguments are set to -1.
      static bool integerPair (const string& arg, int& first, int& second);
      //	Routine from Xspec11 which spaces out a string to aid
      //	the parsing operation. Probably redundant, but at least
      //	requires an overhaul.
      static void spaceString (char** inputString);
      //	routine from Xspec11 for testing whether a string is an
      //	exponential number. Probably obsolete.
      static int checkExponent (char* inputString);
      static void getFileNameFromUser (const string& oldName, string& newName, XSutility::fileType type);
      //	This is meant to handle input of type arg = "name
      //	String:n" or simply "n".  If it is the latter, word will
      //	be returned as an empty string. NOTE: in that case, this
      //	function actually returns "false" even though just "n"
      //	may be a valid input.  It is up to the calling functions
      //	to figure this out.  If n is not an int type, the
      //	"number" argument will be returned unchanged.
      static bool stringIntPair (const string& arg, string& word, size_t& number);
      static void stringRangePair (const string& arg, string& word, IntegerVector& range);
      static void catchSkips (const string& input, bool silent = true);
      //	Parse an int/string pair separated by the first
      //	appearance of the specified delimiter.  If delimiter is
      //	not found, number is set to s_NOTFOUND and word contains
      //	entire arg.  If delimiter is found and the left portion
      //	is not an int, this will throw a SyntaxError.
      static void intStringPair (const string& arg, size_t& number, string& word, char delim = ':');
      static bool addToLibraryPath (const string& newDirectory, string& fullDirectory, int accessMode);
      static string expandDirectoryPath (const string& input);
      static string stripDirectoryPath (const string& input);
      static void collectParams (const std::vector<string>& args, IntegerVector& iParams, StringArray& xsParams);
      static void basicPrompt (const string& promptMsg, string& result, std::deque<string>* batchArgs = 0);
      static void promptResponseArf (string& responseName, const string& defaultName, string& arfName, size_t& arfRow, const size_t specNum, bool demand = true, bool doArf = true, std::deque<string>* batchArgs = 0);
      static void changeExtension (string& fileName, const string& extName, const bool duplicate = true);
      static string promptFilename (const string& defaultName = "", std::deque<string>* batchArgs = 0);
      static void collateByWhitespace (StringArray& outStrings, const string& inString);
      static void checkBrackets (StringArray& args, char bracketChar);
      static string IntToString (size_t num);
      static bool promptReal (const string& prompt, Real& real, std::deque<string>* batchArgs = 0);
      static void separate (string& operand, const string& separators);
      static IntegerVector expandRange (const IntegerVector& range);
      static string trimWhiteSpace (const string& value);
      static RangePair wildRange (const string& inputRange, const RangePair& maxRange, RangePair& prevRange);
      static IntegerVector getRanges (const StringArray& inArgs, RangePair& prevRanges, const RangePair& rangeLimits);

      static bool promptRealTuple(const string& prompt, std::vector<Real>& vals, std::deque<string>* batchArgs);
      //	Return a substring starting at the position given by p
      //	Start, with size up to (but not including) the first
      //	"\n", or the first n=length chars, whichever is
      //	shorter.  If stopping at n=length will break up a word
      //	or number, break instead at the last whitespace prior to
      //	it.  pStart will be reset to the position after the end
      //	of the returned segment (but not a "\n"), or npos if it
      //	has reached the end.  If pStart is initially out of
      //	range, return a blank string.
      static string stringSegment (const string& fullString, const size_t length, string::size_type* pStart);
      //	Looks for a specifier of the form "{n}" appended to a
      //	file name.  Returns the value n, and sets the "fileName"
      //	arg to the substring preceding the first '{'.  If no
      //	brackets, returns 0.  THROWS if anything other than a
      //	single non-negative integer is found between brackets,
      //	or if any non-WS follows the '}'.  Whitespace padding
      //	between the brackets is allowed.
      static int getCurlyBracketInt (const string& fullName, string& fileName);
      //	Designed for the untie/freeze/thaw group of commands and
      //	their resppar equivalents.  This will collate range
      //	strings by left-of-colon specifier, ie.
      //	   untie 3 5 a:1 ,2 b:1-2 a 4
      //	fills map with "":{"3","5"}
      //	                 "a":{"1","2","4"}
      //	                 "b":{"1-2"}
      //	Input:
      //	inArgs - The raw cmd line arg strings, 1-to-1 with Tcl's
      //	objv[], aside from the cmd name itself which is left out.
      //	prevName - Default name (if any) to be applied to empty
      //	left-of-colon args until superseded by a new name.
      //
      //	Output:
      //	prevName - The last specified left-of-colon name.
      //	rangeGroups - The collated map.
      //
      //	This does not actually check for valid range strings,
      //	but CAN THROW if colon is used improperly in string.
      static void collateRanges (const StringArray& inArgs, string& prevName, std::map<string,StringArray>& rangeGroups);
      //	Returns true if the filename includes extended syntax,
      //	currently defined as either ending in square brackets,
      //	or ending in "+<n>" where n is some integer.  Also fills
      //	in the location of either the '[' or the '+' if they
      //	exist, or npos if they don't.
      static bool checkExtendedSyntax (const string& filename, string::size_type& squareLoc, string::size_type& plusLoc);
      //	Convert an absolute directory path to a relative one in
      //	relation to the referencePath position.  Both input
      //	paths must be Unix-style absolute path names, ie. first
      //	character must be '/'.  This will throw if otherwise.
      static string absToRelPath (const string& referencePath, const string& absPath);
      //	Assumes charStr is 0 or points to a NULL-terminated char
      //	string.  Returns true if charStr is 0 or string contains
      //	no non-whitespace chars.
      static bool isBlank (const char* charStr);
      //  Check parSpec for indication of a response parameter ID.
      //  The general form for a response ID is [<sourceNum>:]r|R<parIdx>.
      //  This merely checks whether parSpec includes a ':' followed
      //  immediately by an 'r' (or 'R'), and if no colon, whether the
      //  first character is an 'r' (or 'R').  Neither of these cases would
      //  be a valid MODEL parameter ID.  It does NOT skip over whitespace, 
      //  and it leaves testing of <sourceNum> and <parIdx> formats to other
      //  functions (see integerPair). If check succeeds, it returns the
      //  location of the 'r' (or 'R').  Otherwise it returns npos.      
      static string::size_type checkForRespPar(const string& parSpec);
      
      // Perform a "white list" check on characters in input string.
      // Return false if any characters are not in white list.
      static bool validateForSystem(const string& input);
      
      
      static const size_t CommandLength ();
      static const string& NONE ();
      static const string& SKIP ();
      static const bool rangeIsReal ();
      static void rangeIsReal (bool value);
      static const string::size_type& NOTFOUND ();
      static const bool executingScript ();
      static void executingScript (bool value);
      static const string& USE_DEFAULT ();

  public:
    // Additional Public Declarations
      template <typename T>
      static void
      getArg (std::istream& s, T& value,  const T& defaultValue, const string& prompt);

      template <typename T>
      static string ArrayToRange (const T& array);
  protected:
    // Additional Protected Declarations

  private:
      //	returns true if a string has a range string, and
      //	leaves first '{' and '}'  index numbers in begin and end
      //	arguments. end is return as strg.length() if the close
      //	has been inadvertently left off.
      static bool hasRange (const string& strg, size_t& beginRng, size_t& endRng);
      static size_t validateRangeSpecifier (const string& rangeString);
      //	Utility function used by absToRelPath
      static void pathToStack (const string& referencePath, std::stack<string>& pathStack);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string STRINGNULLS;
      static const string INPUT_DELIMITER;
      static const size_t XCM_LEN;
      static const string s_NONE;
      static const string s_SKIP;
      static bool s_rangeIsReal;
      static const string::size_type s_NOTFOUND;
      static char* s_augmentedLibraryPath;
      static bool s_executingScript;
      static const string s_USE_DEFAULT;

    // Additional Implementation Declarations

};
template <typename T>
void XSparse::getArg (std::istream& s, T& value,  const T& defaultValue, const string& prompt )
{
        string input("");
        while (1) 
        {
                *IosHolder::errHolder() << "re-enter ( \"/*\" to abort or \"/\" to use default value )\n"; 
                XSstream* xscout = dynamic_cast<XSstream*>(IosHolder::outHolder());
                if (xscout)
                {
                   XSstream::setPrompter(s,prompt);
                }
                else
                {  
                   *IosHolder::outHolder() << prompt;
                }
                s >> input;
                std::istringstream t(input);
                t.exceptions(std::ios_base::failbit);
                try
                {
                        if ( t.str() == s_SKIP) throw AbortLoop();
                        if ( t.str() == "/")
                        {
                                value = defaultValue;
                                break;
                        }
                        else
                        {
                                t >> value;
                                break; 
                        }
                }
                catch ( std::exception& )
                {
                        continue;
                }
        }

}

template <typename T>
string XSparse::ArrayToRange (const T& array)
{
    size_t count = array.size(), rangeStart = 0;

    std::string range = (count > 0 ? IntToString(array[0]) : std::string(""));

    for(size_t i = 1; i <= count; ++i) {
        int diff=0;
        if (i != count)
           diff = array[i] - array[i - 1];
	if(i == count || diff >= 2 || diff < 0)
	{
	    if(rangeStart != i - 1)
		range += '-' + IntToString(array[i - 1]);

	    rangeStart = i;
	    if(i != count) 
		range += ',' + IntToString(array[i]);
	}
    }
    return range;
}

// Class XSparse::SkipThis 

// Class XSparse::AbortLoop 

// Class XSparse::SyntaxError 

// Class XSparse::InputError 

// Class XSparse::InvalidRange 

// Class Utility XSparse 

inline const size_t XSparse::CommandLength ()
{
  return XCM_LEN;
}

inline const string& XSparse::NONE ()
{
  return s_NONE;
}

inline const string& XSparse::SKIP ()
{
  return s_SKIP;
}

inline const bool XSparse::rangeIsReal ()
{
  return s_rangeIsReal;
}

inline void XSparse::rangeIsReal (bool value)
{
  s_rangeIsReal = value;
}

inline const string::size_type& XSparse::NOTFOUND ()
{
  return s_NOTFOUND;
}

inline const bool XSparse::executingScript ()
{
  return s_executingScript;
}

inline void XSparse::executingScript (bool value)
{
  s_executingScript = value;
}

inline const string& XSparse::USE_DEFAULT ()
{
  return s_USE_DEFAULT;
}


#endif
