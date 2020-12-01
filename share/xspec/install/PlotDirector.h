//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTDIRECTOR_H
#define PLOTDIRECTOR_H 1

// PlotSettings
#include <XSPlot/Plot/PlotSettings.h>

class PlotPkg;
class PlotCommand;
#include <xsTypes.h>
#include <XSPlot/Plot/PlotTypes.h>
#include <XSUtil/Utils/XSutility.h>

//	Singleton class to perform the central role in gathering
//	data and displaying a plot.  It provides a central
//	location for storing the PlotSettings object and the
//	container of PlotGroups, and reduces the coupling among
//	the various plot classes (ie. Commands, Panes,
//	Packages).  It is not quite the classic GoF Mediator
//	pattern since it doesn't maintain 2-way communication
//	with a set of related Colleague classes (excepting Plot
//	Command), but it serves a similar purpose.



class PlotDirector 
{

  public:
    //	Plot units information:  The map key string is the
    //	identifier the user enters through setplot.  The value
    //	pair is composed of a string containing the unit's plot
    //	label appearance, and a Real for its conversion factor.



    typedef std::map<string,std::pair<string,Real>,XSutility::Nocase> UnitsContainer;
      ~PlotDirector();

      static PlotDirector* Instance (const string& plottingPackage, const string& labelDictionaryPath);
      //	This is the one-step public function for executing a
      //	plot.  It converts the requested PlotCommands into Plot
      //	Pages, and then displays them.
      void makePlot (const std::vector<PlotCommand*>& commands);
      PlotSettings& setplot ();
      //	Note that plotting device get and set functions are
      //	included here rather than PlotSettings since this
      //	setting must be immediately forwarded to the PlotPkg
      //	class.  It can't wait for makePlot to be called.
      void setPlottingDevice (const string& device, bool splashOn = true);
      const string& getPlottingDeviceName ();
      //	Sets PlotSetting's energy and wave unit information
      //	based on a case-insensitive match of the unitID string.
      //	Throws if no match is found. Mode should either be
      //	ENERGY or WAVELENGTH
      void selectUnits (const string& unitID, XaxisMode mode);
      const StringArray& lastCommand () const;
      void lastCommand (const StringArray& value);
      //	Stores the argument positions of the strings stored in
      //	lastCommand.  As per standard Xspec command-line comma
      //	usage, these need not be consecutive.
      const IntegerVector& lastCommandIndices () const;
      void lastCommandIndices (const IntegerVector& value);
      
      //	For accessing the results of a tclout plot call.
      const std::vector<Real>& savedPlotArray () const;
      //        For accessing a plot values array from Python.  Unlike 
      //        the tclout plot case in standard Xspec, in PyXspec the PlotGroups
      //        ARE KEPT until the next plot call.  Therefore this returns
      //        a reference to a currently existing PlotVector's data or errors
      //        array.  It does not copy things into the m_savedPlotArray vector.
      //        If it can't find the requested array, it THROWS. iPane and 
      //        iGroup indices are 0-based.
      const std::vector<Real>& getPlotArray(size_t iPane, size_t iGroup, PlotSettings::SaveArrayOption arrType, size_t& nPts) const;
      
      //	Hardcoding 2 plot features:
      //	1.  Max number of panes in a vertical stack.
      //	2.  Max number of vertical stacks.
      //	Perhaps in future, these should be attributes of
      //	particular PlotPkg classes, but PlotDirector is using
      //	this to determine whether x-axis is shared amongst panes
      //	in a stack.
      static size_t MAX_IN_STACK ();
      static size_t MAX_STACKS ();
      const PlotSettings& setplot () const;

  public:
    // Additional Public Declarations
      const PlotDirector::UnitsContainer& energyUnitsInformation () const;
      const PlotDirector::UnitsContainer& waveUnitsInformation () const;

  protected:
    // Additional Protected Declarations

  private:
      PlotDirector(const PlotDirector &right);
      PlotDirector (const string& plottingPackage, const string& labelDictionaryPath);
      PlotDirector & operator=(const PlotDirector &right);

      void loadLabelDictionary (const string& dictionaryPath);
      void loadUnitsInformation (const string& path);
      void clearPlotGroups () throw ();
      void fillPlotVectorAttributes (size_t iCmd);
      void determinePanesPerStack (std::vector<size_t>& panesPerStack) const;
      void determineSharedXaxis (const std::vector<size_t>& panesPerStack, std::vector<bool>& shareX) const;
      void setPlottingPackage (const string& packageName);
      void saveTcloutArray ();
      void buildLineIDList (const PlotRange& plotRange, LineIDContainer& lineIDs) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static PlotDirector* s_instance;
      const string m_labelDictionaryFile;
      //	Assume this is in the same directory as the label
      //	dictionary  file.  Therefore it doesn't need its own
      //	path specifier.
      const string m_unitsInformationFile;
      PlotDirector::UnitsContainer m_energyUnitsInformation;
      PlotDirector::UnitsContainer m_waveUnitsInformation;
      string m_plottingPackageName;
      StringArray m_lastCommand;
      IntegerVector m_lastCommandIndices;
      std::vector<Real> m_savedPlotArray;
      //	Stores PlotGroups, collated by 0-based PlotPane index.
      PlotGroupContainer m_groups;
      static const size_t s_MAX_IN_STACK;
      static const size_t s_MAX_STACKS;

    // Data Members for Associations
      PlotSettings m_setplot;
      PlotPkg* m_plotPackage;
      std::vector<PlotCommand*> m_plotCommands;

    // Additional Implementation Declarations

};
inline const PlotDirector::UnitsContainer& PlotDirector::energyUnitsInformation () const
{
   return m_energyUnitsInformation;
}

inline const PlotDirector::UnitsContainer& PlotDirector::waveUnitsInformation () const
{
   return m_waveUnitsInformation;
}

// Class PlotDirector 

inline PlotSettings& PlotDirector::setplot ()
{
   return m_setplot;
}

inline const StringArray& PlotDirector::lastCommand () const
{
  return m_lastCommand;
}

inline void PlotDirector::lastCommand (const StringArray& value)
{
  m_lastCommand = value;
}

inline const IntegerVector& PlotDirector::lastCommandIndices () const
{
  return m_lastCommandIndices;
}

inline void PlotDirector::lastCommandIndices (const IntegerVector& value)
{
  m_lastCommandIndices = value;
}

inline const std::vector<Real>& PlotDirector::savedPlotArray () const
{
  return m_savedPlotArray;
}

inline size_t PlotDirector::MAX_IN_STACK ()
{
  return s_MAX_IN_STACK;
}

inline size_t PlotDirector::MAX_STACKS ()
{
  return s_MAX_STACKS;
}

inline const PlotSettings& PlotDirector::setplot () const
{
  return m_setplot;
}


#endif
