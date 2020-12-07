//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MIXUTILITY_H
#define MIXUTILITY_H 1

// xsTypes
#include "xsTypes.h"
// Error
#include <XSUtil/Error/Error.h>

//	Base class for mixing model utility implementations.
//
//	Invoking mixing models will be done in Model::calculate.
//
//	This will call Model::mix(SumComponent&)
//
//	which will transform the model according to the mixing
//	model's prescription.
//
//	The interface for mixing models (initially) consists of
//	an initializing function and a run (perform) function
//	which are both abstract.



class MixUtility 
{

  public:
    //	Throw when loaded data doesn't contain information
    //	needed to compute a mixing model.



    class IncompatibleData : public YellowAlert  //## Inherits: <unnamed>%3F9EE3E503B3
    {
      public:
          IncompatibleData (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class NoDataPresent : public YellowAlert  //## Inherits: <unnamed>%3F9EE3E90321
    {
      public:
          NoDataPresent (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class DataOrderingError : public YellowAlert  //## Inherits: <unnamed>%3F9EE4270207
    {
      public:
          DataOrderingError (const string& diag);

      protected:
      private:
      private: //## implementation
    };
      virtual ~MixUtility() = 0;

      virtual void initialize (const std::vector<Real>& params, const IntegerVector& specNums, const std::string& modelName);
      virtual void perform (const EnergyPointer& energy, const std::vector<Real>& params, GroupFluxContainer& flux, GroupFluxContainer& fluxError) = 0;
      virtual void initializeForFit (const std::vector<Real>& params, bool paramsAreFrozen);
      const string& name () const;

  public:
    // Additional Public Declarations

  protected:
      MixUtility (const string& name);
      
      virtual void verifyData ();
      const IntegerVector& specNums() const;
      void setSpecNums(const IntegerVector& specNums);

    // Additional Protected Declarations

  private:
      MixUtility(const MixUtility &right);
      MixUtility & operator=(const MixUtility &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const string m_name;
      IntegerVector m_specNums;

    // Additional Implementation Declarations

};


inline const string& MixUtility::name () const
{
  return m_name;
}

inline const IntegerVector& MixUtility::specNums () const
{
   return m_specNums;
}

inline void MixUtility::setSpecNums(const IntegerVector& specNums)
{
   m_specNums = specNums;
}

#endif
