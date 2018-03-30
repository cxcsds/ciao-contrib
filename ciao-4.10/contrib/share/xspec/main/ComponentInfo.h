//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef COMPONENTINFO_H
#define COMPONENTINFO_H 1
#include "xsTypes.h"




struct ComponentInfo 
{
      ComponentInfo();
      ComponentInfo (const string& componentName, const string& dataFile, size_t loc, const string& componentType, bool errorFlag, string addString, bool isStandard);

      void reset ();

    // Data Members for Class Attributes
      string name;
      string sourceFile;
      size_t location;
      string type;
      //	true if the model calculates errors.
      bool error;
      //	An additional information string that can be read from
      //	the
      //	"model.dat" file to supply anything that new model
      //	implementations might need.
      //
      //	Initial use might be a generic 'component that needs
      //	to read from a fits file' filename and directory
      string infoString;
      bool isStandardXspec;
      // Currently only Python-coded models are using the following 2 flags.
      //   For other models, isSpecDependent is determined when reading
      //   the model.dat file in Component::read().
      bool isPythonModel;
      bool isSpecDependent;

  public:
  protected:
  private:
  private: //## implementation
};



typedef std::multimap<string,ComponentInfo> NameCacheType;

// Class ComponentInfo 


#endif
