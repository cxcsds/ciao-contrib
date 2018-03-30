//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef REALRESPONSE_H
#define REALRESPONSE_H 1

// xsTypes
#include <xsTypes.h>
// SpectralData
#include <XSModel/Data/SpectralData.h>
// Reference
#include <XSUtil/Utils/Reference.h>
// Response
#include <XSModel/Data/Detector/Response.h>
// ResponseMatrix
#include <XSModel/Data/Detector/ResponseMatrix.h>




class RealResponse : public Response  //## Inherits: <unnamed>%37FDF6C27C90
{

  public:
      virtual ~RealResponse();

      //	Additional Public Declarations
      virtual Model& operator * (Model& model) const;
      virtual size_t read (const string& fileName, bool readFlag = true) = 0;
      virtual void closeSourceFiles () = 0;
      void setData (size_t specNum, size_t groupNumber = 1, size_t nRmf = 0);
      virtual bool readAuxResponse (int rowNum = -1);
      virtual RealResponse* clone () const = 0;
      virtual void setEnergies ();
      void setSharedDescription (size_t specNum, size_t groupNum);
      virtual void prepareForFit ();
      virtual const RealArray& efficiency () const;
      virtual RealArray sensitivity (const SpectralData* data);
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
      virtual void operator * (SumComponent& source) const;
      virtual void calcEffAreaPerChan (RealArray& effArea);
      virtual const RealResponse* toRealResponse () const;
      //	This does nothing unless the savedEffectiveArea array
      //	has already been initialized due to an earlier gain
      //	call.  But once it's initialized, the arf command needs
      //	this function to keep it updated when ARF modifications
      //	are made.
      void setZeroGainEffectiveArea (const RealArray& newEffArea);
      const string& rmfName () const;
      void rmfName (const string& value);
      const string& arfName () const;
      void arfName (const string& value);
      size_t arfRow () const;
      void arfRow (size_t value);
      const string& rspRunPath () const;
      void rspRunPath (const string& value);
      const string& arfRunPath () const;
      void arfRunPath (const string& value);
      const RealArray& effectiveArea () const;
      void setEffectiveArea (const RealArray& value);
      Real effectiveArea (size_t index) const;
      void effectiveArea (size_t index, Real value);
      const RefCountPtr< ResponseMatrix >& rmfData () const;
      void rmfData (const RefCountPtr< ResponseMatrix >& value);
      virtual SpectralData* source () const;
      virtual void source (SpectralData* value);

    // Additional Public Declarations

  protected:
      RealResponse();

      RealResponse(const RealResponse &right);

      virtual void setArrays () = 0;
      virtual void setDescription (size_t specNum, size_t groupNum) = 0;
      virtual const RealArray& eboundsMin () const;
      virtual const RealArray& eboundsMax () const;
      virtual void shiftEffectiveArea (const RealArray& newEnergies);
      virtual void restoreEffectiveArea ();
      const IntegerArray& noticedElements () const;
      int noticedElements (size_t index) const;
      const IntegerArray& noticedElemPos () const;
      int noticedElemPos (size_t index) const;

    // Additional Protected Declarations

  private:
      RealResponse & operator=(const RealResponse &right);

      virtual void RMFremove ();
      virtual bool order (const Response& right) const;
      virtual void convolve (const RealArray& flux, const RealArray& fluxErr, RealArray& foldFlux, RealArray& foldFluxErr) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_rmfName;
      string m_arfName;
      size_t m_arfRow;
      //	m_savedEffectiveArea retains the effective area for the
      //	case of zero gain.  It does not even get initialized
      //	until the first time gain is called for this response,
      //	therefore in most sessions this remains empty.  If it is
      //	in use, it will need updating every time the arf command
      //	modifies the ARF.
      RealArray m_savedEffectiveArea;
      string m_rspRunPath;
      string m_arfRunPath;

    // Data Members for Associations
      RealArray m_effectiveArea;
      RefCountPtr< ResponseMatrix > m_rmfData;
      SpectralData* m_source;
      IntegerArray m_noticedElements;
      IntegerArray m_noticedElemPos;

    // Additional Implementation Declarations

};

// Class RealResponse 

inline const RealResponse* RealResponse::toRealResponse () const
{
   return this;
}

inline const string& RealResponse::rmfName () const
{
  return m_rmfName;
}

inline void RealResponse::rmfName (const string& value)
{
  m_rmfName = value;
}

inline const string& RealResponse::arfName () const
{
  return m_arfName;
}

inline void RealResponse::arfName (const string& value)
{
  m_arfName = value;
}

inline size_t RealResponse::arfRow () const
{
  return m_arfRow;
}

inline void RealResponse::arfRow (size_t value)
{
  m_arfRow = value;
}

inline const string& RealResponse::rspRunPath () const
{
  return m_rspRunPath;
}

inline void RealResponse::rspRunPath (const string& value)
{
  m_rspRunPath = value;
}

inline const string& RealResponse::arfRunPath () const
{
  return m_arfRunPath;
}

inline void RealResponse::arfRunPath (const string& value)
{
  m_arfRunPath = value;
}

inline const RealArray& RealResponse::effectiveArea () const
{
  return m_effectiveArea;
}

inline void RealResponse::setEffectiveArea (const RealArray& value)
{
  m_effectiveArea.resize(value.size(),0);
  m_effectiveArea = value;
}

inline Real RealResponse::effectiveArea (size_t index) const
{
  return m_effectiveArea[index];
}

inline void RealResponse::effectiveArea (size_t index, Real value)
{
  m_effectiveArea[index] = value;
}

inline const RefCountPtr< ResponseMatrix >& RealResponse::rmfData () const
{
  return m_rmfData;
}

inline void RealResponse::rmfData (const RefCountPtr< ResponseMatrix >& value)
{
  m_rmfData = value;
}

inline SpectralData* RealResponse::source () const
{
  return m_source;
}

inline void RealResponse::source (SpectralData* value)
{
  m_source = value;
}

inline const IntegerArray& RealResponse::noticedElements () const
{
  return m_noticedElements;
}

inline int RealResponse::noticedElements (size_t index) const
{
  return m_noticedElements[index];
}

inline const IntegerArray& RealResponse::noticedElemPos () const
{
  return m_noticedElemPos;
}

inline int RealResponse::noticedElemPos (size_t index) const
{
  return m_noticedElemPos[index];
}


#endif
