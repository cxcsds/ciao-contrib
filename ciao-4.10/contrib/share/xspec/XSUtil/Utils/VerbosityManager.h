// C++
#ifndef VERBOSITYMANAGER_H
#define VERBOSITYMANAGER_H

#include <deque>
#include <stack>

class VerbosityManager
{
   public:
       // Verbosity levels must be non-negative.
      VerbosityManager(const int startConLevel, const int startLogLevel);
      ~VerbosityManager();
      
      // If restrictedVerbose is set, the get functions will return that
      // value.  Otherwise they return their own most recent setting.
      int getConVerbose() const;
      int getLogVerbose() const;
      
      // This is intended to be used in pairs with removeVerbose calls.
      // Level input may be positive or negative.  However a negative
      // value is treated as "maintain current setting" for that particular
      // output stream.  This returns "true" if able to set the new levels,
      // and "false" if restrictedVerbose is in use, in which case this
      // function does nothing.
      bool setVerbose(const int conLevel, const int logLevel);
      // This is intended to be used in pairs with setVerbose.  It
      // removes the most recent values sent to setVerbose and restores
      // the previous levels.  This returns "true" if able to remove the 
      // current levels, and "false" if restrictedVerbose is in use,
      // in which case this function does nothing.
      bool removeVerbose();
      
      // The restrictedVerbose setting is a mechanism to override the
      // usual verbosity settings.  It is intended as a way of allowing
      // a caller to enforce a level of output over a block of code, 
      // regardless of any verbosity settings within its nested code.
      // With the normal verbosity settings the inner-most setting
      // of nested calls takes precedence.  With restrictedVerbosity,
      // the outer-most has precedence. While this is set, the
      // setVerbose/removeVerbose functions will do nothing. 
        
      // This returns -1 if restricted verbose is not currently set.
      int getRestrictedVerbose() const;
      // This is intended to be called in pairs with removeRestrictedVerbose.
      // The level must be >= 0.
      void setRestrictedVerbose(const int level);
      // This is intended to be called in pairs with setRestrictedVerbose.
      void removeRestrictedVerbose();
      
   private:
      std::stack<int> m_conVerbose;
      std::stack<int> m_logVerbose;
      
      std::deque<int> m_restrictedVerbose;
};


#endif
