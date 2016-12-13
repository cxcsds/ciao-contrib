//C++
#ifndef HANDLERUTILS_H
#define HANDLERUTILS_H

#include <xsTypes.h>
#include <XSstreams.h>        
#include <XSFit/Fit/Step.h>
#include <XSUser/UserInterface/xstcl.h>
#include <XSUtil/Error/Error.h>
#include <XSUtil/Parse/XSRegEx.h>
#include <XSUtil/Parse/XSparse.h>
#include <functional>
#include <sstream>

class Model;
class Parameter;
class Component;
class TclRegEx;
class Response;
class ResponseParam;


// These clases and utilities depend on objects defined in libXSModel, 
// which is why they are not included in the usual XSutility and 
// XSparse files.  They also tend to depend on tcl, which is why they are 
// here and not in XSModel.

// Traits classes  
  template<typename T>
  class CmdRetrievalTraits;

  template<>
  class CmdRetrievalTraits<Parameter>
  {
     public:
        static const std::string reqString;
        static const std::string objName;
  };

  template<>
  class CmdRetrievalTraits<Component>
  {
     public:
        static const std::string reqString;
        static const std::string objName;
  };

  template<>
  class CmdRetrievalTraits<Response>
  {
     public:
        static const std::string reqString;
        static const std::string objName;
  };

  template<>
  class CmdRetrievalTraits<ResponseParam>
  {
     public:
        static const std::string reqString;
        static const std::string objName;
  };

 // Policy classes
  template<typename T> 
  class LookupPolicy;

  template<>
  class LookupPolicy<Parameter>
  {
     public:
        static Parameter* get(const string& name, size_t num);
  };

  template<>
  class LookupPolicy<Model>
  {
     public:
        static Model* get(const string& name, size_t num);
  };

  template<>
  class LookupPolicy<Component>
  {
     public:
        static Component* get(const string& name, size_t num);
  };

  template<>
  class LookupPolicy<Response>
  {
     public:
        static Response* get(const size_t defSource, const size_t defSpec, 
                        size_t& sourceNum, size_t& specNum);
  };

  template<>
  class LookupPolicy<ResponseParam>
  {
     public:
         // Each of these does the same thing.  The second 2 interfaces
         // are to allow interchangability with Response and Parameter
         // objects respectively.
        static ResponseParam* get(size_t sourceNum, size_t parNum);
        static ResponseParam* get(const size_t defSource, const size_t defPar,
                                size_t& sourceNum, size_t& parNum);
        static ResponseParam* get(const string& name, size_t num);
  };

  // Originally designed for freeze/thaw/untie
  template<typename T>
  class RangeFindPolicy;

  template<>
  class RangeFindPolicy<Parameter>
  {
     public:
        static IntegerArray getIndices(const string& modName, 
                        const StringArray& rangeStrs, RangePair& prevRange);
  };

  template<>
  class RangeFindPolicy<ResponseParam>
  {
     public:
        static IntegerArray getIndices(const string& sourceName, 
                        const StringArray& rangeStrs, RangePair& prevRange);
  };

namespace HandlerUtils
{
  typedef XSRegEx<TclRegEx> RegEx;


  // Template functions utilizing the FIXED traits style described by
  // Vandevoorde and Josuttis, not Alexandrescu's more complicated 
  // parameterized style.

  template<typename T>   
  T* lookupStringIntObj(const string& name, size_t idx);

  template <typename T>
  bool verifyStringInt(const StringArray& rawArgs, size_t pos, 
                string& name, size_t& idx);

  template <typename T>
  T* getFromStringInt(const StringArray& rawArgs);

