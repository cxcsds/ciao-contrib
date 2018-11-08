//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MDEFCONTAINER_H
#define MDEFCONTAINER_H 1

// MathExpression
#include <XSUtil/Parse/MathExpression.h>
// XSutility
#include <XSUtil/Utils/XSutility.h>
#include <xsTypes.h>
#include <XSUtil/FunctionUtils/XSModelFunction.h>
#include <utility>

namespace XSContainer {



    class MdefContainer 
    {

      public:
        //	The string refers to the type of component, ie. "add",
        //	etc.



        typedef std::pair<string,XSCall<MathExpression>*> CompPair;

      private:
        //	The string is the component name.



        typedef std::map<string,CompPair,XSutility::Nocase > CompMap;

      public:
          MdefContainer();
          ~MdefContainer();

          void displayComponents () const;
          string removeComponent (const string& name);
          //	Returns false and will not create a new component if one
          //	with the same name already exists.
          bool addComponent (const string& name, const string& type, const string& expression, std::pair<Real,Real> eLimits);
          void displayComponent (const string& name) const;
          MdefContainer::CompPair getComponent (const string& name) const;
          static const string& NOT_FOUND ();

        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          MdefContainer(const MdefContainer &right);
          MdefContainer & operator=(const MdefContainer &right);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          XSContainer::MdefContainer::CompMap m_components;
          static const string s_NOT_FOUND;

        // Additional Implementation Declarations

    };

    // Class XSContainer::MdefContainer 

    inline const string& MdefContainer::NOT_FOUND ()
    {
      return s_NOT_FOUND;
    }

} // namespace XSContainer


#endif
