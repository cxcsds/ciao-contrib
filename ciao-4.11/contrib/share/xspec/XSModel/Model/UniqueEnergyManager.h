//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef UNIQUEENERGYMANAGER_H
#define UNIQUEENERGYMANAGER_H 1
#include <xsTypes.h>
#include <set>
#include <map>

class Response;


class UniqueEnergy;




class UniqueEnergyManager 
{

  public:



    typedef std::multimap<string,std::pair<size_t, UniqueEnergy*> > NameLookup;



    typedef std::map<size_t,UniqueEnergy*> SpecNumMap;
      UniqueEnergyManager ();
      ~UniqueEnergyManager();

      bool addRespEnergy (const Response* response, bool isSpecDependent);
      void removeRespEnergy (const Response* response);
      void clearAll ();
      void updateEnergyFromResponse (const Response* response);
      std::set<UniqueEnergy*>& uniqueEnergies ();

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      UniqueEnergyManager(const UniqueEnergyManager &right);
      UniqueEnergyManager & operator=(const UniqueEnergyManager &right);

      UniqueEnergy* checkIfUnique (const RealArray& energies, const StringArray& rmfNames, const std::vector<Real>& gainFactor);
      static void findRmfNames (const Response* response, StringArray& rmfNames);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      std::set<UniqueEnergy*> m_uniqueEnergies;
      UniqueEnergyManager::SpecNumMap m_specNumLookup;
      UniqueEnergyManager::NameLookup m_rmfNameLookup;

    // Additional Implementation Declarations

};

// Class UniqueEnergyManager 

inline std::set<UniqueEnergy*>& UniqueEnergyManager::uniqueEnergies ()
{
  return m_uniqueEnergies;
}


#endif
