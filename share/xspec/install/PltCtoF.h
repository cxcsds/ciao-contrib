//
//  XSPEC12  November 2003
//
//

#ifndef PLTCTOF_H
#define PLTCTOF_H

#include "cfortran.h"

/* tcl defines a VOID macro that prevents cfortran headers from compiling */

#ifdef _TCL
#define VOIDTMP VOID
#undef VOID
#endif

PROTOCCALLSFFUN1(INT,PGOPEN,pgopen,STRING)
PROTOCCALLSFSUB0(PGEND,pgend)
PROTOCCALLSFSUB0(PGPAGE,pgpage)
PROTOCCALLSFSUB0(PGUPDT,pgupdt)
PROTOCCALLSFSUB6(PGENV,pgenv,FLOAT,FLOAT,FLOAT,FLOAT,INT,INT)
PROTOCCALLSFSUB1(PGSCH,pgsch,FLOAT)
PROTOCCALLSFSUB3(PGTEXT,pgtext,FLOAT,FLOAT,STRINGV)
PROTOCCALLSFSUB4(PGSCR,pgscr,INT,FLOAT,FLOAT,FLOAT)

extern "C" void plt_(float* y,int* iery,int& nPts, int& mPts,int& nVec,
                        char* cmd,int& nCmd,int& ier,size_t LENGTH);

#define PGOPEN(I)  CCALLSFFUN1(PGOPEN,pgopen,STRING,I)
#define PGEND()  CCALLSFSUB0(PGEND,pgend)
#define PGCLOS()  CCALLSFSUB0(PGCLOS,pgend)
#define PGPAGE()  CCALLSFSUB0(PGPAGE,pgpage)
#define PGUPDT()  CCALLSFSUB0(PGUPDT,pgupdt)
#define PGENV(xmin, xmax, ymin, ymax, just, axis) \
		CCALLSFSUB6(PGENV,pgenv,FLOAT,FLOAT,FLOAT,FLOAT,INT,INT, \
		xmin, xmax, ymin, ymax, just, axis)
#define PGSCH(size)  CCALLSFSUB1(PGSCH,pgsch,FLOAT,size)
#define PGTEXT(x,y,text)  CCALLSFSUB3(PGTEXT,pgtext,FLOAT,FLOAT,STRINGV, \
		x,y,text)
#define PGSCR(ci,cr,cg,cb) CCALLSFSUB4(PGSCR,pgscr,INT,FLOAT,FLOAT,FLOAT,ci,cr,cg,cb)

#endif
