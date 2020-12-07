//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSUTILITY_H
#define XSUTILITY_H 1
#include <locale>
#include <sstream>

// xsTypes
#include <xsTypes.h>
// functional
#include <functional>

#       include <cstdlib>
#       include <iosfwd>
#       include <iomanip>
#       include <valarray>
#       include <utility>
//#       include "Command/Command.h"
        class InvalidRange;
        class InputError;
        struct Tcl_Obj;
        class XSstream;

namespace XSutility {

         void starPrint (const std::string& slogan, int j, std::ostream& s);

         int yesToQuestion (const string& prompt, int defaultAns, std::istream& a);

         // for a command with options listed in a map, prompt the user with
         // a list of valid responses.
         void printValidOptions(std::ostream& s, const string& command, const std::map<string,size_t>& options);

         string lowerCase(const string& inputString);

         string upperCase(const string& inputString);

         void find (const RealArray& array, const Real& target, int& n );

         void bisect( int& lower, int& upper, const RealArray& array, const Real& target, bool increasing); 

         bool isReal (const string& inputString, Real& realResult);

         // equality of RealArrays. Could be generalized to a template, but currently
         // only need to check RealArray objects
         bool equalVector(const RealArray& left, const RealArray& right, Real tolerance = 0);

         size_t isInteger(const string& inputString);

         // Inserts the escape char prior to every appearance of any of
         // the characters in specialChars string.
         // Useful for writing file names w/extended syntax to save files.
         string insertEscapeChars(const string& inputString,
                        const string& specialChars = string("[] \t"),
                        const char ESC = '\\');

         unsigned int openBrackets (const string& ss);

         unsigned int closeBrackets (const string& ss);

         // Printing an array in a tabular format, in order vertically
         void printStrings(const std::vector<string>& strings, std::ostream& s, int perLine, int fieldWidth=8);

         // Version string is actually stored in xs_version.  
         // XSVersionString is named that way for historical reasons.
         const string& xs_version();
         void XSVersionString(string &title, string &buildDate);

         // Read the settings in an Xspec.init type file
         std::map<string,string> readSettingsFile(const string& filename);

         // Find the specified confidence interval among the values in array.
         // This assumes array is unsorted upon input.
         // The default is to perform only a partial sort on array, by calling
         //   std::nth_element (O(N)) to find just the 2 boundaries.
         // If a fully sort of array is desired upon return (O(NlnN)),
         //   set fullSort flag to true. 
         std::pair<Real,Real> confidenceRange(Real confidenceLevel, std::vector<Real>& array, bool fullSort=false);

         template <class T>
         void swap(T& left,T& right)
         {
                T temp(left);
                left = right;
                right = temp;                
         }

         // decodes registry keys of the form  outputName$outputIndex.
         void decodeKey(const string& input, string& outputName, size_t& outputIndex);

         RealArray gehrelsWeighting(const RealArray& rate, Real norm);

         RealArray churazovWeighting(const RealArray& rate, Real norm);

      // The MapType parameter is truly redundant information, since it 
      // should be available from StdMap::mapped_type.  However, when 
      // StdMap::mapped_type is passed along as the vector type param,
      // all sorts of unpredictable compilation problems may arise on
      // Solaris compilers, and they don't always show up in this file.

	 template<typename StlMap, typename MapType>
	 std::vector<MapType> values(typename StlMap::const_iterator beg, 
							  typename StlMap::const_iterator end)
	 {
	     size_t n = 0;
#ifndef STD_COUNT_DEFECT
	     n = std::distance(beg, end);
#else
	     std::distance(beg, end, n);
#endif
	     std::vector<MapType> vals(n);

	     typename StlMap::const_iterator pos = beg;

	     for(size_t i = 0; i < n; ++i, ++pos)
		 vals[i] = pos->second;

	     return vals;
	 }

	 string getRunPath();

	 string peek(std::istream& s, size_t bytes);



    template <class T>
    struct Match1stKeyString : public std::binary_function<T,std::string,bool>  //## Inherits: <unnamed>%38F2462A8830
    {
          bool operator () (const T& t, const std::string& k) const;

      public:
      protected:
      private:
      private: //## implementation
    };



    template <class T>
    struct MatchName : public std::binary_function<T, std::string, bool>  //## Inherits: <unnamed>%38F32AFB98E8
    {
          bool operator () (const T& left, const string& right) const;

      public:
      protected:
      private:
      private: //## implementation
    };



    template <class T>
    struct MatchPtrName : public std::binary_function<T*, std::string, bool>  //## Inherits: <unnamed>%38F32720F660
    {
          //	Parameterized Class MatchPtrName
          bool operator () (const T* left, const string& right) const;

      public:
      protected:
      private:
      private: //## implementation
    };



    template <typename T>
    struct Carray 
    {
          T* operator () (const std::valarray<T>& inArray);
          T* operator () (const std::vector<T>& inArray);
          std::vector<T> operator () (T* inArray, size_t n);

      public:
      protected:
      private:
      private: //## implementation
    };



    typedef enum {NONE,PHA,BCK,COR,RSP,ARF} fileType;
//  template <class T>
//  bool MatchName<T*>::operator() (const T*& left, const string& right) const;



