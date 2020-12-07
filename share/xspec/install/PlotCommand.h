//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTCOMMAND_H
#define PLOTCOMMAND_H 1
#include <xsTypes.h>
#include <XSPlot/Plot/PlotTypes.h>
class PlotGroupCreator;
struct PlotGroup;
class PlotSettings;




class PlotCommand 
{

  public:
      virtual ~PlotCommand();

      //	Actions to be performed once for all PlotCommand objects
      //	at the start of each makePlot run.
      static void commonInit ();
      //	For each PlotCommand object, verifies that the necessary
      //	data and/or models are currently loaded, throws if not.
      void verifyState () const;
      const PlotRange& getRangeSettings () const;
      //	Template pattern method (calling private virtual
      //	functions) for performing command-specific operations on
      //	PlotGroup data (ie. calculations and range setting).
      void processPlotGroups (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);
      //	If not overridden, this does nothing.
      virtual void makeLabels (const PlotSettings& settings, StandardLabels& labels) const;
      //	Some PlotCommands may need to enforce an xOption mode
      //	that differs from the user's current setting.  They can
      //	override this to request a change by returning TRUE, and
      //	by setting the newOption arg with the new value.  If
      //	this returns FALSE, newOption will not be modified
      //	(which is the default function behavior). Note that this
      //	does not actually modify PlotSetting's xOption, it
      //	merely requests.
      virtual bool requestNewXoption (const PlotSettings& settings, XaxisMode& newOption) const;
      //	This provides a way of passing command-line arguments to
      //	the subset of PlotCommand classes which take them.  If
      //	not overriden this does nothing.
      virtual void processAdditionalParams (const StringArray& args, const IntegerVector& argIndices);
      //        Originally needed only for those commands which take additional
      //        parameters.  They use this to clear their parameters at
      //        the end of a makePlot run (or in case of Exception).
      virtual void cleanup();
      //	PlotCommand subclasses will determine whether to create
      //	plot groups from the donated plot group vector (coming
      //	from the previous plot) OR from scratch by calling their
      //	own PlotGroupCreator strategy.  Naturally it will always
      //	do the latter if the donated vector is empty.
      virtual std::vector<PlotGroup*> makePlotGroups (const PlotSettings& settings, const std::vector<const PlotGroup*>& donatedPlotGroups);
      const string& cmdName () const;
      //	True if the command may take additional (optional)
      //	arguments from the command line.
      bool doesTakeParameters () const;
      //	Flag is true for commands which are affected by the
      //	setplot area setting.
      bool isDivisibleByArea () const;
      //	Determines the level of add component display for this
      //	command:  0 = not applicable (never display), 1 =
      //	display add comp if user chooses (w/ setplot add), 2 =
      //	display folded add comp if user chooses, 3 = display
      //	added comp regardless of user's selection, 4 = display
      //	folded add comp regardless of user's selection.
      int addCompLevel () const;
      bool isBackgroundApplicable () const;
      bool isLineIDApplicable () const;
      //	A plot group donor is a PlotCommand which might
      //	influence the succeeding PlotCommand in a multi-pane
      //	plot.  An example being "data ratio" or "icounts ratio",
      //	which produce different behavior in the ratio plot.  In
      //	this situation, the second plot will want to make use of
      //	the first plot's plot groups.
      bool isPlotGroupDonor () const;
      bool isContour () const;
      const std::map<PlotStyle::VectorCategory,PlotAttributes>& styleMap () const;
      //	Stores in a single place the default model line style
      //	from which all subclasses using model PlotVectors may
      //	set their  line-style attribute.  If a general change in
      //	appearance is decided upon, it need only be modified
      //	here.
      static PlotStyle::LineStyle standardModelStyle ();
      //	Stores in a single place the default data symbol style
      //	from which all subclasses using data PlotVectors may set
      //	their  symbol-style attribute.  If a general change in
      //	appearance is decided upon, it need only be modified
      //	here.
      static PlotStyle::Symbol standardDataStyle ();
      PlotGroupCreator* plotGroupStrategy () const;

    // Additional Public Declarations

  protected:
      PlotCommand (const string& cmdName, PlotGroupCreator* plotGroupStrategy);

      void setStyleMap (PlotStyle::VectorCategory category, const PlotAttributes& attributes);
      void doesTakeParameters (bool flag);
      void isDivisibleByArea (bool value);
      void addCompLevel (int level);
      void isBackgroundApplicable (bool value);
      void isLineIDApplicable (bool value);
      void isPlotGroupDonor (bool value);
      void isContour (bool value);
      //	Convert '^' and '_' super and subscript symbols in
      //	parameter labels, originally only used by Contour
      //	Plot<T>.  This is borderline PLT specific, but resides
      //	here since it's more natural to perform the conversions
      //	when the labels are originally set.
      static string processSuperAndSub (const string& inString);
      bool isDataRequired () const;
      void isDataRequired (bool value);
      bool isActiveModelRequired () const;
      void isActiveModelRequired (bool value);
      PlotRange& rangeSettings ();
      //	Updated at the start of each makePlot call, set to true
      //	if any spectra are loaded.
      static bool dataStatus ();
      //	Updated at the start of each makePlot call, set to true
      //	if any active models are found.
      static bool activeModelStatus ();

