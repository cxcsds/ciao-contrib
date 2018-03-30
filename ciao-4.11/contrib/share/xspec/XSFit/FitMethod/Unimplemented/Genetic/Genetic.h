//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef GENETIC_H
#define GENETIC_H 1

// FitMethod
#include <XSFit/Fit/FitMethod.h>




class Genetic : public FitMethod  //## Inherits: <unnamed>%3B7AE250020B
{

  public:
      Genetic(const Genetic &right);
      Genetic (const std::string& initString = std::string());

      virtual Genetic* clone () const;
      virtual string fullName () const;

    // Additional Public Declarations

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
      int m_numberOfGenerations;
      bool m_init;

    // Additional Implementation Declarations

};

// Class Genetic 


#endif
