//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TCL_STREAM_H
#define TCL_STREAM_H 1

// xstcl
#include "XSUser/UserInterface/xstcl.h"
// XSstream
#include <XSUtil/Utils/XSstream.h>




typedef string TclScript;
namespace xstcl {

        static Tcl_ChannelType* xsLogPtr;       

}



class TkIO : public XSchannel  //## Inherits: <unnamed>%38988926AD80
{

  public:
      TkIO(const TkIO &right);
      TkIO (char* winName = 0);
      ~TkIO();

      //	TkIO::read is to be called when information is to be
      //	read from a GUI window created by a tk script.
      //
      //	The read,write functions follow the Unix O/S convention
      //	for return codes: they return 0, -1 as the read, write
      //	was successful or unsuccessful.
      virtual std::streamsize read (char* s, std::streamsize n = 1);
      void setPrompt (const std::string& ps);
      void prompts (const std::string& script, const std::vector<std::string>& prompts, const std::vector<std::string>& infos);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      //	TkIO::write is to be called to write the contents of the
      //	TclOutputStream to a tk window.
      //
      //	The read,write functions follow the Unix O/S convention
      //	for return codes: they return n, -1 as the read, write
      //	was successful or unsuccessful.`, where n is the number
      //	of characters read/written
      virtual std::streamsize write (const char* s, std::streamsize n);
      virtual void internalSetLogger (const std::string& name, bool isErr = false);
      void internalCloseLog ();
      const char* window () const;
      void window (char* value);
      //	For TkIO, the "prompt" is actually a tk script that
      //	defines
      //	a dialogue box. Whatever the user types into the
      //	window must be returned as a variable, and written
      //	eventually to the stream buffer.
      const TclScript prompt () const;
      const Tcl_Channel logChannel () const;
      void logChannel (Tcl_Channel value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      char* m_window;
      TclScript m_prompt;
      Tcl_Channel m_logChannel;

    // Additional Implementation Declarations

};



class TclIO : public XSchannel  //## Inherits: <unnamed>%3898892D1AE8
{

  public:
      TclIO(const TclIO &right);
      TclIO (Tcl_Channel channel);
      ~TclIO();

      //	Must call Tcl_GetsObj, store input in a tcl object,
      //	and insert the contents of the object into a stream
      //	buffer.
      virtual std::streamsize read (char* s, std::streamsize n = 1);
      virtual void setPrompt (const string& ps);
      virtual const string& prompt () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      TclIO();

      virtual std::streamsize write (const char* s, std::streamsize n);
      virtual void internalSetLogger (const std::string& name, bool isErr = false);
      void internalCloseLog ();
      const Tcl_Channel ioChannel () const;
      void ioChannel (Tcl_Channel value);
      const Tcl_Channel logChannel () const;
      void logChannel (Tcl_Channel value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Tcl_Channel m_ioChannel;
      Tcl_Channel m_logChannel;
      string m_prompt;

    // Additional Implementation Declarations

};

// Class TkIO 

inline const char* TkIO::window () const
{
  return m_window;
}

inline void TkIO::window (char* value)
{
  m_window = value;
}

inline const TclScript TkIO::prompt () const
{
  return m_prompt;
}

inline const Tcl_Channel TkIO::logChannel () const
{
  return m_logChannel;
}

inline void TkIO::logChannel (Tcl_Channel value)
{
  m_logChannel = value;
}

// Class TclIO 

inline const Tcl_Channel TclIO::ioChannel () const
{
  return m_ioChannel;
}

inline void TclIO::ioChannel (Tcl_Channel value)
{
  m_ioChannel = value;
}

inline const Tcl_Channel TclIO::logChannel () const
{
  return m_logChannel;
}

inline void TclIO::logChannel (Tcl_Channel value)
{
  m_logChannel = value;
}

inline const string& TclIO::prompt () const
{
  return m_prompt;
}


#endif
