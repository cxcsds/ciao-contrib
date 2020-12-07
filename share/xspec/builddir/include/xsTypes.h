//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSTYPES_H
#define XSTYPES_H 1
#include <vector>
#include <string>
#include <utility>
#include <list>
class UniqueEnergy;

// valarray
#include <valarray>
// map
#include <map>
using std::string;




typedef double Real;



typedef std::valarray<Real> RealArray;
//	std::vector< RealArray >



typedef std::vector< RealArray  > MatrixValue;



typedef std::map<size_t,RealArray> ArrayContainer;



typedef std::map<size_t, const ArrayContainer*> EnergyPointer;



typedef std::map<size_t,ArrayContainer> GroupFluxContainer;



typedef std::vector< bool > BoolArray;



typedef long CodeField;



typedef std::vector<CodeField> CodeContainer;



typedef std::vector<int> IntegerVector;



// Keep this definition for backward compatibility
typedef IntegerVector IntegerArray;



typedef std::vector<IntegerVector> MatrixIndex;



typedef std::pair<MatrixValue, MatrixIndex > XSMatrix;



typedef std::vector<string> StringArray;



typedef std::list< string > StringList;



typedef std::pair<size_t,size_t> RangePair;



typedef std::map<const UniqueEnergy*, RealArray> UniquePhotonContainer;


#endif
