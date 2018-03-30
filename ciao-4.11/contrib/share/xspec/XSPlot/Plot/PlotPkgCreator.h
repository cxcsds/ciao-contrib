//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTPKGCREATOR_H
#define PLOTPKGCREATOR_H 1
#include <xsTypes.h>


class PlotPkg;




class PlotPkgCreator 
{

  public:
      static PlotPkg* MakePlotPkg (const string& plotPackageName);

    // Additional Public Declarations

  protected:
      PlotPkgCreator();

    // Additional Protected Declarations

  private:
      PlotPkgCreator(const PlotPkgCreator &right);
      PlotPkgCreator & operator=(const PlotPkgCreator &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class PlotPkgCreator 


#endif
