//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef HELPCOMPOSITE_H
#define HELPCOMPOSITE_H 1

// Help
#include <XSUser/Help/Help.h>
#include "xsTypes.h"
#include <map>




class HelpComposite : public Help  //## Inherits: <unnamed>%3EF8AD000230
{

  public:
      HelpComposite(const HelpComposite &right);
      HelpComposite (const string& cmd, const string& path, Help::DocTypes docType, bool online = false);
      HelpComposite (const Help& right);
      virtual ~HelpComposite();
      HelpComposite & operator=(const HelpComposite &right);

      void addOrUpdateComponent (const string& cmd, Help* help);
      virtual void execute (const StringArray& strParams, int index) const;
      bool mapParams (const string& cmd, Help*& match, bool exactOnly = false) const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      std::map<string, Help*> m_mapParams;

    // Additional Implementation Declarations

};

// Class HelpComposite 


#endif
