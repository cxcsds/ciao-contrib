//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RANDOMIZERBASE_H
#define RANDOMIZERBASE_H 1

// xsTypes
#include <xsTypes.h>
class Fit;

//	Abstract base class to play the strategy role in the
//	Strategy design pattern.  The strategies in this case
//	are different algorithms for converting an input set of
//	parameter values to a randomized output set.
//
//	The public initialize and randomize functions are
//	wrappers to the private virtual functions which may be
//	overridden.



class RandomizerBase 
{

  public:
      virtual ~RandomizerBase();

      //	Calling functions are expected to fill the parameter
      //	Values array with the current values of all variable fit
      //	parameters.
      void randomize (RealArray& parameterValues, const Fit* fit);
      void initializeRun (const Fit* fit);
      void initializeLoad ();
      void acceptedRejected (const RealArray& parameterValues, bool isAccepted);
      const RealArray* covariance (const Fit* fit);
      const string& name () const;
      const string& initString () const;
      void initString (const string& value);

    // Additional Public Declarations

  protected:
      RandomizerBase(const RandomizerBase &right);
      RandomizerBase (const string& name);

    // Additional Protected Declarations

  private:
      RandomizerBase();
      RandomizerBase & operator=(const RandomizerBase &right);

      //	Inhereting classes should be able to ASSUME that
      //	parameterValues is filled with the current values of all
      //	variable fit parameters prior to when this function gets
      //	called.
      virtual void doRandomize (RealArray& parameterValues, const Fit* fit) = 0;
      //	Function for any optional initializations to be
      //	performed at the start of a series of randomization
      //	calls.
      virtual void doInitializeRun (const Fit* fit);
      //	Function for any optional initializations to be
      //	performed when the Randomizer class is first selected
      //	for usage.
      virtual void doInitializeLoad ();
      //	This is called for each iteration in the chain.  It
      //	passes along the parameter values of the most recent
      //	proposal, and a flag indicating whether the proposal was
      //	accepted.  Inheriting classes may want to use this
      //	information.
      virtual void doAcceptedRejected (const RealArray& parameterValues, bool isAccepted);
      //	This is returned by pointer rather than reference since
      //	subclasses won't always need to store a covariance
      //	array, and therefore won't override the getCovariance
      //	function.  In this case the default version returns a
      //	null pointer.
      //
      //	It is also capable of updating the Randomizer's stored
      //	covariance array, which is why it can't be a const
      //	function.
      virtual const RealArray* getCovariance (const Fit* fit);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const string m_name;
      string m_initString;

    // Additional Implementation Declarations

};

// Class RandomizerBase 

inline void RandomizerBase::randomize (RealArray& parameterValues, const Fit* fit)
{
   doRandomize(parameterValues, fit);
}

inline void RandomizerBase::initializeRun (const Fit* fit)
{
   doInitializeRun(fit);
}

inline void RandomizerBase::initializeLoad ()
{
   doInitializeLoad();
}

inline void RandomizerBase::acceptedRejected (const RealArray& parameterValues, bool isAccepted)
{
   doAcceptedRejected(parameterValues, isAccepted);
}

inline const RealArray* RandomizerBase::covariance (const Fit* fit)
{
   return getCovariance(fit);
}

inline const string& RandomizerBase::name () const
{
  return m_name;
}

inline const string& RandomizerBase::initString () const
{
  return m_initString;
}

inline void RandomizerBase::initString (const string& value)
{
  m_initString = value;
}


#endif
