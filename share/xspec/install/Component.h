//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef COMPONENT_H
#define COMPONENT_H 1
//#include "UserInterface/TclStream.h"

// utility
#include <utility>
// iosfwd
#include <iosfwd>
#include <xsTypes.h>
// Error
#include <XSUtil/Error/Error.h>
// XSutility
#include <XSUtil/Utils/XSutility.h>
// ComponentInfo
#include <XSFunctions/Utilities/ComponentInfo.h>
// Parameter
#include <XSModel/Parameter/Parameter.h>
#include <set>

class UniqueEnergy;
class SumComponent;
class ComponentGroup;

template <typename T>
class XSCall;
class MdefExpression;
class ModParam;
class ModelBase;
class XSModelFunction;


class Component 
{

  public:

    //	Invalid input exception for component object.
    //	Thrown if component name entered is too short (1 character)
    //	Thrown if component name entered is too short (1 character)
    class InvalidInput : public YellowAlert
    {
      public:
          InvalidInput (const string& errMessage = "Invalid Input:");
    };
    
    class InvalidTableModel : public YellowAlert
    {
      public:
          InvalidTableModel();
    };

    class BadTableFileName : public YellowAlert  //## Inherits: <unnamed>%37653EB187D0
    {
      public:
          //	Class Component::BadTableFileName
          BadTableFileName (const string& errName = "(no input file specified)");

      protected:
      private:
      private: //## implementation
    };



