//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PSF_H
#define PSF_H 1
#include <XSContainer.h>
#include <XSstreams.h>
#include <xsTypes.h>
#include <XSUtil/FunctionUtils/FunctionUtility.h>
#include <XSModel/Data/SpectralData.h>
#include <XSModel/GlobalContainer/DataContainer.h>
#include <XSUtil/Numerics/Numerics.h>
#include <XSUtil/Parse/XSparse.h>
#include <CCfits/CCfits>
#include <fstream>
#include <sstream>
#include <cstring>
#include <map>

// utility
#include <utility>
// Error
#include <XSUtil/Error/Error.h>
// MixUtility
#include <XSModel/Model/Component/MixUtility.h>
// PsfRegion
#include <PsfRegion.h>




template <typename T>
class Psf : public MixUtility  //## Inherits: <unnamed>%3F6F1D8401C3
{

  private:



    struct ImageKeys 
    {
          ImageKeys();

        // Data Members for Class Attributes
          Real xrefval;
          Real yrefval;
          Real xrefpix;
          Real yrefpix;
          Real xinc;
          Real yinc;
          Real rot;
          char coordtype[10];

      public:
      protected:
      private:
      private: //## implementation
    };

  public:



    struct Rectangle 
    {
        // Data Members for Class Attributes
          std::pair<Real,Real> lowerLeft;
          std::pair<Real,Real> upperRight;

      public:
      protected:
      private:
      private: //## implementation
    };
      Psf (const string& name);
      virtual ~Psf();

      virtual void initialize (const std::vector<Real>& params, const IntegerArray& specNums, const std::string& modelName);
      virtual void perform (const EnergyPointer& energy, const std::vector<Real>& params, GroupFluxContainer& flux, GroupFluxContainer& fluxError);
      virtual void initializeForFit (const std::vector<Real>& params, bool paramsAreFrozen);
      std::vector<std::vector<PsfRegion<T>*> >& regions ();
      const std::vector<Real>& binSizes () const;
      const RealArray& psfEnergy () const;

  public:
    // Additional Public Declarations

  protected:
      virtual void verifyData ();

  private:
      Psf(const Psf< T > &right);
      Psf< T > & operator=(const Psf< T > &right);

      bool getPosition ();
      void readImage (CCfits::PHDU& primaryHDU);
      Real convertRAorDEC (const string& stringVal, bool isRA);
      void clearRegions ();
      void clearImageKeys ();
      void calcSourceCentersFromCentroid ();
      void calcSurfaceBrightness ();
      void calcSourceCentersFromUser ();
      void sbFromImageFile ();
      void calcRectangle (size_t iObs);
      void fact ();
      void mix (const EnergyPointer& energy, GroupFluxContainer& fluxes, bool isError);
      int findPsfEngBracket (Real energy, int startFrom = 0) const;
      void calcSourceCenters ();
      bool changedParameters (const std::vector<Real>& params) const;
      bool getImageFile ();
      bool readFactFromFile (size_t iObs);
      bool writeFactToFile (size_t iObs, bool overwrite);
      bool checkReadWriteStatus () const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_ra;
      Real m_dec;
      string m_imageFileName;
      std::pair<int,int> m_imageSize;
      static const Real s_NOSET;
      std::vector<std::vector<PsfRegion<T>*> > m_regions;
      RealArray m_image;
      typename Psf<T>::ImageKeys m_ifKeys;
      std::vector<Real> m_binSizes;
      Real m_alpha;
      Real m_beta;
      Real m_core;
      int m_sbModelType;
      RealArray m_psfEnergy;
      RealArray m_factArray;
      bool m_parametersAreFrozen;
      bool m_dataChanged;
      // To keep track of gaps in dg numbering for this model:
      // Key = dg num, Val = 0-based order position of dg.
      std::map<size_t,size_t> m_dgOrder;

    // Data Members for Associations
      std::vector<std::pair< Real,Real > > m_sourceCenters;
      std::vector<Rectangle> m_obsRectangles;

    // Additional Implementation Declarations

};



class PsfError : public YellowAlert  //## Inherits: <unnamed>%3F9063E00366
{
  public:
      PsfError (const string& message);

  protected:
  private:
  private: //## implementation
};

// Class Psf::ImageKeys 

// Class Psf::Rectangle 

// Parameterized Class Psf 

template <typename T>
inline std::vector<std::vector<PsfRegion<T>*> >& Psf<T>::regions ()
{
  return m_regions;
}

template <typename T>
inline const std::vector<Real>& Psf<T>::binSizes () const
{
  return m_binSizes;
}

template <typename T>
inline const RealArray& Psf<T>::psfEnergy () const
{
  return m_psfEnergy;
}

// Class PsfError 

inline PsfError::PsfError (const string& message)
  :YellowAlert("Psf Error: ")
{
   std::cerr << message <<std::endl;
}


// Class Psf::ImageKeys 

template <typename T>
Psf< T >::ImageKeys::ImageKeys()
  : xrefval(.0), yrefval(.0), xrefpix(.0), yrefpix(.0), xinc(.0), yinc(.0),
   rot(.0)
{
  strcpy(coordtype, "");
}


// Class Psf::Rectangle 

// Parameterized Class Psf 
template <typename T>
const Real Psf<T>::s_NOSET = -999.0;

template <typename T>
Psf<T>::Psf (const string& name)
  : MixUtility(name),
        m_ra(s_NOSET),
        m_dec(.0),
        m_imageFileName(string("")),
        m_imageSize(0,0),
        m_regions(),
        m_image(),
        m_ifKeys(),
        m_binSizes(),
        m_alpha(.0),
        m_beta(.0),
        m_core(.0),
        m_sbModelType(0),
        m_psfEnergy(),
        m_factArray(),
        m_parametersAreFrozen(true),
        m_dataChanged(false),
        m_dgOrder(),
        m_sourceCenters(),
        m_obsRectangles()
{
  const size_t NE = T::NE;
  const Real* tmp = T::psfEnergy;
  m_psfEnergy.resize(NE);
  m_psfEnergy = RealArray(tmp, NE);
}


