// Useful functions - mostly using CCfits

#ifndef HAVE_HEASP
#include "heasp.h"
#endif

#define HAVE_SPio 1

// Read a keyword from the primary header.

template <class T> T SPreadKey(PHDU&, string, T);

// Read a keyword from an extension.

template <class T> T SPreadKey(ExtHDU&, string, T);

// Read a keyword from a type II file. Note for type I files RowNumber will necessarily be 1.

template <class T> T SPreadKey(ExtHDU&, string, Integer, T);

// Read a column into a valarray/vector

template <class T> void SPreadCol(ExtHDU&, string, valarray<T>&);
template <class T> void SPreadCol(ExtHDU&, string, vector<T>&);

// Need special case for strings because of the workaround required for a
// missing routine in CCfits

void SPreadCol(ExtHDU&, string, vector<string>&);

// Read a column from a type II file into a valarray/vector
// for type I data the RowNumber is necessarily 1.

template <class T> void SPreadCol(ExtHDU&, string, Integer, valarray<T>&);
template <class T> void SPreadCol(ExtHDU&, string, Integer, vector<T>&);

// Read a vector column into a vector of valarray/vector

template <class T> void SPreadVectorCol(ExtHDU&, string, vector<valarray<T> >&);
template <class T> void SPreadVectorCol(ExtHDU&, string, vector<vector<T> >&);

// Read a single row of vector column into a valarray/vector

template <class T> void SPreadVectorColRow(ExtHDU&, string, Integer, valarray<T>&);
template <class T> void SPreadVectorColRow(ExtHDU&, string, Integer, vector<T>&);

// Write a keyword - at present just a wrap-up of addKey

template <class T> void SPwriteKey(Table&, string, T, string);

// Write a column from a valarray/vector. If the data size is 1 or all 
// values are the same then just write a keyword

template <class T> void SPwriteCol(Table&, string, valarray<T>&);
template <class T> void SPwriteCol(Table&, string, vector<T>&);

// Write a column from a valarray/vector. If the data size is 1 or all 
// values are the same then just write a keyword if the forceCol bool is false.

template <class T> void SPwriteCol(Table&, string, valarray<T>&, bool);
template <class T> void SPwriteCol(Table&, string, vector<T>&, bool);

// Write a column from a valarray/vector. If the data size is 1 or all values are the 
// same then just write a keyword

template <class T> void SPwriteCol(Table&, string, valarray<T>&);
template <class T> void SPwriteCol(Table&, string, vector<T>&);

// Write a column from a vector of valarrays/vectors. If the data size is 1 or 
// all values are the same then just write a keyword. If all values are the same 
// within all valarrays then write a scalar column

template <class T> void SPwriteVectorCol(Table&, string, vector<valarray<T> >&);
template <class T> void SPwriteVectorCol(Table&, string, vector<vector<T> >&);

// Write a column for a vector of valarrays/vectors. If the data size is 1 or all 
// values are the same then just write a keyword if the forceCol bool is false. 
// If all values are the same within all valarrays then write a scalar column

template <class T> void SPwriteVectorCol(Table&, string, vector<valarray<T> >&, bool);
template <class T> void SPwriteVectorCol(Table&, string, vector<vector<T> >&, bool);

// check whether a given column is required and if it needs to be a vector column
// note that T is assumed to be a valarray or vector of a valarray of some type.

template <class T> bool SPneedCol(const T&);

// check whether a given column is required. For this overloaded version
// T is assumed to be a valarray or a vector of a scalar of some type.

template <class T> bool SPneedCol(const T&, bool& isvector);

// Real all keywords from the primary or an extension into a vector of strings

vector<string> SPreadAllPrimaryKeywords(const string& filename);
vector<string> SPreadAllKeywords(const string& filename, const string& hduName, 
				 const int& hduNumber);


