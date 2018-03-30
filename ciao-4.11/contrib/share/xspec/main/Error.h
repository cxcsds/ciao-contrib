//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ERROR_H
#define ERROR_H 1
#include <string>
using std::string;

//	Base Class for exceptions that do not cause program
//	termination



class YellowAlert 
{
  public:
      YellowAlert();
      YellowAlert (const string& message);
      virtual ~YellowAlert();

  protected:
  private:
  private: //## implementation
};



class InputError : public YellowAlert  //## Inherits: <unnamed>%3BD9A51901AF
{
  public:
      InputError (const string& msg = "Input Error");

  protected:
  private:
  private: //## implementation
};

// YellowAlert class that stores rather than streams the diagnostic message.
// Useful for transfering error messages from child to parent for output
// streaming during parallel processing.
class YellowAlertNS : public YellowAlert
{
   public:
      YellowAlertNS(const string& msg);
      virtual ~YellowAlertNS();
      
      const string& message() const;
      
   private:
      string m_message;
};


//	Exception Base Class for exceptions that cause the
//	program
//	to terminate



class RedAlert 
{
  public:
      RedAlert (const string& message, int returnCode);
      RedAlert (const std::string& msg);
      virtual ~RedAlert();

  protected:
      virtual void reportAndExit (const string& message = "Unspecified Fatal Error", const int returnCode = -1);

  private:
  private: //## implementation
};

// Class YellowAlert 

inline YellowAlert::~YellowAlert()
{
}


inline YellowAlertNS::~YellowAlertNS()
{
}

inline const string& YellowAlertNS::message() const
{
   return m_message;
}

// Class RedAlert 

inline RedAlert::~RedAlert()
{
}



#endif