    class SpectrumNotDefined : public YellowAlert  //## Inherits: <unnamed>%3DF6140B029B
    {
      public:
          SpectrumNotDefined (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class NoSuchComponent : public YellowAlert  //## Inherits: <unnamed>%3F1D717402B6
    {
      public:
          NoSuchComponent (const string& msg);

      protected:
      private:
      private: //## implementation
    };
    
      virtual ~Component();
      Component & operator=(const Component &right);

      //	Read function for all model components that are
      //	generated from the model.dat file. read is overloaded
      //	for all other types.
      virtual int read ();
      //	Reads datafile (model.dat) to decide which component clas
      //	s to instantiate and where in the file to find that data.
      //	 Alternatively, grabs equivalent information from table f
      //	its
      //	file.
      static void getSetupData (const string& modelName);
      //	Function to add a parameter (e.g. normalization,
      //	redshift) to the parameterSet member.
      //	      //	With no arguments, addpar will add a normalizati
      //	on
      //	With no arguments, addpar will add a normalization
      //	parameter with the default limits.
      void addParam (const string& paramName = "norm", const string& unit = "", Real value = 1., Real top = 1.e+20, Real max = 1.e+24, Real bot = 0., Real min = 0., Real delta = 0.01);
      virtual Component* clone (ComponentGroup* p) const = 0;
      virtual void calculate (bool saveComponentFlux, bool frozen) = 0;
      //	Method called to set values of parameters from input
      //	strings paramStrings.
      //
      //	The default argument parameterNumbers, if not set, means
      //	'set all numbers'. If the argument is supplied it allows
      //	setting parameters by index number.
      //
      //	If parameterNumbers is non-empty, its size and  the size
      //	of  the paramStrings vector must be the same.
      void setParamValues (const std::vector<string>& paramString, const IntegerVector& parameterNumbers = IntegerVector());
      void getParamValues (const string& modString, std::vector<string>& componentParams) const;
      virtual bool isNested () const;
      const string& name () const;
      int index () const;
      const std::vector<Parameter*>& parameterSet () const;
      void name (const string& id);
      void index (int i);
      const string& parentName () const;
      size_t dataGroup () const;
      void deleteParameters () throw ();
      virtual void registerParameters () const;
      void reindexParameters (int parameterOffset);
      size_t modelIndex () const;
      Parameter* getLocalParameter (size_t i) const;
      Parameter* localParameter (size_t i) const;
      void linkParametersToPrimary ();
      const ArrayContainer& getEnergyArray () const;
      bool isError () const;
      virtual SumComponent& operator * (SumComponent& right) const;
      void isError (bool val);
      static const string& currentType ();
      static const string& currentModelName ();
      static void currentType (const string& value);
      static void currentModelName (const string& value);
      size_t numParams () const;
      void setParent (ComponentGroup* p);
      // ParameterLink needs this, so does CompCombiner:
      ComponentGroup* parent () const;
      void debugPrint (std::ostream& s, const string& descript) const;
      bool recompute () const;
      void recompute (bool value);
      Parameter* parameter (const string& paramName) const;
      const RealArray& energyArray (size_t spectrumNumber) const;
      virtual void clearArrays (const std::set<UniqueEnergy*>& currentUniqueEngs);
      std::vector<ModParam*> getVariableParameters () const;
      bool isGroup () const;
      void setParameterSet (const std::vector<Parameter*>& parameters);
      static const NameCacheType& nameCache ();
      IntegerVector parameterIndices () const;
      int resequenceParameters (int startValue);
      virtual void deregisterParameters () const;
      const std::set<UniqueEnergy*>& getUniqueEnergies () const;
      const UniquePhotonContainer& uniquePhotonArray () const;
      void setUniquePhotonArray (const UniquePhotonContainer& value);
      virtual void saveUniquePhotonArray (bool setSaveFlag = true);
      virtual void restoreUniquePhotonArray ();
      const UniquePhotonContainer& uniquePhotonErrArray () const;
      void setUniquePhotonErrArray (const UniquePhotonContainer& value);
      bool isSpectrumDependency () const;
      
      // The isZeroNorm flag is true for an AddComponent with a frozen
      // zero norm parameter, or a non-AddComponent that only operates on
      // frozen zero AddComponents.
      bool isZeroNorm () const;
      void isZeroNorm (bool flag);
      
      virtual void initializeForFit ();
      bool usingMdef (const XSCall<MdefExpression>* mdef) const;
      //	Alternative to dynamic_cast when checking for Sum
      //	Components.
      virtual SumComponent* toSumComponent ();

  public:
    // Additional Public Declarations
      friend std::ostream& operator<<(std::ostream& stream, const Component& output);
  protected:
      Component(const Component &right);
      Component (ComponentGroup* p);

      //	Access by index number. Convenient for some
      //	applications.
      const Parameter* parameterSet (size_t index) const;
      virtual void swap (Component& right);
      std::vector<Parameter*>& parameterSet ();
      //	Access by index number. Convenient for some
      //	applications.
      Parameter* parameterSet (size_t index);
      void cloneParameters (Component& left, const Component& right);
      const ModelBase* root () const;
      const RealArray& uniquePhotonArray (const UniqueEnergy* uniqueEnergy) const;
      RealArray& uniquePhotonArray (const UniqueEnergy* uniqueEnergy);
      void uniquePhotonArray (const UniqueEnergy* uniqueEnergy, const RealArray& value);
      const RealArray& uniquePhotonErrArray (const UniqueEnergy* uniqueEnergy) const;
      RealArray& uniquePhotonErrArray (const UniqueEnergy* uniqueEnergy);
      void uniquePhotonErrArray (const UniqueEnergy* uniqueEnergy, const RealArray& value);
      //	Table model flag. Table models are a subclass of their
      //	corresponding model type. This static flag is used to
      //	set up the ComponentCreator to instantiate a table model
      //	instance
      static const bool currentIsTable ();
      static void currentIsTable (bool value);
      //	Add one to component count and paramIncrement to
      //	parameter count for the containing model.
      size_t incrementModelParameterCount ();
      //	Add one to component count and paramIncrement to
      //	parameter count for the containing model.
      size_t incrementModelComponentCount ();
      const XSModelFunction* generator () const;
      void generator (XSModelFunction* value);
      const string& initString() const;
      void numParams(size_t num);

    // Additional Protected Declarations

  private:
      virtual void copy (const Component& right) = 0;
      static const ComponentInfo& currentModelInfo ();
      static void currentModelInfo (const ComponentInfo& value);
      size_t parameterIndexBase () const;
      void savedUniquePhotonArray (const UniqueEnergy* uniqueEnergy, const RealArray& value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static bool s_currentIsTable;
      static ComponentInfo s_currentModelInfo;
      
      string m_name;
      int m_index;
      Real m_maxEnergy;
      Real m_minEnergy;
      size_t m_numParams;
      bool m_error;
      bool m_compute;
      bool m_fluxSaved;
      string m_initString;
      bool m_isSpectrumDependency;
      bool m_isZeroNorm;
      
      std::vector<Parameter*> m_parameterSet;
      ComponentGroup* m_parent;
      XSModelFunction* m_generator;
      UniquePhotonContainer m_uniquePhotonArray;
      UniquePhotonContainer m_uniquePhotonErrArray;
      UniquePhotonContainer m_savedUniquePhotonArray;

    // Additional Implementation Declarations
    friend class ComponentCreator;
    friend void Parameter::reset();
};

// Class Component::BadTableFileName 

// Class Component::SpectrumNotDefined 

// Class Component::NoSuchComponent 

// Class Component 

inline size_t Component::numParams () const
{
  return m_numParams;
}

inline SumComponent* Component::toSumComponent ()
{
   return 0;
}

inline const bool Component::currentIsTable ()
{
  return s_currentIsTable;
}

inline void Component::currentIsTable (bool value)
{
  s_currentIsTable = value;
}

inline const ComponentInfo& Component::currentModelInfo ()
{
  return s_currentModelInfo;
}

inline void Component::currentModelInfo (const ComponentInfo& value)
{
  s_currentModelInfo = value;
}

inline bool Component::recompute () const
{
  return m_compute;
}

inline void Component::recompute (bool value)
{
  m_compute = value;
}

inline void Component::setParameterSet (const std::vector<Parameter*>& parameters)
{
  m_parameterSet = parameters;
}

inline std::vector<Parameter*>& Component::parameterSet ()
{

  return m_parameterSet;
}

inline Parameter* Component::parameterSet (size_t index)
{

  return m_parameterSet[index];
}

inline RealArray& Component::uniquePhotonArray (const UniqueEnergy* uniqueEnergy)
{
   return m_uniquePhotonArray[uniqueEnergy];
}

inline const RealArray& Component::uniquePhotonArray (const UniqueEnergy* uniqueEnergy) const
{
   UniquePhotonContainer::const_iterator it = m_uniquePhotonArray.find(uniqueEnergy);
   if (it == m_uniquePhotonArray.end())
      throw RedAlert("Programming error searching for unique photon array.\n");
   return it->second;
}

inline RealArray& Component::uniquePhotonErrArray (const UniqueEnergy* uniqueEnergy)
{
   return m_uniquePhotonErrArray[uniqueEnergy];
}

inline const RealArray& Component::uniquePhotonErrArray (const UniqueEnergy* uniqueEnergy) const
{
   UniquePhotonContainer::const_iterator it = m_uniquePhotonErrArray.find(uniqueEnergy);
   if (it == m_uniquePhotonErrArray.end())
      throw RedAlert("Programming error searching for unique photon error array.\n");
   return it->second;
}

inline const UniquePhotonContainer& Component::uniquePhotonArray () const
{
   return m_uniquePhotonArray;
}

inline void Component::setUniquePhotonArray (const UniquePhotonContainer& value)
{
   m_uniquePhotonArray = value;
}

inline void Component::uniquePhotonArray (const UniqueEnergy* uniqueEnergy, const RealArray& value)
{
  UniquePhotonContainer::iterator f = m_uniquePhotonArray.find(uniqueEnergy);
  if (f != m_uniquePhotonArray.end() )
  {
     if (f->second.size() != value.size())
        f->second.resize(value.size());
     f->second = value;
  }
  else
  {
     m_uniquePhotonArray.insert(UniquePhotonContainer::value_type(uniqueEnergy,value));
  }
}

inline const UniquePhotonContainer& Component::uniquePhotonErrArray () const
{
   return m_uniquePhotonErrArray;
}

inline void Component::setUniquePhotonErrArray (const UniquePhotonContainer& value)
{
   m_uniquePhotonErrArray = value;
}

inline void Component::uniquePhotonErrArray (const UniqueEnergy* uniqueEnergy, const RealArray& value)
{
  UniquePhotonContainer::iterator f = m_uniquePhotonErrArray.find(uniqueEnergy);
  if (f != m_uniquePhotonErrArray.end() )
  {
          if (f->second.size() != value.size()) f->second.resize(value.size());
	  f->second = value;
  }
  else
  {
  	m_uniquePhotonErrArray.insert(UniquePhotonContainer::value_type(uniqueEnergy,value));
  }
}

inline void Component::savedUniquePhotonArray (const UniqueEnergy* uniqueEnergy, const RealArray& value)
{
  UniquePhotonContainer::iterator f = m_savedUniquePhotonArray.find(uniqueEnergy);
  if (f != m_savedUniquePhotonArray.end() )
  {
          if (f->second.size() != value.size()) f->second.resize(value.size());
	  f->second = value;
  }
  else
  {
  	m_savedUniquePhotonArray.insert(UniquePhotonContainer::value_type(uniqueEnergy,value));
  }
}

inline const std::vector<Parameter*>& Component::parameterSet () const
{
  return m_parameterSet;
}

inline ComponentGroup* Component::parent () const
{
  return m_parent;
}

inline void Component::setParent (ComponentGroup* p)
{
  m_parent = p;
}

inline const string& Component::name () const
{
  return m_name;
}

inline void Component::name (const string& id)
{
  m_name = id;
}

inline int Component::index () const
{
  return m_index;
}

inline void Component::index (int i)
{
  m_index = i;
}

inline bool Component::isError () const
{
  return m_error;
}

inline void Component::isError (bool val)
{
  m_error = val;
}

inline bool Component::isSpectrumDependency () const
{
  return m_isSpectrumDependency;
}

inline bool Component::isZeroNorm () const
{
   return m_isZeroNorm;
}

inline void Component::isZeroNorm (bool flag)
{
   m_isZeroNorm = flag;
}

inline const XSModelFunction* Component::generator () const
{
  return m_generator;
}

inline void Component::generator (XSModelFunction* value)
{
  m_generator = value;
}

inline const string& Component::initString() const
{
   return m_initString;
}

inline void Component::numParams(size_t num)
{
   m_numParams = num;
}
#endif
