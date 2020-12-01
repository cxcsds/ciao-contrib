#ifndef XSSYMBOL_H
#define XSSYMBOL_H

#include "xsTypes.h"
#include <string>

// global constant symbols.


extern const int XSPEC_OK;  // just give a new name to zero to make meaning of
                         // status code more than obvious;
extern const int XSPEC_ERROR;
extern const int PARLEN; // maximum length of string parameter read from file.
                         // (e.g. model or parameter name/unit.
                         // this is equal to 8 in Xspec.

extern bool PRINT_DIAGS;
extern const Real SMALL;
extern const Real LARGE;
extern const int MAXLINELEN;
extern const int MAX_FILENAMELEN;
extern const std::string DUMMY_RSP;
extern const std::string USR_DUMMY_RSP;


extern const std::string modchar;
extern const std::string delim;
const char OP='{';

#endif
