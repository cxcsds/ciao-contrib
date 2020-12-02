//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%
//	Command class containing global information
//	about directories etc.

#ifndef GLOBAL_H
#define GLOBAL_H 1

// string
#include <string>
// Error
#include <XSUtil/Error/Error.h>
// Observer
#include <XSUtil/Utils/Observer.h>
class DummyResponse;

#include "xsTypes.h"
#include <XSUser/Help/Help.h>
#include <sys/times.h>
#include <sys/resource.h>
#include <map>

namespace XSGlobal {



    class GlobalData : public Subject  //## Inherits: <unnamed>%381602EE5998
    {

      public:



        class Startup : public RedAlert  //## Inherits: <unnamed>%3AE586F60364
        {
          public:
              Startup (const string& msg);

          protected:
          private:
          private: //## implementation
        };



        class NoSetting : public YellowAlert  //## Inherits: <unnamed>%3AE5B8E9024C
        {
          public:
              NoSetting (const string& msg = string(""));

          protected:
          private:
          private: //## implementation
        };
          ~GlobalData();

          static GlobalData* Instance ();
          void readSettings ();
          void readDefaultSettings ();
          std::string settings (const std::string& key) const;
          void setDisplayMode ();
          void processSettings ();
          DummyResponse* getDummyResponse ();
          //	this function is called whenever a return value
          //	statement is encountered in a handler. It simply passes
          //	back the input tclReturnValue, but executes the autosave
          //	function as part of it.
          int autoSave (int tclReturnValue);
          bool logging () const;
          void logging (bool value);
          bool gui () const;
          void gui (bool value);
          const string& initSettings () const;
          const string& managerDir () const;
          void managerDir (const string& value);
          const string& docuDir () const;
          void docuDir (const string& value);
          const string modDescripFile () const;
          const string& userDir () const;
          const string& initScript () const;
          const string& method () const;
          void method (const string& value);
          const struct rusage* currentTime () const;
          void currentTime (struct rusage* value);
          const struct rusage* initTime () const;
          const string& defaultGraph () const;
          void defaultGraph (const string& value);
          const string defaultLocalModelDirectory () const;
          void defaultLocalModelDirectory (string value);
          const string& scriptDir () const;
          size_t autoSaveFrequency () const;
          void autoSaveFrequency (size_t value);
          const string& autoSaveFile () const;
          void autoSaveFile (const string& value);
          const string userScriptDir () const;
          void userScriptDir (string value);
          const string undoFile () const;
          void undoFile (string value);
          bool useOnlineHelp () const;
          void useOnlineHelp (bool value);
          Help::DocTypes localHelpFormat () const;
          void localHelpFormat (Help::DocTypes value);
          const std::map<string,std::string>& settings () const;
          void settings (const string& key, const std::string& value);
          void defaultSettings (const string& key, const std::string& value);

      public:
        // Additional Public Declarations

      protected:
          GlobalData();

        // Additional Protected Declarations

      private:
          void copyFile (const string& dest, const string& source) const;
          static bool checkInitVersion (const string& filename);
          const string& commandFile () const;
          const string& commandLine () const;
          void commandLine (const string& value);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          static GlobalData* s_instance;
          bool m_logging;
          bool m_gui;
          string m_initSettings;
          string m_managerDir;
          string m_docuDir;
          const string m_modDescripFile;
          const string m_commandFile;
          string m_userDir;
          const string m_initScript;
          string m_commandLine;
          string m_method;
          struct rusage* m_currentTime;
          struct rusage* m_initTime;
          string m_defaultGraph;
          string m_defaultLocalModelDirectory;
          string m_scriptDir;
          size_t m_commandCount;
          size_t m_autoSaveFrequency;
          string m_autoSaveFile;
          string m_userScriptDir;
          string m_undoFile;
          bool m_useOnlineHelp;
          Help::DocTypes m_localHelpFormat;

        // Data Members for Associations
          std::map<string,std::string> m_settings;
          std::map<string,std::string> m_defaultSettings;

        // Additional Implementation Declarations

    };

    // Class XSGlobal::GlobalData::Startup 

    // Class XSGlobal::GlobalData::NoSetting 

    // Class XSGlobal::GlobalData 

    inline bool GlobalData::logging () const
    {
      return m_logging;
    }

    inline void GlobalData::logging (bool value)
    {
      m_logging = value;
    }

    inline bool GlobalData::gui () const
    {
      return m_gui;
    }

    inline void GlobalData::gui (bool value)
    {
      m_gui = value;
    }

    inline const string& GlobalData::initSettings () const
    {
      return m_initSettings;
    }

    inline const string& GlobalData::managerDir () const
    {
      return m_managerDir;
    }

    inline void GlobalData::managerDir (const string& value)
    {
      m_managerDir = value;
    }

    inline const string& GlobalData::docuDir () const
    {
      return m_docuDir;
    }

    inline void GlobalData::docuDir (const string& value)
    {
      m_docuDir = value;
    }

    inline const string GlobalData::modDescripFile () const
    {
      return m_modDescripFile;
    }

