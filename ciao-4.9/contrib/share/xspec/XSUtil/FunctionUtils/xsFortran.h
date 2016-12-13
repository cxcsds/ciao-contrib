
#ifndef XSFORTRAN_H
#define XSFORTRAN_H
#include <sys/types.h>
#include <stdbool.h>

/* functions that the fortran library needs that are implemented in C++ now. */


#ifdef __cplusplus
extern "C"
{
#endif
        char* FGMODF(void);
        char* FGDATD(void);
        float FGABND(char* element);
        char*  FGXSCT(void); 
        char*  FGSOLR(void);
        char*  FGMSTR(char* dname);
        void FPDATD(const char* dataDir);
        void FPSOLR(const char* table, int* ierr);
        void FPXSCT(const char* csection, int* ierr);
        void FPMSTR(const char* value1, const char* value2);
        void FPSLFL(float rvalue[], int nvalue, int *ierr);
        void RFLABD(const char* fname, int *ierr);
        void FNINIT(void);
        int xs_write(char*, int);
        int xs_read(const char*, char*, int*);
        float csmgq0(void);
        float csmgh0(void);
        float csmgl0(void);
        void csmpq0(float q0);
        void csmph0(float H0);
        void csmpl0(float lambda0);
        float fzsq(float z, float q0, float lambda);
        int DGNFLT(int);
        float DGFILT(int, const char*);
        bool DGQFLT(int, const char*);
        void PDBVAL(const char*, double);

   /* These are not xspec's chatter levels.  They are intended for
      use by other programs which link to XSFunctions. */
        int FGCHAT(void);
        void FPCHAT(int chat);
   /* This retrieves xspec's chatter levels, or 0 if not calling
      from xspec. */
        void xs_getChat(int* cons, int* log);

   /* Copies xspec's version string into buffer. 
      Will copy at most buffSize-1 characters, and pads with
      a trailing NULL.  Returns -1 if the copy was truncated, 
      else returns 0. */
       int xs_getVersion(char* buffer, int buffSize);

   /* Interface for user C and Fortran subroutines requiring use of
      Gamma functions in the Numerics subdirectory of the XSUtil library. */
        float xs_erf( float x);
        float xs_erfc(float x);
        float gammap(float a, float x);
        float gammq(float a, float x);

#ifdef __cplusplus                 
}
#endif

#endif
