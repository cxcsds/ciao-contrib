//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XS_STREAM_H
#define XS_STREAM_H 1
#include <cstdio>

// iostream
#include <iostream>
// vector
#include <vector>
// Error
#include <XSUtil/Error/Error.h>

class XSstreambuf;
class XSstream;
class XSchannel;
class VerbosityManager;
struct VerboseManip;

using std::string;

const unsigned int bufSize=1024;
extern const size_t NORM_OUTPUT;




class XSstreambuf : public std::streambuf  //## Inherits: <unnamed>%389888B3C7F0
{
  public:
      XSstreambuf();
      //	Tcl streambuf for input/output. Contains a tcl "channel",
      //	which contains the read/write methods, and overloads
      //	sync and overflow methods for the buffer.
      XSstreambuf (XSchannel* chan, std::streamsize bufferLen = 0);
      virtual ~XSstreambuf();

      void setChannel (XSchannel* channel, std::streamsize bufferLen, XSstream* parent);
      void setChannelPrompt (const std::string& ps);
      void setChannelPrompt (const std::string& ps, const std::vector<std::string>& prompts, const std::vector<std::string>& infos);

  protected:
      virtual int sync ();
      virtual int overflow (int c = EOF);
      //	Allow for buffered or unbuffered input in either
      //	direction, so that  buffering strategies can be changed
      //	later as expedient.
      //
      //	The sign of n is used to denote output (+ve) or input
      //	(-ve).
      //
      //	Unbuffered input needs extra functions pbackfail and
      //	data   members char ch, bool fromBuf.
      //
      //	See Langer & Kreft 2000, Standard C++ IOStreams and
      //	Locales, Sec 3.4
      virtual std::streambuf* setbuf (char* s, std::streamsize n);
      virtual int uflow ();
      virtual int underflow ();
      int pbackfail (int c = EOF);

  private:
      XSstreambuf(const XSstreambuf &right);
      XSstreambuf & operator=(const XSstreambuf &right);

      int fillBuffer ();
      std::streamsize bufferOut ();
      const bool unbuffered () const;
      void unbuffered (bool value);
      const bool charTaken () const;
      void charTaken (bool value);
      const char ch () const;
      void ch (char value);
      //	Data member to support a putback facility.
      //
      //	putback is probably totally irrelevant to this
      //	application,
      //	but is implemented for generality.
      const int pbChars () const;
      void pbChars (int value);
      const std::streamsize bufLen () const;
      void bufLen (std::streamsize value);
      XSchannel* channel ();

  private: //## implementation
    // Data Members for Class Attributes
      bool m_unbuffered;
      bool m_charTaken;
      char m_ch;
      int m_pbChars;
      std::streamsize m_bufLen;
      char* m_buffer;

    // Data Members for Associations
      XSchannel* m_channel;
    friend class XSstream;
};
//	An XSstream object OWNS its dynamically allocated
//	XSstreambuf, and therefore must delete it in its
//	destructor.  (This is not the case with a standard basic_
//	ios and its streambuf.)



class XSstream : public std::iostream  //## Inherits: <unnamed>%38CD29694378
{

  public:



    class NotXSstream : public YellowAlert  //## Inherits: <unnamed>%3BA0DD57003B
    {
      public:
          NotXSstream();

      protected:
      private:
      private: //## implementation
    };
    
      XSstream();
      //	Stream with an XSchannel object.
      XSstream (XSchannel* chan, std::streamsize bufferLen = bufSize);
      virtual ~XSstream();

