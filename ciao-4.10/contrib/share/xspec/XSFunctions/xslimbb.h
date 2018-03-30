//************************************************************************
//    xslimbb.h - 
//------------------------------------------------------------------------
//    Written by:
//    Michal Bursa (bursa@astro.cas.cz)
//    Astronomical Institute
//    Bocni II 1401/1a, 141-31 Praha 4, Czech Republic
//------------------------------------------------------------------------
//    Created: 19.12.2010
//************************************************************************



#ifndef _XSLIMBB_H
#define _XSLIMBB_H

#define FLUX_UNITS             "erg cm^-2 s^-1 keV^-1\0"

#define META_NCOLS             3              // no. of columns in META table (grid size, grid data)
#define META_NROWS             7              // no. of rows in META table
#define META_COL_NAME          1              // index of 1st column (grid size)
#define META_COL_N             2              // index of 1st column (grid size)
#define META_COL_VALUE         3              // index of 2nd column (grid data)
#define META_ROW_SPIN_GRID     1              // index of 1st row (spin)
#define META_ROW_LUMI_GRID     2              // index of 2nd row (lumi)
#define META_ROW_INCL_GRID     3              // index of 3rd row (incl)
#define META_ROW_ENER_GRID     4              // index of 4th row (ener)
#define META_ROW_ALPH_GRID     5              // index of 5th row (alph)
#define META_ROW_REF_MASS      6              // index of 6th row (reference mass)
#define META_ROW_REF_DIST      7              // index of 7th row (reference distance)



#define FLUX_NCOLS        6
#define FLUX_COL_FLUX_I0  1    // no effects 
#define FLUX_COL_FLUX_L0  2    // +limbdk
#define FLUX_COL_FLUX_IV  3    // +vertical profile 
#define FLUX_COL_FLUX_LV  4    // +limbdk + vertical profile
#define FLUX_COL_FLUX_S0  5    // +bhspec 
#define FLUX_COL_FLUX_SV  6    // +bhspec + vertical profile



#endif
