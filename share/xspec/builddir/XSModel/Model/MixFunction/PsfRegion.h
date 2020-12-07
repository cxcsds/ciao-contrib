//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PSFREGION_H
#define PSFREGION_H 1
#include <CCfits/CCfits>
#include <xsTypes.h>

// Error
#include <XSUtil/Error/Error.h>
// WmapRegion
#include "WmapRegion.h"




template <typename T>
class PsfRegion : public WmapRegion  //## Inherits: <unnamed>%3FBBE01B00C5
{

  public:



    class PsfRegionError : public YellowAlert  //## Inherits: <unnamed>%3F98191F02AC
    {
      public:
          PsfRegionError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      PsfRegion (const string& fileName);
      ~PsfRegion();

      std::pair<Real,Real> calcCentroid (int& wmapSum) const;
      const RealArray& psfArray () const;
      const RealArray& surfaceBrightness () const;
      void surfaceBrightness (const RealArray& value);
      int instrument () const;
      void instrument (int value);
      int skybin () const;
      void skybin (int value);
      Real pixSize () const;
      void pixSize (Real value);
      RealArray& psfArray ();
      const Real refxcrval () const;
      void refxcrval (Real value);
      const Real refycrval () const;
      void refycrval (Real value);
      const Real refxcrpix () const;
      void refxcrpix (Real value);
      const Real refycrpix () const;
      void refycrpix (Real value);
      const Real refxcdlt () const;
      void refxcdlt (Real value);
      const Real refycdlt () const;
      void refycdlt (Real value);
      const Real wfxf0 () const;
      void wfxf0 (Real value);
      const Real wfyf0 () const;
      void wfyf0 (Real value);
      const Real wfxh0 () const;
      void wfxh0 (Real value);
      const Real wfyh0 () const;
      void wfyh0 (Real value);
      const Real xsign () const;
      void xsign (Real value);
      const Real ysign () const;
      void ysign (Real value);
      const Real wftheta () const;
      void wftheta (Real value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      virtual void readSpecificKeys ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      RealArray m_surfaceBrightness;
      int m_instrument;
      int m_skybin;
      Real m_pixSize;
      RealArray m_psfArray;
      Real m_refxcrval;
      Real m_refycrval;
      Real m_refxcrpix;
      Real m_refycrpix;
      Real m_refxcdlt;
      Real m_refycdlt;
      Real m_wfxf0;
      Real m_wfyf0;
      Real m_wfxh0;
      Real m_wfyh0;
      Real m_xsign;
      Real m_ysign;
      Real m_wftheta;

    // Additional Implementation Declarations

};

// Class PsfRegion::PsfRegionError 

// Parameterized Class PsfRegion 

template <typename T>
inline const RealArray& PsfRegion<T>::surfaceBrightness () const
{
  return m_surfaceBrightness;
}

template <typename T>
inline void PsfRegion<T>::surfaceBrightness (const RealArray& value)
{
  if (m_surfaceBrightness.size() != value.size())
        m_surfaceBrightness.resize(value.size());
  m_surfaceBrightness = value;
}

template <typename T>
inline int PsfRegion<T>::instrument () const
{
  return m_instrument;
}

template <typename T>
inline void PsfRegion<T>::instrument (int value)
{
  m_instrument = value;
}

template <typename T>
inline int PsfRegion<T>::skybin () const
{
  return m_skybin;
}

template <typename T>
inline void PsfRegion<T>::skybin (int value)
{
  m_skybin = value;
}

template <typename T>
inline Real PsfRegion<T>::pixSize () const
{
  return m_pixSize;
}

template <typename T>
inline void PsfRegion<T>::pixSize (Real value)
{
  m_pixSize = value;
}

template <typename T>
inline RealArray& PsfRegion<T>::psfArray ()
{
  return m_psfArray;
}

template <typename T>
inline const Real PsfRegion<T>::refxcrval () const
{
  return m_refxcrval;
}

template <typename T>
inline void PsfRegion<T>::refxcrval (Real value)
{
  m_refxcrval = value;
}

template <typename T>
inline const Real PsfRegion<T>::refycrval () const
{
  return m_refycrval;
}

template <typename T>
inline void PsfRegion<T>::refycrval (Real value)
{
  m_refycrval = value;
}

template <typename T>
inline const Real PsfRegion<T>::refxcrpix () const
{
  return m_refxcrpix;
}

template <typename T>
inline void PsfRegion<T>::refxcrpix (Real value)
{
  m_refxcrpix = value;
}

template <typename T>
inline const Real PsfRegion<T>::refycrpix () const
{
  return m_refycrpix;
}

template <typename T>
inline void PsfRegion<T>::refycrpix (Real value)
{
  m_refycrpix = value;
}

template <typename T>
inline const Real PsfRegion<T>::refxcdlt () const
{
  return m_refxcdlt;
}

template <typename T>
inline void PsfRegion<T>::refxcdlt (Real value)
{
  m_refxcdlt = value;
}

template <typename T>
inline const Real PsfRegion<T>::refycdlt () const
{
  return m_refycdlt;
}

template <typename T>
inline void PsfRegion<T>::refycdlt (Real value)
{
  m_refycdlt = value;
}

template <typename T>
inline const Real PsfRegion<T>::wfxf0 () const
{
  return m_wfxf0;
}

template <typename T>
inline void PsfRegion<T>::wfxf0 (Real value)
{
  m_wfxf0 = value;
}

template <typename T>
inline const Real PsfRegion<T>::wfyf0 () const
{
  return m_wfyf0;
}

template <typename T>
inline void PsfRegion<T>::wfyf0 (Real value)
{
  m_wfyf0 = value;
}

template <typename T>
inline const Real PsfRegion<T>::wfxh0 () const
{
  return m_wfxh0;
}

template <typename T>
inline void PsfRegion<T>::wfxh0 (Real value)
{
  m_wfxh0 = value;
}

template <typename T>
inline const Real PsfRegion<T>::wfyh0 () const
{
  return m_wfyh0;
}

template <typename T>
inline void PsfRegion<T>::wfyh0 (Real value)
{
  m_wfyh0 = value;
}

template <typename T>
inline const Real PsfRegion<T>::xsign () const
{
  return m_xsign;
}

template <typename T>
inline void PsfRegion<T>::xsign (Real value)
{
  m_xsign = value;
}

template <typename T>
inline const Real PsfRegion<T>::ysign () const
{
  return m_ysign;
}

template <typename T>
inline void PsfRegion<T>::ysign (Real value)
{
  m_ysign = value;
}

template <typename T>
inline const Real PsfRegion<T>::wftheta () const
{
  return m_wftheta;
}

template <typename T>
inline void PsfRegion<T>::wftheta (Real value)
{
  m_wftheta = value;
}

// Class PsfRegion::PsfRegionError 

template <typename T>
PsfRegion< T >::PsfRegionError::PsfRegionError (const string& msg)
  : YellowAlert("Psf region error: ")
{
  std::cerr << msg << std::endl;
}


// Parameterized Class PsfRegion 

template <typename T>
PsfRegion<T>::PsfRegion (const string& fileName)
  : WmapRegion(),
    m_surfaceBrightness(),
    m_instrument(0),
    m_skybin(1),
    m_pixSize(.0),
    m_psfArray(),
    m_refxcrval(.0),
    m_refycrval(.0),
    m_refxcrpix(.0),
    m_refycrpix(.0),
    m_refxcdlt(.0),
    m_refycdlt(.0),
    m_wfxf0(.0),
    m_wfyf0(.0),
    m_wfxh0(.0),
    m_wfyh0(.0),
    m_xsign(1.0),
    m_ysign(1.0),
    m_wftheta(.0)   
{
  read(fileName);
}


template <typename T>
PsfRegion<T>::~PsfRegion()
{
}


template <typename T>
std::pair<Real,Real> PsfRegion<T>::calcCentroid (int& wmapSum) const
{
  std::pair<Real,Real> centroid(.0,.0);
  const std::valarray<int>& w_map = wmap();
  const IntegerVector& w_mapPos = wmapPos();
  //SunCC v6 has linker issues with using w_map.sum() here, so:
  size_t sz = w_map.size();
  for (size_t i=0; i<sz; ++i)
     wmapSum += w_map[i];
  int n_x = nx();

  sz = w_mapPos.size();
  for (size_t i=0; i<sz; ++i)
  {
     int ipos = w_mapPos[i];
     int ixpos = ipos % n_x;
     int iypos = ipos / n_x;
     centroid.first += ixpos*w_map[i];
     centroid.second += iypos*w_map[i];
  }

  centroid.first /= static_cast<Real>(wmapSum);
  centroid.second /= static_cast<Real>(wmapSum);
  return centroid;
}

template <typename T>
const RealArray& PsfRegion<T>::psfArray () const
{
  return m_psfArray;
}

template <typename T>
void PsfRegion<T>::readSpecificKeys ()
{
   T::readSpecificMapKeys(*this);
}

// Additional Declarations


#endif
