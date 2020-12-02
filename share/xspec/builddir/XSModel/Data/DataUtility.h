//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATAUTILITY_H
#define DATAUTILITY_H 1
#include <XSUtil/Utils/XSutility.h>
#include <XSModel/Data/Detector/ResponseMatrix.h>
#include <CCfits/CCfits>
#include <xsTypes.h>

// DataInputRecord
#include <XSModel/Data/DataInputRecord.h>
// DataFactory
#include <XSModel/DataFactory/DataFactory.h>
// OGIP-92aIO
#include <XSModel/DataFactory/OGIP-92aIO.h>
// Weight
#include <XSModel/GlobalContainer/Weight.h>

class SpectralData;
class DataSet;
class BackCorr;
class Response;
class ResponseMatrix;

namespace CCfits
{
        class ExtHDU;       
}                




class DataUtility 
{

  public:



    typedef std::list<DataInputRecord> recordList;



    typedef std::list<DataInputRecord>::iterator recordListIter;



    typedef std::list<DataInputRecord>::const_iterator recordListConstIter;

      static void readArrays (ResponseMatrix& rmf, const CCfits::ExtHDU& fitsData);
      static void groupArrays (ResponseMatrix& rmf, const size_t startChan, const size_t endChan);
      static void setSource (SpectralData* spectrum, Response* response, size_t sourceNum);
      static const CodeContainer& encodeGQ (const IntegerVector& group, const IntegerVector& quality, CodeContainer& coded);
      static void decodeGQ (const CodeContainer& coded, IntegerVector& group, IntegerVector& quality);
      static void encode (const IntegerVector& inputArray, CodeContainer& coded);
      static void decode (const CodeContainer&  coded, IntegerVector& inputArray);
      static void fixSequence (DataUtility::recordList& records, size_t spectraDefined);
      //	Function to parse the input for a data command. This
      //	will be made general enough to serve for
      //	data,background,response and other data reading
      //	commands, although its full functionality is only
      //	required for   data.
      //
      //	Takes the Tcl_Obj array provided by the interpreter and
      //	determines:
      //
      //	An array (names) of data set names that correspond to
      //	filenames.
      //
      //	For each named file, the spectrum number (setNums) to be
      //	assigned to the first spectrum to be read from the file.
      //	The calling code will be responsible for (a) checking
      //	that this is a valid number and (b) incrementing the
      //	spectrum number assigned to following spectra read from
      //	the same file. The spectrum number assigned cannot be
      //	larger than one greater than previously assigned. That
      //	is, if there are  n datasets assigned or to be assigned,
      //	setNum <= n+1.
      //
      //	For each named file, the data group number to be
      //	assigned. Again, if the highest group number currently
      //	assigned is m, groupNum <= m+1.
      //
      //	For each named file, a range of spectra may be read from
      //	the file. The user must supply a range string in {}
      //	following the file name, as described under XSparse::get
      //	Ranges.
      static DataUtility::recordList parseDataCommandString (StringArray& args, XSutility::fileType defaultSuffix);
      static size_t dataToProcess (const recordList& records);
      static const XSContainer::Weight& statWeight ();
      static void fixOverlap (DataUtility::recordList& records);
      static void fixSpectrumGaps (DataUtility::recordList& records, size_t spectraDefined);
      static void fixDataGroupsVsSpecNum (DataUtility::recordList& records);
      static bool searchRecordListSpecNums (const recordList& records, const size_t specNum, recordListConstIter& currRec, size_t& index);
      static DataPrototype* prototypeFromResponse (string& responseName);
      static void getLostChannelNumbers (const IntegerVector& quality, const IntegerVector& grouping, IntegerVector& lostChannels);
      static void patchGrouping (const IntegerVector& quality, IntegerVector& grouping);
      static void weightScheme (XSContainer::Weight* value);

  public:
    // Additional Public Declarations
      typedef struct bitcard 
      {
	 CodeField ntimes;
	 int flag;
      }  bitCard;

      template<class C, class T> 
      static void fillLostChannels(const IntegerVector& lostChans, 
                        const C& input, C& filled, T defVal);
  protected:
    // Additional Protected Declarations

  private:
      static void makeInputRecords (size_t firstSpectrumNumber, size_t groupNumber, const string& inputString, recordList& inputRecordList, XSutility::fileType defaultSuffix);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      static XSContainer::Weight* s_weightScheme;

    // Additional Implementation Declarations

};
template <class C, class T>
void DataUtility::fillLostChannels(const IntegerVector& lostChans,
                const C& input, C& filled, T defVal)
{
   const size_t sz = lostChans.size();
   if (!sz)
   {
      filled = input;
      return;
   }
   size_t nLost = 0;
   for (size_t i=0; i<sz; ++i)
   {
      nLost += lostChans[i];
   }
   const size_t outSz = input.size() + nLost;
   filled.resize(outSz,0);
   T prevVal = (defVal >= static_cast<T>(0)) ? defVal : static_cast<T>(1);
   size_t idx = 0;
   for (size_t i=0; i<sz; ++i)
   {
      const size_t nInsert = lostChans[i];
      for (size_t j=0; j<nInsert; ++j)
      {
         filled[idx] = prevVal;
         ++idx;
      }
      if (i < sz-1)
      {
         filled[idx] = input[i];
         prevVal = (defVal >= static_cast<T>(0)) ? defVal : input[i];
         ++idx;
      }
   }
}

// Class Utility DataUtility 


#endif