    inline const string& GlobalData::commandFile () const
    {
      return m_commandFile;
    }

    inline const string& GlobalData::userDir () const
    {
      return m_userDir;
    }

    inline const string& GlobalData::initScript () const
    {
      return m_initScript;
    }

    inline const string& GlobalData::commandLine () const
    {
      return m_commandLine;
    }

    inline void GlobalData::commandLine (const string& value)
    {
      m_commandLine = value;
    }

    inline const string& GlobalData::method () const
    {
      return m_method;
    }

    inline void GlobalData::method (const string& value)
    {
      m_method = value;
    }

    inline const struct rusage* GlobalData::currentTime () const
    {
      return m_currentTime;
    }

    inline void GlobalData::currentTime (struct rusage* value)
    {
 // From the man pages for getrusage:-
 //      struct timeval  ru_utime;      user time used 
 //    struct timeval  ru_stime;      system time used 
 //    long            ru_maxrss;     maximum resident set size 
 //    long            ru_idrss;      integral resident set size 
 //    long            ru_minflt;     page faults not requiring physical I/O 
 //    long            ru_majflt;     page faults requiring physical I/O 
 //    long            ru_nswap;      swaps 
 //    long            ru_inblock;    block input operations 
 //    long            ru_oublock;    block output operations 
 //    long            ru_msgsnd;     messages sent 
 //    long            ru_msgrcv;     messages received 
 //    long            ru_nsignals;   signals received 
 //    long            ru_nvcsw;      voluntary context switches 
 //    long            ru_nivcsw;     involuntary context switches 



      m_currentTime->ru_utime.tv_sec = value->ru_utime.tv_sec;
      m_currentTime->ru_utime.tv_usec = value->ru_utime.tv_usec;
      m_currentTime->ru_stime.tv_sec = value->ru_stime.tv_sec;
      m_currentTime->ru_stime.tv_usec = value->ru_stime.tv_usec;
      m_currentTime->ru_maxrss = value->ru_maxrss;   
      m_currentTime->ru_idrss = value->ru_idrss;   
      m_currentTime->ru_minflt = value->ru_minflt;  
      m_currentTime->ru_majflt = value->ru_majflt; 
      m_currentTime->ru_nswap = value->ru_nswap;  
      m_currentTime->ru_inblock = value->ru_inblock;  
      m_currentTime->ru_oublock = value->ru_oublock;  
      m_currentTime->ru_msgsnd = value->ru_msgsnd;  
      m_currentTime->ru_msgrcv = value->ru_msgrcv;  
      m_currentTime->ru_nsignals = value->ru_nsignals; 
      m_currentTime->ru_nvcsw = value->ru_nvcsw;   
      m_currentTime->ru_nivcsw = value->ru_nivcsw;  
    }

    inline const struct rusage* GlobalData::initTime () const
    {
      return m_initTime;
    }

    inline const string& GlobalData::defaultGraph () const
    {
      return m_defaultGraph;
    }

    inline void GlobalData::defaultGraph (const string& value)
    {
      m_defaultGraph = value;
    }

    inline const string GlobalData::defaultLocalModelDirectory () const
    {
      return m_defaultLocalModelDirectory;
    }

    inline void GlobalData::defaultLocalModelDirectory (string value)
    {
      m_defaultLocalModelDirectory = value;
    }

    inline const string& GlobalData::scriptDir () const
    {
      return m_scriptDir;
    }

    inline size_t GlobalData::autoSaveFrequency () const
    {
      return m_autoSaveFrequency;
    }

    inline void GlobalData::autoSaveFrequency (size_t value)
    {
      m_autoSaveFrequency = value;
    }

    inline const string& GlobalData::autoSaveFile () const
    {
      return m_autoSaveFile;
    }

    inline void GlobalData::autoSaveFile (const string& value)
    {
      m_autoSaveFile = value;
    }

    inline const string GlobalData::userScriptDir () const
    {
      return m_userScriptDir;
    }

    inline void GlobalData::userScriptDir (string value)
    {
      m_userScriptDir = value;
    }

    inline const string GlobalData::undoFile () const
    {
      return m_undoFile;
    }

    inline void GlobalData::undoFile (string value)
    {
      m_undoFile = value;
    }

    inline bool GlobalData::useOnlineHelp () const
    {
      return m_useOnlineHelp;
    }

    inline void GlobalData::useOnlineHelp (bool value)
    {
      m_useOnlineHelp = value;
    }

    inline Help::DocTypes GlobalData::localHelpFormat () const
    {
      return m_localHelpFormat;
    }

    inline void GlobalData::localHelpFormat (Help::DocTypes value)
    {
      m_localHelpFormat = value;
    }

    inline const std::map<string,std::string>& GlobalData::settings () const
    {
      return m_settings;
    }

    inline void GlobalData::settings (const string& key, const std::string& value)
    {
      m_settings[key] = value;
    }

    inline void GlobalData::defaultSettings (const string& key, const std::string& value)
    {
      m_defaultSettings[key] = value;
    }

} // namespace XSGlobal


#endif
