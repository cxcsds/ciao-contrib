//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RESPONSETYPES_H
#define RESPONSETYPES_H 1
#include <vector>

// string
#include <string>
// map
#include <map>
// Reference
#include <XSUtil/Utils/Reference.h>

class Response;
class RMF;
using std::string;

namespace XSContainer {



    typedef std::multimap<string,RefCountPtr<RMF> > RMFMap;



    typedef std::multimap<string,Response*> ResponseMap;



    typedef ResponseMap::iterator ResponseMapIter;



    typedef ResponseMap::const_iterator ResponseMapConstIter;



    typedef RMFMap::iterator RMFMapIter;



    typedef RMFMap::const_iterator RMFMapConstIter;
    //	Outer vector for sourceNums, inner vector ResponseParams
    //	ordered by parameter index.



    typedef std::vector<std::vector<ResponseParam*> > RespParContainer;

} // namespace XSContainer


#endif
