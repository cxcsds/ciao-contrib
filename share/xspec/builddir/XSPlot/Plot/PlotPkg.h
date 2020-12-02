//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTPKG_H
#define PLOTPKG_H 1
#include <xsTypes.h>
#include <XSPlot/Plot/PlotStyle.h>
#include <list>


class PlotPane;




class PlotPkg 
{

  public:
      virtual ~PlotPkg();

      virtual void setDevice (const string& device, bool splashOn = true) = 0;
      virtual Real BADVALUE () const;
      //	PlotPkg will take ownership of the PlotPane object that
      //	is passed here.  Function returns the number of Panes
      //	loaded (after this one is added).
      size_t addPane (PlotPane* pane) throw ();
      void clearPanes () throw ();
      //	Template Method wrapper for performing conversion of Plot
      //	Pane information to package-dependent display.
      void display ();
      //	Function for performing any optional buffer flushing and
      //	other cleanup tasks.  PlotDirector calls this one time
      //	after all other display functions have been performed,
      //	AND as part of its makePlot exception handling cleanup.
      virtual void flushHardcopy ();
      const string& deviceName () const;
      void deviceName (const string& value);
      //	If true, this tells PlotPkg that it may use the same
      //	x-axis scale (including ticks) for all plots within a
      //	vertical stack.
      const std::vector<bool>& shareXaxis () const;
      void shareXaxis (const std::vector<bool>& value);
      const std::vector<size_t>& panesInStack () const;
      void panesInStack (const std::vector<size_t>& value);
      //	A non-owning pointer, this points to the list of
      //	additional commands the user may have entered.  Leave it
      //	up to PlotPkg subclass to determine what (if anything)
      //	to do with it.
      const std::list<string>* userCommands () const;
      void setUserCommands (const std::list<string>* value);
      bool isInteractive () const;
      void isInteractive (bool value);
      static const std::vector<PlotStyle::VectorCategory>& vectorCategories ();

    // Additional Public Declarations

  protected:
      PlotPkg();
      const std::vector<PlotPane*>& plotPanes () const;

    // Additional Protected Declarations

  private:
      PlotPkg(const PlotPkg &right);
      PlotPkg & operator=(const PlotPkg &right);

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
      //	This is the only function in the display() Template
      //	Method which MUST BE OVERRIDDEN.  It is where any final
      //	plotting commands should be issued, and where the
      //	display is ultimately performed.
      virtual void doDisplay () = 0;
      //	This calculates the positions of each pane in generic
      //	coordinates:  the lower-left and upper-right positions
      //	of the largest allowed single-pane plot are by
      //	definition (0,0) and (1,1).  The actual plotting
      //	packages are free to use or ignore the results of these
      //	calculations within their setPanePosition functions.
      void calculatePanePositions ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_deviceName;
      std::vector<bool> m_shareXaxis;
      std::vector<size_t> m_panesInStack;
      const std::list<string>* m_userCommands;
      bool m_isInteractive;
      static std::vector<PlotStyle::VectorCategory> s_vectorCategories;

    // Data Members for Associations
      std::vector<PlotPane*> m_plotPanes;

    // Additional Implementation Declarations

};

// Class PlotPkg 

inline size_t PlotPkg::addPane (PlotPane* pane) throw ()
{
   m_plotPanes.push_back(pane);
   return m_plotPanes.size();
}

inline const string& PlotPkg::deviceName () const
{
  return m_deviceName;
}

inline void PlotPkg::deviceName (const string& value)
{
  m_deviceName = value;
}

inline const std::vector<bool>& PlotPkg::shareXaxis () const
{
  return m_shareXaxis;
}

inline void PlotPkg::shareXaxis (const std::vector<bool>& value)
{
  m_shareXaxis = value;
}

inline const std::vector<size_t>& PlotPkg::panesInStack () const
{
  return m_panesInStack;
}

inline void PlotPkg::panesInStack (const std::vector<size_t>& value)
{
  m_panesInStack = value;
}

inline const std::list<string>* PlotPkg::userCommands () const
{
  return m_userCommands;
}

inline void PlotPkg::setUserCommands (const std::list<string>* value)
{
  m_userCommands = value;
}

inline bool PlotPkg::isInteractive () const
{
  return m_isInteractive;
}

inline void PlotPkg::isInteractive (bool value)
{
  m_isInteractive = value;
}

inline const std::vector<PlotStyle::VectorCategory>& PlotPkg::vectorCategories ()
{
  return s_vectorCategories;
}

inline const std::vector<PlotPane*>& PlotPkg::plotPanes () const
{
  return m_plotPanes;
}


#endif
