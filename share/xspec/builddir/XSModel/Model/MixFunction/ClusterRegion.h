//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CLUSTERREGION_H
#define CLUSTERREGION_H 1
#include "xsTypes.h"

// Error
#include <XSUtil/Error/Error.h>
// WmapRegion
#include "WmapRegion.h"




class ClusterRegion : public WmapRegion  //## Inherits: <unnamed>%3FBBE83202E5
{

  public:



    class ClusterRegionError : public YellowAlert  //## Inherits: <unnamed>%3FBCEA390112
    {
      public:
          ClusterRegionError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      ClusterRegion (const string& fileName, int regionNumber, size_t spectrumNumber);
      virtual ~ClusterRegion();

      static size_t NINST ();
      const std::pair<Real,Real> optic () const;
      int instrument () const;
      static const std::vector<std::string>& instrumentNames ();
      static const IntegerVector& instMapSizes ();
      std::pair<Real,Real> center () const;
      int nPixInRegion () const;
      int regionNumber () const;
      size_t spectrumNumber () const;
      const RealArray& instMapFractions () const;

  public:
    // Additional Public Declarations

  protected:
      virtual void readSpecificKeys ();

    // Additional Protected Declarations

  private:
      void convertNameToInt (const string& instrument);
      void calcInstMapFractions ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      std::pair<Real,Real> m_optic;
      int m_instrument;
      static std::vector<std::string> s_instrumentNames;
      static const size_t s_NINST;
      static IntegerVector s_instMapSizes;
      std::pair<Real,Real> m_center;
      int m_nPixInRegion;
      int m_regionNumber;
      size_t m_spectrumNumber;

    // Data Members for Associations
      RealArray m_instMapFractions;

    // Additional Implementation Declarations

};

// Class ClusterRegion::ClusterRegionError 

// Class ClusterRegion 

inline size_t ClusterRegion::NINST ()
{
  return s_NINST;
}

inline const std::pair<Real,Real> ClusterRegion::optic () const
{
  return m_optic;
}

inline int ClusterRegion::instrument () const
{
  return m_instrument;
}

inline const std::vector<std::string>& ClusterRegion::instrumentNames ()
{
  return s_instrumentNames;
}

inline const IntegerVector& ClusterRegion::instMapSizes ()
{
  return s_instMapSizes;
}

inline std::pair<Real,Real> ClusterRegion::center () const
{
  return m_center;
}

inline int ClusterRegion::nPixInRegion () const
{
  return m_nPixInRegion;
}

inline int ClusterRegion::regionNumber () const
{
  return m_regionNumber;
}

inline size_t ClusterRegion::spectrumNumber () const
{
  return m_spectrumNumber;
}

inline const RealArray& ClusterRegion::instMapFractions () const
{
  return m_instMapFractions;
}


#endif
