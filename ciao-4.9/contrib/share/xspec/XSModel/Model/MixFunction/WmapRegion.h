//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef WMAPREGION_H
#define WMAPREGION_H 1
#include "xsTypes.h"

// Error
#include <XSUtil/Error/Error.h>
namespace CCfits
{
   class FITS;
}




class WmapRegion 
{

  public:



    class WmapRegionError : public YellowAlert  //## Inherits: <unnamed>%3FBB96D2030F
    {
      public:
          WmapRegionError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      virtual ~WmapRegion() = 0;
      std::pair<Real,Real> lowerLeft () const;
      std::pair<Real,Real> upperRight () const;
      int nx () const;
      int ny () const;
      const std::valarray<int>& wmap () const;
      int wmrbn () const;
      const CCfits::FITS* file () const;
      Real version () const;
      const IntegerArray& wmapPos () const;
      const std::valarray<bool>& isPixOn () const;

  public:
    // Additional Public Declarations

  protected:
      WmapRegion();

      void readCommonKeys ();
      virtual void readWmap (int* nullVal = 0);
      virtual void readSpecificKeys () = 0;
      void read (const string& fileName, int* nullVal = 0);

    // Additional Protected Declarations

  private:
      Real getVersion ();
      void getWmrbn ();
      void getCorners ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      std::pair<Real,Real> m_lowerLeft;
      std::pair<Real,Real> m_upperRight;
      int m_nx;
      int m_ny;
      std::valarray<int> m_wmap;
      int m_wmrbn;
      CCfits::FITS* m_file;
      std::pair<string,string> m_refBinKeys;
      string m_wmrbnKey;
      Real m_version;
      IntegerArray m_wmapPos;
      std::valarray<bool> m_isPixOn;

    // Additional Implementation Declarations

};

// Class WmapRegion::WmapRegionError 

// Class WmapRegion 

inline std::pair<Real,Real> WmapRegion::lowerLeft () const
{
  return m_lowerLeft;
}

inline std::pair<Real,Real> WmapRegion::upperRight () const
{
  return m_upperRight;
}

inline int WmapRegion::nx () const
{
  return m_nx;
}

inline int WmapRegion::ny () const
{
  return m_ny;
}

inline const std::valarray<int>& WmapRegion::wmap () const
{
  return m_wmap;
}

inline int WmapRegion::wmrbn () const
{
  return m_wmrbn;
}

inline const CCfits::FITS* WmapRegion::file () const
{
  return m_file;
}

inline Real WmapRegion::version () const
{
  return m_version;
}

inline const IntegerArray& WmapRegion::wmapPos () const
{
  return m_wmapPos;
}

inline const std::valarray<bool>& WmapRegion::isPixOn () const
{
  return m_isPixOn;
}


#endif