template <typename T>
Psf<T>::~Psf()
{
  clearRegions();
}


template <typename T>
void Psf<T>::initialize (const std::vector<Real>& params, const IntegerArray& spectrumNums, const std::string& modelName)
{
  //This function does a complete initialize.  This is what should
  // be called anytime datasets->Notify() is sent, or whenever
  // the model containing this component is first constructed.
  using namespace XSContainer;

  setSpecNums(spectrumNums);
  clearRegions();
  clearImageKeys();

  // NOTE:  this model requires an equal number of spectra (obs)
  // in each applicable data group (region).  
  verifyData();
  const size_t nObs = m_regions.size();
  // These conditions should been handled in verifyData:
  if (!nObs)
     throw RedAlert("Missing observation in Psf<T>::initialize");
  const size_t nReg = m_regions[0].size();
  if (!nReg)
     throw RedAlert("Missing region spectra in Psf<T>::initialize");
  // PsfRegion constructor can easily throw.  
  try
  {  
     std::vector<size_t> obsCounter(nReg, 0);
     for (size_t iSpec=0; iSpec<specNums().size(); ++iSpec)
     {
        const SpectralData* spec = datasets->lookup(specNums()[iSpec]);
        const size_t groupNum = spec->parent()->dataGroup();
        std::map<size_t,size_t>::const_iterator itOrder = m_dgOrder.find(groupNum);
        if (itOrder == m_dgOrder.end())
           throw RedAlert("Data group indexing error in Psf<T>::initialize");
        const size_t groupPosNum = itOrder->second;
        const size_t iObs = obsCounter[groupPosNum]++;
        const string fileName = spec->parent()->getFullPathName();
        m_regions[iObs][groupPosNum] = new PsfRegion<T>(fileName);
     }
     
     for (size_t i=0; i<nObs; ++i)
     {
        // Assumption:  wmrbn, skybin, and pixSize are the same
        // for all regions in an obs.  Therefore, just retrieve
        // it from the first region.
        
        std::vector<PsfRegion<T>*>& m_regions_i = m_regions[i];
        // WMAP binsize in arcminutes
        m_binSizes[i] = 60.0*m_regions_i[0]->pixSize()*m_regions_i[0]->wmrbn()/
                     static_cast<Real>(m_regions_i[0]->skybin());
        calcRectangle(i);
     }

     // This can also throw, by way of reading image file.
     m_dataChanged = true;
     initializeForFit(params, true);
  }
  catch (YellowAlert&)
  {
     clearRegions();
     throw;
  }
}

template <typename T>
void Psf<T>::perform (const EnergyPointer& energy, const std::vector<Real>& params, GroupFluxContainer& flux, GroupFluxContainer& fluxError)
{
  if (!m_imageFileName.length() && !m_parametersAreFrozen)
  {
     calcSurfaceBrightness();
     fact();
  }
  bool isError(!fluxError.empty());
  mix(energy, flux, false);
  if (isError)
  {
     mix(energy, fluxError, true);
  }
}

template <typename T>
void Psf<T>::verifyData ()
{
   using namespace XSContainer;
   if (!specNums().size())
   {
      string msg("Psf Model Error: No data assigned to projct, mixing will not be performed.");
      throw YellowAlert(msg);
   }
   m_dgOrder.clear();

   // Check that an equal # of spectra are assigned to each data group.
   std::map<size_t,size_t> groupCount;
   for (size_t iSpec=0; iSpec<specNums().size(); ++iSpec)
   {
       const SpectralData* spec = datasets->lookup(specNums()[iSpec]);
       const size_t groupNum = spec->parent()->dataGroup();
       if (groupCount.find(groupNum) == groupCount.end())
       {
          groupCount[groupNum] = 0;
       }
       groupCount[groupNum] += 1;  
   }
   std::map<size_t,size_t>::const_iterator itGroupCount = groupCount.begin();
   std::map<size_t,size_t>::const_iterator itGroupCountEnd = groupCount.end();
   const size_t nObs = itGroupCount->second;
   const size_t nRegions = groupCount.size();
   m_dgOrder[itGroupCount->first] = 0;
   size_t iGroup=1;
   ++itGroupCount;
   while (itGroupCount != itGroupCountEnd)
   {
      if (itGroupCount->second != nObs)
      {
         string msg(": all data groups must have the same number of spectra for psf mix model.");
         throw IncompatibleData(msg);
      }
      m_dgOrder[itGroupCount->first] = iGroup;
      ++itGroupCount;
      ++iGroup;
   }
   m_regions.resize(nObs);
   m_sourceCenters.resize(nObs);
   m_binSizes.resize(nObs, .0);
   m_obsRectangles.resize(nObs);
   for (size_t iObs=0; iObs<nObs; ++iObs)
   {
      m_regions[iObs].resize(nRegions, static_cast<PsfRegion<T>*>(0));
   }
}

template <typename T>
bool Psf<T>::getPosition ()
{
   const string PSF_RA = T::keywordRoot + string("-RA");
   const string PSF_DEC = T::keywordRoot + string("-DEC");
   bool isChanged = false;

   // Routine to get the source center RA and Dec 
   // (in degrees) as set by the user using the XSET command.  
   // If PSF-RA has not been set then m_ra = NOSET. 

   Real oldRa = m_ra;
   Real oldDec = m_dec;

   m_ra = s_NOSET;
   // If no image file specified, read RA instead.
   const string& raStringVal = FunctionUtility::getModelString(PSF_RA);
   if (raStringVal.length() && raStringVal != FunctionUtility::NOT_A_KEY())
   {
      m_ra = convertRAorDEC(raStringVal, true);
   }
   // Repeat for Dec.
   const string& decStringVal = FunctionUtility::getModelString(PSF_DEC);
   if (decStringVal.length() && decStringVal != FunctionUtility::NOT_A_KEY())
   {
      m_dec = convertRAorDEC(decStringVal, false);
   }
   if (std::fabs(m_ra-oldRa) > 1.0e-6 || std::fabs(m_dec-oldDec) > 1.0e-6)
                isChanged = true; 

   return isChanged;
}

