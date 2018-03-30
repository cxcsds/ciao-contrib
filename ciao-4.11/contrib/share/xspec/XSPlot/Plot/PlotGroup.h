//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTGROUP_H
#define PLOTGROUP_H 1

// xsTypes
#include <xsTypes.h>
// PlotVector
#include <XSPlot/Plot/PlotVector.h>
// PlotTypes
#include <XSPlot/Plot/PlotTypes.h>
// PlotSettings
#include <XSPlot/Plot/PlotSettings.h>




struct PlotGroup 
{
      //	Except for xAxis, all PlotVectors will remain size 0
      //	unless explicitly set.  yData and model vectors can be
      //	set here upon construction, all others must be done from
      //	outside.
      PlotGroup (int arraySize, size_t nMods = 0, bool useYdata = true);
      //	Special constructor to be used for 2D contour plotting.
      //	This places the xVals and yVals values into the xAxis
      //	and yData PlotVectors, and sizes the model[0] array to
      //	(x size)*(y size).  No error vectors are created here.
      PlotGroup (const std::vector<Real>& xVals, const std::vector<Real>& yVals);

      friend bool operator < (const PlotGroup& left, const PlotGroup& right);
      //	A utility function intended for copying only the Plot
      //	Group attributes which are NOT dependent upon the
      //	distribution of filled PlotVectors (or their size -- n
      //	is not copied).  It also does not copy the objectIndex,
      //	as that must be unique for every PlotGroup.
      void copyAttributes (const PlotGroup& right);

      //        Find the lower and upper limits over all vectors in the group
      void getLimits(Real& low, Real& high);

    // Data Members for Class Attributes
      //	This is neither the xspec plot group number that the
      //	user may set through setplot, nor the group index number
      //	as used by PLT.  This is the index of the PlotGroup
      //	object where ALL PlotGroup objects in a (possibly
      //	multi-paned)  display are numbered consecutively 1..N.
      //	PlotDirector is the only class with the wherewithal to
      //	set this, as it has knowledge of all the PlotPanes that
      //	will make up the display.
      size_t objectIndex;
      //	ichtot from xspec 11.
      //
      //	This is the spacing in the channel axis (x) between
      //	this and the next plot group.
      int channelPlotSpacing;
      //	For standard plots, n should be the size of all
      //	non-empty PlotVectors.  For PlotGroups used in 2D
      //	contour plots, n = (xAxis size)*(yData size) = aux
      //	Data[0] size.
      size_t n;
      //	If true, the X and Y axis values will be stored in xAxis
      //	and yData vectors, and the grid values will be in the aux
      //	Data[0] vector.
      const bool is2Dcontour;
      Real critSignificance;
      int critNumChans;
      PlotSettings::PlotErrMode errorType;
      bool single;
      int lastInputChannel;
      int bin;
      std::vector<PlotVector*> bundledPlotVectors;
      IntegerArray plotVectorBoundaries;

    // Data Members for Associations
      RealArray saveData;
      PlotVector background;
      std::vector<PlotVectorList> sources;
      PlotVector xAxis;
      PlotVector yData;
      std::vector<PlotVector> model;
      std::vector<PlotVector> auxData;

  public:
  protected:
  private:
  private: //## implementation
};

// Class PlotGroup 


#endif
