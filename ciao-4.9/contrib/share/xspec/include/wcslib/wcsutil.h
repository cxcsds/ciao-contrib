/*============================================================================

  WCSLIB 4.4 - an implementation of the FITS WCS standard.
  Copyright (C) 1995-2009, Mark Calabretta

  This file is part of WCSLIB.

  WCSLIB is free software: you can redistribute it and/or modify it under the
  terms of the GNU Lesser General Public License as published by the Free
  Software Foundation, either version 3 of the License, or (at your option)
  any later version.

  WCSLIB is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
  FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
  more details.

  You should have received a copy of the GNU Lesser General Public License
  along with WCSLIB.  If not, see <http://www.gnu.org/licenses/>.

  Correspondence concerning WCSLIB may be directed to:
    Internet email: mcalabre@atnf.csiro.au
    Postal address: Dr. Mark Calabretta
                    Australia Telescope National Facility, CSIRO
                    PO Box 76
                    Epping NSW 1710
                    AUSTRALIA

  Author: Mark Calabretta, Australia Telescope National Facility
  http://www.atnf.csiro.au/~mcalabre/index.html
  $Id: wcsutil.h,v 1.4 2009/09/14 20:25:15 irby Exp $
*=============================================================================
*
* Summary of the wcsutil routines
* -------------------------------
* Simple utility functions used by WCSLIB.  They are documented here solely as
* an aid to understanding the code.  Thay are not intended for external use -
* the API may change without notice!
*
*
* wcsutil_blank_fill() - Fill a character string with blanks
* ----------------------------------------------------------
* wcsutil_blank_fill() pads a character string with blanks starting with the
* terminating NULL character.
*
* Used by the Fortran wrapper functions in translating C character strings
* into Fortran CHARACTER variables.
*
* Given:
*   n         int       Length of the character array, c[].
*
* Given and returned:
*   c         char[]    The character string.  It will not be null-terminated
*                       on return.
*
* Function return value:
*             void
*
*
* wcsutil_null_fill() - Fill a character string with NULLs
* --------------------------------------------------------
* wcsutil_null_fill() pads a character string with NULL characters.
*
* Used mainly to make character strings intelligible in the GNU debugger - it
* prints the rubbish following the terminating NULL, obscuring the valid part
* of the string.
*
* Given:
*   n         int       Number of characters.
*
* Given and returned:
*   c         char[]    The character string.
*
* Function return value:
*             void
*
*
* wcsutil_allEq() - Test for equality of a particular vector element
* ------------------------------------------------------------------
* wcsutil_allEq() tests for equality of a particular element in a set of
* vectors.
*
* Given:
*   nvec      int       The number of vectors.
*   nelem     int       The length of each vector.
*   first     const double*
*                       Pointer to the first element to test in the array.
*                       The elements tested for equality are
*
=                         *first == *(first + nelem)
=                                == *(first + nelem*2)
=                                           :
=                                == *(first + nelem*(nvec-1));
*
*                       The array might be dimensioned as
*
=                         double v[nvec][nelem];
*
* Function return value:
*             int       Status return value:
*                         0: Not all equal.
*                         1: All equal.
*
*
* wcsutil_setAll() - Set a particular vector element
* --------------------------------------------------
* wcsutil_setAll() sets the value of a particular element in a set of vectors.
*
* Given:
*   nvec      int       The number of vectors.
*   nelem     int       The length of each vector.
*
* Given and returned:
*   first     double*   Pointer to the first element in the array, the value
*                       of which is used to set the others
*
=                         *(first + nelem) = *first;
=                         *(first + nelem*2) = *first;
=                                 :
=                         *(first + nelem*(nvec-1)) = *first;
*
*                       The array might be dimensioned as
*
=                         double v[nvec][nelem];
*
* Function return value:
*             void
*
*
* wcsutil_setAli() - Set a particular vector element
* --------------------------------------------------
* wcsutil_setAli() sets the value of a particular element in a set of vectors.
*
* Given:
*   nvec      int       The number of vectors.
*   nelem     int       The length of each vector.
*
* Given and returned:
*   first     int*      Pointer to the first element in the array, the value
*                       of which is used to set the others
*
=                         *(first + nelem) = *first;
=                         *(first + nelem*2) = *first;
=                                 :
=                         *(first + nelem*(nvec-1)) = *first;
*
*                       The array might be dimensioned as
*
=                         int v[nvec][nelem];
*
* Function return value:
*             void
*
*
* wcsutil_setBit() - Set bits in selected elements of an array
* ------------------------------------------------------------
* wcsutil_setBit() sets bits in selected elements of an array.
*
* Given:
*   nelem     int       Number of elements in the array.
*   sel       const int*
*                       Address of a selection array of length nelem.
*                       May be specified as the null pointer in which case all
*                       elements are selected.
*   bits      int       Bit mask.
*
* Given and returned:
*   array     int*      Address of the array of length nelem.
*
* Function return value:
*             void
*
*===========================================================================*/

#ifndef WCSLIB_WCSUTIL
#define WCSLIB_WCSUTIL

void wcsutil_blank_fill(int n, char c[]);
void wcsutil_null_fill (int n, char c[]);

int  wcsutil_allEq (int nvec, int nelem, const double *first);
void wcsutil_setAll(int nvec, int nelem, double *first);
void wcsutil_setAli(int nvec, int nelem, int *first);
void wcsutil_setBit(int nelem, const int *sel, int bits, int *array);

#endif /* WCSLIB_WCSUTIL */
