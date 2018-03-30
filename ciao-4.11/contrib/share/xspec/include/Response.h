//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RESPONSE_H
#define RESPONSE_H 1
// These forward declarations are required to implement the
// various "to...Response" pointer retrieval functions.  They
// exist to allow an alternative to costly dynamic_casting for
// determining Response subclass type.  The downside is that this
// base class header file must now be aware of subclass types
class RealResponse;
class MultiResponse;
class UserDummyResponse;

// xsTypes
#include <xsTypes.h>
// vector
#include <vector>
// Error
#include <XSUtil/Error/Error.h>
// map
#include <map>
// XspecRegistry
#include <XSModel/DataFactory/XspecRegistry.h>

class SpectralData;
class Model;
class SumComponent;
class ResponseParam;
#include <utility>

//	The Response Matrix class. Its current relationship to
//	datasets in Xspec is 1:1 but it needs to be changed to
//	cope with multiple sources as required by Integral.
//
//	The key point about this implementation is that the data
//	members of each subclass must be
//	identical: in fact, it's the read [and write] functions
//	only that are different. Thus
//	practically everything is inherited from the base class.



class Response : public RegisteredFormat  //## Inherits: <unnamed>%3ACDCDB502EF
{

  public:



    class InvalidBins : public YellowAlert  //## Inherits: <unnamed>%37FE11B0EE20
    {
      public:
          //	Class Response::InvalidBins
          //	Additional Declarations
          InvalidBins (const string& message);

      protected:
      private:
      private: //## implementation
    };



    class InvalidRequest : public YellowAlert  //## Inherits: <unnamed>%3CF6337001E8
    {
      public:
          InvalidRequest();

      protected:
      private:
      private: //## implementation
    };