  // The arg string should contain the int pair or be empty.  
  // "first" and "second" will be set to the indices of the returned T*, 
  // as determined from the arg string.  If arg string is empty, it looks
  // for T* given by input "first" and "second". If only 1 int is found in arg 
  // (and no colon) it will be applied to "second", and "first" will retain 
  // its input value.    
  // Doing it this way since "first" is expected to represent the
  // optional sourceNum parameter in most scenarios. 
  //
  // NOTE: Internal T* lookup functions have the right to change "first"
  // or "second" through reprompting, and they may throw.
  // 
  // If unable to find an object at the requested position, returns 0.
  // "first" and "second" will be set to the values of the attempted position.
  //
  // Throws if invalid syntax or negative integers, in which case
  // "first" and "second" will be unchanged from their input values.
  template <typename T>
  T* getFromIntPair(const string& arg, int& first, int& second);

  // Generic function to do the bulk of the work common to the
  // freeze/thaw/untie commands.  T must be a type for which
  // LookupPolicy and RangeFindPolicy classes are defined.
  // U is a strategy class defined by and specific to the individual
  // command handler.
  //
  // groupName is the left-of-colon group specifier, ie. modName or sourceNum,
  // and may be empty.  rangeStrs are all the range string specifiers for
  // the group.  prevRange will be filled with the last entered range. 
  // Returns true if ANY parameter has had its f/t/u state modified.
  template <typename T, typename U>
  bool freezeThawUntie(const string& groupName, const StringArray& rangeStrs,
                        RangePair& prevRange);


  // Non-templated utilities

  // Does a 1-to-1 copy from each Tcl object in objv (including the 1st) 
  // to a string in cppArgs.  cppArgs will be resized to objc.
  void tclArgsToCpp(const int objc, Tcl_Obj* CONST objv[], StringArray& cppArgs);

  bool getSpecNumParameter(const StringArray& rawArgs, const string& opt,
                        size_t argNum, size_t& specNum);
  const Model* getModFromArg(const StringArray& rawArgs);
  const Model* getModFromName(const string& name);
  bool subExpMatched (const Tcl_RegExpInfo& regExpInfo, const string& search, 
		      int index, std::string& group);
  bool subExpMatched (const Tcl_RegExpInfo& regExpInfo, const string& search, 
		      const IntegerArray& indices, std::map<int, std::string >& group);
  bool compileAndMatch(const string& pattern, const string& search, 
		       const string& whole, Tcl_RegExpInfo& expInfo);
  bool fillArrays(const Tcl_RegExpInfo& expInfo, const string& arg, 
		  std::vector<Real> first, std::vector<Real> second, 
		  std::vector<Real>& _default);
  bool fillArrays(const Tcl_RegExpInfo& expInfo, const std::string& arg, 
		  std::vector<Real>& first, std::vector<Real>& second, 
		  std::vector<Real>& _default, const IntegerArray& subs);
  void IgnoreNoticeParse(const StringArray& args, std::vector<Real>& prevRanges, 
			 bool& isReal, bool& isRespChanged, bool& isChanged, bool value);
  bool fileExists(const string& fileName, std::ofstream& out);
  bool analyzeInfix(const string& infix, string& postfix);
  void commonStepParsing(const StringArray& rawArgs, Grid::ParameterSpec*& prevSettings,
                 Grid::SpecContainer& newStepSettings, bool& isBest, 
                 bool needModParam = true);

  struct CompareSource : public std::binary_function<Model*, Model*, bool>
  {
      public:
      bool operator() (Model* right, Model* left);
  };

  class FreezeThawRange
  {
     public:
        static const RangePair& getRange() {return s_range;}
        static void setRange(const RangePair& newRange)
                        {s_range = newRange;}
        static const string& getGroupName() {return s_groupName;}
        static void setGroupName(const string& groupName)
                        {s_groupName = groupName;}
     private:
        static RangePair s_range;
        static string s_groupName;
  };
}


template <typename T>
T* HandlerUtils::lookupStringIntObj(const string& name, size_t idx)
{
   T* pT = 0;

   pT = LookupPolicy<T>::get(name, idx);
   if (!pT)
   {
      std::ostringstream concat;
      if (name.length())
      {
         concat << name << ":" << idx;
      }
      else
      {
         concat << "[(unnamed):]" << idx;
      }
      string errMsg = "Cannot locate ";
      errMsg += CmdRetrievalTraits<T>::objName + " specified by: " + 
                      concat.str();
      tcerr << errMsg << std::endl;
   }
   return pT;
}

