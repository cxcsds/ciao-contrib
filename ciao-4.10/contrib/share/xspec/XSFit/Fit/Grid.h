//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef GRID_H
#define GRID_H 1
#include <xsTypes.h>

// Error
#include <XSUtil/Error/Error.h>
class ModParam;




class Grid 
{

  public:



    struct ParameterSpec 
    {
          ParameterSpec (int paramIndex = 1, int fullIndex = 1, Real low = Grid::FLAG(), Real high = Grid::FLAG(), int levels = 10, bool logSpacing = false);

        // Data Members for Class Attributes
          bool log;
          Real lowRange;
          Real highRange;
          //	This is the 1-based index corresponding to what the user
          //	enters whenever specifying a parameter.
          int parIndex;
          //	This is the extended idex used as an identifier in Fit's
          //	variableParameters map.
          int fullFitIndex;
          size_t intervals;
          //	This will contain the string [<modName>:]<parName>,
          //	useful in display of steppar output columns.
          string name;
          //	Stores the optional units string of a ModParam.  Useful
          //	for labels in contour plots.
          string units;
          Real value;
          //	CAUTION: This is only valid during a steppar run.  No
          //	guarantees if the steppar grid is accessed at a later
          //	time.  The ModParam this pointed to may no longer exist.
          ModParam* address;
          std::vector<Real> parameterValues;

      public:
      protected:
      private:
      private: //## implementation
    };



    class InvalidParameter : public YellowAlert  //## Inherits: <unnamed>%41F9047B023F
    {
      public:
          InvalidParameter (const std::string& diag);

      protected:
      private:
      private: //## implementation
    };



    class InsufficientParameterArguments : public YellowAlert  //## Inherits: <unnamed>%41F9047D00BB
    {
      public:
          InsufficientParameterArguments (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    typedef std::vector<Grid::ParameterSpec*> SpecContainer;
      Grid();
      virtual ~Grid();

      //	Retrieves the setting of "best/current" (use best fit
      //	parameter or current value of parameter) from the user
      //	input and returns a set of strings and indexes with all
      //	instances of the strings "best" , "current" removed.
      static bool retrieveBestSetting (const StringArray& userString, IntegerArray& userIndex, StringArray& parString, IntegerArray& parIndex);
      static Grid::ParameterSpec* makeParameterSpec (const Grid::ParameterSpec* const parameter, const string& parameterName, int paramIndex, int fullIndex, std::pair<Real,Real>& lim, bool logSetting, int intervals);
      static bool parseParameterRange (const string& inputArg, int argIndex, int& base, std::pair<Real,Real>& lims, int& lev, bool& ls, bool& isDelta);
      void resetContourMap ();
      virtual void doGrid () = 0;
      virtual void report (bool title = false) const = 0;
      const Grid::SpecContainer& getParameter () const;
      const size_t getGridSize () const;
      const RealArray& getGridValues () const;
      void reinitialize (const SpecContainer& newSetting);
      static const Real& FLAG ();
      Real minStat () const;
      void minStat (Real value);
      const RealArray& contourLevels () const;
      void setContourLevels (const RealArray& value);

  public:
    // Additional Public Declarations

  protected:
      Grid::SpecContainer& parameter ();
      RealArray& grid ();

    // Additional Protected Declarations

  private:
      Grid(const Grid &right);
      Grid & operator=(const Grid &right);

      void replaceParameterSettings (const SpecContainer& newSetting) throw ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const Real s_FLAG;
      static const int INTERVALS;
      Real m_minStat;
      Grid::SpecContainer m_parameter;
      RealArray m_grid;
      RealArray m_contourLevels;

    // Additional Implementation Declarations

};

// Class Grid::ParameterSpec 

// Class Grid::InvalidParameter 

// Class Grid::InsufficientParameterArguments 

// Class Grid 

inline const Grid::SpecContainer& Grid::getParameter () const
{
   return m_parameter;
}

inline const size_t Grid::getGridSize () const
{
  return m_grid.size();
}

inline const RealArray& Grid::getGridValues () const
{
   return m_grid;
}

inline const Real& Grid::FLAG ()
{
  return s_FLAG;
}

inline Real Grid::minStat () const
{
  return m_minStat;
}

inline void Grid::minStat (Real value)
{
  m_minStat = value;
}

inline Grid::SpecContainer& Grid::parameter ()
{
  return m_parameter;
}

inline RealArray& Grid::grid ()
{
  return m_grid;
}

inline const RealArray& Grid::contourLevels () const
{
  return m_contourLevels;
}

inline void Grid::setContourLevels (const RealArray& value)
{
  m_contourLevels.resize(value.size());
  m_contourLevels = value;
}


#endif
