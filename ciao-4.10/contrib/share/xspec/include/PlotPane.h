//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTPANE_H
#define PLOTPANE_H 1


struct PlotGroup;
#include <xsTypes.h>
#include <XSPlot/Plot/PlotTypes.h>




class PlotPane 
{

  public:
      PlotPane (const PlotRange& ranges, const StandardLabels& labels, const std::vector<PlotGroup*>& plotGroups);
      ~PlotPane();

      //	This non-const get-by-reference function is to allow the
      //	LineIDContainer to be filled without having to do a
      //	copy, as would be necessary in a standard set function.
      //	This container can be quite large.
      LineIDContainer& lineIDs ();
      const PlotRange& ranges () const;
      void setRanges (const PlotRange& ranges);
      const StandardLabels& labels () const;
      //	This contains the positions of the lower-left and
      //	upper-right corners in generic coordinates, where the
      //	largest single pane may stretch from (0,0) to (1,1).
      //	Note that titles and axis labels and numbering are
      //	intended to reside outside of these coordinates.
      const PlotRectangle& panePosition () const;
      void panePosition (const PlotRectangle& value);
      //	A 0-based index indicating the vertical stack in which
      //	this pane resides.  It ought to be set no later than
      //	when panePosition is set.
      size_t stackIndex () const;
      void stackIndex (size_t value);
      //	True if this is a 2-D contour plot.
      bool isContour () const;
      //	Optional line ID strings.  PlotDirector will attempt to
      //	fill this if setplot ID is turned on AND it is
      //	applicable to the PlotCommand AND the X-axis mode IS NOT
      //	channels.
      const LineIDContainer& lineIDs () const;
      //	PlotPane does not own these.  The are "loaned" to it by
      //	PlotDirector.
      const std::vector<PlotGroup*>& plotGroups () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotPane(const PlotPane &right);
      PlotPane & operator=(const PlotPane &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      PlotRange m_ranges;
      const StandardLabels m_labels;
      PlotRectangle m_panePosition;
      size_t m_stackIndex;
      const bool m_isContour;
      LineIDContainer m_lineIDs;

    // Data Members for Associations
      const std::vector<PlotGroup*> m_plotGroups;

    // Additional Implementation Declarations

};

// Class PlotPane 

inline LineIDContainer& PlotPane::lineIDs ()
{
   return m_lineIDs;
}

inline const PlotRange& PlotPane::ranges () const
{
  return m_ranges;
}

inline void PlotPane::setRanges (const PlotRange& ranges )
{
  m_ranges = ranges;
  return;
}

inline const StandardLabels& PlotPane::labels () const
{
  return m_labels;
}

inline const PlotRectangle& PlotPane::panePosition () const
{
  return m_panePosition;
}

inline void PlotPane::panePosition (const PlotRectangle& value)
{
  m_panePosition = value;
}

inline size_t PlotPane::stackIndex () const
{
  return m_stackIndex;
}

inline void PlotPane::stackIndex (size_t value)
{
  m_stackIndex = value;
}

inline bool PlotPane::isContour () const
{
  return m_isContour;
}

inline const LineIDContainer& PlotPane::lineIDs () const
{
  return m_lineIDs;
}

inline const std::vector<PlotGroup*>& PlotPane::plotGroups () const
{
  return m_plotGroups;
}


#endif
