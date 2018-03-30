// C++

#ifndef MAPANDWRAPPERS_H
#define MAPANDWRAPPERS_H

#include <string>
#include <fstream>
#include <map>
#include "ModelMap.h"

using std::string;

class WrappersError
{
   public:
      WrappersError(const string& msg);
};

class MapAndWrappers : public ModelMap
{
   public:
      // modInitFile is the FULL path to the model.dat file
      // directory is the absolute path to where the map files will
      //    be placed (with no trailing '/').
      // packageName may be empty, which will mean this is used for
      //    Xspec's built-in model functions directory.
      MapAndWrappers(const string& modInitFile, const string& directory,
                  const string& packageName);      
      virtual ~MapAndWrappers();

      void createWrapperFiles();
      void completeWrapperFiles();

   protected:
      virtual void addWrappers(const string& funcName, 
                        const string& funcType, int nPar);

   private:
      void copyCodeTemplate();

      std::ofstream m_wrapHeaderFile;
      std::ofstream m_wrapCodeFile;

      // Some earlier Fortran function names are different than the
      // replacement C++ function names.  For backwards comptability, 
      // store these exceptional cases in a map. 
      static std::map<string,string> s_specialNames;

};


#endif