template <typename T>
void Psf<T>::readImage (CCfits::PHDU& primaryHDU)
{
  fitsfile* fp = primaryHDU.fitsPointer();
  fp->HDUposition = 0;
  int status = 0;
  status = fits_read_img_coord(fp, &m_ifKeys.xrefval, &m_ifKeys.yrefval,
             &m_ifKeys.xrefpix,&m_ifKeys.yrefpix, &m_ifKeys.xinc,
             &m_ifKeys.yinc, &m_ifKeys.rot, m_ifKeys.coordtype, &status);
  if (status != 0 && status != APPROX_WCS_KEY)
  {
     std::ostringstream msg;
     msg << "CFITSIO error " << status <<
       " while attempting to read celestial coordinate system keywords\n" <<
       "   from file: " << m_imageFileName;
     throw PsfError(msg.str());
  }
  long nPix = static_cast<long>(m_imageSize.first)*static_cast<long>(m_imageSize.second);
  primaryHDU.read(m_image, 1, nPix);
}

template <typename T>
Real Psf<T>::convertRAorDEC (const string& stringVal, bool isRA)
{
  // If stringVal contains any ":", assume "hrs:min:sec" format,
  // else assume decimal degrees.
  Real floatVal = 0.0;
  string coord = isRA ? string("RA") : string("DEC");
  if (stringVal.find(':') != string::npos)
  {
     if (!Numerics::AstroFunctions::sexagesimalToDecimal(stringVal, floatVal))
     {
        string msg = "\nFormat error in ";
        msg += coord + " string value as entered with xset command.";
        msg += "\n   Proper format: \"hrs[:min[:sec]]\" or decimal value.";
	msg += "\n   String entered was " + stringVal;
        m_ra = s_NOSET;
        m_dec = .0;
        throw PsfError(msg);
     }
  }
  else
  {
     std::istringstream ssRa(stringVal);
     ssRa >> floatVal;
     if (!ssRa.eof())
     {
        string msg = "\nFormat error in ";
        msg += coord +" string value as entered with xset command.";
        msg += "\n   Proper format: \"hrs[:min[:sec]]\" or decimal value.";
	msg += "\n   String entered was " + stringVal;
        m_ra = s_NOSET;
        m_dec = .0;
        throw PsfError(msg);
     }
  }
  return floatVal;
}

template <typename T>
void Psf<T>::clearRegions ()
{
  size_t nObs = m_regions.size();
  for (size_t i=0; i<nObs; ++i)
  {
     // When regions container is fully filled, nReg should be 
     // the same for each obs.  But, it may not if we got here 
     // as a result of exception handling.
     std::vector<PsfRegion<T>*>& m_regions_i = m_regions[i];
     size_t nReg = m_regions_i.size();
     for (size_t j=0; j<nReg; ++j)
     {
        delete m_regions_i[j];
     }
  }
  m_regions.clear();   
}

template <typename T>
void Psf<T>::clearImageKeys ()
{
  m_ifKeys.xrefval = .0;
  m_ifKeys.yrefval = .0;
  m_ifKeys.xrefpix = .0;
  m_ifKeys.yrefpix = .0;
  m_ifKeys.xinc = .0;
  m_ifKeys.yinc = .0;
  m_ifKeys.rot = .0;
  strcpy(m_ifKeys.coordtype,"");
}

template <typename T>
void Psf<T>::calcSourceCentersFromCentroid ()
{
  size_t nObs = m_regions.size();
  if (m_sourceCenters.size() != nObs)
  {
     throw RedAlert("Psf source centers array not properly sized");
  }
  for (size_t i=0; i<nObs; ++i)
  {
     const std::vector<PsfRegion<T>*>& regions = m_regions[i];
     size_t nReg = regions.size();
     long wmapTot = 0;
     // rectangle is in detector coordinates
     const std::pair<Real,Real>& lowerLeft = m_obsRectangles[i].lowerLeft;
     int wmrbn = 1;
     m_sourceCenters[i].first = .0;
     m_sourceCenters[i].second = .0;
     for (size_t j=0; j<nReg; ++j)
     {
        int wmapSum = 0;
        const PsfRegion<T>* region = regions[j];
        std::pair<Real,Real> centroid = region->calcCentroid(wmapSum);
        wmapTot += wmapSum;
        // centroid is in wmap bins relative to the particular
        // region's xmin,ymin.  Need to convert it to bins relative
        // to the global rectangle.  This makes the assumption that
        // ALL regions in the same OBS have the same WMRBN value,
        // which converts wmap bins to detector coordinates.
        if (!j)
        {
           wmrbn = region->wmrbn();
        }
        std::pair<Real,Real> offset;
        offset.first = (region->lowerLeft().first - lowerLeft.first)/
                        static_cast<Real>(wmrbn);
        offset.second = (region->lowerLeft().second - lowerLeft.second)/
                        static_cast<Real>(wmrbn);
        m_sourceCenters[i].first += (centroid.first + offset.first)*wmapSum;
        m_sourceCenters[i].second += (centroid.second + offset.second)*wmapSum;
     }
     m_sourceCenters[i].first /= static_cast<Real>(wmapTot);
     m_sourceCenters[i].second /= static_cast<Real>(wmapTot);
  }
}

