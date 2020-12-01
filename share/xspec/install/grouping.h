// class definition for grouping class. Useful for setting grouping arrays and binning
// both spectra and responses.

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#define HAVE_grouping 1

class grouping{
 public:

  // constructor

  grouping();

  // constructor from an input array

  grouping(vector<Integer>);

  // destructor

  ~grouping();

  // display grouping information - return as a string

  string disp() const;

  // clear grouping information

  void clear();

  // read from an ascii file of grouping factors

  Integer read(string filename, const Integer Number, const Integer First);

  // set from a single binning factor

  void load(const Integer Binsize, const Integer Number);

  // set from an array of binning factors

  Integer load(const vector<Integer>& StartBin, const vector<Integer>& EndBin, const vector<Integer>& BinFactor, const Integer Number, const Integer First);

  // set from quality and grouping vectors from a pha object

  Integer loadFromVector(const vector<Integer>& QualVector, const vector<Integer>& GroupVector);

  // set from a minimum with optional start and stop channel for the grouping
  // if StartChannel=EndChannel=0 then use all channels.

  template <class T> Integer loadMin(const T Minimum, const vector<T>& Values,
				     const Integer StartChannel = 0, 
				     const Integer EndChannel = 0);

  // set using optimal channel binning based on the instrument FWHM.
  // note that this assumes that FWHM is that for each channel, not for each energy

  Integer loadOptimal(const vector<Real>& FWHM, const vector<Integer>& Counts);

  // set using optimal energy binning based on the instrument FWHM.
  // note that this assumes that FWHM is that for each energy

  Integer loadOptimalEnergy(const vector<Real>& FWHM, const vector<Integer>& Counts);

  // return whether current element is start of new bin

  bool newBin(const Integer i) const;

  // return number of elements in grouping object

  Integer size() const;

  // methods to get and set internal data

  const vector<Integer>& getflag() const;
  Integer setflag(const vector<Integer>& values);
  const Integer getflagElement(const Integer i) const;
  Integer setflagElement(const Integer i, const Integer value);

  // internal data

 private:

  vector<Integer> m_flag;  // Grouping flag: 1=start of bin, -1=continuation of bin, 0=ignore

};

// definition of the binning modes

enum{SumMode,SumQuadMode,MeanMode,FirstEltMode,LastEltMode};

// bin an array based on the grouping factors

template <class T> void GroupBin(const vector<T>&, const Integer, const grouping&, vector<T>&);
template <class T> void GroupBin(const valarray<T>&, const Integer, const grouping&, valarray<T>&);

// read a file with binning factors

Integer ReadBinFactors(string filename, vector<Integer>& StartBin, vector<Integer>& EndBin, vector<Integer>& BinFactor); 

// inline methods to get and set data

inline const vector<Integer>& grouping::getflag() const
{
  return m_flag;
}
inline Integer grouping::setflag(const vector<Integer>& values)
{
  m_flag.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_flag[i] = values[i];
  return OK;
}
inline const Integer grouping::getflagElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_flag.size() ) {
    return m_flag[i];
  } else {
    return -999;
  }
}
inline Integer grouping::setflagElement(const Integer i, const Integer value)
{
  if ( i >= 0 && i < (Integer)m_flag.size() ) {
    m_flag[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}
  

