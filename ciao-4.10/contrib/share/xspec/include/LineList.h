//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef LINELIST_H
#define LINELIST_H 1
#include <CCfits/CCfits>
#include <ostream>

// xsTypes
#include <xsTypes.h>
// map
#include <map>
// Error
#include <XSUtil/Error/Error.h>




class LineList 
{

  protected:



    class CannotOpen : public YellowAlert  //## Inherits: <unnamed>%3F54FB8C038B
    {
      public:
          CannotOpen (const string& msg);

      protected:
      private:
      private: //## implementation
    };



    class FileFormatError : public YellowAlert  //## Inherits: <unnamed>%3F54FDB000A2
    {
      public:
          FileFormatError (const string& msg);

      protected:
      private:
      private: //## implementation
    };

  public:
      LineList();

      LineList(const LineList &right);
      virtual ~LineList();

      static LineList* get (const std::string& name);
      static void registerLineList (const std::string& name, LineList* lineList);
      virtual LineList* clone () const = 0;
      virtual void initialize (Real lowEnergy, Real highEnergy, Real plasmaTemp, Real minEmissivity, bool isWave);
      void showList (std::ostream& os);
      static void clearLineLists ();
      const string& fileName () const;
      void fileName (const string& value);
      std::pair<Real,Real> energyRange () const;
      Real plasmaTemperature () const;
      Real minEmissivity () const;
      bool isWave () const;
      void isWave (bool value);
      static const std::map<std::string, LineList*>& lineLists ();
      static void lineLists (const std::map<std::string, LineList*>& value);

    // Additional Public Declarations

  protected:
      virtual void openFile ();
      virtual void readData ();
      virtual void findLines ();
      virtual void report (std::ostream& os) const;
      CCfits::FITS* file () const;
      void file (CCfits::FITS* value);

    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      string m_fileName;
      std::pair<Real,Real> m_energyRange;
      Real m_plasmaTemperature;
      Real m_minEmissivity;
      CCfits::FITS* m_file;
      bool m_isWave;

    // Data Members for Associations
      static std::map<std::string, LineList*> s_lineLists;

    // Additional Implementation Declarations

};

// Class LineList::CannotOpen 

// Class LineList::FileFormatError 

// Class LineList 

inline const string& LineList::fileName () const
{
  return m_fileName;
}

inline void LineList::fileName (const string& value)
{
  m_fileName = value;
}

inline std::pair<Real,Real> LineList::energyRange () const
{
  return m_energyRange;
}

inline Real LineList::plasmaTemperature () const
{
  return m_plasmaTemperature;
}

inline Real LineList::minEmissivity () const
{
  return m_minEmissivity;
}

inline CCfits::FITS* LineList::file () const
{
  return m_file;
}

inline void LineList::file (CCfits::FITS* value)
{
  m_file = value;
}

inline bool LineList::isWave () const
{
  return m_isWave;
}

inline void LineList::isWave (bool value)
{
  m_isWave = value;
}

inline const std::map<std::string, LineList*>& LineList::lineLists ()
{
  return s_lineLists;
}

inline void LineList::lineLists (const std::map<std::string, LineList*>& value)
{
  s_lineLists = value;
}


#endif
