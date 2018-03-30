//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ResponseMatrix_H
#define ResponseMatrix_H 1

// xsTypes
#include <xsTypes.h>
// XSutility
#include <XSUtil/Utils/XSutility.h>
// Reference
#include <XSUtil/Utils/Reference.h>




class ResponseMatrix : public RefCounter  //## Inherits: <unnamed>%3A77254C03AC
{

  public:



    struct ChanRangeIndicators 
    {
        // Data Members for Class Attributes
          int firstChan;
          int startChan;
          int endChan;

      public:
      protected:
      private:
      private: //## implementation
    };



    typedef long long RMFLONG;
      ResponseMatrix(const ResponseMatrix &right);
      ResponseMatrix (const ResponseMatrix::ChanRangeIndicators& chanLimits, size_t nE = 0, size_t nC = 0, const string& id = "", const CodeContainer& gqString = CodeContainer(), bool retainPositionArray = false);
      virtual ~ResponseMatrix();
      int operator==(const ResponseMatrix &right) const;

      int operator!=(const ResponseMatrix &right) const;

      ResponseMatrix* clone () const;
      void createConvolutionArray ();
      void compressRmfRow (const size_t row, const size_t groupedResponseChannels, const RealArray& rmfRow);
      void expandRmfRow (const size_t row, size_t& maxChans, size_t& numChannels, RealArray &rmfRow);
      void normalizeRMF ();
      bool gqMatch (const CodeContainer& value) const;
      void decodeGQ (IntegerArray& group, IntegerArray& quality);
      Real* convArray ();
      Real convArray (size_t index);
      bool compareChanRange (int firstChan, int startChan, int endChan) const;
      Real eMin () const;
      void eMin (Real value);
      Real eMax () const;
      void eMax (Real value);
      const string& name () const;
      const CodeContainer& gqString () const;
      void gqString (const CodeContainer& value);
      const string& telescope () const;
      void telescope (const string& value);
      const string& instrument () const;
      void instrument (const string& value);
      const string& channelType () const;
      void channelType (const string& value);
      const size_t convArraySize () const;
      int detectorChannels () const;
      RealArray& energyHigh ();
      const Real energyHigh (size_t bin) const;
      void energyHigh (size_t bin, Real value);
      RealArray& energyLow ();
      const Real energyLow (size_t bin) const;
      void energyLow (size_t bin, Real value);
      MatrixIndex& binStart ();
      const IntegerArray& binStart (size_t bin) const;
      void binStart (size_t bin, const IntegerArray& value);
      MatrixIndex& binRunLengths ();
      const IntegerArray& binRunLengths (size_t len) const;
      void binRunLengths (size_t len, const IntegerArray& value);
      const RealArray& eboundsMin () const;
      void setEboundsMin (const RealArray& value);
      Real eboundsMin (size_t bin) const;
      void eboundsMin (size_t bin, Real value);
      const RealArray& eboundsMax () const;
      void setEboundsMax (const RealArray& value);
      Real eboundsMax (size_t bin) const;
      void eboundsMax (size_t bin, Real value);
      MatrixValue& matrixValue ();
      void setMatrixValue (const MatrixValue& value);
      const RealArray& normFactor () const;
      Real normFactor (size_t bin) const;
      IntegerArray& binResponseGroups ();
      int binResponseGroups (size_t index) const;
      void binResponseGroups (size_t index, int value);
      const IntegerArray& channelForRun () const;
      void setChannelForRun (const IntegerArray& value);
      int channelForRun (size_t index) const;
      void channelForRun (size_t index, int value);
      const IntegerArray& energyRunLengths () const;
      void setEnergyRunLengths (const IntegerArray& value);
      int energyRunLengths (size_t index) const;
      void energyRunLengths (size_t index, int value);
      const IntegerArray& energyStart () const;
      void setEnergyStart (const IntegerArray& value);
      int energyStart (size_t index) const;
      void energyStart (size_t index, int value);
      const std::vector<RMFLONG>& positions () const;
      void setPositions (const std::vector<RMFLONG>& value);
      RMFLONG positions (size_t index) const;
      void positions (size_t index, RMFLONG value);

