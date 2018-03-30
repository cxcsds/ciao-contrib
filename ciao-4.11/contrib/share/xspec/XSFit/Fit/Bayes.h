//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef BAYES_H
#define BAYES_H 1


class Fit;




class Bayes 
{

  public:
      Bayes();
      ~Bayes();

      Real lPrior (Fit* fit) const;
      Real dlPrior (Fit* fit, const int iPar) const;
      Real d2lPrior (Fit* fit, const int iPar, const int jPar) const;
      bool isOn () const;
      void isOn (bool value);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_isOn;

    // Additional Implementation Declarations

};

// Class Bayes 

inline bool Bayes::isOn () const
{
  return m_isOn;
}

inline void Bayes::isOn (bool value)
{
  m_isOn = value;
}


#endif
