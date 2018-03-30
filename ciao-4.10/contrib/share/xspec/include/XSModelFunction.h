//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSMODELFUNCTION_H
#define XSMODELFUNCTION_H 1

// xsTypes
#include <xsTypes.h>
// Error
#include <XSUtil/Error/Error.h>
// ComponentInfo
#include <XSUtil/FunctionUtils/ComponentInfo.h>
#ifdef INITPACKAGE
#       include <funcType.h>
#else
#       include <XSUtil/FunctionUtils/funcType.h>
#endif

#include <XSUtil/Parse/XSparse.h>  // invalid exception
#include <XSUtil/Parse/MathExpression.h>
#include <map>

class MixUtility;

typedef std::map<string, std::vector<string> > ParInfoContainer;

class XSModelFunction 
{
  public:


    class NoSuchComponent : public YellowAlert  //## Inherits: <unnamed>%3FBA6F620269
    {
      public:
          NoSuchComponent();

      protected:
      private:
      private: //## implementation
    };
      virtual ~XSModelFunction() = 0;

      virtual void operator () (const RealArray& energyArray, const RealArray& params, int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, const string& initString) const = 0;
      virtual void operator () (const EnergyPointer& energyArray, const std::vector<Real>& params, GroupFluxContainer& fluxArrays, GroupFluxContainer& fluxErrArrays, MixUtility* mixGenerator, const string& modelName) const = 0;
      virtual MixUtility* getUtilityObject() const =0;
      static void updateComponentList (const string& modelDatFile, bool isStandard = false);
      static void printComponentList (std::ostream& s, const string& name = "");
      static std::vector<ComponentInfo> nameCache (const string& fullName	// Full name is the expression representing a model typed
      	// by the user. Only its first two characters are used
      	// here.
      	// Full name resolution in the case of duplicate names
      	// is deferred to the fullMatch function.
      );
      static ComponentInfo fullMatch (const string& fullName);
      static NameCacheType& nameCache ();
      static void nameCache (const string& shortName, const ComponentInfo& value);
      
      static ParInfoContainer& parInfoCache();
      static NameCacheType::iterator exactMatch (const string& fullName);

  public:
  protected:
      XSModelFunction();

      XSModelFunction(const XSModelFunction &right);

  private:
      XSModelFunction & operator=(const XSModelFunction &right);


  private: //## implementation
    // Data Members for Associations
      static NameCacheType s_nameCache;
      
      // Originally added just to hold parameter information strings for
      //  user-defined Python models, since these are not stored in a
      //  model.dat file.  In the future this container may possibly be expanded to
      //  contain ALL models' parameter strings so that Component::read()
      //  won't have to continually retrieve them from the model.dat file.
      static ParInfoContainer s_parInfoCache;

};
//	Interface for calling model calculation functions



template <typename T>
class XSCall : public XSModelFunction  //## Inherits: <unnamed>%3E319B420391
{
  public:
      XSCall(const XSCall< T > &right);
      XSCall (T* generator);
      virtual ~XSCall();

      virtual void operator () (const RealArray& energyArray, const RealArray& params, int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, const string& initString = string()) const;
      virtual void operator () (const EnergyPointer& energyArray, const std::vector<Real>& parameterValues, GroupFluxContainer& fluxArrays, GroupFluxContainer& fluxErrArrays, MixUtility* mixGenerator = 0, const string& modelName = string()) const;
      // More complicated models (ie. mix) may need to create MixUtility objects.  
      // For everything else, the default implementation of this function returns NULL.
      // Note that the MixUtility type isn't defined until a higher level library.
      virtual MixUtility* getUtilityObject() const;
      T* generator () const;
      void generator (T* value);

  protected:
  private:
      XSCall();
      XSCall< T > & operator=(const XSCall< T > &right);

  private: //## implementation
    // Data Members for Class Attributes
      T* m_generator;

};

// Class XSModelFunction::NoSuchComponent 

// Class XSModelFunction 

inline XSModelFunction::XSModelFunction()
{
}

inline XSModelFunction::XSModelFunction(const XSModelFunction &right)
{
}


inline NameCacheType& XSModelFunction::nameCache ()
{
  return s_nameCache;
}

inline void XSModelFunction::nameCache (const string& shortName, const ComponentInfo& value)
{
  s_nameCache.insert(NameCacheType::value_type(shortName,value));
}

inline ParInfoContainer& XSModelFunction::parInfoCache()
{
   return s_parInfoCache;
}

// Parameterized Class XSCall 

template <typename T>
MixUtility* XSCall<T>::getUtilityObject() const
{
   return 0;
}

template <typename T>
inline T* XSCall<T>::generator () const
{
  return m_generator;
}

template <typename T>
inline void XSCall<T>::generator (T* value)
{
  m_generator = value;
}

// Parameterized Class XSCall 

template <typename T>
XSCall<T>::XSCall(const XSCall<T> &right)
  : XSModelFunction(right),
    m_generator(right.m_generator) // default non-owning - shallow copy
                                   // (assume it's a function pointer)
{
}

template <typename T>
XSCall<T>::XSCall (T* generator)
  : m_generator(generator)
{
}


template <typename T>
XSCall<T>::~XSCall()
{
}


template <typename T>
void XSCall<T>::operator () (const RealArray& energyArray, const RealArray& params, int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, const string& initString) const
{
   throw RedAlert("Model function is missing due to specialized template build error (1).");
}

template <typename T>
void XSCall<T>::operator () (const EnergyPointer& energyArray, const std::vector<Real>& parameterValues, GroupFluxContainer& fluxArrays, GroupFluxContainer& fluxErrArrays, MixUtility* mixGenerator, const string& modelName) const
{
   throw RedAlert("Model function is missing due to specialized template build error (2).");
}

template  <> 
void XSCall<xsf77Call>::operator() (const RealArray& energyArray, const RealArray& params,
                        int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, 
                        const string& initString) const;

template  <> 
void XSCall<xsF77Call>::operator() (const RealArray& energyArray, const RealArray& params,
                        int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, 
                        const string& initString) const;

template  <> 
void XSCall<xsccCall>::operator() (const RealArray& energyArray, const RealArray& params,
                        int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, 
                        const string& initString) const;


template  <> 
void XSCall<XSCCall>::operator() (const RealArray& energyArray, const RealArray& params,
                        int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, 
                        const string& initString) const;

template  <> 
void XSCall<XSMixCCall>::operator() (const EnergyPointer& energyArray, 
                        const std::vector<Real>& parameterValues, GroupFluxContainer& flux,
                        GroupFluxContainer& fluxError, MixUtility* mixGenerator, 
                        const string& modelName) const;

template  <> 
void XSCall<xsmixcall>::operator() (const EnergyPointer& energyArray, 
                        const std::vector<Real>& parameterValues, GroupFluxContainer& flux,
                        GroupFluxContainer& fluxError, MixUtility* mixGenerator, 
                        const string& modelName) const;

template <>
void XSCall<MathExpression>::operator() (const RealArray& energyArray, const RealArray& params,
                        int spectrumNumber, RealArray& fluxArray, RealArray& fluxErrArray, 
                        const string& initString) const;

template <>
XSCall<MathExpression>::~XSCall();

template <>
XSCall<MathExpression>::XSCall(const XSCall<MathExpression> &right);


#endif
