//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef TRASHPTR_H
#define TRASHPTR_H 1
#include <list>

namespace XSContainer {



    class TrashPtr 
    {

      public:
          virtual ~TrashPtr();

          virtual void empty () = 0;

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
        // Additional Private Declarations

      private: //## implementation
        // Additional Implementation Declarations

    };



    typedef std::list<TrashPtr*> TrashCan;

    // Class XSContainer::TrashPtr 

    inline TrashPtr::~TrashPtr()
    {
    }


} // namespace XSContainer


#endif
