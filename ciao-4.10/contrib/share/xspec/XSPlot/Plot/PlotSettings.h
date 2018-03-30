//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTSETTINGS_H
#define PLOTSETTINGS_H 1
#include <xsTypes.h>
#include <XSPlot/Plot/PlotStyle.h>
#include <XSPlot/Plot/PlotTypes.h>
#include <list>
#include <utility>

//	An aggregate class of PlotDirector, this is intended to
//	hold the various settings input from the setplot command.



class PlotSettings 
{

  public:



    typedef enum {STD,ROOTN,GEHRELS1,GEHRELS2,GEHRELSM} PlotErrMode;



    struct RebinInfo 
    {
        // Data Members for Class Attributes
          Real sigma;
          int maxBins;
          PlotSettings::PlotErrMode mode;

      public:
      protected:
      private:
      private: //## implementation
    };



    typedef enum {NO_SAVE, X_AR, XERR_AR, Y_AR, YERR_AR, MODEL_AR, BACK_AR, ALL_AR} SaveArrayOption;
      PlotSettings();
      ~PlotSettings();

      void setXOption (const string& option);
      int addUserCommand (const string& command);
      void removeUserCommand (int numCmd);
      void removeUserCommandRange (int firstCmd, int lastCmd);
      int numberUserCommands();
      void setPlotGroupNums (const string& rangesString);
      void setIDs (const std::vector<Real>& values);
      void showUserCommands () const;
      void ungroupAll ();
      void initializeSpectra ();
      const std::map<int,PlotSettings::RebinInfo>& groupsRebinInfo () const;
      //	whichFlag = 0 is for passing along the user's setplot
      //	setting.  = 1 passes along the PlotCommand attribute.
      void setDivideByArea (int whichFlag, bool value);
      //	Sets the user-adjusted (from setplot command) show add
      //	component flag.
      void setShowAddComponent (bool value);
      //	Sets the level of add comp display, as determined by the
      //	particular PlotCommand.
      void setAddCompLevel (int level);
      void setShowBackground (int whichFlag, bool value);
      void setShowLineIDs (int whichFlag, bool value);
      //	Returns the value set with the "setplot area/noarea"
      //	options.
      bool getDivideByArea () const;
      //	Retrieves the value set with the "setplot add/noadd"
      //	options.
      bool getShowAddComponent () const;
      bool getShowBackground () const;
      bool getShowLineIDs () const;
      //	Returns the boolean combination of the user's setplot
      //	request and the PlotCommand's corresponding attribute.
      bool divideByArea () const;
      //	Indicates whether add components will actually be
      //	displayed, based on the information in the m_showAdd
      //	Component pair.
      bool showAddComponent () const;
      bool showFoldedAddComponent () const;
      bool showBackground () const;
      bool showLineIDs () const;
      const string& getUnitID (XaxisMode mode) const;
      const string& getUnitPlotLabel (XaxisMode mode) const;
      Real getUnitFactor (XaxisMode mode) const;
      //	Utility function for PlotCommands sharing the common
      //	Chan/Energ/Wave axis label dependency.  This fills an
      //	x-axis label based upon the current xOption setting and
      //	the units setting.  It also returns the x label key,
      //	which the PlotCommand may want to use for constructing a
      //	y-axis label.
      string makeXOptionDependentLabel (string& xLabel) const;
      //	Plot label utility function.  Any generic unit
      //	placeholder strings in plotLabel are replaced with the
      //	appropriate unit label based upon the current xOption
      //	and units settings.  If checkPerHz flag is true, it will
      //	also check the isWavePerHz setting when in wavelength
      //	mode.  Generally y labels will want this and x labels
      //	will not.
      void insertUnitLabel (string& plotLabel, bool checkPerHz) const;
      //	Returns the plot label entry based on the labelKey.
      //	Throws if labelKey is not found in map.
      const string& lookupLabelName (const string& labelKey) const;
      XaxisMode xOption () const;
      void xOption (XaxisMode value);
      const std::list<string>& userCommands () const;
      Real temperature () const;
      Real emisLimit () const;
      //	This is the Z = V/C value used to shift line IDs from
      //	the source to obs frame.  It is set through the "setplot
      //	id" option.
      Real redshiftLinesToObs () const;
      //	This is the Z = V/C value used to shift the x-axis
      //	energy/wavelength values from the obs frame to the
      //	source frame.  Set using "setplot redshift", separate
      //	from the "setplot id" redshift value.
      Real redshiftToSource () const;
      void redshiftToSource (Real value);
      Real IDLowEnergy() const;
      void IDLowEnergy(Real value);
      Real IDHighEnergy() const;
      void IDHighEnergy(Real value);
      std::map<int,PlotSettings::RebinInfo>& groupsRebinInfo ();
      std::pair<int,PlotSettings::RebinInfo>& lastRebinEntry ();
      bool splashPage () const;
      void splashPage (bool value);
      bool xLog () const;
      void xLog (bool value);
      bool yLog () const;
      void yLog (bool value);
      //	Stores 3 fields of information: the unit ID string as
      //	entered through setplot, the unit as it appears in a
      //	plot label, and the conversion factor.
      void energyUnit (const std::pair<string,std::pair<string,Real> >& value);
      void waveUnit (const std::pair<string,std::pair<string,Real> >& value);
      //	If true, wavelength mode y-axis values will be presented
      //	per Hz rather than per length unit (where applicable).
      bool isWavePerHz () const;
      void isWavePerHz (bool value);
      //	Pointers to spectra, collated by plot group number.
      const SpecGroup& spectra () const;
      bool isInteractive () const;
      void isInteractive (bool value);
      const std::pair<PlotSettings::SaveArrayOption, int> saveArrayInfo () const;
      void saveArrayInfo (std::pair<PlotSettings::SaveArrayOption, int> value);
      //	This is where the plotLabel.dat entries are stored.  It
      //	is publicly modifiable so that PlotDirector may set it
      //	from its loading function.
      std::map<string,string>& labelNames ();
      //	This ought to originate with the specific PlotPkg class.
      //	The plot director should fill this in based on that.
      Real badDataValue () const;
      void badDataValue (Real value);
      bool contBackImage () const;
      void contBackImage (bool value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotSettings(const PlotSettings &right);
      PlotSettings & operator=(const PlotSettings &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      XaxisMode m_xOption;
      std::list<string> m_userCommands;
      std::pair<size_t,size_t> m_prevGroupRange;
      Real m_temperature;
      Real m_emisLimit;
      Real m_redshiftLinesToObs;
      Real m_redshiftToSource;
      Real m_IDLowEnergy;
      Real m_IDHighEnergy;
      std::map<int,PlotSettings::RebinInfo> m_groupsRebinInfo;
      std::pair<int,PlotSettings::RebinInfo> m_lastRebinEntry;
      bool m_splashPage;
      bool m_xLog;
      bool m_yLog;
      std::pair<string,std::pair<string,Real> > m_energyUnit;
      std::pair<string,std::pair<string,Real> > m_waveUnit;
      bool m_isWavePerHz;
      //	The first flag is set by the user through setplot.  The
      //	second is determined by the particular plot command.
      std::pair<bool,bool> m_divideByArea;
      //	Pair's first member is for storing the user adjusted
      //	"setplot add/noadd" flag.  The second is for storing the
      //	most recent PlotCommand's addCompLevel.
      std::pair<bool,int> m_showAddComponent;
      std::pair<bool,bool> m_showBackground;
      std::pair<bool,bool> m_showLineIDs;
      SpecGroup m_spectra;
      bool m_isInteractive;
      std::pair<PlotSettings::SaveArrayOption, int> m_saveArrayInfo;
      std::map<string,string> m_labelNames;
      Real m_badDataValue;
      bool m_contBackImage;

    // Additional Implementation Declarations

};

// Class PlotSettings::RebinInfo 

// Class PlotSettings 

inline const std::map<int,PlotSettings::RebinInfo>& PlotSettings::groupsRebinInfo () const
{
   return m_groupsRebinInfo;
}

inline void PlotSettings::setDivideByArea (int whichFlag, bool value)
{
   whichFlag ? m_divideByArea.second = value : m_divideByArea.first = value;
}

inline void PlotSettings::setShowAddComponent (bool value)
{
   m_showAddComponent.first = value;
}

inline void PlotSettings::setAddCompLevel (int level)
{
   m_showAddComponent.second = level;
}

inline void PlotSettings::setShowBackground (int whichFlag, bool value)
{
   whichFlag ? m_showBackground.second = value : m_showBackground.first = value;
}

inline void PlotSettings::setShowLineIDs (int whichFlag, bool value)
{
   whichFlag ? m_showLineIDs.second = value : m_showLineIDs.first = value;
}

inline bool PlotSettings::getDivideByArea () const
{
   return m_divideByArea.first;
}

inline bool PlotSettings::getShowAddComponent () const
{
   return m_showAddComponent.first;
}

inline bool PlotSettings::getShowBackground () const
{
   return m_showBackground.first;
}

inline bool PlotSettings::getShowLineIDs () const
{
   return m_showLineIDs.first;
}

inline bool PlotSettings::divideByArea () const
{
   return m_divideByArea.first && m_divideByArea.second;
}

inline bool PlotSettings::showBackground () const
{
   return m_showBackground.first && m_showBackground.second;
}

inline bool PlotSettings::showLineIDs () const
{
   return m_showLineIDs.first && m_showLineIDs.second;
}

inline XaxisMode PlotSettings::xOption () const
{
  return m_xOption;
}

inline const std::list<string>& PlotSettings::userCommands () const
{
  return m_userCommands;
}

inline Real PlotSettings::temperature () const
{
  return m_temperature;
}

inline Real PlotSettings::emisLimit () const
{
  return m_emisLimit;
}

inline Real PlotSettings::redshiftLinesToObs () const
{
  return m_redshiftLinesToObs;
}

inline Real PlotSettings::redshiftToSource () const
{
  return m_redshiftToSource;
}

inline void PlotSettings::redshiftToSource (Real value)
{
  m_redshiftToSource = value;
}

inline Real PlotSettings::IDLowEnergy () const
{
  return m_IDLowEnergy;
}

inline void PlotSettings::IDLowEnergy (Real value)
{
  m_IDLowEnergy = value;
}

inline Real PlotSettings::IDHighEnergy () const
{
  return m_IDHighEnergy;
}

inline void PlotSettings::IDHighEnergy (Real value)
{
  m_IDHighEnergy = value;
}

inline std::map<int,PlotSettings::RebinInfo>& PlotSettings::groupsRebinInfo ()
{
  return m_groupsRebinInfo;
}

inline std::pair<int,PlotSettings::RebinInfo>& PlotSettings::lastRebinEntry ()
{
  return m_lastRebinEntry;
}

inline bool PlotSettings::splashPage () const
{
  return m_splashPage;
}

inline void PlotSettings::splashPage (bool value)
{
  m_splashPage = value;
}

inline bool PlotSettings::xLog () const
{
  return m_xLog;
}

inline void PlotSettings::xLog (bool value)
{
  m_xLog = value;
}

inline bool PlotSettings::yLog () const
{
  return m_yLog;
}

inline void PlotSettings::yLog (bool value)
{
  m_yLog = value;
}

inline void PlotSettings::energyUnit (const std::pair<string,std::pair<string,Real> >& value)
{
  m_energyUnit = value;
}

inline void PlotSettings::waveUnit (const std::pair<string,std::pair<string,Real> >& value)
{
  m_waveUnit = value;
}

inline bool PlotSettings::isWavePerHz () const
{
  return m_isWavePerHz;
}

inline void PlotSettings::isWavePerHz (bool value)
{
  m_isWavePerHz = value;
}

inline const SpecGroup& PlotSettings::spectra () const
{
  return m_spectra;
}

inline bool PlotSettings::isInteractive () const
{
  return m_isInteractive;
}

inline void PlotSettings::isInteractive (bool value)
{
  m_isInteractive = value;
}

inline const std::pair<PlotSettings::SaveArrayOption, int> PlotSettings::saveArrayInfo () const
{
  return m_saveArrayInfo;
}

inline void PlotSettings::saveArrayInfo (std::pair<PlotSettings::SaveArrayOption, int> value)
{
  m_saveArrayInfo = value;
}

inline std::map<string,string>& PlotSettings::labelNames ()
{
  return m_labelNames;
}

inline Real PlotSettings::badDataValue () const
{
  return m_badDataValue;
}

inline void PlotSettings::badDataValue (Real value)
{
  m_badDataValue = value;
}

inline bool PlotSettings::contBackImage () const
{
  return m_contBackImage;
}

inline void PlotSettings::contBackImage (bool value)
{
  m_contBackImage = value;
}


#endif
