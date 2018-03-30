//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef CONTOURPLOT_H
#define CONTOURPLOT_H 1

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
#include <xsTypes.h>
#include <XSstreams.h>
#include <XSPlot/Plot/CreateContourPlotGroups.h>
#include <XSPlot/Plot/PlotGroup.h>
#include <XSPlot/Plot/PlotSettings.h>
#include <XSPlot/Plot/PlotStyle.h>
#include <XSPlot/Plot/PlotTypes.h>
#include <XSFit/Fit/Grid.h>
#include <XSUtil/Error/Error.h>
#include <sstream>




template <typename T>
class ContourPlot : public PlotCommand  //## Inherits: <unnamed>%4B4D059B00CB
{

  public:
      ContourPlot();
      virtual ~ContourPlot();

      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;
      //	This provides a way of passing command-line arguments to
      //	the subset of PlotCommand classes which take them.  If
      //	not overriden this does nothing.
      virtual void processAdditionalParams (const StringArray& args, const IntegerArray& argIndices);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      ContourPlot(const ContourPlot< T > &right);
      ContourPlot< T > & operator=(const ContourPlot< T > &right);

      static bool verifyNLevels (size_t prevNLevels, size_t newNLevels, const IntegerArray& argIndices);
      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Parameterized Class ContourPlot 

// Parameterized Class ContourPlot 

template <typename T>
ContourPlot<T>::ContourPlot()
  : PlotCommand(ContourTraits<T>::cmdName, new CreateContourPlotGroups<T>())
{
   doesTakeParameters(true);
   isDataRequired(false);
   isActiveModelRequired(false);
   isDivisibleByArea(false);
   addCompLevel(0);
   isBackgroundApplicable(false);
   isContour(true);

   // 1-D contours will use x and yData.  2-D will
   // use x, yData, and model[0].
   PlotAttributes styles;
   styles.symbolStyle = PlotStyle::BLANK;
   styles.lineStyle = PlotCommand::standardModelStyle();
   styles.lineStep = false;
   styles.lineWidth = 1;
   setStyleMap(PlotStyle::DATA, styles);
   setStyleMap(PlotStyle::MODEL, styles);
}


template <typename T>
ContourPlot<T>::~ContourPlot()
{
}


template <typename T>
bool ContourPlot<T>::verifyNLevels (size_t prevNLevels, size_t newNLevels, const IntegerArray& argIndices)
{
   // Utility routine, checks that level values are available for all newNLevels
   // the user is requesting.  It assumes it can always fill in the first
   // prevNLevels with already existing values.  
   bool isOK = true;
   if (newNLevels > prevNLevels)
   {
      const size_t nArgs = argIndices.size();
      const int nOffset = 3; // 1st 3 arg positions are not level specifiers.
      BoolArray isEntered(newNLevels-prevNLevels, false);
      for (size_t i=0; i<nArgs; ++i)
      {
         int iLevel = argIndices[i] - nOffset;
         int alreadyExisting = static_cast<int>(prevNLevels);
         if (iLevel >= alreadyExisting && iLevel < static_cast<int>(newNLevels))
         {
            isEntered[iLevel - alreadyExisting] = true;
         }
      }
      for (size_t i=0; i<isEntered.size(); ++i)
      {
         if (!isEntered[i])
         {
            isOK = false;
            break;
         }
      }
   }
   return isOK;
}

template <typename T>
void ContourPlot<T>::setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings)
{
   PlotRange& rangeVals = rangeSettings();
   const Grid* grid = ContourPolicy<T>::getGrid();

   // NOTE: Ranges are NOT taken from the lowRange and highRange
   // members of ParameterSpec.  Those correspond to the user-
   // entered ranges, which may then be shifted to bin centers
   // (ie. as with margin).  The parameterValues array takes
   // this into account.   
   const Grid::SpecContainer& paramArray = grid->getParameter();
   // By this point we KNOW that grid is either 1-D or 2-D.
   const Grid::ParameterSpec* parSpec1 = paramArray[0];
   rangeVals.ranges.x1 = parSpec1->parameterValues.front();
   rangeVals.ranges.x2 = parSpec1->parameterValues.back();
   rangeVals.xScaleType = parSpec1->log ? PlotStyle::LOG : PlotStyle::LINEAR;
   rangeVals.horizontalLine.first = false;
   rangeVals.addCrosshairs.first = false;
   if (paramArray.size() < 2)
   {
      rangeVals.yScaleType = PlotStyle::LINEAR;
      rangeVals.ranges.y1 = grid->getGridValues().min();
      rangeVals.ranges.y2 = grid->getGridValues().max();
      rangeVals.useRangeFlags = PlotStyle::XMIN + PlotStyle::XMAX +
                              PlotStyle::YMIN + PlotStyle::YMAX;
      if (ContourTraits<T>::addHorizontalLine) {
	rangeVals.horizontalLine.first = true;
	rangeVals.horizontalLine.second = 
	  ContourPolicy<T>::getHorizLineVal(grid);
      }
   }
   else
   {
      const Grid::ParameterSpec* parSpec2 = paramArray[1];
      rangeVals.yScaleType = parSpec2->log ? PlotStyle::LOG : PlotStyle::LINEAR;
      rangeVals.ranges.y1 = parSpec2->parameterValues.front();
      rangeVals.ranges.y2 = parSpec2->parameterValues.back();
      rangeVals.useRangeFlags = PlotStyle::XMIN + PlotStyle::XMAX +
                              PlotStyle::YMIN + PlotStyle::YMAX;
      rangeVals.minStat = grid->minStat();
      rangeVals.contourLevels.resize(grid->contourLevels().size());
      rangeVals.contourLevels = grid->contourLevels();
      if (ContourTraits<T>::addCrosshair)
      {
         // Step grids set the value member of the ParameterSpecs to the
         // the x-y locations corresponding to the best fit.
         rangeVals.addCrosshairs.first = true;
         rangeVals.addCrosshairs.second.first = parSpec1->value;
         rangeVals.addCrosshairs.second.second = parSpec2->value;
      }
   }
   if ( settings.contBackImage() ) {
     rangeVals.imageRange.first = grid->getGridValues().min();
     rangeVals.imageRange.second = grid->getGridValues().max();
   } else {
     rangeVals.imageRange.first = settings.badDataValue();
     rangeVals.imageRange.second = rangeVals.imageRange.first;
   }
   rangeVals.imageSpec = ContourTraits<T>::imageSpec;

}

