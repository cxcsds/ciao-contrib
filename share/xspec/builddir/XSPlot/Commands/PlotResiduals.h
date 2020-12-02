//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTRESIDUALS_H
#define PLOTRESIDUALS_H 1

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
struct PlotGroup;
class PlotSettings;
struct StandardLabels;




class PlotResiduals : public PlotCommand  //## Inherits: <unnamed>%4B3274F50137
{

  public:
      PlotResiduals();
      virtual ~PlotResiduals();

      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;
      //	PlotCommand subclasses will determine whether to create
      //	plot groups from the donated plot group vector (coming
      //	from the previous plot) OR from scratch by calling their
      //	own PlotGroupCreator strategy.  Naturally it will always
      //	do the latter if the donated vector is empty.
      virtual std::vector<PlotGroup*> makePlotGroups (const PlotSettings& settings, const std::vector<const PlotGroup*>& donatedPlotGroups);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotResiduals(const PlotResiduals &right);
      PlotResiduals & operator=(const PlotResiduals &right);

      //	Once the raw data has been gathered into PlotGroup
      //	objects, this is the function that performs the various
      //	mathematical operations specific to each PlotCommand
      //	subclass.
      virtual void manipulate (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);
      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class PlotResiduals 


#endif
