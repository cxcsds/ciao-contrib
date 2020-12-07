


/* prototypes for FORTRAN calling C */

#ifndef XSCF_H
#define XSCF_H


/* tcl defines a VOID macro that prevents cfortran headers from compiling */

#ifdef _TCL
#define VOIDTMP VOID
#undef VOID
#endif

/* prototypes for FORTRAN calling C */

#include "cfortran.h"
#include "pctype.h"

/* these are defined in different headers on different systems,
   so to avoid preprocessor ugliness, define here
*/

#undef MAX
#define MAX(a,b) (((a) > (b)) ? (a) : (b))

#undef MIN
#define MIN(a,b) (((a) < (b)) ? (a) : (b))


#ifdef __cplusplus
extern "C" {
#endif
/* actual Xparse prototypes, to be replaced */

PROTOCCALLSFSUB4(squeeze,xsquez,STRING, STRING, INT, INT)


PROTOCCALLSFSUB7(XparseGetArgs,xgtarg,STRING, PCINT, PCINT, PCINT, PCINT, PCINT, PCINT)


PROTOCCALLSFSUB13(XparseGetRange,xgtrng, STRING, PCINT, INT, STRINGV, STRINGV, INTV, INTV, \
        INTV, INTV, INTV, INT, PCINT, PCINT)

/* prototypes for command processing */

PROTOCCALLSFFUN0(INT,autosaveLevel,cgasav)

PROTOCCALLSFSUB0(autoWrite,autpro)


/* prototypes for file name processing */

PROTOCCALLSFFUN2(STRING,auxFilename,fgauxf, INT, STRING)

PROTOCCALLSFFUN1(STRING,dataFilename,fgflnm, INT)

PROTOCCALLSFSUB4(FPAUXF, fpauxf, PINT,  STRING, STRING, PINT)

PROTOCCALLSFSUB3(FPFLNM, fpflnm, PINT,  STRING, PINT)

PROTOCCALLSFSUB2(DPQFST, dpqfst, LOGICAL, PINT)


/* prototypes for fake data handling */

PROTOCCALLSFSUB5(getFakeFile,gtfkfl,STRING, INT, LOGICALV, LOGICALV, PCLOGICAL)

PROTOCCALLSFSUB2(setFakeFile,stfkfl,LOGICALV,LOGICALV)

PROTOCCALLSFSUB1(setFake,setfak,LOGICALV)

PROTOCCALLSFSUB4(makeFakeData,makfak,LOGICALV, LOGICALV, PFLOAT, INT)

/*
        Dataset handling prototypes
*/

PROTOCCALLSFFUN0(INT,numberOfDatasets,dgndst)

/*
 *  cfortran prototypes for DPSET routines.
 */

PROTOCCALLSFSUB3(DPTIME, dptime, INT,   FLOAT,  PINT)

PROTOCCALLSFSUB3(DPAREA, dparea, INT,   FLOAT,  PINT)

PROTOCCALLSFSUB3(DPREGN, dpregn, INT,   FLOAT,  PINT)

PROTOCCALLSFSUB3(DPCRNM, dpcrnm, INT,   FLOAT,  PINT)

PROTOCCALLSFSUB2(DWTIME, dwtime, PFLOAT, INT)

PROTOCCALLSFSUB2(DWAREA, dwarea, PFLOAT, INT)

PROTOCCALLSFSUB2(DWREGN, dwregn, PFLOAT, INT)

PROTOCCALLSFSUB2(DWCRNM, dwcrnm, PFLOAT, INT)


PROTOCCALLSFSUB0(XS_START,xs_start)


PROTOCCALLSFFUN1(LOGICAL,paramIsLinked,mgqlnk,INT)

PROTOCCALLSFFUN1(LOGICAL,paramLimitsInvalid,mgqblt,INT)


PROTOCCALLSFSUB1(printParameter, prtpar, INT)

PROTOCCALLSFSUB2(XWRITE,xwrite,STRING,INT)

PROTOCCALLSFSUB2(initializeParam,inipar, INT, INT)

PROTOCCALLSFSUB2(unlinkParam, mpnlnk,INT,PCINT)

PROTOCCALLSFFUN0(INT,numberOfParameters,mgnmpr)

PROTOCCALLSFFUN1(LOGICAL,isLinearGain,dgisgl,INT)  /* dgisgl */

PROTOCCALLSFFUN1(LOGICAL,isConstantGain,dgisgc,INT)  /* dgisgc */

PROTOCCALLSFFUN1(INT,paramDataGroup,mgdtgr,INT)  /* mgdtgr */

PROTOCCALLSFFUN1(INT, paramComponent, mgcomp, INT)

PROTOCCALLSFFUN1(STRING, paramName, mgpnam, INT)

PROTOCCALLSFFUN1(STRING, paramUnit, mgpunt, INT)

PROTOCCALLSFSUB0(writeParamHistory,wprhis)

PROTOCCALLSFSUB2(writeParameter, wrtpar, INT, LOGICAL)

PROTOCCALLSFSUB2(unlinkParam, mpnlnk, INT, PCINT)

PROTOCCALLSFFUN2(DOUBLE, paramValue, mgpval, INT, STRING)

PROTOCCALLSFSUB4(setParamValue,mppval,INT, DOUBLE, STRING, PCINT)

PROTOCCALLSFSUB5(makeParamLink,mpeqpm, INT, DOUBLE, DOUBLE, INT, PCINT)

PROTOCCALLSFSUB7(getParamValues,gtpval,STRING, PCINT,INT,INT,LOGICAL,INT,PCINT)

/* Data Group Prototypes */

PROTOCCALLSFFUN0(INT,numberOfDataGroups,dgndtg)

PROTOCCALLSFFUN1(INT,endBin,dgnbne,INT)

/* Component Prototypes */

PROTOCCALLSFFUN1(STRING, componentName, cgname, INT)

/* fit routine prototypes */

PROTOCCALLSFSUB2(writeStat,xswstt, FLOAT, INT)

#ifdef __cplusplus
}
#endif

#ifdef _TCL
#define VOID VOIDTMP
#undef VOIDTMP
#endif
#endif  /* xscf_h */
