//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MEKAL_H
#define MEKAL_H 1

// LineList
#include <XSModel/Model/EmissionLines/LineList.h>




class Mekal : public LineList  //## Inherits: <unnamed>%3F4FAF2900F1
{

  public:
      Mekal();

      Mekal(const Mekal &right);
      virtual ~Mekal();

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
      static string s_WAVE;
      static string s_ION;
      static string s_TRANS;
      static string s_FVALUE;
      static StringArray s_colNames;
      RealArray m_wave;
      StringArray m_ion;
      StringArray m_trans;
      RealArray m_fvalue;
      std::pair<size_t,size_t> m_iRows;

    // Additional Implementation Declarations

};

// Class Mekal 

inline const std::pair<size_t,size_t> Mekal::iRows () const
{
  return m_iRows;
}

inline void Mekal::iRows (std::pair<size_t,size_t> value)
{
  m_iRows = value;
}


#endif
