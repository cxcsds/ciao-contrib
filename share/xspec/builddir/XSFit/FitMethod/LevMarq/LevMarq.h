//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef LEVMARQ_H
#define LEVMARQ_H 1
#include <XSModel/Parameter/ModParam.h>

// FitMethod
#include <XSFit/Fit/FitMethod.h>

class LevMarq : public FitMethod  //## Inherits: <unnamed>%3B7AE241020E
{

  public:
      LevMarq(const LevMarq &right);
      LevMarq (const std::string& initString = std::string());

      virtual LevMarq* clone () const;
      virtual void reportProgress (std::ostream& s, Fit* fit) const;
      virtual string settingString () const;
      virtual string fullName () const;
      //	dLambda is the constant used in Levenberg-Marquadt to
      //	bind its two
      //	modes (inverse Hessian / steepest descent).
      const Real dLambda () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:

     LevMarq& operator=(const LevMarq &right);
     void curFitXspec (int& errorFlag, IntegerVector& errorPar);
     void calcNewPars (RealArray& parVals);
      void invertCorrelationMatrix ();
      void calcStatAndDerivatives (const RealArray& parValues, bool doDerivatives, int& errorFlag, IntegerVector& errorPar);
      void reportEigenvectors () const;

    // Additional Private Declarations

  private: //## implementation
      virtual void doPerform (Fit* fit);

    // Data Members for Class Attributes
      // required to be double by fortran algorithm.
      double m_dLambda;
      //	This is a subset of the Fit m_variableParameters map.
      //	It does not include any parameters belonging to
      //	components with zero norms, or pegged parameters.
      std::map<int,ModParam*> m_variableParameters;
      Real m_fitStatistic;
      RealArray m_alpha;
      RealArray m_beta;

    // Additional Implementation Declarations

};

// Class LevMarq 

inline const Real LevMarq::dLambda () const
{
  return m_dLambda;
}


#endif
