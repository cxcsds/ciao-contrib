//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TRASHADAPTER_H
#define TRASHADAPTER_H 1

// TrashPtr
#include "XSModel/GlobalContainer/TrashPtr.h"

namespace XSContainer {



    template <typename T>
    class TrashAdapter : public TrashPtr  //## Inherits: <unnamed>%41DED4B10158
    {

      public:
          TrashAdapter (T obj);
          virtual ~TrashAdapter();

          virtual void empty ();

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          T m_obj;

        // Additional Implementation Declarations

    };

    // Parameterized Class XSContainer::TrashAdapter 

    template <typename T>
    inline TrashAdapter<T>::TrashAdapter (T obj)
	: m_obj(obj)
    {
    }


    template <typename T>
    inline TrashAdapter<T>::~TrashAdapter()
    {
    }


    template <typename T>
    inline void TrashAdapter<T>::empty ()
    {
	delete m_obj;
    }

} // namespace XSContainer


#endif
