//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTSUM_H
#define PLOTSUM_H 1

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
struct PlotGroup;
class PlotSettings;
struct StandardLabels;

//	This class is nothing but an empty shell -- a
//	placeholder of type PlotCommand.  When PlotDirector sees
//	this, it should replace it with a combination of other
//	PlotCommands.



class PlotSum : public PlotCommand  //## Inherits: <unnamed>%4B67503E0096
{

  public:
      PlotSum();
      virtual ~PlotSum();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotSum(const PlotSum &right);
      PlotSum & operator=(const PlotSum &right);

      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class PlotSum 


#endif
