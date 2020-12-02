/* Some standard routines in common between xscompmag.c and xscomptb.c */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdarg.h>
#include <string.h>

#define NR_END 1
#define FREE_ARG char*

typedef double Real;

Real gammln(Real xx);
Real zeta(Real xx);
Real interp_funct (Real *array_x, Real *array_y, int dimen, Real x);
Real *dvector(long nl, long nh);
void free_dvector(Real *v, long nl, long nh);
double **dmatrix(long nrl, long nrh, long ncl, long nch);
void free_dmatrix(double **m, long nrl, long nrh, long ncl, long nch);

