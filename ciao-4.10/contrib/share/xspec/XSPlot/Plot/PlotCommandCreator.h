//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTCOMMANDCREATOR_H
#define PLOTCOMMANDCREATOR_H 1

// PlotTypes
#include <XSPlot/Plot/PlotTypes.h>

class PlotCommand;




class PlotCommandCreator 
{

  public:
      ~PlotCommandCreator();

      static string registerPlotCommands ();
      static PlotCommand* commands (const std::string& name);
      static void destroy ();
      static StringArray commandNames ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      PlotCommandCreator();

      PlotCommandCreator(const PlotCommandCreator &right);
      PlotCommandCreator & operator=(const PlotCommandCreator &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      static PlotCommandContainer s_commands;

    // Additional Implementation Declarations

};

// Class PlotCommandCreator 


#endif
