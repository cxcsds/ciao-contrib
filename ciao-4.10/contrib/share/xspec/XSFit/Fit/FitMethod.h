//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef FITSTAT_H
#define FITSTAT_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// map
#include <map>
// Error
#include <XSUtil/Error/Error.h>
// FitStrategy
#include <XSFit/Fit/FitStrategy.h>
#include <set>




class FitMethod : public FitStrategy  //## Inherits: <unnamed>%3A7EC4820169
{

  public:



    class FitError : public YellowAlert  //## Inherits: <unnamed>%3C8795A0026A
    {
      public:
          FitError (int errCode, int paramNumber = 0);

      protected:
      private:
      private: //## implementation
    };
      virtual ~FitMethod();

      static FitMethod* get (const std::string& name);
      static void registerMethod (const string& name, FitMethod* method);
      void processMethodString (const IntegerArray& iParams, const StringArray& params);
      static string fitNames ();
      virtual FitMethod* clone () const = 0;
      virtual void reportProgress (std::ostream& s, Fit* fit) const;
      void perform (Fit* fit);
      const RealArray& evalue () const;
      const RealArray& evector () const;
      virtual string settingString () const = 0;
      virtual string fullName () const = 0;
      virtual bool getErrors (Fit* fit, const IntegerArray& paramNums);
      const RealArray& covariance () const;
      void reportCovariance () const;
      static void clearMethods ();
      virtual void processMethodStringExtras (const IntegerArray& iParams, const StringArray& params);
      virtual void improve (Fit* fit);
      bool secondDerivativeRequired () const;
      bool firstDerivativeRequired () const;
      Real deltaCrit () const;
      void deltaCrit (Real value);
      int numberOfTrials () const;
      void numberOfTrials (int value);
      bool delayedGratification () const;
      void delayedGratification (bool value);
      Real betaNormCrit () const;
      void betaNormCrit (Real value);
      const string& selectedSubMethod () const;
      RealArray& evalue ();
      void setEvalue (const RealArray& value);
      RealArray& evector ();
      void setEvector (const RealArray& value);
      RealArray& covariance ();
      void setCovariance (const RealArray& value);

  public:
    // Additional Public Declarations

  protected:
      FitMethod(const FitMethod &right);
      FitMethod (const std::string& initString);

      void secondDerivativeRequired (bool value);
      void firstDerivativeRequired (bool value);
      void selectedSubMethod (const string& subMethod);

    // Additional Protected Declarations

  private:
      FitMethod & operator=(const FitMethod &right);
      const bool pegsParameters () const;
      void pegsParameters (bool value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_secondDerivativeRequired;
      bool m_pegsParameters;
      bool m_firstDerivativeRequired;
      Real m_deltaCrit;
      int m_numberOfTrials;
      bool m_delayedGratification;
      Real m_betaNormCrit;
      string m_selectedSubMethod;
      //	This container will own all FitMethod object prototypes.
      static std::set<FitMethod*> s_fitMethodObjs;
      //	String keys refer to the names users may enter with the
      //	method command.  Multiple name keys may refer to the
      //	same FitMethod* since FitMethod can be a general package
      //	containing many "sub" methods (ie. Minuit). For this
      //	reason, delete should never be called on pointers from
      //	this map.  s_fitMethodObjs contains single copies of
      //	these pointers and therefore should handle deletions.
      static std::map<string,FitMethod*> s_subMethods;

    // Data Members for Associations
      RealArray m_evalue;
      RealArray m_evector;
      RealArray m_covariance;

    // Additional Implementation Declarations

};

// Class FitMethod::FitError 

// Class FitMethod 

inline void FitMethod::selectedSubMethod (const string& subMethod)
{
  m_selectedSubMethod = subMethod;
}

inline bool FitMethod::secondDerivativeRequired () const
{
  return m_secondDerivativeRequired;
}

inline const bool FitMethod::pegsParameters () const
{
  return m_pegsParameters;
}

inline void FitMethod::pegsParameters (bool value)
{
  m_pegsParameters = value;
}

inline bool FitMethod::firstDerivativeRequired () const
{
  return m_firstDerivativeRequired;
}

inline Real FitMethod::deltaCrit () const
{
  return m_deltaCrit;
}

inline void FitMethod::deltaCrit (Real value)
{
  m_deltaCrit = value;
}

inline int FitMethod::numberOfTrials () const
{
  return m_numberOfTrials;
}

inline void FitMethod::numberOfTrials (int value)
{
  m_numberOfTrials = value;
}

inline bool FitMethod::delayedGratification () const
{
  return m_delayedGratification;
}

inline void FitMethod::delayedGratification (bool value)
{
  m_delayedGratification = value;
}

inline Real FitMethod::betaNormCrit () const
{
  return m_betaNormCrit;
}

inline void FitMethod::betaNormCrit (Real value)
{
  m_betaNormCrit = value;
}

inline const string& FitMethod::selectedSubMethod () const
{
  return m_selectedSubMethod;
}

inline RealArray& FitMethod::evalue ()
{
  return m_evalue;
}

inline void FitMethod::setEvalue (const RealArray& value)
{
  m_evalue.resize(value.size());
  m_evalue = value;
}

inline RealArray& FitMethod::evector ()
{
  return m_evector;
}

inline void FitMethod::setEvector (const RealArray& value)
{
  m_evector.resize(value.size());
  m_evector = value;
}

inline RealArray& FitMethod::covariance ()
{
  return m_covariance;
}

inline void FitMethod::setCovariance (const RealArray& value)
{
  m_covariance = value;
}


#endif
