//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CREATEBINNEDPLOTGROUPS_H
#define CREATEBINNEDPLOTGROUPS_H 1
#include <XSPlot/Plot/PlotTypes.h>
#include <list>

// PlotGroupCreator
#include <XSPlot/Plot/PlotGroupCreator.h>




class CreateBinnedPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7CB9102EF
{

  public:
      CreateBinnedPlotGroups (bool isUnfolded, bool isCounts);
      virtual ~CreateBinnedPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);
      bool isUnfolded () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateBinnedPlotGroups(const CreateBinnedPlotGroups &right);
      CreateBinnedPlotGroups & operator=(const CreateBinnedPlotGroups &right);

      void itemizePlotGroupModels ();
      PlotGroup* initializePlotGroup (size_t groupIndex, std::list<SpectralData*>& groupSpectra);
      bool getNextPlotBin (PlotGroup* gr, int npts, std::list<SpectralData*>& groupSpectra, int& latestChannel);
      void integrateModelFluxes (std::list<SpectralData*>& spectra, Real eMin, Real eMax, PlotGroup* group, int point);
      void setError (PlotGroup* gr, int npts, Real areaSum, Real backAreaSum, 
        Real count, Real backgroundCount, Real bscaleRatio, bool allUsingChiSquare);
      static void initEffectiveAreas (std::list<SpectralData*>& spectraInGroup);
      static void clearEffectiveAreas (std::list<SpectralData*>& spectraInGroup);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const bool m_isUnfolded;
      ModelPositionInfo m_modelPositionDirectory;
      SpectraModelHolder m_modelsForSpectra;
      const PlotSettings* m_settings;
      const bool m_counts;

    // Additional Implementation Declarations

};

// Class CreateBinnedPlotGroups 

inline bool CreateBinnedPlotGroups::isUnfolded () const
{
  return m_isUnfolded;
}


#endif
