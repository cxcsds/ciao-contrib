//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MODELTYPES_H
#define MODELTYPES_H 1
#include <xsTypes.h>
#include <utility>

// string
#include <string>
// map
#include <map>

class Model;
class Parameter;

namespace XSContainer {



    typedef std::multimap<std::string, Model*> ModelMap;



    typedef std::map<std::string, Parameter*> ParamMap;



    typedef ParamMap::const_iterator ParamMapConstIter;



    typedef ModelMap::iterator ModelMapIter;



    typedef ModelMap::const_iterator ModelMapConstIter;



    typedef ParamMap::iterator ParamMapIter;

    // For storage of 0-based component indices of mix or amx type.
    typedef std::pair<std::vector<size_t>,std::vector<size_t> > MixLocations;

    struct EqWidthRecord 
    {
          EqWidthRecord();

        // Data Members for Class Attributes
          string modelName;
          size_t compNumber;
          Real fraction;

      public:
      protected:
      private:
      private: //## implementation
    };



    typedef std::map<string, IntegerVector> DataGroupMap;



    struct ExtendRecord 
    {
          ExtendRecord (Real eng = 1.0, bool log = false, size_t nEbin = 0);
          ExtendRecord & operator=(const ExtendRecord &right);

        // Data Members for Class Attributes
          Real energy;
          bool isLog;
          size_t nBins;

      public:
      protected:
      private:
      private: //## implementation
    };



    typedef std::pair<ExtendRecord,ExtendRecord> ExtendRange;

    // Class XSContainer::EqWidthRecord 

    inline EqWidthRecord::EqWidthRecord()
      :modelName(""), compNumber(0), fraction(.0)
    {
    }


    // Class XSContainer::ExtendRecord 

    inline ExtendRecord::ExtendRecord (Real eng, bool log, size_t nEbin)
      : energy(eng), isLog(log), nBins(nEbin)
    {
    }


    inline ExtendRecord & ExtendRecord::operator=(const ExtendRecord &right)
    {
       if (this != &right)
       {
          energy = right.energy;
          isLog = right.isLog;
          nBins = right.nBins;
       }
       return *this;
    }


    // Class XSContainer::EqWidthRecord 

} // namespace XSContainer


#endif
