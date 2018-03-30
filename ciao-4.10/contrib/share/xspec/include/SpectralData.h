//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SPECTRALDATA_H
#define SPECTRALDATA_H 1

#include <sstream>

// xsTypes
#include <xsTypes.h>
// valarray
#include <valarray>
// ctype
#include <ctype.h>
// Error
#include <XSUtil/Error/Error.h>
// Memento
#include <XSModel/GlobalContainer/Memento.h>

class Response;
class UserDummyResponse;
class BackCorr;
class DataSet;
typedef BackCorr Background;
typedef BackCorr Correction;
#include <XSUtil/Utils/XSstream.h>
#include <XSstreams.h>



class SpectralData 
{

  public:



    class NoEnergyRange : public YellowAlert  //## Inherits: <unnamed>%3BDDB9B601EC
    {
      public:
          NoEnergyRange (int spectrumNumber);

      protected:
      private:
      private: //## implementation
    };



    struct FluxCalc 
    {

        // Data Members for Class Attributes
          Real value;
          Real errLow;
          Real errHigh;
          Real photonValue;
          Real photonLow;
          Real photonHigh;
          std::vector<Real> errorTrialVals;

      public:
        // Additional Public Declarations
          FluxCalc (Real val = .0, Real elow = .0, Real ehigh = .0,
                Real pval = .0, Real plow = .0, Real phigh = .0)
            : value(val), errLow(elow), errHigh(ehigh),
              photonValue(pval), photonLow(plow), photonHigh(phigh),
              errorTrialVals() {}
      protected:
        // Additional Protected Declarations

      private:
        // Additional Private Declarations

      private: //## implementation
        // Additional Implementation Declarations

    };



    class SpectralMemento : public XSContainer::Memento  //## Inherits: <unnamed>%41C9DA6D009D
    {

      public:
        // Data Members for Class Attributes
          size_t m_dataGroup;
          string m_dataName;
          std::vector<Response*> m_responses;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          SpectralMemento & operator=(const SpectralMemento &right);

        // Additional Private Declarations

      private: //## implementation
        // Additional Implementation Declarations

    };



    typedef struct { size_t m_firstChan; size_t m_startChan; size_t m_endChan; size_t m_detChans;} ChannelInfo;
      SpectralData (DataSet* parent, size_t channels = 0, size_t rowNumber = 1, size_t sourceNums = 1);
      virtual ~SpectralData();