template <typename T>
void Psf<T>::calcSurfaceBrightness ()
{
  // If this function is used, it means there is no user-specified
  // image file from which to get the surface brightness.
  size_t nObs = m_regions.size();
  // Option for integrating over pixel bin
  const int ISUB = 1;  const Real SUBINV = 1.0/ISUB;

  for (size_t i=0; i<nObs; ++i)
  {
     size_t nReg = m_regions[i].size();
     const std::pair<Real,Real>& center = m_sourceCenters[i];
     const Rectangle& obsRect = m_obsRectangles[i];
     Real corbin = m_core/m_binSizes[i];
     for (size_t j=0; j<nReg; ++j)
     {
        PsfRegion<T>* region = m_regions[i][j];
        const IntegerArray& wmapPos = region->wmapPos();
        int wmapPosSz = wmapPos.size();
        int nx = region->nx();
        RealArray sbArray(.0, region->nx()*region->ny());
        // For each bin, need its distance from source center in 
        // bin units.  First, calc the offset of the region from the
        // entire observation's xmin,ymin.
        Real xOffset = (region->lowerLeft().first - obsRect.lowerLeft.first)
                        / region->wmrbn();
        Real yOffset = (region->lowerLeft().second - obsRect.lowerLeft.second)
                        / region->wmrbn();
        if (m_sbModelType == 0)
        {
           // Simple beta model           
           for (int k=0; k<wmapPosSz; ++k)
           {
              int ielem = wmapPos[k];
              int ixbin = ielem % nx;
              int iybin = ielem / nx;
              Real x = ixbin + xOffset - center.first;
              Real y = iybin + yOffset - center.second;
              for (int isubx=0; isubx<ISUB; ++isubx)
              {
                 for (int isuby=0; isuby<ISUB; ++isuby)
                 {
                    Real dist2 = (x-(isubx-ISUB/2.+.5)*SUBINV)*
                                 (x-(isubx-ISUB/2.+.5)*SUBINV) +
                                 (y-(isuby-ISUB/2.+.5)*SUBINV)*
                                 (y-(isuby-ISUB/2.+.5)*SUBINV);
                    sbArray[ielem] += SUBINV*SUBINV*pow((1.0+dist2/(corbin*corbin)),
                                        (-3.0*m_beta+.5));
                 }
              }
           }
        }
        else if (m_sbModelType == 1)
        {
           // two slope model
           for (int k=0; k<wmapPosSz; ++k)
           {
              int ielem = wmapPos[k];
              int ixbin = ielem % nx;
              int iybin = ielem / nx;
              Real x = ixbin + xOffset - center.first;
              Real y = iybin + yOffset - center.second;
              for (int isubx=0; isubx<ISUB; ++isubx)
              {
                 for (int isuby=0; isuby<ISUB; ++isuby)
                 {
                    Real dist2 = (x-(isubx-ISUB/2.+.5)*SUBINV)*
                                 (x-(isubx-ISUB/2.+.5)*SUBINV) +
                                 (y-(isuby-ISUB/2.+.5)*SUBINV)*
                                 (y-(isuby-ISUB/2.+.5)*SUBINV);
                    sbArray[ielem] += SUBINV*SUBINV*(pow(dist2,-m_alpha)*
                          exp(-dist2) + pow(dist2,-m_beta)*(1.0-exp(-dist2)));
                 }
              }
           }
        }

        // Normalize
        Real sbSum = sbArray.sum();
        if (sbSum != .0)
        {
           sbArray /= sbSum;
        }
        region->surfaceBrightness(sbArray);         

     } // end regions loop
  }
}

template <typename T>
void Psf<T>::calcSourceCentersFromUser ()
{
  size_t nObs = m_regions.size();
  for (size_t i=0; i<nObs; ++i)
  {
     const PsfRegion<T>* region1 = m_regions[i][0];
     Real rapnt = region1->refxcrval();
     Real decpnt = region1->refycrval();
     Real wmrbn = region1->wmrbn();
     Real xpix = region1->refxcrpix();
     Real ypix = region1->refycrpix();
     Real xpos = .0, ypos = .0;
     Real xdelt = region1->refxcdlt();
     Real ydelt = region1->refycdlt();
     char coordtype[] = "-TAN";
     int status = 0;
     fits_world_to_pix(m_ra, m_dec, rapnt, decpnt, xpix, ypix, xdelt, ydelt,
                0.0, coordtype, &xpos, &ypos, &status);
     if (status)
     {
        std::ostringstream msg;
        msg << "CFITSIO error " << status <<
           " while calculating source center from user RA and DEC for obs "
            << i+1;
	msg << "\n Source RA and DEC = " << m_ra << " " << m_dec;
	msg << "\n Reference RA and DEC = " << rapnt << " " << decpnt;
        throw PsfError(msg.str());
     }
     Real wfxf0 = region1->wfxf0();
     Real wfyf0 = region1->wfyf0();
     Real xsign = region1->xsign();
     Real ysign = region1->ysign();
     Real wftheta = region1->wftheta();
     Real xh = region1->wfxh0() + xsign*(xpos-wfxf0)*cos(wftheta)
                - xsign*(ypos-wfyf0)*sin(wftheta);
     Real yh = region1->wfyh0() + ysign*(xpos-wfxf0)*sin(wftheta)
                + ysign*(ypos-wfyf0)*cos(wftheta);

     m_sourceCenters[i].first = (xh - m_obsRectangles[i].lowerLeft.first)/wmrbn;
     m_sourceCenters[i].second = (yh - m_obsRectangles[i].lowerLeft.second)/wmrbn;
  }  
}

