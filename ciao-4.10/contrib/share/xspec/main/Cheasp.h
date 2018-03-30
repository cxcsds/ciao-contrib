/* Header file for heasp routines
   Defines structures for RMF, RMFchain, ARF, PHA, BinFactors
   Includes prototypes for functions */

#include "fitsio.h"
#include "headas.h"

#ifdef __cplusplus
extern "C"
{
#endif

/* define the RMF structure */

struct RMF {

  long NumberChannels;                            /* Number of spectrum channels */
  long NumberEnergyBins;                          /* Number of response energies */
  long NumberTotalGroups;                         /* Total number of response groups */
  long NumberTotalElements;                       /* Total number of response elements */
  long FirstChannel;                              /* First channel number */
  long isOrder;                                   /* If true grating order information included */

  long* NumberGroups; /*NumberEnergyBins*/        /* Number of response groups for this energy bin */
  long* FirstGroup;  /*NumberEnergyBins*/         /* First response group for this energy bin (counts from 0)*/

  long* FirstChannelGroup; /*NumberTotalGroups*/  /* First channel number in this group */
  long* NumberChannelGroups; /*NumberTotalGroups*//* Number of channels in this group */
  long* FirstElement; /*NumberTotalGroups*/       /* First response element for this group (counts from 0)*/
  long* OrderGroup; /*NumberTotalGroups*/         /* The grating order of this group */

  float* LowEnergy; /*NumberEnergyBins*/         /* Start energy of bin */
  float* HighEnergy; /*NumberEnergyBins*/        /* End energy of bin */

  float* Matrix; /*NumberTotalElements*/         /* Matrix elements */

  float* ChannelLowEnergy; /*NumberChannels*/    /* Start energy of channel */
  float* ChannelHighEnergy; /*NumberChannels*/   /* End energy of channel */

  float AreaScaling;                             /* Value of EFFAREA keyword */
  float ResponseThreshold;                       /* Minimum value in response */

  char EnergyUnits[FLEN_KEYWORD];                /* Units for energies */
  char RMFUnits[FLEN_KEYWORD];                   /* Units for RMF */

  char ChannelType[FLEN_KEYWORD];                /* Value of CHANTYPE keyword */
  char RMFVersion[FLEN_KEYWORD];                 /* MATRIX extension format version */
  char EBDVersion[FLEN_KEYWORD];                 /* EBOUNDS extension format version */
  char Telescope[FLEN_KEYWORD];                             
  char Instrument[FLEN_KEYWORD];
  char Detector[FLEN_KEYWORD];
  char Filter[FLEN_KEYWORD];
  char RMFType[FLEN_KEYWORD];                    /* Value of HDUCLAS3 keyword in MATRIX extension */
  char RMFExtensionName[FLEN_VALUE];             /* Value of EXTNAME keyword in MATRIX extension */
  char EBDExtensionName[FLEN_VALUE];             /* Value of EXTNAME keyword in EBOUNDS extension */

};

/* define the RMFchan structure - the RMF transposed with channels as rows */

struct RMFchan {

  long NumberChannels;                            /* Number of spectrum channels */
  long NumberEnergyBins;                          /* Number of response energies */
  long NumberTotalGroups;                         /* Total number of response groups */
  long NumberTotalElements;                       /* Total number of response elements */
  long FirstChannel;                              /* First channel number */
  long isOrder;                                   /* If true grating order information included */

  long* NumberGroups; /*NumberChannels*/          /* Number of response groups for this channel bin */
  long* FirstGroup;  /*NumberChannels*/           /* First response group for this channel bin (counts from 0)*/

  long* FirstEnergyGroup; /*NumberTotalGroups*/   /* First energy bin in this group */
  long* NumberEnergyGroups; /*NumberTotalGroups*/ /* Number of energy bins in this group */
  long* FirstElement; /*NumberTotalGroups*/       /* First response element for this group (counts from 0)*/
  long* OrderGroup; /*NumberTotalGroups*/         /* The grating order of this group */

  float* LowEnergy; /*NumberEnergyBins*/         /* Start energy of bin */
  float* HighEnergy; /*NumberEnergyBins*/        /* End energy of bin */

  float* Matrix; /*NumberTotalElements*/         /* Matrix elements */

  float* ChannelLowEnergy; /*NumberChannels*/    /* Start energy of channel */
  float* ChannelHighEnergy; /*NumberChannels*/   /* End energy of channel */

  float AreaScaling;                             /* Value of EFFAREA keyword */
  float ResponseThreshold;                       /* Minimum value in response */

  char EnergyUnits[FLEN_KEYWORD];                /* Units for energies */
  char RMFUnits[FLEN_KEYWORD];                   /* Units for RMF */

  char ChannelType[FLEN_KEYWORD];                /* Value of CHANTYPE keyword */
  char RMFVersion[FLEN_KEYWORD];                 /* MATRIX extension format version */
  char EBDVersion[FLEN_KEYWORD];                 /* EBOUNDS extension format version */
  char Telescope[FLEN_KEYWORD];                             
  char Instrument[FLEN_KEYWORD];
  char Detector[FLEN_KEYWORD];
  char Filter[FLEN_KEYWORD];
  char RMFType[FLEN_KEYWORD];                    /* Value of HDUCLAS3 keyword in MATRIX extension */
  char RMFExtensionName[FLEN_VALUE];             /* Value of EXTNAME keyword in MATRIX extension */
  char EBDExtensionName[FLEN_VALUE];             /* Value of EXTNAME keyword in EBOUNDS extension */

};

/* define the ARF structure */

struct ARF {

  long NumberEnergyBins;                         /* Number of response energies */

  float* LowEnergy; /*NumberEnergyBins*/         /* Start energy of bin */
  float* HighEnergy; /*NumberEnergyBins*/        /* End energy of bin */

  float* EffArea;    /*NumberEnergyBins*/        /* Effective areas */

  char EnergyUnits[FLEN_KEYWORD];                /* Units for energies */
  char arfUnits[FLEN_KEYWORD];                   /* Units for effective areas */

  char ARFVersion[FLEN_KEYWORD];                 /* SPECRESP extension format version */
  char Telescope[FLEN_KEYWORD];                             
  char Instrument[FLEN_KEYWORD];
  char Detector[FLEN_KEYWORD];
  char Filter[FLEN_KEYWORD];
  char ARFExtensionName[FLEN_VALUE];             /* Value of EXTNAME keyword in SPECRESP extension */

};

/* define the PHA structure */

struct PHA {

  long NumberChannels;                           /* Number of spectrum channels */
  long FirstChannel;                             /* First channel number */

  float* Pha; /*NumberChannels*/                 /* PHA data */
  float* StatError; /*NumberChannels*/           /* Statistical error */
  float* SysError; /*NumberChannels*/            /* Statistical error */

  int*   Quality; /*NumberChannels*/             /* Data quality */
  int*   Grouping;  /*NumberChannels*/           /* Data grouping */
  int*   Channel;  /*NumberChannels*/            /* Channel number */

  float* AreaScaling; /*NumberChannels*/         /* Area scaling factor */
  float* BackScaling; /*NumberChannels*/         /* Background scaling factor */

  float Exposure;                                /* Exposure time */
  float CorrectionScaling;                       /* Correction file scale factor */
  int   DetChans;                                /* Content of DETCHANS keyword */

  int Poisserr;                                  /* If true, errors are Poisson */
  char Datatype[FLEN_KEYWORD];                   /* "COUNT" for count data and "RATE" for count/sec */
  char Spectrumtype[FLEN_KEYWORD];               /* "TOTAL", "NET", or "BKG" */

  char ResponseFile[FLEN_FILENAME];              /* Response filename */
  char AncillaryFile[FLEN_FILENAME];             /* Ancillary filename */
  char BackgroundFile[FLEN_FILENAME];            /* Background filename */
  char CorrectionFile[FLEN_FILENAME];            /* Correction filename */

  char ChannelType[FLEN_KEYWORD];                /* Value of CHANTYPE keyword */
  char PHAVersion[FLEN_KEYWORD];                 /* PHA extension format version */
  char Telescope[FLEN_KEYWORD];                             
  char Instrument[FLEN_KEYWORD];
  char Detector[FLEN_KEYWORD];
  char Filter[FLEN_KEYWORD];
  char Datamode[FLEN_KEYWORD];

  char *XSPECFilter[100];                       /* Filter keywords */
};

/* define the BinFactors structure */

struct BinFactors {

  long NumberBinFactors;

  long *StartBin;
  long *EndBin;
  long *Binning;

};

/* function proto-types */

/* read the RMF matrix and ebounds from a FITS file. this assumes that there is only one
   of each in the file. */

int ReadRMF(char *filename, struct RMF *rmf);

/* write the RMF matrix and ebounds to a FITS file */

int WriteRMF(char *filename, struct RMF *rmf);

/* read the RMF matrix from a FITS file - if there are multiple RMF extensions then
   read the one in RMFnumber */

int ReadRMFMatrix(char *filename, long RMFnumber, struct RMF *rmf);

/* write the RMF matrix to a FITS file */

int WriteRMFMatrix(char *filename, struct RMF *rmf);

/* read the RMF ebounds from a FITS file - if there are multiple EBOUNDS extensions then
   read the one in EBDnumber */

int ReadRMFEbounds(char *filename, long EBDnumber, struct RMF *rmf);

/* write the RMF ebounds to a FITS file */

int WriteRMFEbounds(char *filename, struct RMF *rmf);

/* write information about RMF to stdout */

void DisplayRMF(struct RMF *rmf);
 
/* return the channel for a photon of the given input energy - draws random
   numbers to return NumberPhotons entries in the channel array */

void ReturnChannel(struct RMF *rmf, float energy, int NumberPhotons, long *channel);

/* return channels for photons of the given input energies - draws random
   numbers to return NumberPhotons[i] entries for energy[i] in the channel array */

  void ReturnChannelMultiEnergies(struct RMF *rmf, int NumberEnergies, float *energy, 
				  int *NumberPhotons, long *channel);

/* normalize the response to unity in each energy */

void NormalizeRMF(struct RMF *rmf);

/* compress the response to remove all elements below the threshold value */

void CompressRMF(struct RMF *rmf, float threshold);

/* rebin the RMF in channel space */

int RebinRMFChannel(struct RMF *rmf, struct BinFactors *bins);

/* rebin the RMF in energy space */

int RebinRMFEnergy(struct RMF *rmf, struct BinFactors *bins);

/* transpose the matrix */

void TransposeRMF(struct RMF *rmf, struct RMFchan *rmfchan);

/* return a single value from the matrix */

float ReturnRMFElement(struct RMF *rmf, long channel, long energybin);
 float ReturnRMFchanElement(struct RMFchan *rmfchan, long channel, long energybin);

/* add rmf2 onto rmf1 */

int AddRMF(struct RMF *rmf1, struct RMF *rmf2);

/* read the effective areas from a FITS file - if there are multiple SPECRESP extensions then
   read the one in ARFFnumber */

int ReadARF(char *filename, long ARFnumber, struct ARF *arf);

/* write the ARF to a FITS file */

int WriteARF(char *filename, struct ARF *arf);

/* write information about ARF to stdout */

void DisplayARF(struct ARF *arf);

/* add arf2 onto arf1 */

int AddARF(struct ARF *arf1, struct ARF *arf2);

/* multiply the ARF into the RMF */

long MergeARFRMF(struct ARF *arf, struct RMF *rmf);

/* read the type I PHA extension from a FITS file - if there are multiple PHA 
   extensions then read the one in PHAnumber */

int ReadPHAtypeI(char *filename, long PHAnumber, struct PHA *phastruct);
 
/* read the type II PHA extension from a FITS file - if there are multiple PHA
   extensions then read the one in PHAnumber - within the typeII extension reads the 
   spectra listed in the SpectrumNumber vector */

int ReadPHAtypeII(char *filename, long PHAnumber, long NumberSpectra, long *SpectrumNumber, struct PHA **phastructs);

/* write the type I PHA extension to a FITS file */

int WritePHAtypeI(char *filename, struct PHA *phastruct);

/* write the type II PHA extension to a FITS file */

int WritePHAtypeII(char *filename, long NumberSpectra, struct PHA **phastructs);

/* return the type of a PHA extension */

int ReturnPHAtype(char *filename, long PHAnumber);

/* write information about spectrum to stdout */

void DisplayPHAtypeI(struct PHA *phastruct);

/* write information about spectra to stdout */

void DisplayPHAtypeII(long NumberSpectra, struct PHA **phastructs);

/* Rebin spectrum */

int RebinPHA(struct PHA *phastruct, struct BinFactors *bin);

/* return 0 if COUNTS column exists and is integer or COUNTS column does not exist */

int CheckPHAcounts(char *filename, long PHAnumber);

/* return the number of spectra in a type II PHA extension */

long ReturnNumberofSpectra(char *filename, long PHAnumber);

/* Read an ascii file with binning factors and load the binning array */

int SPReadBinningFile(char *filename, struct BinFactors *binning);

/* Set up a grouping array using the BinFactors structure */

int SPSetGroupArray(int inputSize, struct BinFactors *binning, int *groupArray);

/* Bin an array using the information in the grouping array */

int SPBinArray(int inputSize, float *input, int *groupArray, int mode, float *output);

/* Set the CCfits verbose mode */

void SPsetCCfitsVerbose(int mode);

/* copy all HDUs which are not manipulated by this library */

int SPcopyExtensions(char *infile, char *outfile);

/* copy all non-critical keywords for the hdunumber instance of the extension hduname. */

int SPcopyKeywords(char *infile, char *outfile, char *hduname, int hdunumber);

#ifdef __cplusplus
}
#endif
