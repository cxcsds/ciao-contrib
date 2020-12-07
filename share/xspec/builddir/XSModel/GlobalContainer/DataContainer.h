//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATACONTAINER_H
#define DATACONTAINER_H 1

// xsTypes
#include <xsTypes.h>
// ctype
#include <ctype.h>
// map
#include <map>
// DataSet
#include <XSModel/Data/DataSet.h>
// Error
#include <XSUtil/Error/Error.h>
// Observer
#include <XSUtil/Utils/Observer.h>
// DataUtility
#include <XSModel/Data/DataUtility.h>
// XspecRegistry
#include <XSModel/DataFactory/XspecRegistry.h>
// DataSetTypes
#include <XSModel/GlobalContainer/DataSetTypes.h>
#include <set>

namespace XSContainer {
    //	Singleton Class containing entire data structure.
    //	     No Copy, assignment or Equality operators.
    //	Implemented as a list of data groups.



    class DataContainer : public Subject  //## Inherits: <unnamed>%3C72CDB400F1
    {

      public:
        //	Exception to be thrown by lookup failures.



        class NoSuchSpectrum : public YellowAlert  //## Inherits: <unnamed>%3BD980FF017A
        {
          public:
              NoSuchSpectrum (int number);

          protected:
          private:
          private: //## implementation
        };


        class DataGroupHistory 
        {

          public:
              DataGroupHistory();
              ~DataGroupHistory();

              void initOldArray (size_t nGroups);
              void swapHistory ();
              void reassign (size_t oldVal, size_t newVal);
              size_t getReassignment (size_t oldVal) const;
              size_t getOriginal (size_t newVal) const;
              void createReverseLookup (size_t nGroups);
              void erase ();
              bool isEmpty ();

            // Additional Public Declarations

          protected:
            // Additional Protected Declarations

          private:
              DataGroupHistory(const DataGroupHistory &right);
              DataGroupHistory & operator=(const DataGroupHistory &right);

            // Additional Private Declarations

          private: //## implementation
            // Data Members for Class Attributes
              std::vector<size_t> m_reassignment;
              std::vector<size_t> m_reverseLookup;

            // Additional Implementation Declarations

        };
          ~DataContainer();

          static DataContainer* Instance ();
          void plot (const string& dataSet, const string& args);
          void addToList (DataSet* newDataSet);
          SpectralData* lookup (size_t spectrumNumber) const;
          std::vector<bool> insertAndDelete (DataUtility::recordList& records, size_t spectraDefined, bool preserve);
          void clear ();
          void deleteRange (size_t begin, size_t end);
          void deleteRange (const std::vector<bool>& marked, bool preserve = false);
          DataSet* dataArray (const string& name, size_t index) const;
          void ignoreBadChannels ();
          void setChannels (bool value, IntegerVector& channelRange, IntegerVector& spectrumRange);
          void setChannels (bool value, std::pair<Real,Real>& realRange, IntegerVector& spectrumRange);
          void saveData (std::ostream& s, const string& defaultStat);
          void dataArray (const std::string& name, DataSet* value);
          DataSet* dataSetLookup (size_t specNum, size_t& row) const;
          void renumberPlotGroups (size_t specNum, size_t high);
          bool resetDetectors (const IntegerVector& spectra);
          void saveIgnoredChannels (const DataSet* pDataSet, const SpectralData* pSData, std::ostringstream& ignoreInfo);
          DataArray& dataArray ();
          void verifySpectrumRange ();
          void countPlotGroups ();
          bool adjustNumSources (size_t addedSourceNum);
          void determineDgSourceRelations ();
          size_t getLowestGroupForSource (size_t source) const;
          size_t getNumberOfGroupsForSource (size_t sourceNum) const;
          void showData (bool isAll) const;
          size_t numberOfSpectra () const;
          void numberOfSpectra (size_t value);
          size_t numberOfGroups () const;
          size_t numSourcesForSpectra () const;
          size_t numberOfPlotGroups () const;
          const std::pair<Real,Real>& realRange () const;
          void setRealRange (const std::pair<Real,Real>& value);
          DataContainer::DataGroupHistory& dgHistory ();
          const std::map<size_t, std::set<size_t> >& dgToSources () const;
          const std::map<size_t, std::map<size_t,size_t> >& sourceToDgs () const;
          const IntegerVector& integerRange () const;
          void setIntegerRange (const IntegerVector& value);
          const IntegerVector& spectrumRange () const;
          void setSpectrumRange (const IntegerVector& value);
          const DataArray& dataArray () const;
          const IntegerVector& plotGroupNums () const;
          void setPlotGroupNums (const IntegerVector& value);
          int plotGroupNums (size_t index) const;
          void setPlotGroupNums (size_t index, int value);

