//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MULTIRESPONSE_H
#define MULTIRESPONSE_H 1

// xsTypes
#include <xsTypes.h>
// string
#include <string>
// SpectralData
#include <XSModel/Data/SpectralData.h>
// Reference
#include <XSUtil/Utils/Reference.h>
// Response
#include <XSModel/Data/Detector/Response.h>
// ResponseMatrix
#include <XSModel/Data/Detector/ResponseMatrix.h>




class MultiResponse : public Response  //## Inherits: <unnamed>%3A92DB1C0130
{

  public:



    struct positionInfo 
    {
          friend bool operator > (const positionInfo& left, const positionInfo& right);

        // Data Members for Class Attributes
          size_t rmfNum;
          size_t rmfSize;
          ResponseMatrix::RMFLONG posValue;
          size_t pos;

      public:
      protected:
      private:
      private: //## implementation
    };
      virtual ~MultiResponse();

      //	Additional Public Declarations
      virtual Model& operator * (Model& model) const;
      virtual size_t read (const string& fileName, bool readFlag = true) = 0;
      virtual void closeSourceFiles (size_t index = 0) = 0;
      void setData (size_t specNum, size_t groupNumber, size_t nRmf = 0);
      virtual bool readAuxResponse ();
      virtual MultiResponse* clone () const = 0;
      virtual void setEnergies ();
      void setSharedDescription (size_t specNum, size_t groupNum);
      virtual void prepareForFit ();
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
      virtual const MultiResponse* toMultiResponse () const;
      const std::vector<RefCountPtr< ResponseMatrix > >& rmfData () const;
      void setRmfData (const std::vector<RefCountPtr< ResponseMatrix > >& value);
      const RefCountPtr< ResponseMatrix >& rmfData (size_t rmfNum) const;
      void rmfData (size_t rmfNum, const RefCountPtr< ResponseMatrix >& value);
      const std::vector<RealArray>& effectiveArea () const;
      void setEffectiveArea (const std::vector<RealArray>& value);
      const RealArray& effectiveArea (size_t rmfNum) const;
      void effectiveArea (size_t rmfNum, const RealArray& value);
      virtual SpectralData* source () const;
      virtual void source (SpectralData* value);
      const std::vector<std::string>& rmfNames () const;
      void setRmfNames (const std::vector<std::string>& value);
      const std::string& rmfNames (size_t rmfNum) const;
      void rmfNames (size_t rmfNum, const std::string& value);
      const std::vector<std::string>& arfNames () const;
      void setArfNames (const std::vector<std::string>& value);
      const std::string& arfNames (size_t rmfNum) const;
      void arfNames (size_t rmfNum, const std::string& value);

  public:
    // Additional Public Declarations

  protected:
      MultiResponse();

      MultiResponse(const MultiResponse &right);

      virtual void setArrays () = 0;
      virtual void setDescription (size_t specNum, size_t groupNum) = 0;
      void combineRMF (Real* cvUnion) const;
      virtual const RealArray& eboundsMin () const;
      virtual const RealArray& eboundsMax () const;
      virtual void shiftEffectiveArea (const RealArray& newEnergies);
      virtual void restoreEffectiveArea ();
      size_t currentRMF () const;
      void currentRMF (size_t value);
      size_t unionSize () const;
      const IntegerVector& noticedElements () const;
      int noticedElements (size_t index) const;
      const IntegerVector& noticedElemPos () const;
      int noticedElemPos (size_t index) const;
      const IntegerVector& energyStart () const;
      int energyStart (size_t index) const;
      const IntegerVector& energyRunLengths () const;
      int energyRunLengths (size_t index) const;
      const IntegerVector& channelForRun () const;
      int channelForRun (size_t index) const;

    // Additional Protected Declarations

  private:
      MultiResponse & operator=(const MultiResponse &right);

      virtual void RMFremove ();
      virtual bool order (const Response& right) const;
      virtual void convolve (const RealArray& flux, const RealArray& fluxErr, RealArray& foldFlux, RealArray& foldFluxErr) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      size_t m_currentRMF;
      size_t m_unionSize;