      void destroy () throw ();
      virtual void closeAncillaryFiles ();
      //	change spectrum number and the number of all the
      //	associated objects.
      void renumber (size_t newIndex);
      void removeResponses (size_t index = 0) throw ();
      Response* detector (size_t index) const;
      void attachDetector (Response* value, size_t index = 0);
      void setChannels (bool value, IntegerArray& range);
      std::vector<RealArray> sensitivity () const;
      bool setBadChannels ();
      void setChannels (bool value, std::pair<Real,Real>& range);
      bool responseLoaded (size_t index = 0);
      void setBackgroundSpectrum (const RealArray& value, bool scaleCounts = false);
      void debugPrint (XSstream& s, const string& type) const;
      void prepareForFit ();
      //	return the energy from the Ebounds array(s)
      //	corresponding to the input channel number. The channel
      //	number is
      //	a non-const reference so the results of the last search
      //	can be reused.
      int energyChannel (const Real& energy, int& channel) const;
      Real channelEnergy (size_t channel);
      //	Expects spectrum already has vector M*R vector, then
      //        combines with background and correction.   This is 
      //        randomized to produce a simulated spectrum and variance 
      //	which are then stored in the class data member arrays.
      void simulateSpectrum(bool useCountingStat);
      void setBackgroundVariance (const RealArray& value);
      void setSpectrum (const RealArray& value, bool scaleCounts = false);
      void computeTotals ();
      bool energiesEqual (SpectralData* right) const;
      void attachUserDummy (UserDummyResponse* dummyResponse, size_t index);
      bool removeUserDummy (size_t index);
      bool removeAllDummies ();
      void setNumberOfChannels (size_t nChans);
      void initializeFake (const SpectralData* origSpectrum);
      RealArray& spectrum ();
      Background* getBackground ();
      bool isDummyrspMode2 (size_t iDet = 0) const;
      void reportNoticed () const;
      void buildIndirectNotice (std::valarray<size_t>& indirectNotice) const;
      void reportKeywords () const;
      void reportRates () const;
      void resetDetsDataGroupNums (size_t dataGroup);
      void initializeFake (const SpectralData::ChannelInfo& chanInfo);
      void reinitFromBackground ();
      void CreateMemento ();
      bool checkForPoisson (const SpectralData* parentSpec = 0);
      void SetMemento ();
      void calcEffectiveAreas ();
      void clearEffectiveAreas ();
      void addToSpectrum (const RealArray& addValue, bool scaleCounts = false);
      void reduceNDets (size_t newNDets);
      void increaseNDets (size_t newNDets);
      void reportPha () const;
      void reportGrouping () const;
      void report (bool orderByFile = true) const;
      Real exposureTime () const;
      void exposureTime (Real value);
      Real correctionScale () const;
      void correctionScale (Real value);
      size_t channels () const;
      void channels (size_t value);
      size_t startChan () const;
      void startChan (size_t value);
      size_t endChan () const;
      void endChan (size_t value);
      const string& telescope () const;
      void telescope (const string& value);
      const string& instrument () const;
      void instrument (const string& value);
      string channelType () const;
      void channelType (string value);
      const string& backgroundFile () const;
      void backgroundFile (const string& value);
      //	Name of the file stem from which the data were read
      //	(i.e. without the fits,pha,rmf,arf,bck,cor ...
      //	extension).
      const string& correctionFile () const;
      void correctionFile (const string& value);
      size_t spectrumNumber () const;
      void spectrumNumber (size_t value);
      size_t plotGroup () const;
      void plotGroup (size_t value);
      Real netFlux () const;
      void netFlux (Real value);
      Real totalFlux () const;
      void totalFlux (Real value);
      Real netVariance () const;
      void netVariance (Real value);
      const CodeContainer& gqString () const;
      void gqString (const CodeContainer& value);
      const size_t firstChan () const;
      void firstChan (size_t value);
      size_t rowNumber () const;
      bool spectrumIsZeroed () const;
      const SpectralData::FluxCalc& lastEqWidthCalc () const;
      void lastEqWidthCalc (const SpectralData::FluxCalc& value);
      const bool backgroundChanged () const;
      void backgroundChanged (bool value);
      const bool correctionChanged () const;
      void correctionChanged (bool value);
      const DataSet* parent () const;
      void parent (DataSet* value);
      bool isPoisson () const;
      void isPoisson (bool value);
      const RealArray& effectiveAreas () const;

