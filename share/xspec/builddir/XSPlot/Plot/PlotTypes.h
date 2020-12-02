//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTTYPES_H
#define PLOTTYPES_H 1
#include <xsTypes.h>
#include <XSPlot/Plot/PlotStyle.h>
#include <utility>


class SpectralData;
class Model;
class SumComponent;
struct PlotGroup;
struct PlotVector;
class PlotCommand;

struct PlotRectangle
{
   Real x1;
   Real x2;
   Real y1;
   Real y2;
};

struct StandardLabels
{
   string x;
   string y;
   string title;
};




typedef std::list<SumComponent*> SourceList;



typedef std::list<PlotVector> PlotVectorList;
//	The outer vector indices correspond to the 0-based Plot
//	Pane index.  The inner vector contains the PlotGroups
//	assigned to that PlotPane.



typedef std::vector<std::vector<PlotGroup*> > PlotGroupContainer;



typedef std::multimap<size_t,SpectralData*> SpecGroup;



typedef SpecGroup::iterator SpecGroupIter;



typedef enum {VECTOR, CONTOUR} PlotKind;



typedef std::map<string,PlotCommand*> PlotCommandContainer;



typedef PlotCommandContainer::iterator PC_Iter;



typedef PlotCommandContainer::const_iterator PC_ConstIter;



typedef std::vector<std::map<size_t,size_t> > ModelPositionInfo;



typedef std::vector<std::vector<const Model*> > SpectraModelHolder;



struct PlotAttributes 
{
      PlotAttributes();

    // Data Members for Class Attributes
      PlotStyle::Colour color;
      PlotStyle::Symbol symbolStyle;
      PlotStyle::LineStyle lineStyle;
      int lineWidth;
      bool lineStep;

  public:
  protected:
  private:
  private: //## implementation
};



struct PlotRange 
{
      PlotRange();

    // Data Members for Class Attributes
      PlotStyle::ScaleType xScaleType;
      PlotStyle::ScaleType yScaleType;
      PlotRectangle ranges;
      //	Uses 4 PlotStyle::RangeFlags enumerators for bitwise
      //	coding of values 0-15.  If a particular bit is 0, its
      //	corresponding range limit will be set using the plotting
      //	package's default range finder.  Otherwise the ranges
      //	struct value is used.
      int useRangeFlags;
      //	The first member of the pair sets whether to draw a
      //	horizontal line across the full width of the viewport.
      //	The second member is the y-axis position of the line.
      std::pair<bool,Real> horizontalLine;
      //	May be used for storing the minimum statistic parameter
      //	of a 2D contour plot.
      std::pair<bool,Real> verticalLine;
      Real minStat;
      RealArray contourLevels;
      //	Intended only for 2D contour plots, the first (bool)
      //	member indicates whether a crosshair symbol should be
      //	displayed, while the second (pair<Real,Real>) gives its
      //	x-y position.
      std::pair<bool,std::pair<Real,Real> > addCrosshairs;
      //        Stores the min and max in an image. Intended for contour plots.
      std::pair<Real,Real> imageRange;
      //        String with image specification information such as cct
      string imageSpec;

  public:
  protected:
  private:
  private: //## implementation
};



typedef enum {CHANNELS, ENERGY, WAVELENGTH} XaxisMode;
//	Each entry in the line ID container is a pair containing
//	the label string for the line ID, and a Real specifying
//	its X-axis position.



typedef std::list<std::pair<string,Real> > LineIDContainer;

// Class PlotAttributes 

inline PlotAttributes::PlotAttributes()
  : color(PlotStyle::BLACK),
    symbolStyle(PlotStyle::BLANK),
    lineStyle(PlotStyle::NONE),
    lineWidth(1),
    lineStep(false)
{
}


// Class PlotRange 

inline PlotRange::PlotRange()
  :xScaleType(PlotStyle::LINEAR),
   yScaleType(PlotStyle::LINEAR),
   ranges(),
   useRangeFlags(0),
   horizontalLine(false,0.0),
   minStat(0.0),
   contourLevels(),
   addCrosshairs(false,std::pair<Real,Real>(.0,.0))
{
   ranges.x1 = ranges.y1 = 0.0;
   ranges.x2 = ranges.y2 = 1.0;
}



#endif
