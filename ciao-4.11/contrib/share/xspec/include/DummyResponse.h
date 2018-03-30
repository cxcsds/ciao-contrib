//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DUMMYRESPONSE_H
#define DUMMYRESPONSE_H 1

// Response
#include <XSModel/Data/Detector/Response.h>
// UserDummyResponse
#include <XSModel/Data/Detector/UserDummyResponse.h>




class DummyResponse : public UserDummyResponse  //## Inherits: <unnamed>%3E567C600043
{

  public:
      ~DummyResponse();

      static DummyResponse* Instance (Real eMin = 0.5, 	// Default value 0.5 keV for lower end of energy range in
      	// Dummy response. All defaults are user redefinable.
      Real eMax = 20., 	// Default upper energy range
      size_t nE = 40, bool ln = false);
      void resetEnergies (Real eMin, Real eMax, size_t nE = 10, bool ln = false);
      //	Additional Public Declarations
      virtual Model& operator * (Model& model) const;
      //	Convolution method for responses. Input model component,
      //	output folded model component.
      //
      //	For the time being implement output as RealArray.
      //	There might be a better implementation that involved
      //	adding a folded array data member to the Component
      //	class. In the meantime the idea is to output the
      //	RealArray folded component and sum for the total
      //	model.
      //
      //	This must be modified to throw a YellowAlert Exception
      //	for invalid computations and to throw standard numeric
      //	exceptions.
      virtual void operator * (SumComponent& source) const;

    // Additional Public Declarations

  protected:
      virtual void generateResponse ();

    // Additional Protected Declarations
      //virtual void setArrays(size_t row) { }

      //virtual void setDescription (size_t spectrumNumber, 
      //	size_t dataGroupNumber, size_t row)  {}
  private:
      DummyResponse();
      DummyResponse& operator=(const DummyResponse &right);
      //	Constructor for DummyResponse.
      //	      //	The DummyResponse is a singleton class accessed
      //	The DummyResponse is a singleton class accessed
      //	only by a pointer.
      //	      //	The values passed to it will be read from the
      //	The values passed to it will be read from the
      //	initialization
      //	file when this is set up, and that will define its energy
      //	array and whether it is logarithmic or linear.
      //	      //	If the initialization file does not contain a
      //	string
      //	If the initialization file does not contain a string
      //	then default values will be used.
      //	      //	Otherwise, accessor functions will set the size
      //	of the
      //	Otherwise, accessor functions will set the size of the
      //	bins and the energy arrays etc.
      //	      //	The use of dummy response is twofold:
      //	The use of dummy response is twofold:
      //	      //	a) as an energy array for plotting models
      //	a) as an energy array for plotting models
      //	      //	b) as a square channel/energy matrix for showing
      //	b) as a square channel/energy matrix for showing
      //	raw data.
      //	      //	The first use will be given a default value in
      //	the
      //	The first use will be given a default value in the
      //	constructor.
      DummyResponse (Real eMin, Real eMax, size_t nE, bool ln);

      virtual DummyResponse* clone () const;
      virtual void source (SpectralData* value);
      virtual SpectralData* source () const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      static DummyResponse* s_instance;

    // Additional Implementation Declarations

};

// Class DummyResponse 

inline DummyResponse* DummyResponse::clone () const
{

  return const_cast<DummyResponse*>(this);
}


#endif
