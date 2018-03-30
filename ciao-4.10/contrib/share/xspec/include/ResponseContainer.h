//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RESPONSECONTAINER_H
#define RESPONSECONTAINER_H 1
#include <utility>
#include <XSUtil/Error/Error.h>
#include <set>

// Reference
#include <XSUtil/Utils/Reference.h>
// Response
#include <XSModel/Data/Detector/Response.h>
// ResponseMatrix
#include <XSModel/Data/Detector/ResponseMatrix.h>
// ResponseTypes
#include <XSModel/GlobalContainer/ResponseTypes.h>

class DummyResponse;
class ResponseParam;
class Parameter;

namespace XSContainer {



    class ResponseContainer 
    {

      public:
        //	Key = specNum, Value = parameter index offset



        typedef std::map<size_t,size_t> IndexOffsetMap;
          ResponseContainer (DummyResponse* dummy);
          ~ResponseContainer();

          //	Additional Public Declarations
          static ResponseContainer* Instance (DummyResponse* dummy);
          void addToList (const string& name, Response* newResponse);
          void addToList (const RefCountPtr<ResponseMatrix>& newRMF);
          const Response* responseList (const string& name, size_t index) const;
          Response* responseList (const string& name, size_t index);
          size_t numberOfResponses () const;
          void removeByToken (const std::vector<Response*>& doomed, size_t sourceNum = 0);
          void removeByToken (const RefCountPtr<ResponseMatrix>& doomed) throw ();
          Response* swapResponses (Response* inResponse, Response* outResponse);
          void clearGainParameters ();
          void adjustNumSources (size_t nSources);
          //	Allow Response objects to enter all or a subset (for a
          //	future equivalent of addcomp) of their parameters into
          //	the global container.  startIdx is the 0-BASED position
          //	of the first parameter in the vector w/respect to the
          //	first parameter in the Response.  The vector arg itself
          //	would become obsolete if Response were to maintain its
          //	own vector<ResponseParam*>  as a data member as part of
          //	a future generalization of Response functions.
          void addToRespParContainer (const Response* resp, size_t startIdx, const std::vector<ResponseParam*>& respParams);
          //	Allow Response objects to remove all or a subset of
          //	their ResponseParams from the global container.  start
          //	Idx is the 0-BASED position of the first parameter to be
          //	removed w/respect to the first parameter in the
          //	Response.  nPars is the number of consecutively indexed
          //	parameters to be removed, beginning with startIdx.
          void removeFromRespParContainer (const Response* resp, size_t startIdx, size_t nPars);
          void reportResponseParams () const;
          //	This must be called when spectrum numbers change due to
          //	a delete with preserve xsData operation.  The Response
          //	Container will need to update the entries in its respPar
          //	IndexOffsets bookkeeping container.  All keys larger
          //	than start will be shifted DOWN by offset.
          void renumberSpectrum (const size_t start, const size_t offset);
          //	A vector of vector to ResponseParam pointers.  Outer
          //	vector size should always equal DataContainer's num
          //	SourcesForSpectra, and will contain empty vectors for
          //	sources without response parameters.  Pointers will be
          //	placed in sequential order of parameter index numbers
          //	for each source.  The ResponseParam pointers are
          //	non-owning.
          const RespParContainer& respParContainer () const;
          size_t totalResponseParams () const;
          const RMFMap& RMFmap () const;
          void RMFmap (const RMFMap& value);
          ResponseMap& responseList ();

      public:
        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          void responseList (const string& name, Response* value);
          void RMFmap (const string& name, const RefCountPtr<ResponseMatrix>& rmf);
          Response* internalFind (const string& name, size_t index) const;
          void rerouteBrokenParLinks (std::set<Parameter*>& doomedPars) const;
          //	Reindex parameters due to insertion/deletion of nChanged
          //	parameters occuring at given source and spectrum.  All
          //	indices below this location should be unaffected.  iResp
          //	Start is the position in the ResponseParam* vector of
          //	the first parameter in the affected Response.  Positive n
          //	Changed indicates insertion took place, negative
          //	indicates deletion.
          void reindexResponseParams (size_t sourceNum, size_t specNum, size_t iRespStart, int nChanged);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          static ResponseContainer* s_instance;
          RespParContainer m_respParContainer;
          //	Private bookkeeping container needed to determine
          //	starting ResponseParam index value for a given spectrum
          //	for each source.  Outer vector corresponds to sources
          //	and should always be sized to DataContainer's numSources
          //	ForSpectra.  Each map contains entries of (spec
          //	Num,offset) pairs and may be empty.  Pairs should only
          //	be entered for spectra that actually have response
          //	parameters at a given source.
          std::vector<IndexOffsetMap> m_respParIndexOffsets;
          size_t m_totalResponseParams;

        // Data Members for Associations
          RMFMap m_RMFmap;
          ResponseMap m_responseList;

        // Additional Implementation Declarations

    };

    // Class XSContainer::ResponseContainer 

    inline const RespParContainer& ResponseContainer::respParContainer () const
    {
      return m_respParContainer;
    }

    inline size_t ResponseContainer::totalResponseParams () const
    {
      return m_totalResponseParams;
    }

    inline const RMFMap& ResponseContainer::RMFmap () const
    {
      return m_RMFmap;
    }

    inline void ResponseContainer::RMFmap (const RMFMap& value)
    {
      m_RMFmap = value;
    }

} // namespace XSContainer


#endif
