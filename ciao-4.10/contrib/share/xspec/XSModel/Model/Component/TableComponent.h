//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TABLECOMPONENT_H
#define TABLECOMPONENT_H 1
#include <set>

// xsTypes
#include <xsTypes.h>
// Error
#include <XSUtil/Error/Error.h>

class UniqueEnergy;
class Component;
class Parameter;




class TableComponent 
{

  public:



    class ParameterRangeError : public YellowAlert  //## Inherits: <unnamed>%3D6B85E70304
    {
      public:
          ParameterRangeError (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class WrongTableType : public YellowAlert  //## Inherits: <unnamed>%3D6B89F602BC
    {
      public:
          WrongTableType (const string& diag);

      protected:
      private:
      private: //## implementation
    };
      virtual ~TableComponent();

      //	If p is a valid Component pointer, isAddRequest argument
      //	is irrelevant.  It only needs to be filled to verify Add
      //	or Mult type when TableComponent is used in isolation,
      //	and there is no owning Component.
      virtual void read (bool readSpectralData, Component* p, bool isAddRequest = true) = 0;
      void interpolate (const UniqueEnergy* uniqueEng, RealArray& spectrum, RealArray& variance, bool rebin, bool exponential = false);
      virtual TableComponent* clone (Component* parent) const = 0;
      virtual bool formatCheck (const string& fileName) = 0;
      static TableComponent* returnTable (string& fileName);
      static void registerTableFormat (TableComponent* format);
      const std::vector<Parameter*>& parameters ();
      virtual void energyWeights (const UniqueEnergy* uniqueEng);
      virtual void clearArrays (const std::set<UniqueEnergy*>& currentEngs);
      static void clearTableFormats ();
      const string& filename () const;
      void filename (const string& value);
      //	Fits Keyword MODLNAME
      const string& name () const;
      void name (const string& value);
      //	Number of energy bins for which model is specified.
      int numEngVals () const;
      void numEngVals (int value);
      //	Number of interpolated parameters.
      //	FITS keyword NINTPARM
      const int numIntPar () const;
      void numIntPar (int value);
      //	Number of additional parameters (parameters not for
      //	interpolation).
      //	      //	This is the NADDPARM keyword.
      //	This is the NADDPARM keyword.
      const int numAddPar () const;
      void numAddPar (int value);
      bool isError () const;
      const RealArray& engLow () const;
      void setEngLow (const RealArray& value);
      Real engLow (size_t index) const;
      void engLow (size_t index, Real value);
      const RealArray& engHigh () const;
      void setEngHigh (const RealArray& value);
      Real engHigh (size_t index) const;
      void engHigh (size_t index, Real value);

  public:
    // Additional Public Declarations

  protected:
      TableComponent(const TableComponent &right);
      TableComponent (const string& nameString, Component* p);

      //	rebin model component fluxes using weighting array.
      virtual void rebinComponent (const UniqueEnergy* uniqueEng, const RealArray& inputArray, RealArray& outputArray, bool variance = false) = 0;
      //	rebin model component fluxes using weighting array.
      virtual void interpolateComponent (const UniqueEnergy* uniqueEng, const RealArray& inputArray, RealArray& outputArray, bool exponential = false) = 0;
      void isError (bool value);
      const std::vector<Parameter*>& params () const;
      virtual void getInterpolant (RealArray& spectrum, RealArray& variance) = 0;
      virtual void setParamPointersFromCopy ();
      std::vector<Parameter*>& params ();
      void params (const std::vector<Parameter*>& value);
      const Component* parent () const;
      void parent (Component* value);

    // Additional Protected Declarations

  private:
      TableComponent & operator=(const TableComponent &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_filename;
      string m_name;
      int m_numEngVals;
      int m_numIntPar;
      int m_numAddPar;
      bool m_isError;

    // Data Members for Associations
      static std::map<const char*,TableComponent*> s_formats;
      RealArray m_engLow;
      RealArray m_engHigh;
      std::vector<Parameter*> m_params;
      Component* m_parent;

    // Additional Implementation Declarations

};

// Class TableComponent::ParameterRangeError 

// Class TableComponent::WrongTableType 

// Class TableComponent 

inline const string& TableComponent::filename () const
{
  return m_filename;
}

inline void TableComponent::filename (const string& value)
{
  m_filename = value;
}

inline const string& TableComponent::name () const
{
  return m_name;
}

inline void TableComponent::name (const string& value)
{
  m_name = value;
}

inline int TableComponent::numEngVals () const
{
  return m_numEngVals;
}

inline void TableComponent::numEngVals (int value)
{
  m_numEngVals = value;
}

inline const int TableComponent::numIntPar () const
{
  return m_numIntPar;
}

inline void TableComponent::numIntPar (int value)
{
  m_numIntPar = value;
}

inline const int TableComponent::numAddPar () const
{
  return m_numAddPar;
}

inline void TableComponent::numAddPar (int value)
{
  m_numAddPar = value;
}

inline bool TableComponent::isError () const
{
  return m_isError;
}

inline const RealArray& TableComponent::engLow () const
{
  return m_engLow;
}

inline void TableComponent::setEngLow (const RealArray& value)
{
  m_engLow.resize(value.size());
  m_engLow = value;
}

inline Real TableComponent::engLow (size_t index) const
{
  return m_engLow[index];
}

inline void TableComponent::engLow (size_t index, Real value)
{
  m_engLow[index] = value;
}

inline const RealArray& TableComponent::engHigh () const
{
  return m_engHigh;
}

inline void TableComponent::setEngHigh (const RealArray& value)
{
  m_engHigh.resize(value.size());
  m_engHigh = value;
}

inline Real TableComponent::engHigh (size_t index) const
{
  return m_engHigh[index];
}

inline void TableComponent::engHigh (size_t index, Real value)
{
  m_engHigh[index] = value;
}

inline std::vector<Parameter*>& TableComponent::params ()
{
  return m_params;
}

inline void TableComponent::params (const std::vector<Parameter*>& value)
{
  m_params = value;
}

inline const Component* TableComponent::parent () const
{
  return m_parent;
}

inline void TableComponent::parent (Component* value)
{
  m_parent = value;
}


#endif
