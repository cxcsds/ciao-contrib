//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTEFFICIENCY_H
#define PLOTEFFICIENCY_H 1

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
struct PlotGroup;
class PlotSettings;
struct StandardLabels;




class PlotEfficiency : public PlotCommand  //## Inherits: <unnamed>%4B438914022A
{

  public:
      PlotEfficiency();
      virtual ~PlotEfficiency();

      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;
      virtual bool requestNewXoption (const PlotSettings& settings, XaxisMode& newOption) const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotEfficiency(const PlotEfficiency &right);
      PlotEfficiency & operator=(const PlotEfficiency &right);

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

// Class PlotEfficiency 


#endif