template <typename T>
void Psf<T>::sbFromImageFile ()
{
  size_t nObs = m_regions.size();
  for (size_t i=0; i<nObs; ++i)
  {
     std::vector<PsfRegion<T>*>& regions_i = m_regions[i];
     size_t nReg = regions_i.size();
     Real rfxval=.0, rfyval=.0, rfxpix=.0, rfypix=.0, rfxdlt=.0, rfydlt=.0;
     Real wfxh0=.0, wfyh0=.0, wfxf0=.0, wfyf0=.0;
     Real xsign=.0, ysign=.0, wftheta=.0;
     int wmrbn=1;
     for (size_t j=0; j<nReg; ++j)
     {
        PsfRegion<T>* region = regions_i[j];
        // Assume these are the same for each region in an obs.
        if (!j)
        {
           rfxval = region->refxcrval();
           rfyval = region->refycrval();
           rfxpix = region->refxcrpix();
           rfypix = region->refycrpix();
           rfxdlt = region->refxcdlt();
           rfydlt = region->refycdlt();
           wmrbn = region->wmrbn();
           wfxh0 = region->wfxh0();
           wfyh0 = region->wfyh0();
           wfxf0 = region->wfxf0();
           wfyf0 = region->wfyf0();
           xsign = region->xsign();
           ysign = region->ysign();
           wftheta = region->wftheta();
        }
        const size_t nx = region->nx();
        const size_t ny = region->ny();
        const Real xmin = region->lowerLeft().first;
        const Real ymin = region->lowerLeft().second;
        RealArray sbArray(.0, nx*ny);
        // For each pixel in sbArray (corresponding to an "on" pixel
        // in the wmap) calculate the sky position, then
        // take that sky position and find the appropriate pixel in the
        // image array.
        const IntegerArray& wmapPos = region->wmapPos();
        int wmapPosSz = wmapPos.size();
        for (int k=0; k<wmapPosSz; ++k)
        {
           int ielem = wmapPos[k];
           int ix = ielem % nx;
           int iy = ielem / nx;
           Real yh = static_cast<Real>(iy*wmrbn) + ymin - wfyh0;
           Real xh = static_cast<Real>(ix*wmrbn) + xmin - wfxh0;

           // Calculate the sky coordinate.
           Real xpxli = wfxf0 + xsign*xh*cos(wftheta) + ysign*yh*sin(wftheta);
           Real ypxli = wfyf0 - xsign*xh*sin(wftheta) + ysign*yh*cos(wftheta);

           Real xpos, ypos, xpxout, ypxout;
           int status = 0;
           char tantype[] = "-TAN";

           // Convert to input surface brightness image coordinates 
           // using the WCS keywords from the image

           fits_pix_to_world(xpxli, ypxli, rfxval, rfyval, rfxpix, rfypix, 
                     rfxdlt, rfydlt, 0.0, tantype, &xpos, &ypos, &status);

           // Convert to input surface brightness image 
           // coordinates using the WCS keywords from the image

          fits_world_to_pix(xpos, ypos, m_ifKeys.xrefval, m_ifKeys.yrefval,
                     m_ifKeys.xrefpix, m_ifKeys.yrefpix, m_ifKeys.xinc,
                     m_ifKeys.yinc, m_ifKeys.rot, m_ifKeys.coordtype, &xpxout,
                     &ypxout, &status);
           if (status)
           {
              std::ostringstream msg;
              msg << "CFITSIO error " << status << 
                " during surface brightness from image file calculation";
              throw PsfError(msg.str());
           }
           int ixpxl = int(xpxout) - 1;
           int iypxl = int(ypxout) - 1;
           if (ixpxl >= 0 && ixpxl < m_imageSize.first &&
                     iypxl >=0 && iypxl < m_imageSize.second)
           {
              sbArray[ielem] = m_image[iypxl*m_imageSize.first+ixpxl];
           }
        }
        // Normalize
        Real sbSum = sbArray.sum();
        if (sbSum != .0)
        {
           sbArray /= sbSum;
        }
        region->surfaceBrightness(sbArray);         
     }
  }
}

template <typename T>
void Psf<T>::calcRectangle (size_t iObs)
{
  // Get the smallest rectangle that encompasses all the regions
  // in a particular observation.
  const std::vector<PsfRegion<T>*>& regions = m_regions[iObs];
  size_t nReg = regions.size();
  Real globalXmin, globalYmin, globalXmax, globalYmax;
  std::pair<Real,Real> tmp;
  if (nReg)
  {
     tmp = regions[0]->lowerLeft();
     globalXmin = tmp.first;
     globalYmin = tmp.second;
     tmp = regions[0]->upperRight();
     globalXmax = tmp.first;
     globalYmax = tmp.second;
  }
  for (size_t i=1; i<nReg; ++i)
  {
     tmp = regions[i]->lowerLeft();
     globalXmin = std::min(globalXmin, tmp.first);
     globalYmin = std::min(globalYmin, tmp.second);
     tmp = regions[i]->upperRight();
     globalXmax = std::max(globalXmax, tmp.first);
     globalYmax = std::max(globalYmax, tmp.second); 
  }
  m_obsRectangles[iObs].lowerLeft.first = globalXmin;
  m_obsRectangles[iObs].lowerLeft.second = globalYmin;
  m_obsRectangles[iObs].upperRight.first = globalXmax;
  m_obsRectangles[iObs].upperRight.second = globalYmax;
}

template <typename T>
void Psf<T>::fact ()
{
  // Routine to calculate weighting from source to target regions. 
  // Returns fact(i,j,E) which is the weighting from region j to 
  // region i at energy E.
  bool overwrite = checkReadWriteStatus();      
  size_t nObs = m_regions.size();
  // nReg must be the same for each Obs, and if its reached this far
  // it and nObs must be non-zero.
  size_t nReg = m_regions[0].size();
  size_t npsfe = m_psfEnergy.size();
  m_factArray.resize(npsfe*nReg*nReg*nObs, .0);
  for (size_t iObs=0; iObs<nObs; ++iObs)
  {
     if (!readFactFromFile(iObs))
     {
        const std::vector<PsfRegion<T>*>& regions = m_regions[iObs];
        for (size_t iReg=0; iReg<nReg; ++iReg)
        {
           const PsfRegion<T>* sregion = regions[iReg];
           // wmapPos contains the positions of all non-neg pixels.
           const IntegerArray& sourcePixPos = sregion->wmapPos();
           size_t nSourcePix = sourcePixPos.size();
           size_t nxPix = sregion->nx();
           const RealArray& sourceSB = sregion->surfaceBrightness();
           // loop over source detector pixels
           for (size_t indSPix=0; indSPix<nSourcePix; ++indSPix)
           {
              int iSourceIdx = sourcePixPos[indSPix];
              size_t ixPix = iSourceIdx % nxPix;
              size_t iyPix = iSourceIdx / nxPix; 
	      Real SBfact = sourceSB[iSourceIdx];
              // loop over psf energies
              for (size_t ipsfe=0; ipsfe<npsfe; ++ipsfe)
              {
                 T::pointSpreadFunction(*this, iObs, iReg, ixPix, iyPix, ipsfe);
                 // loop over target regions
                 for (size_t itReg=0; itReg<nReg; ++itReg)
                 {
                    const PsfRegion<T>* tregion = regions[itReg];
                    const IntegerArray& targPixPos = tregion->wmapPos();
                    size_t nTargPix = targPixPos.size();
                    const RealArray& targetPSF = tregion->psfArray();
                    size_t iElem = iObs*nReg*nReg*npsfe + nReg*nReg*ipsfe
                                   + nReg*iReg + itReg;
                    // loop over target detector pixels
                    for (size_t indTPix=0; indTPix<nTargPix; ++indTPix)
                    {
                       int iTargIdx = targPixPos[indTPix];
                       // Accumulate in the factArray
                       // NOTE: the order in which the 4-D matrix is
                       // filled into the 1-D factArray is made to
                       // conform with the original FORTRAN code, 
                       // ie. fact(itReg,iReg,ipsfe,iobs) with itReg 
                       // varied first.
                       m_factArray[iElem] += SBfact*targetPSF[iTargIdx];
                    } // end loop over target detector pixels
                 } // end loop over target regions 
              } // end loop over psf energies             
           } // end loop source detector pixels
        } // end regions loop
     } // end if !readFromFile
     writeFactToFile(iObs, overwrite);
  } // end obs loop

  if (tpout.consoleChatterLevel() >=25 || tpout.logChatterLevel() >= 25)
  {
     tcout << xsverbose(25)<< "Psf fact array:" << std::endl;
     for (size_t iObs=0; iObs<nObs; ++iObs)
     {
        tcout << "Obs " << iObs+1 << "\n" << std::endl;
        for (size_t ipsfe=0; ipsfe<npsfe; ++ipsfe)
        {
           tcout << "Energy = " << m_psfEnergy[ipsfe] << std::endl;
           for (size_t itReg=0; itReg<nReg; ++itReg)
           {
              tcout << "  target " << itReg+1 <<": ";
              for (size_t iReg=0; iReg<nReg; ++iReg)
              {
                 size_t iElem = iObs*nReg*nReg*npsfe + nReg*nReg*ipsfe
                                   + nReg*iReg + itReg;
                 tcout << m_factArray[iElem] << " ";
              }
              tcout << std::endl;
           }
           tcout << std::endl;
        }
     }
     tcout << xsverbose();
  }
}

