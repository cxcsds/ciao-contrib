//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef OBSERVER_H
#define OBSERVER_H 1
#include <list>


class Subject;




class Observer 
{

  public:
      Observer();
      virtual ~Observer();

      virtual void Update (Subject* changed) = 0;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      Observer(const Observer &right);
      Observer & operator=(const Observer &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



class Subject 
{

  public:
      Subject();
      virtual ~Subject();

      virtual void Attach (Observer* obs);
      virtual void Detach (Observer* obs);
      virtual void Notify ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      Subject(const Subject &right);
      Subject & operator=(const Subject &right);
      void observers (std::list<Observer*> * value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Associations
      std::list<Observer*> *m_observers;

    // Additional Implementation Declarations

};

// Class Observer 

// Class Subject 

inline void Subject::observers (std::list<Observer*> * value)
{
  m_observers = value;
}


#endif
