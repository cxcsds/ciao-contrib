// Definition of the arfII object. Just a wrap-up for a vector array of arf objects

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#ifndef HAVE_SPutils
#include "SPutils.h"
#endif

#ifndef HAVE_arf
#include "arf.h"
#endif

#define HAVE_arfII 1

class arfII{
 public:

  // constructors

  arfII();
  arfII(const arfII& a);
  arfII(const string filename, const Integer ARFnumber = 1,
	const vector<Integer>& RowNumber = vector<Integer>());

  
  // destructor

  ~arfII();

  // read file into object. 

  Integer read(const string filename, const Integer ARFnumber = 1,
	       const vector<Integer>& RowNumber = vector<Integer>());

  // Deep copy

  arfII& copy(const arfII&);
  arfII& operator= (const arfII&);

  // Get arf object (counts from zero).

  arf get(const Integer number) const;

  // Push arf object into arfII object

  void push(arf ea);

  // Display information about the ARFs - return as a string

  string disp() const;

  // Clear information from the ARFs

  void clear();

  // Check completeness and consistency of information in arfs
  // if there is a problem then return diagnostic in string

  string check() const;

  // Write ARFs as type II file

  Integer write(const string filename) const;

  // Return information

  const Integer NumberARFs() const;          // Number of ARFs in the object
  const Integer getNumberARFs() const;

  // get and set internal data

  const vector<arf>& getarfs() const;
  Integer setarfs(const vector<arf>& values);
  arf getarfsElement(const Integer i) const;
  Integer setarfsElement(const Integer i, const arf& value);
  
  // Internal data

 private:
  vector<arf> m_arfs;           // vector of arf objects
  
};

// Return the number of ARFs in the object

inline const Integer arfII::NumberARFs() const
{
  return m_arfs.size();
}
inline const Integer arfII::getNumberARFs() const
{
  return m_arfs.size();
}

// inline routines to get and set internal data

inline const vector<arf>& arfII::getarfs() const
{
  return m_arfs;
}
inline Integer arfII::setarfs(const vector<arf>& values)
{
  m_arfs.resize(values.size());
  for (size_t i=0; i<values.size(); i++) m_arfs[i] = values[i];
  return OK;
}
inline arf arfII::getarfsElement(const Integer i) const
{
  if ( i >= 0 && i < (Integer)m_arfs.size() ) {
    return m_arfs[i];
  } else {
    arf nothing;
    return nothing;
  }
}
inline Integer arfII::setarfsElement(const Integer i, const arf& value)
{
  if ( i >= 0 && i < (Integer)m_arfs.size() ) {
    m_arfs[i] = value;
    return OK;
  } else {
    return VectorIndexOutsideRange;
  }
}

// return the number of ARFs in a type II ARF extension

Integer NumberofARFs(const string filename, const Integer HDUnumber);
Integer NumberofARFs(const string filename, const Integer HDUnumber, Integer& Status);



