// Classes for NEI ionization balances. Uses eigenvector representation.

#include <xsTypes.h>

using namespace std;

const size_t TOTZ = 30;
const string atomName[30] = {"h" , "he", "li", "be", "b" , "c" , "n" , "o" , "f" ,
			     "ne", "na", "mg", "al", "si", "p" , "s" , "cl", "ar",
			     "k" , "ca", "sc", "ti", "v" , "cr", "mn", "fe", "co",
			     "ni", "cu", "zn"};

// older versions of NEI did not include eigenvector files for all elements so
// keep lists of elements included

const int NoldVersionZ = 11;
const int oldVersionZ[11] = {6,7,8,10,12,14,16,18,20,26,28};

// information about temperatures stored in data files
#define MINLOGT 4.0
#define DELTALOGT 4.0e-3
#define NUMBTEMP 1251

// conversion from keV to Kelvin
#define KEVTOK 1.1604505e7

class IonBalElementRecord{
 public:

  int AtomicNumber;
  RealArray EquilibriumPopulation;
  RealArray Eigenvalues;
  vector<RealArray> LeftEigenvectors;
  vector<RealArray> RightEigenvectors;
  
  IonBalElementRecord();     // default constructor
  ~IonBalElementRecord();    // destructor

  void Clear();  // clear out the contents

  IonBalElementRecord& operator=(const IonBalElementRecord&);  // deep copy

};

class IonBalTemperatureRecord{
 public:

  Real Temperature;
  vector<IonBalElementRecord> ElementRecord;

  IonBalTemperatureRecord();        // default constructor
  ~IonBalTemperatureRecord();       // destructor

  void LoadElementRecord(IonBalElementRecord input);

  void Clear();   // clear out the contents

  IonBalTemperatureRecord& operator=(const IonBalTemperatureRecord&);  // deep copy

};

class IonBalNei{
 public:

  vector<IonBalTemperatureRecord> TemperatureRecord;
  RealArray Temperature;
  string Version;

  IonBalNei();       // default constructor
  ~IonBalNei();      // destructor

  //  Set and get the version string. Note that if the version is changed
  //  we call Clear to reset the object and setVersion returns true.
  //  The setVersion method with no input checks NEIVERS and uses that if
  //  set.

  string getVersion();
  bool setVersion();
  bool setVersion(string version);

  //  ReadElements loads eigenvector data for these elements

  int ReadElements(int Z, string dirname);
  int ReadElements(vector<int> Z, string dirname);

  void LoadTemperatureRecord(IonBalTemperatureRecord input);

  RealArray Temperatures();     // return tabulated temperatures
  int NumberTemperatures();     // return number of tabulated temperatures
  int NumberElements();         // return number of tabulated elements
  bool ContainsElement(const int& Z); // returns true if data for Z

  IonBalNei& operator=(const IonBalNei&);    // deep copy

  void Clear();  // clear out the contents

  // return the collisional equilibrium ionization fractions for electron
  // temperature Te and element Z

  RealArray CEI(const Real& Te, const int& Z);

  // calculate the NEI ion fractions for electron temperature Te, ionization
  // parameter tau and element Z.

  RealArray Calc(const Real& Te, const Real& tau, const int& Z);
  RealArray Calc(const Real& Te, const Real& tau, const int& Z, const RealArray& initIonFrac);

  // Calculates ionization fractions at electron temperatures
  // Te and a set of ionization parameters tau(i), i=1,..,n,
  // where each tau is given weight(i). Electron temperature is
  // assumed to be linear function of tau.
  // Based on the old noneq.f.

  RealArray Calc(const RealArray& Te, const RealArray& tau, 
		 const RealArray& weight, const int& Z);
  RealArray Calc(const RealArray& Te, const RealArray& tau, 
		 const RealArray& weight, const int& Z, const RealArray& initIonFrac);

  // Calculates ionization fractions at electron temperature
  // Te(n) and ionization parameter tau(n), for electron 
  // temperatures Te given in a tabular form as a function of 
  // ionization parameter tau.
  // Based on the old noneqr.f.
  // Does initIonFrac make sense in this case.

  RealArray Calc(const RealArray& Te, const RealArray& tau, 
		 const int& Z);
  RealArray Calc(const RealArray& Te, const RealArray& tau, 
		 const int& Z, const RealArray& initIonFrac);

};

// wrapper functions which read (if necessary) the eigen* files and calculate
// the ion fractions. They use the NEISPEC xset variable to choose which version
// of the files to use. These match to the Calc methods in the IonBalNei class.

void calcNEIfractions(const Real& Te, const Real& tau, const int& Z, 
		      RealArray& IonFrac);
void calcNEIfractions(const Real& Te, const Real& tau, const IntegerVector& Z, 
		      vector<RealArray>& IonFrac);

void calcNEIfractions(const Real& Te, const Real& tau, const int& Z, 
		      const RealArray& initIonFrac, RealArray& IonFrac);
void calcNEIfractions(const Real& Te, const Real& tau, const IntegerVector& Z, 
		      const vector<RealArray>& initIonFrac, 
		      vector<RealArray>& IonFrac);

void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const int& Z, RealArray& IonFrac);
void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const IntegerVector& Z, vector<RealArray>& IonFrac);

void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const int& Z, const RealArray& initIonFrac, 
		      RealArray& IonFrac);
void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const IntegerVector& Z, const vector<RealArray>& initIonFrac, 
		      vector<RealArray>& IonFrac);

void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const RealArray& weight, const int& Z, RealArray& IonFrac);
void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const RealArray& weight, const IntegerVector& Z, 
		      vector<RealArray>& IonFrac);

void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const RealArray& weight, const int& Z, 
		      const RealArray& initIonFrac, RealArray& IonFrac);
void calcNEIfractions(const RealArray& Te, const RealArray& tau, 
		      const RealArray& weight, const IntegerVector& Z, 
		      const vector<RealArray>& initIonFrac, 
		      vector<RealArray>& IonFrac);


// wrapper routine to return the collisional ionization equilibrium fractions

void calcCEIfractions(const Real Te, const IntegerVector& Z, vector<RealArray>& IonFrac);

// helpful routines to return an index into the temperatures and the
// number of temperatures

int getNEItempIndex(const Real& tkeV);
int getNEInumbTemp();

// useful debugging routine

string writeIonFrac(const IntegerVector& Zarray, const vector<RealArray>& IonFrac);
string writeIonFrac(const int& Z, const IntegerVector& Zarray, 
		    const vector<RealArray>& IonFrac);

// helpful routine to do a binary search on a RealArray and return the index
// of the element of xx immediately less than x.

int locateIndex(const RealArray& xx, const Real x);

// functions to check whether arrays are identical. Could do this with a
// template but not worth it at the moment. These routines should ideally
// be in utility routines. Better would be to set up RealArray and IntegerVector
// as classes with the comparison operators defined (note the C++11 standard
// does include these for arrays).

bool identicalArrays(const vector<RealArray>& a, const vector<RealArray>& b);
bool identicalArrays(const RealArray& a, const RealArray& b);
bool identicalArrays(const IntegerVector& a, const IntegerVector& b);
