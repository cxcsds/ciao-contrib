
#ifndef BINARYSEARCH_H
#define BINARYSEARCH_H

#include <xsTypes.h>


namespace Numerics {

  // Binary search on a RealArray to return the index of the element immediately
  // before the input value. Assumes that the RealArray is in ascending order

  int BinarySearch(const RealArray& x, const Real& y);

  // Binary search on a RealArray to return the indices of the element immediately
  // before the input values assuming the input values are in ascending order.

  IntegerArray BinarySearch(const RealArray& x, const RealArray& y);

}

#endif
