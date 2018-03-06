//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PARAMDATA_H
#define PARAMDATA_H 1

// xsTypes
#include "xsTypes.h"

//	The  class Param encapulates the common data elements
//	of model and fit parameters. They have functions that
//	get, set and print them, and 6 data members, which are
//	read into
//	the program from the model.dat file by ModParam objects.
//	//	value - the parameter value
//	value - the parameter value
//	max - the specified upper limit of the parameter > top
//	min - the specified lower limit of the parameter < bot
//	top - the top of the parameter pegged range
//	bot - the bottom of the parameter pegged range
//	delta - the fitting routine default stepsize



class ParamData 
{

  public:
      ParamData(const ParamData &right);
      ParamData (Real value = 0., Real delta = 0., Real max = 0., Real min = 0., Real top = 0., Real bot = 0.);
      ~ParamData();
      ParamData & operator=(const ParamData &right);
      int operator==(const ParamData &right) const;

      int operator!=(const ParamData &right) const;

      void init (Real values, Real delta, Real max, Real min, Real top, Real bottom);
      const Real value () const;
      void value (Real value);
      //	The size of the parameter step taken by the fitting
      //	routine
      const Real delta () const;
      void delta (Real value);
      const Real max () const;
      void max (Real value);
      const Real min () const;
      void min (Real value);
      const Real top () const;
      void top (Real value);
      const Real bot () const;
      void bot (Real value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
      bool compare (const ParamData& right) const;
      void swap (ParamData& right) throw ();

    // Data Members for Class Attributes
      Real m_value;
      Real m_delta;
      Real m_max;
      Real m_min;
      Real m_top;
      Real m_bot;

    // Additional Implementation Declarations

};

// Class ParamData 

inline int ParamData::operator==(const ParamData &right) const
{
  return compare(right);
}

inline int ParamData::operator!=(const ParamData &right) const
{
  return !compare(right);
}


inline bool ParamData::compare (const ParamData& right) const
{
        if (m_value != right.m_value) return false;
        if (m_delta != right.m_delta) return false;
        if (m_top != right.m_top) return false;
        if (m_bot != right.m_bot) return false;
        if (m_max != right.m_max) return false;
        if (m_min != right.m_min) return false;
        return true;
}

inline const Real ParamData::value () const
{
  return m_value;
}

inline void ParamData::value (Real value)
{
  m_value = value;
}

inline const Real ParamData::delta () const
{
  return m_delta;
}

inline void ParamData::delta (Real value)
{
  m_delta = value;
}

inline const Real ParamData::max () const
{
  return m_max;
}

inline void ParamData::max (Real value)
{
  m_max = value;
}

inline const Real ParamData::min () const
{
  return m_min;
}

inline void ParamData::min (Real value)
{
  m_min = value;
}

inline const Real ParamData::top () const
{
  return m_top;
}

inline void ParamData::top (Real value)
{
  m_top = value;
}

inline const Real ParamData::bot () const
{
  return m_bot;
}

inline void ParamData::bot (Real value)
{
  m_bot = value;
}


#endif
