#define MAXSTRLEN 1024

#define MAXMODELS 100
#define MAXENERGY 100000

struct SIGMA_TABLE {
  int Nrows;    /* Total number of rows */
  int Nenergy;  /* Number of energies */
  int Nxpos;    /* Number of dust (x) positions */ 
  int Nrext;    /* Number of extraction radii */
  float *energy; /* Energy of X-ray (in keV) */
  float *xpos;   /* Position of dust (between 0-1) */
  float *rext;   /* Extraction radii (in arcsec) */
  float *sigma;  /* Cross section (in cm^2) */
};

// Function definitions from calc_xscat.cxx
Real interpol_huntf(int n, Real *x, Real *y, Real z);
void calc_xscat(const RealArray& energyArray, 
		RealArray& fluxmult, 
		struct SIGMA_TABLE *xscat_dat, 
		Real NH, Real xpos, Real rext);

// Function definitions from xscat_init.cxx
void read_xscat(const char *filename, int *Nmodel, 
		struct SIGMA_TABLE *xscat_dat[]);
void xscat_init(int *Nmodel, struct SIGMA_TABLE *xscatdata[]);


