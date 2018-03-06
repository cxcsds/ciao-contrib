//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATASETTYPES_H
#define DATASETTYPES_H 1

// string
#include <string>
// map
#include <map>

class SpectralData;
class DataSet;

namespace XSContainer {



    typedef std::multimap<std::string,DataSet*> DataArray;



    typedef std::map<size_t,SpectralData*> SpectralDataMap;



    typedef DataArray::iterator DataArrayIt;



    typedef DataArray::const_iterator DataArrayConstIt;



    typedef SpectralDataMap::iterator SpectralDataMapIt;



    typedef SpectralDataMap::const_iterator SpectralDataMapConstIt;

} // namespace XSContainer


#endif
