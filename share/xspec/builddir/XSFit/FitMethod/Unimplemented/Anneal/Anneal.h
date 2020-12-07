//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef ANNEAL_H
#define ANNEAL_H 1

// FitMethod
#include <XSFit/Fit/FitMethod.h>




class Anneal : public FitMethod  //## Inherits: <unnamed>%3B7AE24602F9
{

  public:
      Anneal(const Anneal &right);
      Anneal (const std::string& initString = std::string());

      virtual Anneal* clone () const;
      virtual string fullName () const;

    // Additional Public Declarations
      virtual string settingString() const;
  protected:
    // Additional Protected Declarations

  private:
      virtual void doProcessMethodString (const string& methodInput);
      virtual void copy (const FitMethod& right);
      virtual void swap (FitMethod& right);

    // Additional Private Declarations

  private: //## implementation
      virtual void doPerform (Fit* fit);

    // Data Members for Class Attributes
      int m_evaluations;
      Real m_startTemp;
      Real m_reductionFactor;
      int m_cycles;

    // Additional Implementation Declarations

};

// Class Anneal 
inline string Anneal::settingString() const {
    return string("");
}


#endif
