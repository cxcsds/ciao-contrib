//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CREATECONTOURPLOTGROUPS_H
#define CREATECONTOURPLOTGROUPS_H 1
#include <xsTypes.h>
#include <XSFit/Fit/Grid.h>
#include <XSPlot/Plot/PlotGroup.h>
#include <XSPlot/Plot/PlotSettings.h>
#include <XSPlot/Plot/PlotStyle.h>
#include <XSPlot/Plot/PlotTypes.h>
#include <XSUtil/Error/Error.h>
#include <memory>

//debug
#include <XSstreams.h>


// PlotGroupCreator
#include <XSPlot/Plot/PlotGroupCreator.h>
class Step;
class MarginGrid;
class IntegProbGrid;

template<typename T>
class ContourPolicy;

template<>
class ContourPolicy<Step>
{
   public:
      static Grid* getGrid();
      static void validate(const Grid* grid);
      static Real getMinVal(const Grid* grid);
      static Real getHorizLineVal(const Grid* grid);
      static void getInitLevels(const Grid* grid, RealArray& relativeLevels);
      static void getAbsoluteLevels(const Grid* grid, 
				    const RealArray& relativeLevels, 
				    RealArray& absoluteLevels);
      static string getParLabel(size_t idx, const Grid* grid);
      static string getYLabel(const PlotSettings& settings);
      static string getTitle(const PlotSettings& settings, size_t nDim);
};

template<>
class ContourPolicy<MarginGrid>
{
   public:
      static Grid* getGrid();
      static void validate(const Grid* grid);
      static Real getMinVal(const Grid* grid);
      static Real getHorizLineVal(const Grid* grid);
      static void getInitLevels(const Grid* grid, RealArray& relativeLevels);
      static void getAbsoluteLevels(const Grid* grid, 
				    const RealArray& relativeLevels, 
				    RealArray& absoluteLevels);
      static string getParLabel(size_t idx, const Grid* grid);
      static string getYLabel(const PlotSettings& settings);
      static string getTitle(const PlotSettings& settings, size_t nDim);
};

template<>
class ContourPolicy<IntegProbGrid>
{
   public:
      static Grid* getGrid();
      static void validate(const Grid* grid);
      static Real getMinVal(const Grid* grid);
      static Real getHorizLineVal(const Grid* grid);
      static void getInitLevels(const Grid* grid, RealArray& relativeLevels);
      static void getAbsoluteLevels(const Grid* grid, 
				    const RealArray& relativeLevels, 
				    RealArray& absoluteLevels);
      static string getParLabel(size_t idx, const Grid* grid);
      static string getYLabel(const PlotSettings& settings);
      static string getTitle(const PlotSettings& settings, size_t nDim);
};

template<typename T>
struct ContourTraits;

template<>
struct ContourTraits<Step>
{
   static const string cmdName;
   static const bool addCrosshair;
   static const bool addHorizontalLine;
   static const string imageSpec;
};

template<>
struct ContourTraits<MarginGrid>
{
   static const string cmdName;
   static const bool addCrosshair;
   static const bool addHorizontalLine;
   static const string imageSpec;
};

template<>
struct ContourTraits<IntegProbGrid>
{
   static const string cmdName;
   static const bool addCrosshair;
   static const bool addHorizontalLine;
   static const string imageSpec;
};




template <typename T>
class CreateContourPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4B4CDBAE02A1
{

  public:
      CreateContourPlotGroups();
      virtual ~CreateContourPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateContourPlotGroups(const CreateContourPlotGroups< T > &right);
      CreateContourPlotGroups< T > & operator=(const CreateContourPlotGroups< T > &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Parameterized Class CreateContourPlotGroups 

// Parameterized Class CreateContourPlotGroups 

template <typename T>
CreateContourPlotGroups<T>::CreateContourPlotGroups()
  : PlotGroupCreator()
{
}


template <typename T>
CreateContourPlotGroups<T>::~CreateContourPlotGroups()
{
}


template <typename T>
std::vector<PlotGroup*> CreateContourPlotGroups<T>::createPlotGroups (const PlotSettings& settings)
{
   // ASSUME that ContourPlot has already verified the existence of the relevant
   // Grid during its processAdditionalArguments phase, and it should have
   // checked that it is 1 or 2D.

   std::vector<PlotGroup*> plotGroups;   
   const Grid* grid = ContourPolicy<T>::getGrid();
   const size_t nDim = grid->getParameter().size();

   if (nDim == 1)
   {
      const Grid::ParameterSpec* ps = grid->getParameter()[0];
      // Though this is a contour plot, for 1-D case it uses
      // the regular PlotGroup constructor.
      std::auto_ptr<PlotGroup> apGr(new PlotGroup(ps->parameterValues.size(),0,true));
      const size_t nPts = apGr->n;
      const RealArray& gridData = grid->getGridValues();
      std::vector<Real>& yVals = apGr->yData.data;
      apGr->xAxis.data = ps->parameterValues;
      for (size_t i=0; i<nPts; ++i)
         yVals[i] = gridData[i];
      apGr->xAxis.errors.clear();
      apGr->yData.errors.clear();
      plotGroups.push_back(apGr.release());
   }
   else if (nDim == 2)
   {   
      const Grid::ParameterSpec* xps = grid->getParameter()[0];
      const Grid::ParameterSpec* yps = grid->getParameter()[1];
      std::auto_ptr<PlotGroup> apGr(new PlotGroup(xps->parameterValues,
                           yps->parameterValues));

      std::vector<Real>& pgData = apGr->model[0].data;
      const RealArray& gridData = grid->getGridValues();
      const size_t nPts = gridData.size();
      if (nPts != apGr->n)
         throw RedAlert("Grid size mismatch in createPlotGroups function.");
      for (size_t i=0; i<nPts; ++i)
         pgData[i] = gridData[i];

      plotGroups.push_back(apGr.release());
   }
   return plotGroups;
}

// Additional Declarations


#endif