      public:
        // Additional Public Declarations

      protected:
          DataContainer();

        // Additional Protected Declarations

      private:
          void enumerateSpectra ();
          void removeNumberedSpectrum (size_t index, bool remove = false);
          void renumberSpectra (size_t start, int offset = -1);
          void enumerateGroups ();
          bool firstInPlotGroup (size_t specNum);
          static void examineResponse (const std::vector<const SpectralData*>& spectra, std::ostream& outFile, string& currentDir);
          void bundleSpectra (const IntegerVector& specRanges, std::vector<SpectralData*>& spectra) const;
          void fixDataGroupGaps ();
          static void examineArf (const std::vector<const SpectralData*>& spectra, std::ostream& outFile, string& currentDir);
          static void examineBackCorr (const std::vector<const SpectralData*>& spectra, std::ostream& outFile, bool isBack, string& currentDir);
          void bundleSpectra ();
          void reinsertSpectrum (SpectralData* s);
          void examineResponseFunctions (const SpectralData* spectrum, std::ostringstream& respFuncs, std::ostringstream& respParLinks);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          static DataContainer* s_instance;
          mutable size_t m_numberOfSpectra;
          mutable size_t m_numberOfGroups;
          mutable size_t m_numSourcesForSpectra;
          size_t m_numberOfPlotGroups;
          std::pair<Real,Real> m_realRange;
          std::vector<SpectralData*> m_bundledSpectra;
          DataContainer::DataGroupHistory m_dgHistory;
          std::map<size_t, std::set<size_t> > m_dgToSources;
          std::map<size_t, std::map<size_t,size_t> > m_sourceToDgs;

        // Data Members for Associations
          IntegerVector m_integerRange;
          IntegerVector m_spectrumRange;
          DataArray m_dataArray;
          IntegerVector m_plotGroupNums;

        // Additional Implementation Declarations

    };

    // Class XSContainer::DataContainer::NoSuchSpectrum 

    // Class XSContainer::DataContainer::DataGroupHistory 

    // Class XSContainer::DataContainer 

    inline size_t DataContainer::numberOfSpectra () const
    {
      return m_numberOfSpectra;
    }

    inline void DataContainer::numberOfSpectra (size_t value)
    {
      m_numberOfSpectra = value;
    }

    inline size_t DataContainer::numberOfGroups () const
    {
      return m_numberOfGroups;
    }

    inline size_t DataContainer::numSourcesForSpectra () const
    {
      return m_numSourcesForSpectra;
    }

    inline size_t DataContainer::numberOfPlotGroups () const
    {
      return m_numberOfPlotGroups;
    }

    inline const std::pair<Real,Real>& DataContainer::realRange () const
    {
      return m_realRange;
    }

    inline void DataContainer::setRealRange (const std::pair<Real,Real>& value)
    {
      m_realRange.first = value.first;
      m_realRange.second = value.second;
    }

    inline DataContainer::DataGroupHistory& DataContainer::dgHistory ()
    {
      return m_dgHistory;
    }

    inline const std::map<size_t, std::set<size_t> >& DataContainer::dgToSources () const
    {
      return m_dgToSources;
    }

    inline const std::map<size_t, std::map<size_t,size_t> >& DataContainer::sourceToDgs () const
    {
      return m_sourceToDgs;
    }

    inline const IntegerVector& DataContainer::integerRange () const
    {
      return m_integerRange;
    }

    inline void DataContainer::setIntegerRange (const IntegerVector& value)
    {
      m_integerRange = value;
    }

    inline const IntegerVector& DataContainer::spectrumRange () const
    {
      return m_spectrumRange;
    }

    inline void DataContainer::setSpectrumRange (const IntegerVector& value)
    {
      m_spectrumRange = value;
    }

    inline const DataArray& DataContainer::dataArray () const
    {
      return m_dataArray;
    }

    inline const IntegerVector& DataContainer::plotGroupNums () const
    {
      return m_plotGroupNums;
    }

    inline void DataContainer::setPlotGroupNums (const IntegerVector& value)
    {
      m_plotGroupNums = value;
    }

    inline int DataContainer::plotGroupNums (size_t index) const
    {
      return m_plotGroupNums[index];
    }

} // namespace XSContainer


#endif