      //	setPrompter hands to input stream s the prompt
      //	ps, which can be a script or a text prompt depending
      //	on the context. BY CONVENTION, all text prompts
      //	must end in ">" or ":" or they will be assumed to be
      //	script names. This version is to be used for
      //	scripts that do not take a vector of arguments.
      //
      //	setPrompter is static and virtual: this allows the
      //	first (istream&) argument to be cast inside the
      //	function and thus allow the stream to look like a
      //	"normal" istream.
      //
      //	The virtualness allows a default implementation to
      //	exist even for channel classes that don't use it,
      //	to allow compilation to proceed.
      static void setPrompter (std::istream& s, const std::string& ps = ">");
      //	The overloaded versions of setPrompter with signature
      //
      //	(istream&, const string&, const vector<string>&, const
      //	vector<string>&)
      //
      //	Provide the facility for the internal code to send
      //	strings to a script that describes a dialog box.
      //
      //	Typically it might be used to provide prompt strings
      //	and information strings to the script ps.
      //
      //	This concept can be used for the command line
      //	interface too, if it is desired to make the dialogue
      //	with the user a single function call that returns
      //	a set of strings (as will the GUI).
      //
      //	The setPrompter function, which chains into the
      //	channel implementation through the streambuf is
      //	of static void type.
      static void setPrompter (std::istream& s, const std::string& ps, const std::vector<std::string>& prompts, const std::vector<std::string>& infos);
      void setLogger (const std::string& name = "xspec.log", bool isErr = false);
      void closeLog ();
      static void defineChannel (std::ostream& s, XSchannel* chan, std::streamsize bufLen = 0);
      static void defineChannel (std::istream& s, XSchannel* chan, std::streamsize bufLen = 0);
      int maxChatter ();
      XSchannel* getChannel ();
      const int consoleChatterLevel () const;
      void consoleChatterLevel (int value);
      const int logChatterLevel () const;
      void logChatterLevel (int value);
      
      // This sets console and log verbose to the same level.  If level is
      // negative, it will undo the most reset verbose setting.  Note
      // that xsverbose() provides a stream manipulator interface for
      // this function.
      void setVerbose (int level=-1);
      // An overload for when con and log should differ.  To change
      // just one of the levels, set the other to a negative value.
      void setVerbose(int conLevel, int logLevel);
      // Restricted verbosity is only intended for special cases and 
      // should be used with caution.  The idea is to allow a section of
      // code to FORCE a verbosity setting on nested subroutines.  When
      // this is set, all intervening standard verbosity calls will be
      // ignored.  Note that setRestrictedVerbose calls may themselves
      // be nested, in which case the outer-most has precedence.  Also
      // note that this doesn't allow for independent console/log settings.
      void setRestrictedVerbose(int level);
      void removeRestrictedVerbose();
      // These get functions are sensitive to the resetrictedVerbose
      // setting -- that's what they'll return if restrictedVerbose is in use.
      int conVerbose () const;
      int logVerbose () const;
      friend VerboseManip xsverbose(int);
      
  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      XSstream(const XSstream &right);
      XSstream & operator=(const XSstream &right);

      void defineChannel (XSchannel* chan, std::streamsize bufLen = 0);

      // Helper functions needed to implement xsverbose stream
      // manipulator below.
      static XSstream& set_verbose(XSstream& s, int level);
      static XSstream& undo_verbose(XSstream& s, int dummy);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      int m_consoleChatterLevel;
      int m_logChatterLevel;
      
      VerbosityManager* m_verbosity;

    // Additional Implementation Declarations

};

//////////////////////////////////////////////////

// This is to allow setting verbose levels with stream manipulators,
// ie.  xss << xsverbose(5).  See Stroustrup 21.4.6.1.
   
struct VerboseManip
{
   VerboseManip(XSstream& (*ff) (XSstream&, int), int level)
     : m_f(ff), m_level(level) { }
   
   // m_f is a pointer to a wrapper of an XSstream verbosity member function.
   XSstream& (*m_f) (XSstream&, int);
   int m_level;
};

// Note that this takes a reference to the base class ostream rather
// than an XSstream.  This is to allow it to come after a std manipulator
// in an output stream chain, ie. xss << std::endl << xsverbose();
// However the stream object had better really be an XSstream, else
// this will throw a RedAlert.
XSstream& operator<< (std::ostream& xss, const VerboseManip& vm);

// xsverbose stream manipulator is deliberately not enclosed in a namespace.
// This is to keep its name shorter when inserted into an output stream chain.
inline VerboseManip xsverbose(int level=-1)
{
   if (level < 0)
      return VerboseManip(XSstream::undo_verbose, level);
   else
      return VerboseManip(XSstream::set_verbose, level);
}
////////////////////////////////////////////////////