    template <typename X>
    class auto_array_ptr 
    {
      public:
          explicit auto_array_ptr (X* p = 0) throw ();
          explicit auto_array_ptr (auto_array_ptr<X>& right) throw ();
          ~auto_array_ptr();
          X& operator*() const;

          X* get () const throw ();
          X* reset (X* p) throw ();
          static void remove (X*& x) throw ();
          X* release () throw ();
          void operator = (auto_array_ptr<X>& right) throw ();
          X& operator [] (size_t index) throw ();
          X operator [] (size_t index) const throw ();

      protected:
      private:
      private: //## implementation
        // Data Members for Class Attributes
          X* m_p;

    };



    template <typename T>
    struct MatchSubKey : public std::binary_function<T,string,bool>  //## Inherits: <unnamed>%3C2259EE0036
    {
          bool operator () (const T& t, const string& k) const;

      public:
      protected:
      private:
      private: //## implementation
    };
    //	Functor class which can be used as the Cmp template
    //	argument for a std::map container, when case-insensitive
    //	searches and ordering are required.  (This code comes
    //	from Stroustrup C++ 17.1.4.1.)



    struct Nocase 
    {
          bool operator () (const string& x, const string& y) const;

      public:
      protected:
      private:
      private: //## implementation
    };

    // Parameterized Class XSutility::Match1stKeyString 

    template <class T>
    inline bool Match1stKeyString<T>::operator () (const T& t, const std::string& k) const
    {
          // match against the first string of a map key delimited by colons.
          // T& t is a pair and T& t.first is a string. error...
          int i = t.first.find_first_of(':');
          if (i < 0 ) return (t.first == k);
          else
          {
                return (t.first.substr(0,i) == k);   
          }
    }

    // Parameterized Class XSutility::MatchName 

    template <class T>
    inline bool MatchName<T>::operator () (const T& left, const string& right) const
    {
  return left.name() == right;
    }

    // Parameterized Class XSutility::MatchPtrName 

    template <class T>
    inline bool MatchPtrName<T>::operator () (const T* left, const string& right) const
    {
  return left->name() == right;
    }

    // Parameterized Class XSutility::Carray 

    template <typename T>
    inline T* Carray<T>::operator () (const std::valarray<T>& inArray)
    {
        size_t n = inArray.size();
        T* c = new T[n];
        for (size_t j = 0; j < n; ++j) c[j] = inArray[j];
        return c;    
    }

    template <typename T>
    inline T* Carray<T>::operator () (const std::vector<T>& inArray)
    {
        size_t n = inArray.size();
        T* c = new T[n];
        for (size_t j = 0; j < n; ++j) c[j] = inArray[j];
        return c;    
    }

    template <typename T>
    inline std::vector<T> Carray<T>::operator () (T* inArray, size_t n)
    {
    std::vector<T> value(n);
    for (size_t j = 0; j < n; ++j) value[j] = inArray[j];
    return value;
    }

    // Parameterized Class XSutility::auto_array_ptr 

    // Parameterized Class XSutility::MatchSubKey 

    // Class XSutility::Nocase 

    // Parameterized Class XSutility::auto_array_ptr 

    template <typename X>
    auto_array_ptr<X>::auto_array_ptr (X* p) throw ()
          : m_p(p)
    {
    }

    template <typename X>
    auto_array_ptr<X>::auto_array_ptr (auto_array_ptr<X>& right) throw ()
        : m_p(right.release())
    {
    }


    template <typename X>
    auto_array_ptr<X>::~auto_array_ptr()
    {
    delete [] m_p;
    }


    template <typename X>
    X& auto_array_ptr<X>::operator*() const
    {
    return *m_p;
    }


    template <typename X>
    X* auto_array_ptr<X>::get () const throw ()
    {
    return m_p;
    }

    template <typename X>
    X* auto_array_ptr<X>::reset (X* p) throw ()
    {
      // set the auto_ptr to manage p and return the old pointer it was managing.
      X* __tmp(m_p); 
      m_p = p;
      return __tmp;
    }

    template <typename X>
    void auto_array_ptr<X>::remove (X*& x) throw ()
    {
      X* __tmp(x);
      x = 0;
      delete [] __tmp;
    }

    template <typename X>
    X* auto_array_ptr<X>::release () throw ()
    {
      return reset(0);
    }

    template <typename X>
    void auto_array_ptr<X>::operator = (auto_array_ptr<X>& right) throw ()
    {
    if (this != &right)
    {
              remove(m_p);
              m_p = right.release();       
    }   
    }

    template <typename X>
    X& auto_array_ptr<X>::operator [] (size_t index) throw ()
    {
      return m_p[index];
    }

    template <typename X>
    X auto_array_ptr<X>::operator [] (size_t index) const throw ()
    {
      return m_p[index];
    }

    // Parameterized Class XSutility::MatchSubKey 

    template <typename T>
    bool MatchSubKey<T>::operator () (const T& t, const string& k) const
    {
          // match when then string k is a substring or equal to the key.
          // T& t is a pair and T& t.first is a string. will get compile errors
          // otherwise.
          bool match = false;
          if (t.first != k)
          {
              if (t.first.length() < k.length()) match = false;
              if (t.first.substr(0,k.length()) == k) return true;    
          }
          else 
          {
                  match = true;
          }

          return match;
    }

} // namespace XSutility
namespace XSutility
{
         string addSuffix(const string&  oldName, XSutility::fileType  type = NONE);
} 


#endif
