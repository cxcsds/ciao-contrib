//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTFOLDMODEL_H
#define PLOTFOLDMODEL_H 1

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
struct PlotGroup;
class PlotSettings;
struct StandardLabels;




class PlotFoldmodel : public PlotCommand  //## Inherits: <unnamed>%4B2006E90112
{

  public:
      PlotFoldmodel();
      virtual ~PlotFoldmodel();

      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotFoldmodel(const PlotFoldmodel &right);
      PlotFoldmodel & operator=(const PlotFoldmodel &right);

      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class PlotFoldmodel 


#endif