template <typename T>
void Psf<T>::mix (const EnergyPointer& energy, GroupFluxContainer& fluxes, bool isError)
{

  // EnergyPointer and GroupFluxContainer are maps of maps.  
  // The outer map being a collection of regions (data groups),
  // the inner map a collection of obs within the region.
  GroupFluxContainer tmpFlux(fluxes);
  GroupFluxContainer::iterator t(tmpFlux.begin());
  GroupFluxContainer::iterator tEnd(tmpFlux.end());
  // recall ArrayContainer == std::map<size_t,std::valarray<Real> > so that
  // s->second has a vectorized assignment operator that takes a scalar. 
  while ( t != tEnd )
  {
        ArrayContainer::iterator s (t->second.begin());
        ArrayContainer::iterator sEnd (t->second.end());
        for ( ; s != sEnd; ++s ) s->second = 0;
        ++t;         
  }

  const size_t nReg = fluxes.size();
  const size_t nPsfe = m_psfEnergy.size();
  // First loop: target regions (data groups)
  GroupFluxContainer::iterator itTFluxes = tmpFlux.begin();
  for (size_t iTReg=0; iTReg<nReg; ++iTReg, ++itTFluxes)
  {
     const size_t outerDgNum = itTFluxes->first;
     const ArrayContainer& energyContainer = *(energy.find(outerDgNum)->second);
     ArrayContainer& tregFlux = itTFluxes->second;
     const size_t nObs = tregFlux.size();
     // perform for each obs in the target region
     ArrayContainer::iterator itTObsFlux = tregFlux.begin();
     ArrayContainer::const_iterator itTEng = energyContainer.begin();
     for (size_t iObs=0; iObs<nObs; ++iObs, ++itTObsFlux, ++itTEng)
     {
        const RealArray& obsEngs = itTEng->second;
        RealArray& targetFlux = itTObsFlux->second;
        const size_t nE = obsEngs.size();
        size_t startFrom = 0;
        // loop through energies
        for (size_t iEng=0; iEng<nE-1; ++iEng)
        {
           Real centerE = (obsEngs[iEng] + obsEngs[iEng+1])/2.0;
           Real frac0=0.;
           Real frac1=0.;
           // get the psfEnergies which bracket this energy.
           int iPsfe = findPsfEngBracket(centerE, startFrom);
           if (iPsfe < 0)
           {
              startFrom = 0;
              iPsfe = 0;
              frac0 = 1.0;
              frac1 = 0.0;
           }
           else if (iPsfe == (int)nPsfe-1)
           {
              startFrom = iPsfe;
              frac0 = 0.0;
              frac1 = 1.0;
           }
           else
           {
              startFrom = iPsfe;
              Real deltaE = m_psfEnergy[iPsfe+1] - m_psfEnergy[iPsfe];
              frac1 = (centerE - m_psfEnergy[iPsfe])/deltaE;
              frac0 = (m_psfEnergy[iPsfe+1] - centerE)/deltaE;
           }
           // loop over source regions (data groups)
           GroupFluxContainer::const_iterator itSFluxes = fluxes.begin();
           for (size_t isReg=0; isReg<nReg; ++isReg, ++itSFluxes)
           {
              // See note in fact function for order of elements
              // in m_factArray.
              size_t iElem0 = iTReg + isReg*nReg + iPsfe*nReg*nReg + 
                                iObs*nPsfe*nReg*nReg;
              // Equivalent to incrementing iPsfe by 1 in above equation.
              size_t iElem1 = iElem0 + nReg*nReg;
              // Carefull, if iPsfe==nPsfe-1, then iElem1 is out of bounds.
              // But, in that case frac1 will be 0.0 anyway.
              Real weight = frac0*m_factArray[iElem0];
              if (iPsfe != (int)(nPsfe-1))
              {
                 weight += frac1*m_factArray[iElem1];
              }
              ArrayContainer::const_iterator itSObsFlux = itSFluxes->second.begin();
              for (size_t io=0; io<iObs; ++io, ++itSObsFlux);
              const RealArray& sourceFlux = itSObsFlux->second;
              if (isError)
              {
                 weight *= weight;
              }
              targetFlux[iEng] += sourceFlux[iEng]*weight;                            
           }
        } // end loop over energies
     } // end loop over obs
  } // end loop over target regions
  fluxes = tmpFlux;
}

