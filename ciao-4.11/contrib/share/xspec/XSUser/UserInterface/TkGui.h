//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TKGUI_H
#define TKGUI_H 1
#include "xstcl.h"

// string
#include <string>
// TclRedAlert
#include <XSUser/UserInterface/TclRedAlert.h>//## begin module%38501A4201C0.declarations preserve=no
using std::string;




class TkGUI 
{

  public:
      ~TkGUI();

      static TkGUI* Instance (const string& console = "XScon", const string& text = "XStext", const string& plot = "XSplot");
      //	tk pathname for text widget
      char* textPath ();
      char* conPath ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      TkGUI (char* console, char* text, char* plot) throw (TclInitErr);
      char* plotPath ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static TkGUI* s_instance;
      char* m_plotPath;
      char* m_textPath;
      char* m_conPath;

    // Additional Implementation Declarations

};

// Class TkGUI 

inline char* TkGUI::plotPath ()
{
  return m_plotPath;
}

inline char* TkGUI::textPath ()
{
  return m_textPath;
}

inline char* TkGUI::conPath ()
{
  return m_conPath;
}


#endif
