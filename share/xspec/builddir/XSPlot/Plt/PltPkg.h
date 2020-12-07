//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLTPKG_H
#define PLTPKG_H 1
#include <xsTypes.h>
#include <XSPlot/Plot/PlotVector.h>

// PlotPkg
#include <XSPlot/Plot/PlotPkg.h>




class PltPkg : public PlotPkg  //## Inherits: <unnamed>%4AAE8B2403D8
{

  public:
      PltPkg();
      virtual ~PltPkg();

      virtual void setDevice (const string& device, bool splashOn = true);
      virtual Real BADVALUE () const;
      //	Function for performing any optional buffer flushing and
      //	other cleanup tasks.  PlotDirector calls this one time
      //	after all other display functions have been performed,
      //	AND as part of its makePlot exception handling cleanup.
      virtual void flushHardcopy ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PltPkg(const PltPkg &right);
      PltPkg & operator=(const PltPkg &right);

      void alignPlotVectors ();
      void determineMaxInCategory ();
      //	Wrapper for any operations or plotting commands that
      //	should be issued at the start, independent of the
      //	individual PlotPanes.
      virtual void doInitialize ();
      virtual void setPanePosition (const size_t iPane);
      virtual void setPaneRanges (const size_t iPane);
      virtual void setPaneStyles (const size_t iPane);
      virtual void setPaneLabels (const size_t iPane);
      virtual void setPaneLineIDs (const size_t iPane);
      //	This will be called only if pane is doing a 2-D contour
      //	plot.  It is intended to issue any additional
      //	package-specific commands required by the contour plot.
      virtual void setContourCmds (const size_t iPane);
      virtual void doDisplay ();
      size_t determineMaxCmdLength () const;
      //	Copy command strings to a C-style array of size nCmds*cmd
      //	Length for sending to Plt's Fortran function.
      char* commandsToC (int* pnCmds, int* pcmdLength) const;
      //	Copy m_nVecs of plot data (each with iery[iVec] error
      //	arrays) of size nPts to C-array for sending to Plt's
      //	Fortran function.
      float* dataToC (int** pnErrArrays, int* pnpts) const;
      //	This is for applying the Plt "mmaster" command to stacks
      //	of shared-X panes.  One pane must be set as the master
      //	to the rest of the panes in the stack.  It ensures that
      //	any rescaling of the master x-axis will also be applied
      //	to the other panes.
      void makeMasterWindows ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      //	Needed due to PLT's constraint that every PlotGroup must
      //	have an equal number of PlotVectors.  alignedPlotVectors
      //	will hold exactly m_nVec PlotVector pointers for every
      //	PlotGroup.  Some of these may be NULL pointers,
      //	indicating a dummy vector.
      std::vector<std::vector<PlotVector*> > m_alignedPlotVectors;
      std::vector<size_t> m_vecsInCategory;
      std::vector<size_t> m_errorVecsInCategory;
      std::vector<string> m_commands;
      //	This is the NVEC parameter sent to the PLT subroutine.
      //	It is the number of PlotVectors in each PlotGroup.  This
      //	includes the X vector but does not include error arrays.
      size_t m_nVec;
      //	PLT's constant for flagging "no data" and for
      //	delineating plot groups.
      static const float s_NO;
      //	Maximum number of numbered labels PLT is able to handle,
      //	counted over ALL plot panes.  This does not include
      //	standard x,y,title labels.
      static const size_t s_MAXNLABELS;
      static size_t s_lineIDCount;

    // Additional Implementation Declarations

};

// Class PltPkg 


#endif