template <typename T>
int Psf<T>::findPsfEngBracket (Real energy, int startFrom) const
{
  // Given an input energy, this function should find the energies 
  // that bracket it in the m_psfEnergy array.  It returns the index
  // of the lower energy of the bracket.  If energy is less than
  // all energies in the psfArray, it returns -1 (unless startFrom
  // parameter is used). If energy is greater than all psfArray 
  // energies, it returns nPsfe-1.

  // If startFrom parameter is used, only begin the search from 
  // index = startFrom.
  int iLowPsfe = (startFrom > 0) ? startFrom-1 : -1;
  int nPsfe = static_cast<int>(m_psfEnergy.size());
  if (energy >= m_psfEnergy[iLowPsfe + 1])
  {
     ++iLowPsfe;
     // iLowPsfe should now = 0, or startFrom, and 
     // energy is >= m_psfEnergy[iLowPsfe].
     while (iLowPsfe < (nPsfe-1) && energy >= m_psfEnergy[iLowPsfe+1])
     {
        ++iLowPsfe;
     }
     // Either m_psfEnergy[iLowPsfe] <= energy < m_psfEnergy[iLowPsfe+1]
     // or m_psfEnergy[nPsfe-1] <= energy.
  }
  return iLowPsfe;
}

template <typename T>
void Psf<T>::initializeForFit (const std::vector<Real>& params, bool paramsAreFrozen)
{
  // This is the initialization that should be performed in response
  // to a fit command, or a fit update call.  It is a subset of the  
  // general initialize function.
  bool paramsChanged = changedParameters(params);
  bool imageFileChanged = getImageFile();
  bool usingImageFile = m_imageFileName.length();
  bool positionChanged = getPosition();
  m_parametersAreFrozen = paramsAreFrozen;

  // If we got here immediately after first getting here from the 
  // initialize function (such as from the datasets->models->fit 
  // notify update chain), no problem. In that case, nothing below 
  // will be done. 
  if (paramsChanged)
  {
     m_alpha = params[0];
     m_beta = params[1];
     m_core = params[2];
     m_sbModelType = static_cast<int>(params[3]);
     if (usingImageFile)
     {
        tcout << "\n***Warning: psf mix model is calculating surface brightness from"
             << "\nuser specified image file.  Therefore, changing the mix model"
             << "\nparameters will have no effect on the calculation." 
             <<std::endl;
     }
  }

  if (m_dataChanged || positionChanged || paramsChanged || imageFileChanged)
  {
     if (usingImageFile)
     {
        if (imageFileChanged)
        {
           sbFromImageFile();
        }
     }
     else
     {
       // Although we're not reading from an image file, we still 
       // can get here when only the imageFileChanged flag 
       // is true.  In that case, the file name has been erased, 
       // yet ra,dec, and the params remain unchanged. The
       // surfaceBrightness array still needs to be recalculated.
        calcSourceCenters();
        calcSurfaceBrightness();
     }
     fact();
     // Now that m_dataChanged has had its desired effect, reset.
     m_dataChanged = false;
  }  
}

template <typename T>
void Psf<T>::calcSourceCenters ()
{
  // If no RA, DEC specified, will need to get source center
  // from centroid of regions.
  if (m_ra == s_NOSET)
  {
     calcSourceCentersFromCentroid();
  }
  else
  {
     calcSourceCentersFromUser();
  }
}

template <typename T>
bool Psf<T>::changedParameters (const std::vector<Real>& params) const
{
  return (std::fabs(m_alpha-params[0]) > 1.0e-6 ||
          std::fabs(m_beta-params[1]) > 1.0e-6  ||
          std::fabs(m_core-params[2]) > 1.0e-6  ||
          m_sbModelType != static_cast<int>(params[3]));
}


template <typename T>
bool Psf<T>::getImageFile ()
{
  using namespace CCfits;
  bool isChanged = false;
  const string PSF_IMAGE = T::keywordRoot + string("-IMAGE");
  string oldImageFile(m_imageFileName);
  std::pair<int,int> oldImageSize(m_imageSize);
  m_imageFileName = "";
  m_imageSize = std::pair<int,int>(0,0);

  const string& imageFile = FunctionUtility::getModelString(PSF_IMAGE);
  if (imageFile.length() && imageFile != FunctionUtility::NOT_A_KEY())
  {
     m_imageFileName = imageFile;
     try
     {
        std::auto_ptr<FITS> p(new FITS(m_imageFileName));
        PHDU& primary = p->pHDU();

        if (primary.axes() == 2)
        {
           m_imageSize.first = static_cast<int>(primary.axis(0));
           m_imageSize.second = static_cast<int>(primary.axis(1));
        }
        else
        {
           string msg("Primary HDU does not have 2 axes in image file");
           throw PsfError(msg);        
        }
        isChanged = (m_imageFileName != oldImageFile || m_imageSize != oldImageSize);
        if (isChanged)
        {
           readImage(primary);
        }
     }
     catch (CCfits::FITS::CantOpen)
     {
        string msg = "Cannot open image file: ";
        msg += m_imageFileName;
        throw PsfError(msg);
     }
     catch (CCfits::FitsException&)
     {
        string msg = "Error attempting to read image from file: ";
        msg += m_imageFileName;
        throw PsfError(msg);
     }
  }
  else
  {
     isChanged = (oldImageFile != string(""));
  }

  return isChanged;
}