  public:
    // Additional Public Declarations

  protected:
      virtual bool compare (const ResponseMatrix& right) const;

    // Additional Protected Declarations

  private:
      ResponseMatrix & operator=(const ResponseMatrix &right);
      const bool retainPosition () const;
      void retainPosition (bool value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_eMin;
      Real m_eMax;
      string m_name;
      CodeContainer m_gqString;
      string m_telescope;
      string m_instrument;
      string m_channelType;
      bool m_retainPosition;
      size_t m_convArraySize;
      int m_detectorChannels;
      ResponseMatrix::ChanRangeIndicators m_chanRangeIndicator;

    // Data Members for Associations
      RealArray m_energyHigh;
      RealArray m_energyLow;
      MatrixIndex m_binStart;
      MatrixIndex m_binRunLengths;
      RealArray m_eboundsMin;
      RealArray m_eboundsMax;
      MatrixValue m_matrixValue;
      RealArray m_normFactor;
      XSutility::auto_array_ptr< Real > m_convArray;
      IntegerArray m_binResponseGroups;
      IntegerArray m_channelForRun;
      IntegerArray m_energyRunLengths;
      IntegerArray m_energyStart;
      std::vector<RMFLONG> m_positions;

    // Additional Implementation Declarations

};

// Class ResponseMatrix::ChanRangeIndicators 

// Class ResponseMatrix 

inline Real ResponseMatrix::eMin () const
{
  return m_eMin;
}

inline void ResponseMatrix::eMin (Real value)
{
  m_eMin = value;
}

inline Real ResponseMatrix::eMax () const
{
  return m_eMax;
}

inline void ResponseMatrix::eMax (Real value)
{
  m_eMax = value;
}

inline const string& ResponseMatrix::name () const
{
  return m_name;
}

inline const CodeContainer& ResponseMatrix::gqString () const
{
  return m_gqString;
}

inline void ResponseMatrix::gqString (const CodeContainer& value)
{
  m_gqString = value;
}

inline const string& ResponseMatrix::telescope () const
{
  return m_telescope;
}

inline void ResponseMatrix::telescope (const string& value)
{
  m_telescope = value;
}

inline const string& ResponseMatrix::instrument () const
{
  return m_instrument;
}

inline void ResponseMatrix::instrument (const string& value)
{
  m_instrument = value;
}

inline const string& ResponseMatrix::channelType () const
{
  return m_channelType;
}

inline void ResponseMatrix::channelType (const string& value)
{
  m_channelType = value;
}

inline const bool ResponseMatrix::retainPosition () const
{
  return m_retainPosition;
}

inline void ResponseMatrix::retainPosition (bool value)
{
  m_retainPosition = value;
}

inline const size_t ResponseMatrix::convArraySize () const
{
  return m_convArraySize;
}

inline int ResponseMatrix::detectorChannels () const
{
  return m_detectorChannels;
}

inline RealArray& ResponseMatrix::energyHigh ()
{
  return m_energyHigh;
}

inline const Real ResponseMatrix::energyHigh (size_t bin) const
{
  return m_energyHigh[bin];
}

inline void ResponseMatrix::energyHigh (size_t bin, Real value)
{
  m_energyHigh[bin] = value;
}

inline RealArray& ResponseMatrix::energyLow ()
{
  return m_energyLow;
}

inline const Real ResponseMatrix::energyLow (size_t bin) const
{
  return m_energyLow[bin];
}

inline void ResponseMatrix::energyLow (size_t bin, Real value)
{
  m_energyLow[bin] = value;
}

inline MatrixIndex& ResponseMatrix::binStart ()
{
  return m_binStart;
}

inline const IntegerArray& ResponseMatrix::binStart (size_t bin) const
{
  return m_binStart[bin];
}

inline void ResponseMatrix::binStart (size_t bin, const IntegerArray& value)
{
  m_binStart[bin] = value;
}

inline MatrixIndex& ResponseMatrix::binRunLengths ()
{
  return m_binRunLengths;
}

inline const IntegerArray& ResponseMatrix::binRunLengths (size_t len) const
{
  return m_binRunLengths[len];
}

inline void ResponseMatrix::binRunLengths (size_t len, const IntegerArray& value)
{
  m_binRunLengths[len] = value;
}

inline const RealArray& ResponseMatrix::eboundsMin () const
{
  return m_eboundsMin;
}

inline void ResponseMatrix::setEboundsMin (const RealArray& value)
{
  m_eboundsMin.resize(value.size());
  m_eboundsMin = value;
}

inline Real ResponseMatrix::eboundsMin (size_t bin) const
{
  return m_eboundsMin[bin];
}

inline void ResponseMatrix::eboundsMin (size_t bin, Real value)
{
  m_eboundsMin[bin] = value;
}

inline const RealArray& ResponseMatrix::eboundsMax () const
{
  return m_eboundsMax;
}

inline void ResponseMatrix::setEboundsMax (const RealArray& value)
{
  m_eboundsMax.resize(value.size());
  m_eboundsMax = value;
}

inline Real ResponseMatrix::eboundsMax (size_t bin) const
{
  return m_eboundsMax[bin];
}

inline void ResponseMatrix::eboundsMax (size_t bin, Real value)
{
  m_eboundsMax[bin] = value;
}

inline MatrixValue& ResponseMatrix::matrixValue ()
{
  return m_matrixValue;
}

inline void ResponseMatrix::setMatrixValue (const MatrixValue& value)
{
  m_matrixValue.resize(value.size());
  m_matrixValue = value;
}

inline const RealArray& ResponseMatrix::normFactor () const
{
  return m_normFactor;
}

inline Real ResponseMatrix::normFactor (size_t bin) const
{
  return m_normFactor[bin];
}

inline IntegerArray& ResponseMatrix::binResponseGroups ()
{
  return m_binResponseGroups;
}

inline int ResponseMatrix::binResponseGroups (size_t index) const
{
  return m_binResponseGroups[index];
}

inline void ResponseMatrix::binResponseGroups (size_t index, int value)
{
  m_binResponseGroups[index] = value;
}

inline const IntegerArray& ResponseMatrix::channelForRun () const
{
  return m_channelForRun;
}

inline void ResponseMatrix::setChannelForRun (const IntegerArray& value)
{
  m_channelForRun = value;
}

inline int ResponseMatrix::channelForRun (size_t index) const
{
  return m_channelForRun[index];
}

inline void ResponseMatrix::channelForRun (size_t index, int value)
{
  m_channelForRun[index] = value;
}

inline const IntegerArray& ResponseMatrix::energyRunLengths () const
{
  return m_energyRunLengths;
}

inline void ResponseMatrix::setEnergyRunLengths (const IntegerArray& value)
{
  m_energyRunLengths = value;
}

inline int ResponseMatrix::energyRunLengths (size_t index) const
{
  return m_energyRunLengths[index];
}

inline void ResponseMatrix::energyRunLengths (size_t index, int value)
{
  m_energyRunLengths[index] = value;
}

inline const IntegerArray& ResponseMatrix::energyStart () const
{
  return m_energyStart;
}

inline void ResponseMatrix::setEnergyStart (const IntegerArray& value)
{
  m_energyStart = value;
}

inline int ResponseMatrix::energyStart (size_t index) const
{
  return m_energyStart[index];
}

inline void ResponseMatrix::energyStart (size_t index, int value)
{
  m_energyStart[index] = value;
}

inline const std::vector<ResponseMatrix::RMFLONG>& ResponseMatrix::positions () const
{
  return m_positions;
}

inline void ResponseMatrix::setPositions (const std::vector<ResponseMatrix::RMFLONG>& value)
{
  m_positions = value;
}

inline ResponseMatrix::RMFLONG ResponseMatrix::positions (size_t index) const
{
  return m_positions[index];
}

inline void ResponseMatrix::positions (size_t index, ResponseMatrix::RMFLONG value)
{
  m_positions[index] = value;
}


#endif