    // Additional Protected Declarations

  private:
      PlotCommand(const PlotCommand &right);
      PlotCommand & operator=(const PlotCommand &right);

      //	Once the raw data has been gathered into PlotGroup
      //	objects, this is the function that performs the various
      //	mathematical operations specific to each PlotCommand
      //	subclass.
      virtual void manipulate (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings);
      //	Determines plot-time range settings based on current
      //	setplot settings and PlotGroup data.
      virtual void setRanges (std::vector<PlotGroup*>& plotGroups, const PlotSettings& settings) = 0;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const string m_cmdName;
      PlotGroupCreator* const m_plotGroupStrategy;
      bool m_doesTakeParameters;
      bool m_isDataRequired;
      bool m_isActiveModelRequired;
      bool m_isDivisibleByArea;
      int m_addCompLevel;
      bool m_isBackgroundApplicable;
      bool m_isLineIDApplicable;
      bool m_isPlotGroupDonor;
      bool m_isContour;
      std::map<PlotStyle::VectorCategory,PlotAttributes> m_styleMap;
      PlotRange m_rangeSettings;
      static bool s_dataStatus;
      static bool s_activeModelStatus;
      static const PlotStyle::LineStyle s_standardModelStyle;
      static const PlotStyle::Symbol s_standardDataStyle;

    // Data Members for Associations

    // Additional Implementation Declarations

};

// Class PlotCommand 

inline void PlotCommand::doesTakeParameters (bool flag)
{
   m_doesTakeParameters = flag;
}

inline void PlotCommand::isDivisibleByArea (bool value)
{
   m_isDivisibleByArea = value;
}

inline void PlotCommand::addCompLevel (int level)
{
   m_addCompLevel = level;
}

inline void PlotCommand::isBackgroundApplicable (bool value)
{
   m_isBackgroundApplicable = value;
}

inline void PlotCommand::isLineIDApplicable (bool value)
{
   m_isLineIDApplicable = value;
}

inline void PlotCommand::isPlotGroupDonor (bool value)
{
   m_isPlotGroupDonor = value;
}

inline void PlotCommand::isContour (bool value)
{
   m_isContour = value;
}

inline const PlotRange& PlotCommand::getRangeSettings () const
{
   return m_rangeSettings;
}

inline const string& PlotCommand::cmdName () const
{
  return m_cmdName;
}

inline bool PlotCommand::doesTakeParameters () const
{
  return m_doesTakeParameters;
}

inline bool PlotCommand::isDataRequired () const
{
  return m_isDataRequired;
}

inline void PlotCommand::isDataRequired (bool value)
{
  m_isDataRequired = value;
}

inline bool PlotCommand::isActiveModelRequired () const
{
  return m_isActiveModelRequired;
}

inline void PlotCommand::isActiveModelRequired (bool value)
{
  m_isActiveModelRequired = value;
}

inline bool PlotCommand::isDivisibleByArea () const
{
  return m_isDivisibleByArea;
}

inline int PlotCommand::addCompLevel () const
{
  return m_addCompLevel;
}

inline bool PlotCommand::isBackgroundApplicable () const
{
  return m_isBackgroundApplicable;
}

inline bool PlotCommand::isLineIDApplicable () const
{
  return m_isLineIDApplicable;
}

inline bool PlotCommand::isPlotGroupDonor () const
{
  return m_isPlotGroupDonor;
}

inline bool PlotCommand::isContour () const
{
  return m_isContour;
}

inline const std::map<PlotStyle::VectorCategory,PlotAttributes>& PlotCommand::styleMap () const
{
  return m_styleMap;
}

inline PlotRange& PlotCommand::rangeSettings ()
{
  return m_rangeSettings;
}

inline bool PlotCommand::dataStatus ()
{
  return s_dataStatus;
}

inline bool PlotCommand::activeModelStatus ()
{
  return s_activeModelStatus;
}

inline PlotStyle::LineStyle PlotCommand::standardModelStyle ()
{
  return s_standardModelStyle;
}

inline PlotStyle::Symbol PlotCommand::standardDataStyle ()
{
  return s_standardDataStyle;
}

inline PlotGroupCreator* PlotCommand::plotGroupStrategy () const
{
  return m_plotGroupStrategy;
}


#endif
