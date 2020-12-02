//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef HELP_H
#define HELP_H 1
#include "xsTypes.h"

// string
#include <string>




class Help 
{

  public:



    typedef enum {PDF, HTML} DocTypes;
      Help(const Help &right);
      Help (const string& fileName, const string& path, Help::DocTypes docType, bool composite = false, bool online = false);
      virtual ~Help();
      Help & operator=(const Help &right);

      static void initHelpTree ();
      virtual void execute (const StringArray& strParams, int index) const;
      static const Help* helpTree ();
      static void helpTree (Help* tree);
      static const std::string& pdfCommand ();
      static void pdfCommand (const std::string& value);
      static const std::string& htmlCommand ();
      static void htmlCommand (const std::string& value);
      bool isOnline () const;
      void isOnline (bool value);
      Help::DocTypes docType () const;
      void docType (Help::DocTypes value);

  public:
    // Additional Public Declarations

  protected:
      const bool isComposite () const;
      void isComposite (bool value);
      const std::string strFile () const;
      void strFile (std::string value);
      static void pHelpTree (Help* value);

    // Additional Protected Declarations

  private:
      void copy ();
      void erase () throw ();
      static const StringArray parseUserHelpDir ();
      string fileToCommand (const string& fileName) const;
      static void nameToObjects (const string& fileName, const string& dir, bool online);
      static void processOnlineFiles ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_isComposite;
      static const string PREFIX;
      static const std::string PDF_EXT;
      static const std::string HTML_EXT;
      static std::string s_pdfCommand;
      static std::string s_htmlCommand;
      bool m_isOnline;
      Help::DocTypes m_docType;

    // Data Members for Associations
      std::string m_strFile;
      static Help* s_pHelpTree;

    // Additional Implementation Declarations
    std::string m_strRelativePath;
};

// Class Help 

inline const Help* Help::helpTree ()
{
  return s_pHelpTree;
}

inline const bool Help::isComposite () const
{
  return m_isComposite;
}

inline void Help::isComposite (bool value)
{
  m_isComposite = value;
}

inline const std::string& Help::pdfCommand ()
{
  return s_pdfCommand;
}

inline void Help::pdfCommand (const std::string& value)
{
  s_pdfCommand = value;
}

inline const std::string& Help::htmlCommand ()
{
  return s_htmlCommand;
}

inline void Help::htmlCommand (const std::string& value)
{
  s_htmlCommand = value;
}

inline bool Help::isOnline () const
{
  return m_isOnline;
}

inline void Help::isOnline (bool value)
{
  m_isOnline = value;
}

inline Help::DocTypes Help::docType () const
{
  return m_docType;
}

inline void Help::docType (Help::DocTypes value)
{
  m_docType = value;
}

inline const std::string Help::strFile () const
{
  return m_strFile;
}

inline void Help::strFile (std::string value)
{
  m_strFile = value;
}

inline void Help::pHelpTree (Help* value)
{
  s_pHelpTree = value;
}


#endif
