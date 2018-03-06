//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RESPONSEPARAM_H
#define RESPONSEPARAM_H 1

// Response
#include <XSModel/Data/Detector/Response.h>
// ModParam
#include <XSModel/Parameter/ModParam.h>




class ResponseParam : public ModParam  //## Inherits: <unnamed>%414999C30367
{

  public:
      ResponseParam (const string& initString, Response* responseParent, Response::ResponseParType parType);
      ~ResponseParam();

      virtual ResponseParam* clone (Component* p = 0) const;
      virtual void freeze ();
      virtual void rePrompt (string& newString) const;
      //	Note: Unless isPrompt flag is set to true, this will
      //	automatically call parent's applyGainFromFit function
      //	for key values a,v,z.
      virtual int setValue (Real val, const char key = 'v');
      virtual void setCompute (bool flag) const;
      Response* responseParent ();
      const Response* responseParent () const;
      //	reset parameter value to its initial values.
      //
      //	This is a virtual function whose default implementation
      //	is to assume that the parameter is defined in XSPEC's
      //	model.{version} file.
      virtual void reset () throw (Parameter::ResetFailure);
      //	This is called when the response param to which this is
      //	linked gets changed.  It needs to tell its Response
      //	parent to apply a new gain.
      void reevaluateLink () const;
      //	Essentially a wrapper around the Parameter::modify
      //	function, this ensures the isPrompt flag is set to true
      //	when the values are changed (preventing an applyGainFrom
      //	Fit call), and restores it to false even in the event of
      //	an exception.  Also any leading whitespace is removed
      //	from paramStr prior to calling modify.
      void setValuesFromString (const string& paramStr);
      //	Constructs a string from the source number and parameter
      //	index, useful for Fit output column headings.
      virtual string getParameterLabel () const;
      Response::ResponseParType parType () const;
      bool isPrompt () const;
      void isPrompt (bool value);

    // Additional Public Declarations

  protected:
      virtual void changeValue (const string& parString);
      virtual bool processValues (const string& parString);
      virtual std::ostream& put (std::ostream& s) const;

    // Additional Protected Declarations

  private:
      ResponseParam();
      ResponseParam & operator=(const ResponseParam &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Response* const m_responseParent;
      Response::ResponseParType m_parType;
      bool m_isPrompt;

    // Additional Implementation Declarations

};

// Class ResponseParam 

inline Response* ResponseParam::responseParent ()
{
  return m_responseParent;
}

inline const Response* ResponseParam::responseParent () const
{
  return m_responseParent;
}

inline Response::ResponseParType ResponseParam::parType () const
{
  return m_parType;
}

inline bool ResponseParam::isPrompt () const
{
  return m_isPrompt;
}

inline void ResponseParam::isPrompt (bool value)
{
  m_isPrompt = value;
}


#endif
