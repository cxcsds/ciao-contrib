//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSPECREGISTRY_H
#define XSPECREGISTRY_H 1

// map
#include <map>
// Error
#include <XSUtil/Error/Error.h>
// XspecDataIO
#include <XSModel/DataFactory/XspecDataIO.h>

class DataFactory;
class DataPrototype;
#include <typeinfo>




class XspecRegistry 
{

  public:



    class UnrecognizedFormat : public YellowAlert  //## Inherits: <unnamed>%39FF3430021F
    {
      public:
          UnrecognizedFormat (const string& msg);

      protected:
      private:
      private: //## implementation
    };
      virtual ~XspecRegistry();

      virtual void addToRegistry (DataFactory* factory);
      static XspecRegistry* Instance ();
      DataPrototype* returnPrototype (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      DataPrototype* returnPrototype (const std::type_info& dataClass);

  public:
    // Additional Public Declarations

  protected:
      XspecRegistry();

    // Additional Protected Declarations

  private:
      void registerNativeTypes ();
      const std::map<const char*, DataPrototype*> dataFormats () const;
      void dataFormats (std::map<const char*, DataPrototype*> value);
      const DataPrototype* dataFormats (const char* type) const;
      void dataFormats (const char* type, DataPrototype* value);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static XspecRegistry* s_instance;

    // Data Members for Associations
      std::map<const char*, DataPrototype*> m_dataFormats;

    // Additional Implementation Declarations

};
//	Abstract interface representing the behavior of classes
//	that represent datasets. The datasets are read in from
//	files.
//
//	The formatFound() instruction returns true if the file
//	is of the format appropriate to the class.
//
//	The register() operation adds a pointer to an empty
//	class instance to a container type in a registry.
//
//	The datasets to be represented are required to register
//	themselves at some initialization stage. The  companion
//	type Registry class holds containers of pointers to
//	dummy dataset pointers.
//
//	Thus, when a new file is read, the registry can be
//	traversed and the format() operation called for each
//	class in the registry in turn to identify which subclass
//	of the base datatype to instantiate.



class RegisteredFormat 
{

  public:
      RegisteredFormat();
      virtual ~RegisteredFormat() = 0;

      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      virtual bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType) = 0;
      bool isRegistered (const XspecRegistry& registry) const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      RegisteredFormat(const RegisteredFormat &right);
      RegisteredFormat & operator=(const RegisteredFormat &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class XspecRegistry::UnrecognizedFormat 

// Class XspecRegistry 

inline const std::map<const char*, DataPrototype*> XspecRegistry::dataFormats () const
{
  return m_dataFormats;
}

inline void XspecRegistry::dataFormats (std::map<const char*, DataPrototype*> value)
{
  m_dataFormats = value;
}

inline const DataPrototype* XspecRegistry::dataFormats (const char* type) const
{
  return m_dataFormats.find(type)->second;
}

inline void XspecRegistry::dataFormats (const char* type, DataPrototype* value)
{
  m_dataFormats[type] = value;
}

// Class RegisteredFormat 


#endif
