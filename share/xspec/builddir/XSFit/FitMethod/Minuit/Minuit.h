//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MINUIT_H
#define MINUIT_H 1
#include <XSModel/Parameter/ModParam.h>

// FitMethod
#include <XSFit/Fit/FitMethod.h>

// Minuit output class
#include "Minuit2/FunctionMinimum.h"

class MinuitCalcStat;

class Minuit : public FitMethod  //## Inherits: <unnamed>%3D17388203CC
{

  public:
      Minuit(const Minuit &right);
      Minuit (const string& initString = string());
      ~Minuit();

      virtual Minuit* clone () const;
      virtual bool getErrors (Fit* fit, const IntegerVector& paramNums);
      virtual string settingString () const;
      virtual string fullName () const;
      virtual void improve (Fit* fit);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:

     Minuit& operator=(const Minuit &right);
     void reportMinos (const ModParam& param) const;

    // Additional Private Declarations

  private: //## implementation
      void doPerform (Fit* fit);
      ROOT::Minuit2::FunctionMinimum doMinuitMinimize(Fit* fit, MinuitCalcStat& theStat, ROOT::Minuit2::MnUserParameters& upar, const string& method);
      void reportProgress(Fit* fit, ROOT::Minuit2::FunctionMinimum& min, const bool& first);
      void reportEigenvectors(Fit* fit) const;
      bool isFitDone(Fit* fit, size_t& trialsRemaining, double& saveStat, double currentStat);
      unsigned int numberFunctionEvals();
      void initializeNumberFunctionEvals();
      void incrementNumberFunctionEvals(const unsigned int& number);

    // Additional Implementation Declarations

      unsigned int m_FunctionEvals;

};

// Class Minuit 


#endif
