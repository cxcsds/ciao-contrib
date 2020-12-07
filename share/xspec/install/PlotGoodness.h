//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

// Class to handle the plotting of a histogram of goodness simulations created
// by the last goodness command and stored in the Fit object.

#ifndef PLOTGOODNESS_H
#define PLOTGOODNESS_H 1

#include <XSUtil/Utils/XSutility.h>
// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
struct PlotGroup;
class PlotSettings;
struct StandardLabels;




class PlotGoodness : public PlotCommand  //## Inherits: <unnamed>%4B42732B01AF
{

  public:
      PlotGoodness();
      virtual ~PlotGoodness();

      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;
      virtual void processAdditionalParams(const StringArray& args, const IntegerVector& argIndices);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotGoodness(const PlotGoodness &right);
      PlotGoodness & operator=(const PlotGoodness &right);

      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class PlotGoodness 


#endif
