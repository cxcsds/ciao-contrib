//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTVECTOR_H
#define PLOTVECTOR_H 1
#include <xsTypes.h>
#include <XSPlot/Plot/PlotTypes.h>




struct PlotVector 
{
      PlotVector();
      PlotVector (size_t arraySize);

      // npts corresponds to PlotGroup->n, the actual number of
      //  plotted points.  This is not necessarily the same as arraySize
      //  due to ignore/notice and plot binning.
      void getLimits(const size_t npts, Real& low, Real& high);

    // Data Members for Class Attributes
      std::vector<Real> data;
    // outer index of errors is data.size() while inner index is 1 or 2
    // depending on whether the errors are 1 or 2 sided.
      std::vector<std::vector<Real> > errors;
      PlotAttributes styles;

  public:
  protected:
  private:
  private: //## implementation
};

// Class PlotVector 


#endif