template <typename T>
void ContourPlot<T>::makeLabels (const PlotSettings& settings, StandardLabels& labels) const
{
   const Grid* grid = ContourPolicy<T>::getGrid();
   const size_t nDim = grid->getParameter().size();
   const string xparamLabel = ContourPolicy<T>::getParLabel(0, grid);
   // borrow label from chain plot:
   labels.x = settings.lookupLabelName("x:chain:parameter");
   labels.x += string(" ") + processSuperAndSub(xparamLabel);
   if (nDim == 2)
   {
      const string yparamLabel = ContourPolicy<T>::getParLabel(1, grid);
      labels.y = settings.lookupLabelName("x:chain:parameter");
      labels.y += string(" ") + processSuperAndSub(yparamLabel);
      labels.title = ContourPolicy<T>::getTitle(settings, 2);
   }
   else
   {
      labels.y = ContourPolicy<T>::getYLabel(settings);
      labels.title = ContourPolicy<T>::getTitle(settings, 1);
   }
}

template <typename T>
void ContourPlot<T>::processAdditionalParams (const StringArray& args, const IntegerArray& argIndices)
{
   // First lets verify that the required Grid exists.  This search is
   // different than the data/model validation in PlotCommand's verifyState
   // function, so we'll do it here instead.
   Grid* grid = ContourPolicy<T>::getGrid();
   ContourPolicy<T>::validate(grid);

   // Grid must either be 1D or 2D.
   if (grid->getParameter().size() > 2)
   {
      throw YellowAlert(" plot type not implemented: > 2-D confidence grid.\n");
   }

   // Args are <min stat> <# levels> <level values>
   // The default values are NOT taken from the user's previous entries.
   Real minStat = ContourPolicy<T>::getMinVal(grid);
   RealArray origLevels;
   ContourPolicy<T>::getInitLevels(grid,origLevels);
   size_t nLevels = origLevels.size();

   // First just handle the <min stat> and <# levels>.
   // If they exist, they must fall within the first nOFFSET args,
   // but note that arg index = 0 refers to the "contour" subcommand 
   // string which is NOT passed in here as part of args vector.  These
   // arg index values start at 1.
   const size_t nOFFSET = 2;
   size_t preLevelArgs = (args.size() < nOFFSET) ? args.size() : nOFFSET;
   for (size_t i=0; i<preLevelArgs; ++i)
   {
      std::istringstream iss(args[i]);
      if (argIndices[i] == 1)
      {
         Real testFloat = 0.0;
         if (!(iss >> testFloat) || !iss.eof())
         {
            string err("Invalid <min stat> argument: ");
            err += args[i] + "\n";
            throw YellowAlert(err);
         }
         minStat = testFloat;
      }
      else if (argIndices[i] == 2)
      {
         int testNLevels=0;
         if (!(iss >> testNLevels) || !iss.eof() || testNLevels < 1)
         {
            string err("Invalid <# levels> argument: ");
            err += args[i] + "\n";
            throw YellowAlert(err);
         }
         nLevels = static_cast<size_t>(testNLevels);
      }
   }
   const size_t prevNLevels = origLevels.size();
   if (!verifyNLevels(prevNLevels, nLevels, argIndices))
   {
      std::ostringstream msg;
      msg << "Not enough contour level values entered to create the "
          << nLevels << " requested levels.\n";
      throw YellowAlert(msg.str());
   }

   // OK, the number of levels requested is consistent with the level
   // values entered, now process the level values.
   RealArray newLevels(.0, nLevels);
   for (size_t i=0; i<prevNLevels && i<nLevels; ++i)
      newLevels[i] = origLevels[i];
   for (size_t i=0; i<args.size(); ++i)
   {
      const size_t iArg = static_cast<size_t>(argIndices[i]);
      if (iArg > nOFFSET)
      {
         const size_t iLevel = iArg - (nOFFSET+1);
         if (iLevel >= nLevels)
         {
            tcout << "***Warning: Contour levels entered beyond the number of\n"
              << "         requested levels will be ignored." << std::endl;
            break;
         }
         Real testLevel=.0;
         std::istringstream iss(args[i]);
         if (!(iss >> testLevel) || !iss.eof())
         {
            std::ostringstream msg;
            msg << "Improper value for contour level: " << args[i]<<"\n";
            throw YellowAlert(msg.str());
         }
         newLevels[iLevel] = testLevel;
      }
   }
   // And finally, verify that levels are in monotonically 
   // increasing order.
   Real prevLevel = newLevels[0];
   for (size_t j=1; j<nLevels; ++j)
   {
      if (newLevels[j] <= prevLevel)
      {
         string msg("Specified contour levels are not in increasing order.\n");
         throw YellowAlert(msg);
      }
      prevLevel = newLevels[j];
   }
   // Now convert these relative levels to absolute values and save in the
   // grid object
   RealArray absLevels;
   ContourPolicy<T>::getAbsoluteLevels(grid, newLevels, absLevels);
   grid->setContourLevels(absLevels);
   grid->minStat(minStat);
}

// Additional Declarations


#endif
