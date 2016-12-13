//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CLUSTER_H
#define CLUSTER_H 1

// xsTypes
#include "xsTypes.h"
// utility
#include <utility>
// Error
#include <XSUtil/Error/Error.h>
// MixUtility
#include <XSModel/Model/Component/MixUtility.h>
namespace XSContainer {
    class DataContainer;
} // namespace XSContainer

class ClusterRegion;
class PsfImage;
class XRTResponse;




class Cluster : public MixUtility  //## Inherits: <unnamed>%3F6F1DD3004A
{

  public:



    class ClusterError : public YellowAlert  //## Inherits: <unnamed>%3FCBC3CB00C0
    {
      public:
          ClusterError (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      Cluster (const string& name);
      virtual ~Cluster();

      virtual void initialize (const std::vector<Real>& params, const IntegerArray& specNums, const std::string& modelName);
      virtual void perform (const EnergyPointer& energy, const std::vector<Real>& params, GroupFluxContainer& flux, GroupFluxContainer& fluxError);
      virtual void initializeForFit (const std::vector<Real>& params, bool paramsAreFixed);

  public:
    // Additional Public Declarations

  protected:
      virtual void verifyData ();

  private:
      Cluster(const Cluster &right);
      Cluster & operator=(const Cluster &right);

      void clearRegions ();
      void calcCentersOfEmission ();
      void clusterFact ();
      void calcEngIndices ();
      std::pair<Real,Real> getOptic (int instrument) const;
      bool isPixInRegions (int instrument, int ix, int iy) const;
      static void calcCoordinates (const Real xoff, const Real yoff, Real& theta, Real& phi);
      Real integrateSurfaceBrightness (const Real x, const Real y) const;
      int findPsfEngBracket (Real energy, int startFrom = 0) const;
      void doPerform (GroupFluxContainer& fluxes, bool isError);
      void calcGISEfficiency (int inst);
      bool changedParameters (const std::vector<Real>& params) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_alpha;
      Real m_beta;
      Real m_core;
      int m_sbModelType;
      RealArray m_factArray;
      bool m_parametersAreFrozen;
      std::vector<std::vector<ClusterRegion*> > m_regions;
      BoolArray m_instInUse;
      RealArray m_psfEnergy;
      std::string m_modelName;
      std::vector<std::vector<int> > m_engIndices;
      static Real s_PI;
      PsfImage* m_psfImage;
      static const string s_psfFileName;
      RealArray m_weight;
      static const string s_xrtFileName;
      XRTResponse* m_xrtResponse;
      bool m_dataChanged;
      EnergyPointer m_allEnergies;

    // Data Members for Associations
      std::vector<std::pair< Real,Real > > m_centers;
      std::vector<RealArray> m_psfArray;

    // Additional Implementation Declarations

};

// Class Cluster::ClusterError 

// Class Cluster 


#endif