template <typename T>
bool Psf<T>::readFactFromFile (size_t iObs)
{
   using namespace CCfits;
   bool status = false;
   const string nameKeyRoot = T::keywordRoot + string("-MIXFACT-IFILE");

   tpout << xsverbose(25);
   tcout << "Psf::readFactFromFile: Entry" << std::endl;
   std::ostringstream osstmp;
   osstmp << nameKeyRoot << iObs+1;
   const string nameKey(osstmp.str());
   const string fileName(FunctionUtility::getModelString(nameKey));
   if (fileName != FunctionUtility::NOT_A_KEY())
   {
      string errContext("Failed to open fact file: ");
      try
      {
         std::auto_ptr<FITS> pFile(new FITS(fileName));
         errContext = "Error reading header keys: ";
         PHDU& header = pFile->pHDU();
         long bitpix = header.bitpix();
         int nAxes = static_cast<int>(header.axes());
         errContext = "Fact file has wrong structure: ";
         if (bitpix != -64 || nAxes != 3)
            throw YellowAlert();
         size_t nRegs = m_regions[iObs].size();
         if (header.axis(0) != (int)nRegs || header.axis(1) != (int)nRegs
	     || header.axis(2) != (int)m_psfEnergy.size())
            throw YellowAlert();
         errContext = "Error reading fact array from image: ";
         long szCube = nRegs*nRegs*m_psfEnergy.size(); 
         RealArray tmpFact(.0, szCube); 
         header.read(tmpFact, 1, szCube);
         // Avoiding using a slice_array even though it may be
         // quicker due to some compilation trouble on 
         // Sci.Linux 4.0 w/ gcc 3.4.3.
         size_t offset = iObs*szCube;
         for (size_t i=0; i<static_cast<size_t>(szCube); ++i)
         {
            m_factArray[offset + i] = tmpFact[i];
         }
         status = true;
         tpout << xsverbose();
         tcout << "  Successfully read " << fileName << std::endl;
      }
      catch (...)
      {
         tpout << xsverbose();
         string msg = errContext + fileName + "\n";
         throw YellowAlert(msg);
      }
   }
   else
      tpout << xsverbose();
   return status;
}

template <typename T>
bool Psf<T>::writeFactToFile (size_t iObs, bool overwrite)
{

   using namespace CCfits;
   bool status = false;
   const string nameKeyRoot = T::keywordRoot + string("-MIXFACT-OFILE");

   tpout << xsverbose(25);
   tcout << "Psf::writeFactToFile Entry" << std::endl;
   std::ostringstream osstmp;
   osstmp << nameKeyRoot << iObs+1;
   const string nameKey(osstmp.str());
   const string fileName(FunctionUtility::getModelString(nameKey));
   if (fileName != FunctionUtility::NOT_A_KEY())
   {
      string errContext("Failed to initialize fact file: ");
      try
      {
         bool doWrite = true;
         // Test for already existing file.
         std::ifstream testFile(fileName.c_str());
         if (testFile && !overwrite)
         {
            doWrite = false;
         }
         testFile.close();
         if (doWrite)
         {
            const int bitpix = -64;
            const int nAxes = 3;
            long axisLengths[nAxes];
            const int nRegs = m_regions[iObs].size();
            axisLengths[0] = axisLengths[1] = static_cast<long>(nRegs);
            axisLengths[2] = static_cast<long>(m_psfEnergy.size());
            string qualFileName(fileName);
            // The '!' will force overwrites.
            qualFileName.insert(0, "!");
            std::auto_ptr<FITS> pFile(new FITS(qualFileName, bitpix, nAxes, axisLengths)); 
            errContext = "Failed to write data array: ";
            long szCube = nRegs*nRegs*m_psfEnergy.size();
            RealArray factSlice = m_factArray[std::slice(iObs*(size_t)szCube, 
                                (size_t)szCube, 1)];
            pFile->pHDU().write(1, szCube, factSlice);          
            status = true;
            tcout << xsverbose(10) <<"  Successfully wrote " << fileName 
               << std::endl << xsverbose();
         }
         tpout << xsverbose();
      }
      catch (...)
      {
         tpout << xsverbose();
         string msg = errContext + fileName + "\n";
         throw YellowAlert(msg);
      }
   }
   else   
      tpout << xsverbose();  
   return status;
}

template <typename T>
bool Psf<T>::checkReadWriteStatus () const
{
   bool status = true;
   size_t nObs = m_regions.size();
   const string inNameKeyRoot = T::keywordRoot + string("-MIXFACT-IFILE");
   const string outNameKeyRoot = T::keywordRoot + string("-MIXFACT-OFILE");
   // If any requested input files are missing, throw.
   for (size_t i=0; i<nObs; ++i)
   {
      std::ostringstream osstmp;
      osstmp << inNameKeyRoot << i+1;
      const string nameKey(osstmp.str());
      const string fileName(FunctionUtility::getModelString(nameKey));
      if (fileName == FunctionUtility::NOT_A_KEY())
      {
         tcout << "   No " << nameKey << " specified." << std::endl;
      }
      else
      {
         // Test for already existing file.
         std::ifstream testFile(fileName.c_str());
         if (!testFile)
         {
            string errMsg("Cannot open input fact array file: ");
            errMsg += fileName;
            throw PsfError(errMsg);
         }
      }
   }
   // If any output files exist, prompt user (all or nothing).
   StringArray existingFiles;
   for (size_t i=0; i<nObs; ++i)
   {
      std::ostringstream osstmp;
      osstmp << outNameKeyRoot << i+1;
      const string nameKey(osstmp.str());
      const string fileName(FunctionUtility::getModelString(nameKey));
      if (fileName == FunctionUtility::NOT_A_KEY())
      {
         tcout << "   No " << nameKey << " specified." << std::endl;
      }
      else
      {
         std::ifstream testFile(fileName.c_str());
         if (testFile)
         {
            existingFiles.push_back(fileName);
         }         
      }
   }
   if (existingFiles.size())
   {
      tcout << "The following requested output fact files already exist:"<<std::endl;
      for (size_t i=0; i<existingFiles.size(); ++i)
         tcout << "    " << existingFiles[i] << std::endl;
      string prompt("Do you want to replace these (y/n/a(bort))?");
      string reply;
      XSparse::basicPrompt(prompt, reply);
      status = reply.length() && (reply[0] == 'y' || reply[0] == 'Y');
      if (reply.length() && (reply[0] == 'a' || reply[0] == 'A'))
      {
         throw XSparse::AbortLoop();
      }  
   }
   return status;
}

// Additional Declarations


#endif
