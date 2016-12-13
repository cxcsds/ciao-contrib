//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef BEARDEN_H
#define BEARDEN_H 1

// LineList
#include <XSModel/Model/EmissionLines/LineList.h>




class Bearden : public LineList  //## Inherits: <unnamed>%3F4FAF23001A
{

  public:
      Bearden();

      Bearden(const Bearden &right);
      virtual ~Bearden();

      virtual LineList* clone () const;

    // Additional Public Declarations

  protected:
      virtual void readData ();
      virtual void report (std::ostream& os) const;
      virtual void findLines ();

    // Additional Protected Declarations

  private:
      const std::pair<size_t,size_t> iRows () const;
      void iRows (std::pair<size_t,size_t> value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static string s_ELEMENT;
      static string s_TRANS;
      static string s_ENERGY;
      static string s_WAVE;
      static StringArray s_colNames;
      RealArray m_energyWave;
      StringArray m_trans;
      StringArray m_element;
      std::pair<size_t,size_t> m_iRows;

    // Additional Implementation Declarations

};

// Class Bearden 

inline const std::pair<size_t,size_t> Bearden::iRows () const
{
  return m_iRows;
}

inline void Bearden::iRows (std::pair<size_t,size_t> value)
{
  m_iRows = value;
}


#endif
