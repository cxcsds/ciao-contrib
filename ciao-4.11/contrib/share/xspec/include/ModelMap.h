// C++

#ifndef MODELMAP_H
#define MODELMAP_H

#include <vector>
#include <string>

using std::string;

class ModelMap
{

   public:
      // modInitFile is the FULL path to the model.dat file
      // directory is the absolute path to where the map files will
      //    be placed (with no trailing '/').
      // packageName may be empty, which will mean this is used for
      //    Xspec's built-in model functions directory.
      ModelMap(const string& modInitFile, const string& directory,
                  const string& packageName);
      virtual ~ModelMap();

      // ASSUMES model.dat readability has already been checked.            
      void processModelFile();
      void writeMapFiles() const;

      const string& modInitFile() const;
      const string& directory() const;
      const string& packageName() const;
      static const string& ccfuncType();
      static const string& CXXfuncType();

   protected:
      // This doesn't do anything unless overridden.
      virtual void addWrappers(const string& funcName, 
                        const string& funcType, int nPar);

   private:
      const string m_modInitFile;
      const string m_directory;
      const string m_packageName;

      std::vector<string> m_headerFileLines;
      std::vector<string> m_codeFileLines;
      std::vector<string> m_codeFileMixHeaders; 

      static const string s_funcMapContainer;
      static const string s_f77linkPrefix;
      static const string s_f77linkSuffix;
      static const string s_f77funcType;
      static const string s_F77funcType;
      static const string s_CXXfuncType;
      static const string s_ccfuncType;
      static const string s_ccmixfuncType;
      static const string s_CXXmixfuncType;

};

inline const string& ModelMap::modInitFile() const
{
   return m_modInitFile;
}


inline const string& ModelMap::directory() const
{
   return m_directory;
}

inline const string& ModelMap::packageName() const
{
   return m_packageName;
}

inline const string& ModelMap::ccfuncType()
{
   return s_ccfuncType;
}

inline const string& ModelMap::CXXfuncType()
{
   return s_CXXfuncType;
}

#endif