      const string& statName() const;
      void statName(const string& value);
      const string& testStatName() const;
      void testStatName(const string& value);
      //	Plot x-axis setting which is needed here for purposes of
      //	evaluating ignore/notice.  chan = 0, energy = 1, wave =
      //	2 (The PlotTypes.h enumerators can't be seen from this
      //	library.)
      static void chanEngWave (int value);
      //	Units conversion factor relative to keV, set from
      //	setplot handler and needed for ignore/notice.
      static void engUnits (Real value);
      //	Units conversion factor relative to Angstroms, set from
      //	setplot handler and needed for ignore/notice.
      static void waveUnits (Real value);
      const Background* background () const;
      void background (Background* value);
      const Correction* correction () const;
      void correction (Correction* value);
      const RealArray& rawVariance () const;
      void setRawVariance (const RealArray& value);
      Real rawVariance (size_t index) const;
      void rawVariance (size_t index, Real value);
      const BoolArray& noticedChannels () const;
      void setNoticedChannels (const BoolArray& value);
      bool noticedChannels (size_t index) const;
      void noticedChannels (size_t index, bool value);
      const RealArray& variance () const;
      void setVariance (const RealArray& value);
      Real variance (size_t index) const;
      void variance (size_t index, Real value);
      const RealArray& spectrum () const;
      Real spectrum (size_t index) const;
      void spectrum (size_t index, Real value);
      const std::vector<Response*>& detector () const;
      void setDetector (const std::vector<Response*>& value);
      const std::valarray< size_t >& indirectNotice () const;
      const RealArray& areaScale () const;
      void setAreaScale (const RealArray& value);
      Real areaScale (size_t index) const;
      void areaScale (size_t index, Real value);
      const RealArray& backgroundScale () const;
      void setBackgroundScale (const RealArray& value);
      Real backgroundScale (size_t index) const;
      void backgroundScale (size_t index, Real value);
      const IntegerArray& quality () const;
      void setQuality (const IntegerArray& value);
      int quality (size_t index) const;
      void quality (size_t index, int value);
      const IntegerArray& qualityInfo () const;
      void setQualityInfo (const IntegerArray& value);
      int qualityInfo (size_t index) const;
      void qualityInfo (size_t index, int value);
      const IntegerArray& groupingInfo () const;
      void setGroupingInfo (const IntegerArray& value);
      int groupingInfo (size_t index) const;
      void groupingInfo (size_t index, int value);
      const Response* responseHooks (size_t index) const;
      const std::vector<bool>& responseChanged () const;
      void setResponseChanged (const std::vector<bool>& value);
      bool responseChanged (size_t index) const;
      void responseChanged (size_t index, bool value);
      const std::map<string, Real>& xflt () const;
      void setxflt (size_t key, Real value);
      void setxflt (string key, Real value);
      void setxflt (string keyvalue);
      void setxflt (const std::map<string, Real>& value);
      Real xflt (size_t key) const;
      Real xflt (string key) const;
      bool inxflt (size_t key) const;
      bool inxflt (string key) const;
      const std::vector<bool>& arfChanged () const;
      void setArfChanged (const std::vector<bool>& value);
      bool arfChanged (size_t index) const;
      void arfChanged (size_t index, bool value);
      const std::vector<FluxCalc>& lastModelFluxCalc () const;
      void setLastModelFluxCalc (const std::vector<FluxCalc>& value);
      const SpectralData::FluxCalc& lastModelFluxCalc (size_t index) const;
      void lastModelFluxCalc (size_t index, const SpectralData::FluxCalc& value);
      const std::vector<FluxCalc>& lastModelLuminCalc () const;
      void setLastModelLuminCalc (const std::vector<FluxCalc>& value);
      const SpectralData::FluxCalc& lastModelLuminCalc (size_t index) const;
      void lastModelLuminCalc (size_t index, const SpectralData::FluxCalc& value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      SpectralData(const SpectralData &right);
      SpectralData & operator=(const SpectralData &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_exposureTime;
      Real m_correctionScale;
      size_t m_channels;
      size_t m_startChan;
      size_t m_endChan;
      string m_telescope;
      string m_instrument;
      string m_channelType;
      string m_backgroundFile;
      string m_correctionFile;
      size_t m_spectrumNumber;
      size_t m_plotGroup;
      Real m_netFlux;
      Real m_totalFlux;
      Real m_netVariance;
      CodeContainer m_gqString;
      size_t m_firstChan;
      size_t m_rowNumber;
      bool m_spectrumIsZeroed;
      SpectralData::FluxCalc m_lastEqWidthCalc;
      bool m_backgroundChanged;
      bool m_correctionChanged;
      DataSet* m_parent;
      SpectralData::SpectralMemento* m_memento;
      bool m_isPoisson;
      RealArray m_effectiveAreas;

      string m_statName;
      string m_testStatName;
      static int s_chanEngWave;
      static Real s_engUnits;
      static Real s_waveUnits;

    // Data Members for Associations
      Background* m_background;
      Correction* m_correction;
      RealArray m_rawVariance;
      BoolArray m_noticedChannels;
      RealArray m_variance;
      RealArray m_spectrum;
      std::vector<Response*> m_detector;
      std::valarray< size_t > m_indirectNotice;
      RealArray m_areaScale;
      RealArray m_backgroundScale;
      IntegerArray m_quality;
      IntegerArray m_qualityInfo;
      IntegerArray m_groupingInfo;
      std::vector<Response*> m_responseHooks;
      std::vector<bool> m_responseChanged;
      std::map<string, Real> m_xflt;
      std::vector<bool> m_arfChanged;
      std::vector<FluxCalc> m_lastModelFluxCalc;
      std::vector<FluxCalc> m_lastModelLuminCalc;

    // Additional Implementation Declarations

};

// Class SpectralData::NoEnergyRange 

// Class SpectralData::FluxCalc 

// Class SpectralData::SpectralMemento 

// Class SpectralData 

inline RealArray& SpectralData::spectrum ()
{
   return m_spectrum;
}

inline Background* SpectralData::getBackground ()
{
   return m_background;
}

inline Real SpectralData::exposureTime () const
{
  return m_exposureTime;
}

inline void SpectralData::exposureTime (Real value)
{
  m_exposureTime = value;
}

inline Real SpectralData::correctionScale () const
{
  return m_correctionScale;
}

inline void SpectralData::correctionScale (Real value)
{
  m_correctionScale = value;
}

inline size_t SpectralData::channels () const
{
  return m_channels;
}

inline void SpectralData::channels (size_t value)
{
  m_channels = value;
}

inline size_t SpectralData::startChan () const
{
  return m_startChan;
}

inline void SpectralData::startChan (size_t value)
{
  m_startChan = value;
}

inline size_t SpectralData::endChan () const
{
  return m_endChan;
}

inline void SpectralData::endChan (size_t value)
{
  m_endChan = value;
}

inline const string& SpectralData::telescope () const
{
  return m_telescope;
}

inline void SpectralData::telescope (const string& value)
{
  m_telescope = value;
}

inline const string& SpectralData::instrument () const
{
  return m_instrument;
}

inline void SpectralData::instrument (const string& value)
{
  m_instrument = value;
}

inline string SpectralData::channelType () const
{
  return m_channelType;
}

inline void SpectralData::channelType (string value)
{
  m_channelType = value;
}

inline const string& SpectralData::backgroundFile () const
{
  return m_backgroundFile;
}

inline void SpectralData::backgroundFile (const string& value)
{
  m_backgroundFile = value;
}

inline const string& SpectralData::correctionFile () const
{
  return m_correctionFile;
}

inline void SpectralData::correctionFile (const string& value)
{
  m_correctionFile = value;
}

inline size_t SpectralData::spectrumNumber () const
{
  return m_spectrumNumber;
}

inline void SpectralData::spectrumNumber (size_t value)
{
  m_spectrumNumber = value;
}

inline size_t SpectralData::plotGroup () const
{
  return m_plotGroup;
}

inline void SpectralData::plotGroup (size_t value)
{
  m_plotGroup = value;
}

inline Real SpectralData::netFlux () const
{
  return m_netFlux;
}

inline void SpectralData::netFlux (Real value)
{
  m_netFlux = value;
}

inline Real SpectralData::totalFlux () const
{
  return m_totalFlux;
}

inline void SpectralData::totalFlux (Real value)
{
  m_totalFlux = value;
}

inline Real SpectralData::netVariance () const
{
  return m_netVariance;
}

inline void SpectralData::netVariance (Real value)
{
  m_netVariance = value;
}

inline const CodeContainer& SpectralData::gqString () const
{
  return m_gqString;
}

inline void SpectralData::gqString (const CodeContainer& value)
{
  m_gqString = value;
}

inline const size_t SpectralData::firstChan () const
{
  return m_firstChan;
}

inline void SpectralData::firstChan (size_t value)
{
  m_firstChan = value;
}

inline size_t SpectralData::rowNumber () const
{
  return m_rowNumber;
}

inline bool SpectralData::spectrumIsZeroed () const
{
  return m_spectrumIsZeroed;
}

inline const SpectralData::FluxCalc& SpectralData::lastEqWidthCalc () const
{
  return m_lastEqWidthCalc;
}

inline void SpectralData::lastEqWidthCalc (const SpectralData::FluxCalc& value)
{
  m_lastEqWidthCalc = value;
}

inline const bool SpectralData::backgroundChanged () const
{
  return m_backgroundChanged;
}

inline void SpectralData::backgroundChanged (bool value)
{
  m_backgroundChanged = value;
}

inline const bool SpectralData::correctionChanged () const
{
  return m_correctionChanged;
}

inline void SpectralData::correctionChanged (bool value)
{
  m_correctionChanged = value;
}

inline const DataSet* SpectralData::parent () const
{
  return m_parent;
}

inline void SpectralData::parent (DataSet* value)
{
  m_parent = value;
}

inline bool SpectralData::isPoisson () const
{
  return m_isPoisson;
}

inline void SpectralData::isPoisson (bool value)
{
  m_isPoisson = value;
}

inline const RealArray& SpectralData::effectiveAreas () const
{
  return m_effectiveAreas;
}

inline const string& SpectralData::statName() const
{
   return m_statName;
}

inline void SpectralData::statName(const string& value)
{
   m_statName = value;
}

inline const string& SpectralData::testStatName() const
{
   return m_testStatName;
}

inline void SpectralData::testStatName(const string& value)
{
   m_testStatName = value;
}

inline void SpectralData::chanEngWave (int value)
{
  s_chanEngWave = value;
}

inline void SpectralData::engUnits (Real value)
{
  s_engUnits = value;
}

inline void SpectralData::waveUnits (Real value)
{
  s_waveUnits = value;
}

inline const Background* SpectralData::background () const
{
  return m_background;
}

inline const Correction* SpectralData::correction () const
{
  return m_correction;
}

inline const RealArray& SpectralData::rawVariance () const
{
  return m_rawVariance;
}

inline void SpectralData::setRawVariance (const RealArray& value)
{
  size_t N(value.size());
  if (m_rawVariance.size() != N) m_rawVariance.resize(N);
  m_rawVariance = value;
}

inline Real SpectralData::rawVariance (size_t index) const
{
  return m_rawVariance[index];
}

inline void SpectralData::rawVariance (size_t index, Real value)
{
  m_rawVariance[index] = value;
}

inline const BoolArray& SpectralData::noticedChannels () const
{
  return m_noticedChannels;
}

inline void SpectralData::setNoticedChannels (const BoolArray& value)
{
  m_noticedChannels = value;
}

inline bool SpectralData::noticedChannels (size_t index) const
{
  return m_noticedChannels[index];
}

inline void SpectralData::noticedChannels (size_t index, bool value)
{
  m_noticedChannels[index] = value;
}

inline const RealArray& SpectralData::variance () const
{
  return m_variance;
}

inline void SpectralData::setVariance (const RealArray& value)
{
  m_variance.resize(value.size());
  m_variance = value;
}

inline Real SpectralData::variance (size_t index) const
{
  return m_variance[index];
}

inline void SpectralData::variance (size_t index, Real value)
{
  m_variance[index] = value;
}

inline const RealArray& SpectralData::spectrum () const
{
  return m_spectrum;
}

inline Real SpectralData::spectrum (size_t index) const
{
  return m_spectrum[index];
}

inline void SpectralData::spectrum (size_t index, Real value)
{
  m_spectrum[index] = value;
}

inline const std::vector<Response*>& SpectralData::detector () const
{
  return m_detector;
}

inline void SpectralData::setDetector (const std::vector<Response*>& value)
{
  m_detector = value;
}

inline const std::valarray< size_t >& SpectralData::indirectNotice () const
{
  return m_indirectNotice;
}

inline const RealArray& SpectralData::areaScale () const
{
  return m_areaScale;
}

inline void SpectralData::setAreaScale (const RealArray& value)
{
  m_areaScale.resize(value.size());
  m_areaScale = value;
}

inline Real SpectralData::areaScale (size_t index) const
{
  return m_areaScale[index];
}

inline void SpectralData::areaScale (size_t index, Real value)
{
  m_areaScale[index] = value;
}

inline const RealArray& SpectralData::backgroundScale () const
{
  return m_backgroundScale;
}

inline void SpectralData::setBackgroundScale (const RealArray& value)
{
  m_backgroundScale.resize(value.size());
  m_backgroundScale = value;
}

inline Real SpectralData::backgroundScale (size_t index) const
{
  return m_backgroundScale[index];
}

inline void SpectralData::backgroundScale (size_t index, Real value)
{
  m_backgroundScale[index] = value;
}

inline const IntegerArray& SpectralData::quality () const
{
  return m_quality;
}

inline void SpectralData::setQuality (const IntegerArray& value)
{
  m_quality = value;
}

inline int SpectralData::quality (size_t index) const
{
  return m_quality[index];
}

inline void SpectralData::quality (size_t index, int value)
{
  m_quality[index] = value;
}

inline const IntegerArray& SpectralData::qualityInfo () const
{
  return m_qualityInfo;
}

inline void SpectralData::setQualityInfo (const IntegerArray& value)
{
  m_qualityInfo = value;
}

inline int SpectralData::qualityInfo (size_t index) const
{
  return m_qualityInfo[index];
}

inline void SpectralData::qualityInfo (size_t index, int value)
{
  m_qualityInfo[index] = value;
}

inline const IntegerArray& SpectralData::groupingInfo () const
{
  return m_groupingInfo;
}

inline void SpectralData::setGroupingInfo (const IntegerArray& value)
{
  m_groupingInfo = value;
}

inline int SpectralData::groupingInfo (size_t index) const
{
  return m_groupingInfo[index];
}

inline void SpectralData::groupingInfo (size_t index, int value)
{
  m_groupingInfo[index] = value;
}

inline const Response* SpectralData::responseHooks (size_t index) const
{
  return m_responseHooks[index];
}

inline const std::vector<bool>& SpectralData::responseChanged () const
{
  return m_responseChanged;
}

inline void SpectralData::setResponseChanged (const std::vector<bool>& value)
{
  m_responseChanged = value;
}

inline bool SpectralData::responseChanged (size_t index) const
{
  return m_responseChanged[index];
}

inline void SpectralData::responseChanged (size_t index, bool value)
{
  m_responseChanged[index] = value;
}

inline const std::map<string, Real>& SpectralData::xflt () const
{
  return m_xflt;
}

inline void SpectralData::setxflt (size_t key, Real value)
{
  // convert the size_t key into the corresponding string
  std::ostringstream keystream;
  keystream << "key" << key;
  m_xflt[keystream.str()] = value;
}

inline void SpectralData::setxflt (string key, Real value)
{
  m_xflt[key] = value;
}

inline void SpectralData::setxflt (string keyvalue)
{
  // split keyvalue into its two parts
  size_t ipos = keyvalue.find(":");
  string key;
  Real value;
  if ( ipos != string::npos ) {
    key = keyvalue.substr(0,ipos);
    std::stringstream valstream;
    valstream << keyvalue.substr(ipos+1,string::npos);
    valstream >> value;
    m_xflt[key] = value;
  }
}

inline void SpectralData::setxflt (const std::map<string, Real>& value)
{
  m_xflt = value;
}

inline Real SpectralData::xflt (size_t key) const
{
  // convert the size_t key into the corresponding string
  std::ostringstream keystream;
  keystream << "key" << key;

  return xflt(keystream.str());
}

inline Real SpectralData::xflt (string key) const
{
    using namespace std;

    map<string, Real>::const_iterator match = m_xflt.find(key);

    if(match != m_xflt.end()) 
	return match->second;
    else
	return -1.2e34;
}

inline bool SpectralData::inxflt (size_t key) const
{
  // convert the size_t key into the corresponding string
  std::ostringstream keystream;
  keystream << "key" << key;

  return inxflt(keystream.str());
}

inline bool SpectralData::inxflt (string key) const
{
    if ( m_xflt.count(key) > 0 ) {
      return true;
    } else {
      return false;
    }
}

inline const std::vector<bool>& SpectralData::arfChanged () const
{
  return m_arfChanged;
}

inline void SpectralData::setArfChanged (const std::vector<bool>& value)
{
  m_arfChanged = value;
}

inline bool SpectralData::arfChanged (size_t index) const
{
  return m_arfChanged[index];
}

inline void SpectralData::arfChanged (size_t index, bool value)
{
  m_arfChanged[index] = value;
}

inline const std::vector<SpectralData::FluxCalc>& SpectralData::lastModelFluxCalc () const
{
  return m_lastModelFluxCalc;
}

inline void SpectralData::setLastModelFluxCalc (const std::vector<SpectralData::FluxCalc>& value)
{
  m_lastModelFluxCalc = value;
}

inline const SpectralData::FluxCalc& SpectralData::lastModelFluxCalc (size_t index) const
{
  return m_lastModelFluxCalc[index];
}

inline void SpectralData::lastModelFluxCalc (size_t index, const SpectralData::FluxCalc& value)
{
  m_lastModelFluxCalc[index] = value;
}

inline const std::vector<SpectralData::FluxCalc>& SpectralData::lastModelLuminCalc () const
{
  return m_lastModelLuminCalc;
}

inline void SpectralData::setLastModelLuminCalc (const std::vector<SpectralData::FluxCalc>& value)
{
  m_lastModelLuminCalc = value;
}

inline const SpectralData::FluxCalc& SpectralData::lastModelLuminCalc (size_t index) const
{
  return m_lastModelLuminCalc[index];
}

inline void SpectralData::lastModelLuminCalc (size_t index, const SpectralData::FluxCalc& value)
{
  m_lastModelLuminCalc[index] = value;
}


#endif
