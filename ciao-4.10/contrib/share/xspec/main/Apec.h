//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef APEC_H
#define APEC_H 1

// LineList
#include <XSModel/Model/EmissionLines/LineList.h>




class Apec : public LineList  //## Inherits: <unnamed>%3F4FAF2C01FE
{

  public:
      Apec();

      Apec(const Apec &right);
      virtual ~Apec();

      virtual LineList* clone () const;

    // Additional Public Declarations

  protected:
      virtual void readData ();
      virtual void report (std::ostream& os) const;
      virtual void findLines ();

    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static const string s_KT;
      static const string s_LAMBDA;
      static const string s_EPSILON;
      static const string s_ELEMENT;
      static const string s_ION;
      static const string s_UPPERLEV;
      static const string s_LOWERLEV;
      RealArray m_lambda;
      RealArray m_epsilon;
      IntegerArray m_element;
      IntegerArray m_ion;
      IntegerArray m_upperlev;
      IntegerArray m_lowerlev;
      static StringArray s_colNames;
      static StringArray s_symbols;
      static StringArray s_ionsyms;
      IntegerArray m_iRows;

    // Additional Implementation Declarations

};

// Class Apec 


#endif
