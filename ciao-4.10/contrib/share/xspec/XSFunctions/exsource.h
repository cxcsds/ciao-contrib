/* wcslib stuff */

#ifndef EXSOURCE_H
#define EXSOURCE_H

#include "fitsio.h"
#include "wcslib/wcslib.h"

typedef struct hgram {
  int   nch;
  float limit[2];
  float *values;
} hgram;

typedef struct rotmat {
  double elem[3][3];
} rotmat;

typedef struct vec {
  double comp[3];
} vec;

typedef struct coords {
  double ra,dec;
} coords;

typedef struct aspect {
  coords c;
  double roll;
} aspect;

typedef struct exsource_projection {
  int initialized;
  aspect asp;
  /* for internal use; would be private if c++ */
  hgram  fullreshist; 
  /* space where histogram is returned. */
  hgram  hist;        
  /* name of variable containing image */
  char   *image;      
  /* value of variable containing image */
  char   *image_val;      
  /* name of variable containing boresight (sexages.) */
  char   *bores;      
  /* value of variable containing boresight (sexages.) */
  char   *bores_val;      
  /* name of variable containing extraction width (arcmin) */
  char   *extraction; 
  /* value of variable containing extraction width (arcmin) */
  char   *extraction_val; 
} exsource_projection;


#ifdef EXSOURCE_CODE
int exsource (exsource_projection *exs);
int img2exhist (char *file,aspect *asp,float exhw,hgram *hg);
void str2coords (char *s,aspect *a);
void printerror ( int status );
void exsource_complain (char *s);
void hist2hist (hgram *to_hg, hgram *fm_hg);
double matrix_determinant(rotmat *m);
rotmat *matrix321 ( rotmat *m, double psi, double theta, double phi );
rotmat *matrix123 ( rotmat *m, double psi, double theta, double phi );
rotmat *matrix_matrix_multiply ( rotmat *prod, rotmat *m1, rotmat *m2 );
vec    *matrix_vector_multiply ( vec *prod, rotmat *m, vec *v );
vec    *ccoords2vec ( double ra, double dec, vec *v );
void   print_vec(vec *v);
double dotproduct (vec *v1,vec *v2);
#else
extern int exsource (exsource_projection *exs);
#endif

#endif


