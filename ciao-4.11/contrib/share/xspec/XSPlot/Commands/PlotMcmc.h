//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTMCMC_H
#define PLOTMCMC_H 1
#include <utility>

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>
struct PlotGroup;
class PlotSettings;
struct StandardLabels;




class PlotMcmc : public PlotCommand  //## Inherits: <unnamed>%4B465023033D
{

  public:
      PlotMcmc();
      virtual ~PlotMcmc();

      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;
      virtual void processAdditionalParams (const StringArray& args, const IntegerArray& argIndices);
      virtual void cleanup();
      
      // Override this function in order to keep track of pane indexing.
      virtual std::vector<PlotGroup*> makePlotGroups (const PlotSettings& settings, const std::vector<const PlotGroup*>& donatedPlotGroups);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotMcmc(const PlotMcmc &right);
      PlotMcmc & operator=(const PlotMcmc &right);

      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
       // This is for multiple panels of chain plots.  Need to know
       // the current chain plot pane index in order to access the 
       // proper values from the x,y name vector below. It is an int
       // since it is assigned -1 prior to first increment:  It
       // must be incremented PRIOR to its use in makeLabels since
       // makeLabels is a const function that can't perform the
       // increment. 
      int  m_paneCounter;
       // These are the x,y names of the user selected parameters,
       // which will be needed to make plot labels.  Any empty
       // string indicates that the fit statistic is to be used
       // instead (or row numbers if the xIsRowNum flag is set).
      std::vector<std::pair<string,string> > m_parNamesForPanes;
      std::vector<bool> m_xIsRowNumForPanes;

    // Additional Implementation Declarations

};

// Class PlotMcmc 


#endif
