//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MIXBASE_H
#define MIXBASE_H 1

// xsTypes
#include "xsTypes.h"
// Error
#include <XSUtil/Error/Error.h>

//	Base class for mixing model implementations.
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



class MixBase 
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
      virtual ~MixBase() = 0;

      virtual void initialize (const std::vector<Real>& params, const std::string& modelName = std::string(""));
      virtual void perform (const EnergyPointer& energy, const std::vector<Real>& params, GroupFluxContainer& flux, GroupFluxContainer& fluxError) = 0;
      virtual void verifyData () const;
      virtual void initializeForFit (const std::vector<Real>& params, bool paramsAreFrozen);
      virtual void refreshTransform ();
      const string& name () const;

  public:
    // Additional Public Declarations

  protected:
      MixBase (const string& name);

    // Additional Protected Declarations

  private:
      MixBase & operator=(const MixBase &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const string m_name;

    // Additional Implementation Declarations

};

// Class MixBase::IncompatibleData 

// Class MixBase::NoDataPresent 

// Class MixBase::DataOrderingError 

// Class MixBase 

inline const string& MixBase::name () const
{
  return m_name;
}


#endif