class XSchannel 
{

  public:



    class LogFileOpenFailure : public YellowAlert  //## Inherits: <unnamed>%3B969D5500F0
    {
      public:
          LogFileOpenFailure (const std::string& diag);

      protected:
      private:
      private: //## implementation
    };
      virtual ~XSchannel();

      //	Abstract read function for tcl channels.
      //
      //	The int returned will be the number of characters
      //	successfully read by tcl.
      //
      //	Desire here is to implement logging for
      //	the CLI version, handled in subclass TclIO.
      //
      //	The TkIO version will read input from a graphical
      //	window and will thus need a (tk) script name to prompt
      //	user. In this sense the tk GUI occupies the same
      //	function as the CLI prompt.
      //
      //	The read,write functions follow the Unix O/S convention
      //	for return codes: they return 0, -1 as the read, write
      //	was successful or unsuccessful.
      virtual std::streamsize read (char* s, std::streamsize n = 1) = 0;
      virtual void setPrompt (const std::string& ps);
      virtual void prompts (const std::string& script, const std::vector<std::string>& prompts, const std::vector<std::string>& infos);
      void setLogger (const std::string& name, bool isErr = false);
      void closeLog ();
      int toDevice (const char* s, std::streamsize n);

  public:
    // Additional Public Declarations
      //friend void XSstreambuf::setChannel(XSchannel* channel, std::streamsize bufferLen, XSstream* parent);
      friend class XSstreambuf;            
  protected:
      XSchannel();

      size_t logVerbose () const;
      size_t conVerbose () const;
      const XSstream* stream () const;
      void stream (XSstream* value);

    // Additional Protected Declarations

  private:
      //	write will call Tcl_Write in the case of
      //	the CLI version, and a tk window pathname in the case of
      //	the GUI.
      //
      //	Logging will be implemented in the case of CLI.
      //
      //	The read,write functions follow the Unix O/S convention
      //	for return codes: they return 0, -1 as the read, write
      //	was successful or unsuccessful.
      virtual std::streamsize write (const char *s, std::streamsize n) = 0;
      virtual void internalSetLogger (const std::string& name, bool isErr = false) = 0;
      virtual void internalCloseLog () = 0;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      XSstream* m_stream;

    // Additional Implementation Declarations

};

// Class XSstreambuf 

inline const bool XSstreambuf::unbuffered () const
{
  return m_unbuffered;
}

inline void XSstreambuf::unbuffered (bool value)
{
  m_unbuffered = value;
}

inline const bool XSstreambuf::charTaken () const
{
  return m_charTaken;
}

inline void XSstreambuf::charTaken (bool value)
{
  m_charTaken = value;
}

inline const char XSstreambuf::ch () const
{
  return m_ch;
}

inline void XSstreambuf::ch (char value)
{
  m_ch = value;
}

inline const int XSstreambuf::pbChars () const
{
  return m_pbChars;
}

inline void XSstreambuf::pbChars (int value)
{
  m_pbChars = value;
}

inline const std::streamsize XSstreambuf::bufLen () const
{
  return m_bufLen;
}

inline void XSstreambuf::bufLen (std::streamsize value)
{
  m_bufLen = value;
}

inline XSchannel* XSstreambuf::channel ()
{
  return m_channel;
}

// Class XSstream::NotXSstream 

// Class XSstream 

inline const int XSstream::consoleChatterLevel () const
{
  return m_consoleChatterLevel;
}

inline void XSstream::consoleChatterLevel (int value)
{
  m_consoleChatterLevel = value;
}

inline const int XSstream::logChatterLevel () const
{
  return m_logChatterLevel;
}

inline void XSstream::logChatterLevel (int value)
{
  m_logChatterLevel = value;
}

// Class XSchannel::LogFileOpenFailure 

// Class XSchannel 

inline const XSstream* XSchannel::stream () const
{
  return m_stream;
}

inline void XSchannel::stream (XSstream* value)
{
  m_stream = value;
}


#endif