    class GainError : public YellowAlert  //## Inherits: <unnamed>%414211010036
    {
      public:
          GainError (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    typedef enum {OFFSET, LINEAR} ResponseParType;
      virtual ~Response();

      //	Convolution method for responses. Input model component,
      //	output folded model component.
      //	      //	For the time being implement output as Real
      //	Array.
      //	For the time being implement output as RealArray.
      //	There might be a better implementation that involved
      //	adding a folded array data member to the Component
      //	class. In the meantime the idea is to output the
      //	RealArray folded component and sum for the total
      //	model.
      //	      //	This must be modified to throw a YellowAlert
      //	Exception
      //	This must be modified to throw a YellowAlert Exception
      //	for invalid computations and to throw standard numeric
      //	exceptions.
      virtual Model& operator * (Model& model) const = 0;
      void renumber (size_t newIndex);
      virtual Response* clone () const = 0;
      virtual void setEnergies () = 0;
      //	fileFormat() returns true if the input filename is of
      //	the format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      //	Template method for removing RMF data from Response
      //	classes.
      //
      //	Default implementation is to call the protected virtual
      //	base class implementation which is empty
      void checkRMFdata () throw ();
      virtual RealArray sensitivity (const SpectralData* data);
      //	template method for ordering of Response objects.
      friend bool operator < (const Response& left, const Response& right);
      virtual SpectralData* source () const = 0;
      virtual void source (SpectralData* spectrum) = 0;
      //	template method for ordering of Response objects.
      friend bool operator > (const Response& left, const Response& right);
      const RealArray& lowerBoundNominalEnergy () const;
      const RealArray& upperBoundNominalEnergy () const;
      virtual const RealArray& eboundsMin () const;
      virtual const RealArray& eboundsMax () const;
      virtual void prepareForFit ();
      virtual const RealArray& efficiency () const;
      //	Convolution method for responses. Input model component,
      //	output folded model component.
      //
      //
      //	For the time being implement output as RealArray.
      //	There might be a better implementation that involved
      //	adding a folded array data member to the Component
      //	class. In the meantime the idea is to output the
      //	RealArray folded component and sum for the total
      //	model.
      //
      //	This must be modified to throw a YellowAlert Exception
      //	for invalid computations and to throw standard numeric
      //	exceptions.
      virtual void operator * (SumComponent& source) const = 0;
      const RealArray& energies () const;
      void applyGainFromPrompt (Real slope, Real intercept);
      void removeGain ();
      bool isGainApplied () const;
      bool makeGainParams (const string& slopeParamVals, const string& offsetParamVals);
      void removeGainParams ();
      string makeParamPromptString () const;
      void promptParamValues (string& paramVals, Response::ResponseParType parType) const;
      void setParamValues (const string& paramVals, Response::ResponseParType parType);
      void applyGainFromFit (Response::ResponseParType parType);
      const ResponseParam* getConstGain () const;
      const ResponseParam* getLinearGain () const;
      virtual void calcEffAreaPerChan (RealArray& effArea);
      virtual const RealResponse* toRealResponse () const;
      virtual const MultiResponse* toMultiResponse () const;
      virtual const UserDummyResponse* toUserDummyResponse () const;
      //	An obscure function originally created for dummyrsp.
      //	The idea is to prevent leaving any gain parameters
      //	intact if the Response is placed on a dummy hook.
      void untieParamLinks () const;
      //	register and deregisterResponseParams only need to be
      //	called externally for cases where the Response object is
      //	unaware that it has been relocated (primarily, during a
      //	swap with a dummy response).  In all other contexts, the
      //	Response functions know when they need to insert or
      //	remove their parameters from the global ResponseParam
      //	container, and will do so without this prompting.
      void registerResponseParams () const;
      //	See registerResponseParams comments.
      void deregisterResponseParams () const;
      //	Number of Energy bins
      unsigned int numEnergies () const;
      void numEnergies (unsigned int value);
      //	Number of detector channels.
      unsigned int numChannels () const;
      void numChannels (unsigned int value);
      size_t spectrumNumber () const;
      void spectrumNumber (size_t value);
      size_t sourceNumber () const;
      void sourceNumber (size_t value);
      size_t dataGroup () const;
      void dataGroup (size_t value);
      //	Giving responses a unique id for management of
      //	multiple responses with the same name.
      size_t index () const;
      bool active () const;
      static Real NO_KEYVAL ();
      //	Gain slope lower/upper hard limits read from the
      //	response file.  Leave it up to inheriting classes to
      //	store keyword names and perform the read.  If a
      //	particular bound is not found, it is set to NO_KEYVAL.
      //	These values are NOT AFFECTED by rnewpar, and therefore
      //	will not necessarily be equivalent to the actual current
      //	limits of the parameter.
      std::pair<Real,Real> slopeKeyLimits () const;
      //	Gain offset lower/upper hard limits as stored in the
      //	response file.  See comments for slopeKeyLimits.
      std::pair<Real,Real> offsetKeyLimits () const;
      const std::vector<Real>& gainFactor () const;

  public:
    // Additional Public Declarations

  protected:
      Response();

      Response(const Response &right);

      virtual void RMFremove ();
      virtual bool order (const Response& right) const;
      void setActive (bool activeStatus);
      virtual void shiftEffectiveArea (const RealArray& newEnergies);
      virtual void restoreEffectiveArea ();
      void setSlopeKeyLimits (const Real lower, const Real upper);
      void setOffsetKeyLimits (const Real lower, const Real upper);
      const std::string& eboundsExtName () const;
      void eboundsExtName (const std::string& value);
      ResponseParam* constGain () const;
      ResponseParam* linearGain () const;
      RealArray& energies ();
      Real energies (size_t index) const;
      void energies (size_t index, Real value);

    // Additional Protected Declarations

  private:
      Response & operator=(const Response &right);

      virtual void convolve (const RealArray& flux, const RealArray& fluxErr, RealArray& foldFlux, RealArray& foldFluxErr) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static int s_count;
      unsigned int m_numEnergies;
      unsigned int m_numChannels;
      size_t m_spectrumNumber;
      size_t m_sourceNumber;
      size_t m_dataGroup;
      size_t m_index;
      std::string m_eboundsExtName;
      bool m_active;
      ResponseParam* m_constGain;
      ResponseParam* m_linearGain;
      static const Real s_NO_KEYVAL;
      std::pair<Real,Real> m_slopeKeyLimits;
      std::pair<Real,Real> m_offsetKeyLimits;

    // Data Members for Associations
      RealArray m_energies;
      std::vector<Real> m_gainFactor;

    // Additional Implementation Declarations

};

// Class Response::InvalidBins 

// Class Response::InvalidRequest 

// Class Response::GainError 

// Class Response 

inline const RealArray& Response::energies () const
{
  return m_energies;
}

inline const ResponseParam* Response::getConstGain () const
{
  return m_constGain;
}

inline const ResponseParam* Response::getLinearGain () const
{
  return m_linearGain;
}

inline const RealResponse* Response::toRealResponse () const
{
   return 0;
}

inline const MultiResponse* Response::toMultiResponse () const
{
   return 0;
}

inline const UserDummyResponse* Response::toUserDummyResponse () const
{
   return 0;
}

inline void Response::setSlopeKeyLimits (const Real lower, const Real upper)
{
   m_slopeKeyLimits.first = lower;
   m_slopeKeyLimits.second = upper;
}

inline void Response::setOffsetKeyLimits (const Real lower, const Real upper)
{
   m_offsetKeyLimits.first = lower;
   m_offsetKeyLimits.second = upper;
}

inline unsigned int Response::numEnergies () const
{
  return m_numEnergies;
}

inline void Response::numEnergies (unsigned int value)
{
  m_numEnergies = value;
}

inline unsigned int Response::numChannels () const
{
  return m_numChannels;
}

inline void Response::numChannels (unsigned int value)
{
  m_numChannels = value;
}

inline size_t Response::spectrumNumber () const
{
  return m_spectrumNumber;
}

inline void Response::spectrumNumber (size_t value)
{
  m_spectrumNumber = value;
}

inline size_t Response::sourceNumber () const
{
  return m_sourceNumber;
}

inline void Response::sourceNumber (size_t value)
{
  m_sourceNumber = value;
}

inline size_t Response::dataGroup () const
{
  return m_dataGroup;
}

inline void Response::dataGroup (size_t value)
{
  m_dataGroup = value;
}

inline size_t Response::index () const
{
  return m_index;
}

inline const std::string& Response::eboundsExtName () const
{
  return m_eboundsExtName;
}

inline void Response::eboundsExtName (const std::string& value)
{
  m_eboundsExtName = value;
}

inline bool Response::active () const
{
  return m_active;
}

inline ResponseParam* Response::constGain () const
{
  return m_constGain;
}

inline ResponseParam* Response::linearGain () const
{
  return m_linearGain;
}

inline Real Response::NO_KEYVAL ()
{
  return s_NO_KEYVAL;
}

inline std::pair<Real,Real> Response::slopeKeyLimits () const
{
  return m_slopeKeyLimits;
}

inline std::pair<Real,Real> Response::offsetKeyLimits () const
{
  return m_offsetKeyLimits;
}

inline RealArray& Response::energies ()
{
  return m_energies;
}

inline Real Response::energies (size_t index) const
{
  return m_energies[index];
}

inline void Response::energies (size_t index, Real value)
{
  m_energies[index] = value;
}

inline const std::vector<Real>& Response::gainFactor () const
{
  return m_gainFactor;
}
inline bool operator < (const Response& left, const Response& right)
{
        return left.order(right);       
}

inline bool operator > (const Response& left, const Response& right)
{
        return !left.order(right);       
}


#endif
