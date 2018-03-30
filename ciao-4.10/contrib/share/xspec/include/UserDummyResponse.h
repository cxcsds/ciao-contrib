//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef USERDUMMYRESPONSE_H
#define USERDUMMYRESPONSE_H 1

// xsTypes
#include <xsTypes.h>
// cstdlib
#include <cstdlib>
// Error
#include <XSUtil/Error/Error.h>
// SpectralData
#include <XSModel/Data/SpectralData.h>
// Response
#include <XSModel/Data/Detector/Response.h>




class UserDummyResponse : public Response  //## Inherits: <unnamed>%3E2EB43E0220
{

  public:



    class NoRealResponse : public YellowAlert  //## Inherits: <unnamed>%3E7B8DC802A8
    {
      public:
          NoRealResponse (size_t spectrumNumber, size_t detNumber);

      protected:
      private:
      private: //## implementation
    };
      UserDummyResponse(const UserDummyResponse &right);
      UserDummyResponse (Real eLow, Real eHigh, int numEnergies, bool isLog, SpectralData* spectrum, Real channelOffset = .0, Real channelWidth = .0, size_t detNum = 0);
      UserDummyResponse (SpectralData* spectrum, size_t detNum);
      virtual ~UserDummyResponse();

      virtual UserDummyResponse* clone () const;
      virtual Model& operator * (Model& model) const;
      virtual void setEnergies ();
      virtual SpectralData* source () const;
      virtual void source (SpectralData* spectrum);
      virtual void operator * (SumComponent& source) const;
      void getEffectiveArea (RealArray& effectiveArea) const;
      virtual const RealArray& eboundsMin () const;
      virtual const RealArray& eboundsMax () const;
      virtual const UserDummyResponse* toUserDummyResponse () const;
      Real eLow () const;
      void eLow (Real value);
      Real eHigh () const;
      void eHigh (Real value);
      bool isLog () const;
      void isLog (bool value);
      Real channelOffset () const;
      void channelOffset (Real value);
      Real channelWidth () const;
      void channelWidth (Real value);
      bool usingChannels () const;
      const RealArray& channels () const;
      void channels (const RealArray& value);
      bool diagRspMode () const;
      size_t detNum () const;
      const StringArray& arfNames () const;
      void arfNames (const StringArray& value);

  public:
    // Additional Public Declarations

  protected:
      UserDummyResponse();

      virtual void generateResponse ();
      void setChannels ();
      MatrixValue& matrix ();
      std::vector<std::size_t>& dmyStartEngs ();

    // Additional Protected Declarations

  private:
      UserDummyResponse & operator=(const UserDummyResponse &right);

      void convolve (const RealArray& flux, const RealArray& fluxErr, RealArray& foldFlux, RealArray& foldFluxErr) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      Real m_eLow;
      Real m_eHigh;
      bool m_isLog;
      Real m_channelOffset;
      Real m_channelWidth;
      bool m_usingChannels;
      MatrixValue m_matrix;
      RealArray m_channels;
      bool m_diagRspMode;
      size_t m_detNum;
      RealArray m_eboundsMin;
      RealArray m_eboundsMax;

    // Data Members for Associations
      std::vector<std::size_t> m_dmyStartEngs;
      SpectralData* m_source;
      StringArray m_arfNames;

    // Additional Implementation Declarations

};

// Class UserDummyResponse::NoRealResponse 

// Class UserDummyResponse 

inline const UserDummyResponse* UserDummyResponse::toUserDummyResponse () const
{
   return this;
}

inline Real UserDummyResponse::eLow () const
{
  return m_eLow;
}

inline void UserDummyResponse::eLow (Real value)
{
  m_eLow = value;
}

inline Real UserDummyResponse::eHigh () const
{
  return m_eHigh;
}

inline void UserDummyResponse::eHigh (Real value)
{
  m_eHigh = value;
}

inline bool UserDummyResponse::isLog () const
{
  return m_isLog;
}

inline void UserDummyResponse::isLog (bool value)
{
  m_isLog = value;
}

inline Real UserDummyResponse::channelOffset () const
{
  return m_channelOffset;
}

inline void UserDummyResponse::channelOffset (Real value)
{
  m_channelOffset = value;
}

inline Real UserDummyResponse::channelWidth () const
{
  return m_channelWidth;
}

inline void UserDummyResponse::channelWidth (Real value)
{
  m_channelWidth = value;
}

inline bool UserDummyResponse::usingChannels () const
{
  return m_usingChannels;
}

inline MatrixValue& UserDummyResponse::matrix ()
{
  return m_matrix;
}

inline const RealArray& UserDummyResponse::channels () const
{
  return m_channels;
}

inline bool UserDummyResponse::diagRspMode () const
{
  return m_diagRspMode;
}

inline size_t UserDummyResponse::detNum () const
{
  return m_detNum;
}

inline std::vector<std::size_t>& UserDummyResponse::dmyStartEngs ()
{
  return m_dmyStartEngs;
}

inline const StringArray& UserDummyResponse::arfNames () const
{
  return m_arfNames;
}

inline void UserDummyResponse::arfNames (const StringArray& value)
{
  m_arfNames = value;
}


#endif
