//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef UNIQUEENERGY_H
#define UNIQUEENERGY_H 1
#include <xsTypes.h>
#include <set>




class UniqueEnergy 
{

  public:
      UniqueEnergy (const RealArray& energies);
      ~UniqueEnergy();

      void addClient (size_t specNum);
      bool removeClient (size_t specNum);
      void removeAllClients ();
      void changeEnergy (const RealArray& newEnergy);
      const RealArray& energy () const;
      const std::set<size_t>& clientSpectra () const;
      const std::vector<Real>& associatedGain () const;
      void associatedGain (const std::vector<Real>& value);
      bool dontShare () const;
      void dontShare (bool value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      UniqueEnergy & operator=(const UniqueEnergy &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      RealArray m_energy;
      std::set<size_t> m_clientSpectra;
      std::vector<Real> m_associatedGain;
      bool m_dontShare;

    // Additional Implementation Declarations

};

// Class UniqueEnergy 

inline void UniqueEnergy::removeAllClients ()
{
  m_clientSpectra.clear();
}

inline const RealArray& UniqueEnergy::energy () const
{
  return m_energy;
}

inline const std::set<size_t>& UniqueEnergy::clientSpectra () const
{
  return m_clientSpectra;
}

inline const std::vector<Real>& UniqueEnergy::associatedGain () const
{
  return m_associatedGain;
}

inline void UniqueEnergy::associatedGain (const std::vector<Real>& value)
{
  m_associatedGain = value;
}

inline bool UniqueEnergy::dontShare () const
{
  return m_dontShare;
}

inline void UniqueEnergy::dontShare (bool value)
{
  m_dontShare = value;
}


#endif
