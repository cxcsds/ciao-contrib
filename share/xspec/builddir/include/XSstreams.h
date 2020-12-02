#ifndef XSSTREAMS_H
#define XSSTREAMS_H

#include <iosfwd>

class XSstream;

// XSPEC's streams declarations

extern std::ostream& tcerr;
extern std::istream&  tcin;
extern std::ostream& tcout;
extern std::ostream& tccon;

extern  XSstream tpout;   
extern  XSstream tperr;   
extern  XSstream tpin;   
extern  XSstream tpcon;   


extern const size_t NORM_OUTPUT;

#endif