    // Data Members for Associations
      std::vector<RefCountPtr< ResponseMatrix > > m_rmfData;
      std::vector<RealArray> m_effectiveArea;
      SpectralData* m_source;
      std::vector<std::string> m_rmfNames;
      std::vector<std::string> m_arfNames;
      IntegerVector m_noticedElements;
      IntegerVector m_noticedElemPos;
      IntegerVector m_energyStart;
      IntegerVector m_energyRunLengths;
      IntegerVector m_channelForRun;
      std::vector<RealArray> m_savedEffectiveArea;

    // Additional Implementation Declarations

};
inline bool operator>(const MultiResponse::positionInfo& left,const MultiResponse::positionInfo& right)
{
   return (left.posValue > right.posValue);
}

// Class MultiResponse::positionInfo 

// Class MultiResponse 

inline const MultiResponse* MultiResponse::toMultiResponse () const
{
   return this;
}

inline size_t MultiResponse::currentRMF () const
{
  return m_currentRMF;
}

inline void MultiResponse::currentRMF (size_t value)
{
  m_currentRMF = value;
}

inline size_t MultiResponse::unionSize () const
{
  return m_unionSize;
}

inline const std::vector<RefCountPtr< ResponseMatrix > >& MultiResponse::rmfData () const
{
  return m_rmfData;
}

inline void MultiResponse::setRmfData (const std::vector<RefCountPtr< ResponseMatrix > >& value)
{
  m_rmfData = value;
}

inline const RefCountPtr< ResponseMatrix >& MultiResponse::rmfData (size_t rmfNum) const
{
  return m_rmfData[rmfNum];
}

inline void MultiResponse::rmfData (size_t rmfNum, const RefCountPtr< ResponseMatrix >& value)
{
  m_rmfData[rmfNum] = value;
}

inline const std::vector<RealArray>& MultiResponse::effectiveArea () const
{
  return m_effectiveArea;
}

inline void MultiResponse::setEffectiveArea (const std::vector<RealArray>& value)
{
  m_effectiveArea = value;
}

inline const RealArray& MultiResponse::effectiveArea (size_t rmfNum) const
{
  return m_effectiveArea[rmfNum];
}

inline void MultiResponse::effectiveArea (size_t rmfNum, const RealArray& value)
{
  m_effectiveArea[rmfNum].resize(value.size());
  m_effectiveArea[rmfNum] = value;
}

inline SpectralData* MultiResponse::source () const
{
  return m_source;
}

inline void MultiResponse::source (SpectralData* value)
{
  m_source = value;
}

inline const std::vector<std::string>& MultiResponse::rmfNames () const
{
  return m_rmfNames;
}

inline void MultiResponse::setRmfNames (const std::vector<std::string>& value)
{
  m_rmfNames = value;
}

inline const std::string& MultiResponse::rmfNames (size_t rmfNum) const
{
  return m_rmfNames[rmfNum];
}

inline void MultiResponse::rmfNames (size_t rmfNum, const std::string& value)
{
  m_rmfNames[rmfNum] = value;
}

inline const std::vector<std::string>& MultiResponse::arfNames () const
{
  return m_arfNames;
}

inline void MultiResponse::setArfNames (const std::vector<std::string>& value)
{
  m_arfNames = value;
}

inline const std::string& MultiResponse::arfNames (size_t rmfNum) const
{
  return m_arfNames[rmfNum];
}

inline void MultiResponse::arfNames (size_t rmfNum, const std::string& value)
{
  m_arfNames[rmfNum] = value;
}

inline const IntegerVector& MultiResponse::noticedElements () const
{
  return m_noticedElements;
}

inline int MultiResponse::noticedElements (size_t index) const
{
  return m_noticedElements[index];
}

inline const IntegerVector& MultiResponse::noticedElemPos () const
{
  return m_noticedElemPos;
}

inline int MultiResponse::noticedElemPos (size_t index) const
{
  return m_noticedElemPos[index];
}

inline const IntegerVector& MultiResponse::energyStart () const
{
  return m_energyStart;
}

inline int MultiResponse::energyStart (size_t index) const
{
  return m_energyStart[index];
}

inline const IntegerVector& MultiResponse::energyRunLengths () const
{
  return m_energyRunLengths;
}

inline int MultiResponse::energyRunLengths (size_t index) const
{
  return m_energyRunLengths[index];
}

inline const IntegerVector& MultiResponse::channelForRun () const
{
  return m_channelForRun;
}

inline int MultiResponse::channelForRun (size_t index) const
{
  return m_channelForRun[index];
}


#endif
