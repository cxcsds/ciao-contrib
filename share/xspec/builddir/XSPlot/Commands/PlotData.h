//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTDATA_H
#define PLOTDATA_H 1
class PlotSettings;
struct StandardLabels;

// PlotCommand
#include <XSPlot/Plot/PlotCommand.h>




class PlotData : public PlotCommand  //## Inherits: <unnamed>%4ACCF32A0231
{

  public:
      PlotData (const string& name, bool isCounts);
      virtual ~PlotData();

      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotData(const PlotData &right);
      PlotData & operator=(const PlotData &right);

      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const bool m_isCounts;

    // Additional Implementation Declarations

};

// Class PlotData 


#endif
