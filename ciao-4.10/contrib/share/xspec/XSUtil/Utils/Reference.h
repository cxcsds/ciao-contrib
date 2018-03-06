//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef REFERENCE_H
#define REFERENCE_H 1

//	Mixin class for reference counted objects.
//
//	C++ Utilities for xspec.
//	Created to add Scott Meyer's reference counting
//	machinery to component classes. This is felt needed to
//	deal with the implementation of component groups. The
//	calculated part of ComponentGroup (the result of
//	evaluating a set of components which are to be combined)
//	is a SumComponent which is a subclass of AddComponent.
//	This is contained by value in some ComponentGroup and is
//	pointed to by a pointer in the list of components in a
//	different component group.
//
//
//	Since the processes of manipulation require copying
//	this, component and assigning it to new temporary
//	copies, care must be taken that the by-value object is
//	never "deep copied" or destructed, unlike other
//	temporaries created in manipulating the list.
//	Implementing reference counts appears to be the most
//	efficient way of dealing with this type of problem/usage.
//	Reference counted classes hold a single copy of the data
//	and reproduce another copy if it is needed to change it.
//	Identical copies are produced by simply adding a pointer.
//	6/28/99, revised 8/16/2000



class RefCounter 
{

  public:
      RefCounter();
      virtual ~RefCounter();

      void addReference ();
      void removeReference ();
      void markUnshareable ();
      bool isShared ();
      int refCount () const;
      bool shareable () const;
      void shareable (bool value);

    // Additional Public Declarations

  protected:
      RefCounter (const RefCounter& );

      RefCounter& operator = (const RefCounter& );

    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      int m_refCount;
      bool m_shareable;

    // Additional Implementation Declarations

};



template <class T>
class RefCountPtr 
{

  public:
      RefCountPtr(const RefCountPtr< T > &right);
      RefCountPtr (T* real = 0);
      ~RefCountPtr();
      RefCountPtr< T > & operator=(const RefCountPtr< T > &right);
      T* operator->() const;
      T& operator*() const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void init ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      T* m_pointed;

    // Data Members for Associate Classes



    // Additional Implementation Declarations

};

// Class RefCounter 

inline int RefCounter::refCount () const
{
  return m_refCount;
}

inline bool RefCounter::shareable () const
{
  return m_shareable;
}

inline void RefCounter::shareable (bool value)
{
  m_shareable = value;
}

// Parameterized Class RefCountPtr 

template <class T>
inline T* RefCountPtr<T>::operator->() const
{
  return m_pointed;
}


template <class T>
inline T& RefCountPtr<T>::operator*() const
{
  return *m_pointed;
}


// Parameterized Class RefCountPtr 

template <class T>
RefCountPtr<T>::RefCountPtr(const RefCountPtr<T> &right)
  : m_pointed(right.m_pointed)
{
  init();
}

template <class T>
RefCountPtr<T>::RefCountPtr (T* real)
  : m_pointed(real)
{
  init();
}


template <class T>
RefCountPtr<T>::~RefCountPtr()
{
  if (m_pointed) m_pointed->removeReference();
}


template <class T>
RefCountPtr<T> & RefCountPtr<T>::operator=(const RefCountPtr<T> &right)
{
  if (m_pointed != right.m_pointed)
  {
        if (m_pointed) m_pointed->removeReference();

        m_pointed = right.m_pointed;

        init();

  }

  return *this;
}


template <class T>
void RefCountPtr<T>::init ()
{
  if ( m_pointed == 0 ) return;

  // T must:
  // a) inherit from RefCount (so that isShareable and addReference exist)
  // b) have a deep copy constructor
  // c) Must have a virtual copy constructor if there are derived classes.

  if ( !m_pointed->shareable() )
  {
        m_pointed = m_pointed->clone();
  }

  m_pointed->addReference();
}

// Additional Declarations


#endif