template <typename T>
bool HandlerUtils::verifyStringInt(const StringArray& rawArgs, size_t pos, 
                        string& name, size_t& idx)
{
   bool status = true;
   string errMsg = "Must specify ";
   errMsg += CmdRetrievalTraits<T>::reqString;
   if (rawArgs.size() < pos)
   {
      tcerr << errMsg << std::endl;
      status = false;
   }
   else
   {
      string arg(rawArgs[pos-1]);
      name = string("");
      idx = string::npos;
      XSparse::stringIntPair(arg, name, idx);
      if (idx == string::npos)
      {
         tcerr << errMsg << std::endl;
         status = false;
      }        
   }
   return status;
}

template <typename T>
T* HandlerUtils::getFromStringInt(const StringArray& rawArgs)
{
   T* pT = 0;
   string name;
   size_t idx=string::npos;
   if (verifyStringInt<T>(rawArgs, 3, name, idx))
   {
      pT = lookupStringIntObj<T>(name, idx);
   }
   return pT;
}

template <typename T>
T* HandlerUtils::getFromIntPair(const string& arg, int& first, int& second)
{
   T* pT = 0;
   int i1=0, i2=0;
   bool validSyntax = false;
   if (!arg.length())
   {
      i1 = first;
      i2 = second;
      validSyntax = true;
   }
   else if (XSparse::integerPair(arg, i1, i2))
   {
      if (i2 == -1)
      {
         // Only 1 int and no colon.  Apply this to second for reasons
         // given in the function declaration above.
         i2 = i1;
         i1 = first;
      }
      validSyntax = true;
   }
   else
   {
      std::ostringstream errMsg;
      errMsg << "Invalid syntax: " << arg << ": should be of form "
            << CmdRetrievalTraits<T>::reqString << '\n';
      throw YellowAlert(errMsg.str());
   }

   if (validSyntax)
   {
      if (i1 < 0 || i2 < 0)
      {
         std::ostringstream errMsg;
         errMsg << "Negative indices are not allowed when selecting a "
               << CmdRetrievalTraits<T>::objName << " with\n" 
               << CmdRetrievalTraits<T>::reqString << '\n';
         throw YellowAlert(errMsg.str()); 
      }
      else
      {
         size_t tmp1 = static_cast<size_t>(i1);
         size_t tmp2 = static_cast<size_t>(i2);
         // Assume that for some T this may change input args
         // due to reprompting.
         pT = LookupPolicy<T>::get(static_cast<size_t>(first),
                        static_cast<size_t>(second),tmp1, tmp2);
         first = static_cast<int>(tmp1);
         second = static_cast<int>(tmp2);
      }
   }

   return pT;
}

template <typename T, typename U>
bool freezeThawUntie(const string& groupName, const StringArray& rangeStrs,
                      RangePair& prevRange)
{
   bool isChanged = false;

   IntegerArray parIndices(RangeFindPolicy<T>::getIndices(groupName,
                        rangeStrs, prevRange));
   const size_t nPars = parIndices.size();
   for (size_t i=0; i<nPars; ++i)
   {
      Parameter* par = LookupPolicy<T>::get(groupName, 
                        static_cast<size_t>(parIndices[i]));
      if (par)
      {
         string msg;         
         if (!U::perform(par, msg))
         {
            tcout << "  "<< CmdRetrievalTraits<T>::objName << " ";
            if (groupName.length())
               tcout << groupName <<":";
            tcout << parIndices[i] << msg << std::endl;
         }
         else
            isChanged = true;
      }
      else
      {
         // Don't think it can even get here, as RangeFindPolicy
         // would most likely have thrown.  Just to be sure...
         std::ostringstream oss;
         oss << "No such " << CmdRetrievalTraits<T>::objName << ": ";
         if (groupName.length())
            oss << groupName <<":";
         oss << parIndices[i] <<"\n";
         throw YellowAlert(oss.str());          
      }
   }

   return isChanged;
}

#endif
