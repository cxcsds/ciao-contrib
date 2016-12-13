//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef FUNCTIONUTILITY_H
#define FUNCTIONUTILITY_H 1

// vector
#include <vector>
// string
#include <string>
// Error
#include <XSUtil/Error/Error.h>

#include <map>

#include <xsTypes.h>

static const double BADVAL = -1.2e-34;


class FunctionUtility 
{

  public:



    class NoInitializer : public YellowAlert  //## Inherits: <unnamed>%3E9D81E10009
    {
      public:
          NoInitializer();
          NoInitializer (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class InvalidAbundanceFile : public YellowAlert  //## Inherits: <unnamed>%3E9DC91A002B
    {
      public:
          InvalidAbundanceFile (const string& diag);

      protected:
      private:
      private: //## implementation
    };



    class FunctionException : public YellowAlert  //## Inherits: <unnamed>%3FFEC7FF0133
    {
      public:
          FunctionException (const string& diag);

      protected:
      private:
      private: //## implementation
    };

  private:



    struct Cosmology 
    {
          Cosmology ();

        // Data Members for Class Attributes
          float H0;
          float q0;
          float lambda0;

      public:
      protected:
      private:
      private: //## implementation
    };

  public:
      static bool checkXsect (const string& arg);
      static bool checkAbund (const string& arg);
      static void readInitializers (string& xsects, string& abunds);
      static void readNewAbundances (const string& file);
      static float getAbundance (const string& element);
      static float getAbundance (const size_t Z);
      static float getAbundance (const string& table, const string& element);
      static float getAbundance (const string& table, const size_t Z);
      static const string& elements (size_t index);
      static const string& getModelString (const string& key);
      static void setModelString (const string& key, const string& value);
      static void eraseModelStringDataBase ();
      static float getH0 ();
      static float getq0 ();
      static float getlambda0 ();
      static void setH0 (float H0);
      static void setq0 (float q0);
      static void setlambda0 (float lambda0);
      static void setFunctionCosmoParams (double H0, double q0, double lambda0);
      static const string& XSECT ();
      static void XSECT (const string& value);
      static const string& ABUND ();
      static void ABUND (const string& value);
      static const string& abundanceFile ();
      static void abundanceFile (const string& value);
      static const string& managerPath ();
      static void managerPath (const string& value);
      static const size_t& NELEMS ();
      static const string& modelDataPath ();
      static void modelDataPath (const string& value);
      static const string& NOT_A_KEY ();
      static const string& abundPath ();
      static void abundPath (const string& value);
      static const string& atomdbVersion ();
      static void atomdbVersion (const string& value);
      static const bool abundChanged ();
      static void abundChanged (bool value);
      static int xwriteChatter ();
      static void xwriteChatter (int value);
      static std::vector<double>& tempsDEM ();
      static std::vector<double>& DEM ();
      static const std::vector< float >& abundanceVectors (string table);
      static void abundanceVectors (string table, const std::vector< float >& value);
      static const std::string& crossSections (string table);
      static void crossSections (string table, const std::string& value);
      static const std::string abundDoc (string name);
      static void abundDoc (string name, std::string value);
      static const std::map<string,std::string>& modelStringDataBase ();
      static int getNumberXFLT(int ifl);
      static bool inXFLT(int ifl, int i);
      static bool inXFLT(int ifl, string skey);
      static double getXFLT(int ifl, int i);
      static double getXFLT(int ifl, string skey);
      static void loadXFLT(int ifl, const std::map<string, Real>& values);
      static void clearXFLT();
      static double getDbValue(const string keyword);
      static void loadDbValue(const string keyword, const double value);
      static void clearDb();
      static string getDbKeywords();
      static const std::map<string,double>& getAllDbValues();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static string s_XSECT;
      static string s_ABUND;
      static const string CROSSSECTFILE;
      static string s_abundanceFile;
      static std::vector<string> s_elements;
      static string s_managerPath;
      static const size_t s_NELEMS;
      static string s_modelDataPath;
      static string s_NOT_A_KEY;
      static FunctionUtility::Cosmology s_COSMO;
      static string s_abundPath;
      static string s_atomdbVersion;
      static bool s_abundChanged;
      static int s_xwriteChatter;
      static std::vector<double> s_tempsDEM;
      static std::vector<double> s_DEM;
      static std::map<int, std::map<string, Real> > s_XFLT;
      static std::map<string,double> s_valueDataBase;

    // Data Members for Associations
      static std::map<string,std::vector< float > > s_abundanceVectors;
      static std::map<string,std::string> s_crossSections;
      static std::map<string,std::string> s_abundDoc;
      static std::map<string,std::string> s_modelStringDataBase;

    // Additional Implementation Declarations

};

// Class FunctionUtility::NoInitializer 

// Class FunctionUtility::InvalidAbundanceFile 

// Class FunctionUtility::FunctionException 

// Class FunctionUtility::Cosmology 

// Class Utility FunctionUtility 

inline float FunctionUtility::getH0 ()
{
  return s_COSMO.H0;
}

inline float FunctionUtility::getq0 ()
{
  return s_COSMO.q0;
}

inline float FunctionUtility::getlambda0 ()
{
  return s_COSMO.lambda0;
}

inline void FunctionUtility::setH0 (float H0)
{
  s_COSMO.H0 = H0;
}

inline void FunctionUtility::setq0 (float q0)
{
  s_COSMO.q0 = q0;
}

inline void FunctionUtility::setlambda0 (float lambda0)
{
  s_COSMO.lambda0 = lambda0;
}

inline const string& FunctionUtility::XSECT ()
{
  return s_XSECT;
}

inline const string& FunctionUtility::ABUND ()
{
  return s_ABUND;
}

inline const string& FunctionUtility::abundanceFile ()
{
  return s_abundanceFile;
}

inline void FunctionUtility::abundanceFile (const string& value)
{
  s_abundanceFile = value;
}

inline const string& FunctionUtility::managerPath ()
{
  return s_managerPath;
}

inline void FunctionUtility::managerPath (const string& value)
{
  s_managerPath = value;
}

inline const size_t& FunctionUtility::NELEMS ()
{
  return s_NELEMS;
}

inline const string& FunctionUtility::modelDataPath ()
{
  return s_modelDataPath;
}

inline void FunctionUtility::modelDataPath (const string& value)
{
  s_modelDataPath = value;
}

inline const string& FunctionUtility::NOT_A_KEY ()
{
  return s_NOT_A_KEY;
}

inline const string& FunctionUtility::abundPath ()
{
  return s_abundPath;
}

inline void FunctionUtility::abundPath (const string& value)
{
  s_abundPath = value;
}

inline const string& FunctionUtility::atomdbVersion ()
{
  return s_atomdbVersion;
}

inline void FunctionUtility::atomdbVersion (const string& value)
{
  s_atomdbVersion = value;
}

inline const bool FunctionUtility::abundChanged ()
{
  return s_abundChanged;
}

inline void FunctionUtility::abundChanged (bool value)
{
  s_abundChanged = value;
}

inline int FunctionUtility::xwriteChatter ()
{
  return s_xwriteChatter;
}

inline void FunctionUtility::xwriteChatter (int value)
{
  s_xwriteChatter = value;
}

inline std::vector<double>& FunctionUtility::tempsDEM ()
{
  return s_tempsDEM;
}

inline std::vector<double>& FunctionUtility::DEM ()
{
  return s_DEM;
}

inline void FunctionUtility::abundanceVectors (string table, const std::vector< float >& value)
{
  s_abundanceVectors[table] = value;
}

inline void FunctionUtility::crossSections (string table, const std::string& value)
{
  s_crossSections[table] = value;
}

inline void FunctionUtility::abundDoc (string name, std::string value)
{
  s_abundDoc[name] = value;
}

inline const std::map<string,std::string>& FunctionUtility::modelStringDataBase ()
{
  return s_modelStringDataBase;
}

inline const std::map<string,double>& FunctionUtility::getAllDbValues ()
{
  return s_valueDataBase;
}

#endif
