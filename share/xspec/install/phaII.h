// Definition of the SpectrumII object. Just a wrap-up for a vector array of Spectrum objects

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_pha
#include "pha.h"
#endif

#define HAVE_phaII 1

class phaII{
 public:

  // constructors

  phaII();
  phaII(const phaII& a);
  phaII(const string filename, const Integer PHAnumber = 1,
	const vector<Integer>& SpectrumNumber = vector<Integer>());

  // destructor

  ~phaII();

  // read file into object. 

  Integer read(const string filename, const Integer PHAnumber = 1,
	       const vector<Integer>& SpectrumNumber = vector<Integer>());

  // Deep copy

  phaII& copy(const phaII&);
  phaII& operator= (const phaII&);

  // Get pha object (counts from zero).

  pha get(const Integer number) const;

  // Push pha object into phaII object

  void push(pha spectrum);

  // Display information about the spectra - return as a string

  string disp() const;

  // Clear information about the spectra

  void clear();

  // Check completeness and consistency of information in spectrum
  // if there is a problem then return diagnostic in string

  string check() const;

  // Write spectra as type II file

  Integer write(string filename) const;

  // Return information

  Integer NumberSpectra() const;          // Number of Spectra in the object
  Integer getNumberSpectra() const;

  // get and set internal data

  const vector<pha>& getphas() const;
  Integer setphas(const vector<pha>& values);
  pha getphasElement(const Integer i) const;
  Integer setphasElement(const Integer i, const pha& value);

  // internal data
 private:
  vector<pha> m_phas;           // vector of pha objects
  
};

// number of spectra

inline Integer phaII::NumberSpectra() const
{
  return m_phas.size();
}
inline Integer phaII::getNumberSpectra() const
{
  return m_phas.size();
}

// inline routines to get and set internal data

inline const vector<pha>& phaII::getphas() const
{
  return m_phas;
}
inline Integer phaII::setphas(const vector<pha>& values)
{
  m_phas.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_phas[i] = values[i];
  return OK;
}
inline pha phaII::getphasElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_phas.size() ) {
    return m_phas[i];
  } else {
    pha nothing;
    return nothing;
  }
}
inline Integer phaII::setphasElement(const Integer i, const pha& value)
{
  if ( i >= 0 && i < (Integer)m_phas.size() ) {
    m_phas[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}


