//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTGROUPCREATOR_H
#define PLOTGROUPCREATOR_H 1
#include <xsTypes.h>
#include <vector>


struct PlotGroup;
class PlotSettings;

//	Abstract strategy class for acquiring data from various
//	parts of Xspec and bundling into PlotGroups



class PlotGroupCreator 
{

  public:
      virtual ~PlotGroupCreator();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings) = 0;
      static void determineXRange (const std::vector<PlotGroup*>& plotGroups, Real* pXlow, Real* pXhigh);
      static void determineYRange (const std::vector<PlotGroup*>& plotGroups, Real* pYlow, Real* pYhigh);
      static Real NODATA ();

    // Additional Public Declarations

  protected:
      PlotGroupCreator();

      static void setXaxis (const PlotSettings& settings, PlotGroup* group, int firstChannel, int lastChannel, Real eMin, Real eMax, int point);

    // Additional Protected Declarations

  private:
      PlotGroupCreator(const PlotGroupCreator &right);
      PlotGroupCreator & operator=(const PlotGroupCreator &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const Real s_NODATA;

    // Additional Implementation Declarations

};

// Class PlotGroupCreator 

inline Real PlotGroupCreator::NODATA ()
{
  return s_NODATA;
}


#endif
