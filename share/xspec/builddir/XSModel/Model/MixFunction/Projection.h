//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PROJECTION_H
#define PROJECTION_H 1

// utility
#include <utility>
// xsTypes
#include <xsTypes.h>
// MixUtility
#include <XSModel/Model/Component/MixUtility.h>
namespace XSContainer {
    class DataContainer;

} // namespace XSContainer




class Projection : public MixUtility  //## Inherits: <unnamed>%3F6F1D4700CC
{

  public:



    struct Ellipsoid 
    {
          Ellipsoid (Real maj = Projection::Ellipsoid::FLAG, Real min = Projection::Ellipsoid::FLAG, Real orient = Projection::Ellipsoid::FLAG);
          int operator==(const Ellipsoid &right) const;

          int operator!=(const Ellipsoid &right) const;

        // Data Members for Class Attributes
          Real a;
          Real b;
          Real orientation;
          static Real FLAG;
          //	Since definition of projct model doesn't actually
          //	specify that data groups must be loaded in order of
          //	increasing shell size, this stores the 0-based index of
          //	the shell immediately to the inside of this ellipse.  A
          //	negative value indicates this is the innermost shell.
          int innerShellNum;

        // Data Members for Associations
          std::vector<std::pair< Real,Real > > angleBound;

      public:
      protected:
      private:
      private: //## implementation
    };
      Projection (const string& name);
      virtual ~Projection();

      //	for projection, initialize reads the input  keys,
      //	defines the ellipsoid  sections and defines the
      //	projection matrix.
      virtual void initialize (const std::vector<Real>& params, const IntegerVector& specNums, const std::string& modelName);
      virtual void perform (const EnergyPointer& energy, const std::vector<Real>& params, GroupFluxContainer& flux, GroupFluxContainer& fluxError);
      virtual void initializeForFit (const std::vector<Real>& params, bool paramsAreFrozen);

  public:
    // Additional Public Declarations

  protected:
      virtual void verifyData ();

  private:
      Projection(const Projection &right);
      Projection & operator=(const Projection &right);

      //	prjint from fortran code. Compute the projection of a
      //	section ('element' is from the idea that the return
      //	value from this function is an element of the projection
      //	matrix).
      //
      //	The output is the fractional contribution to shell shell
      //	Number from ellipsoid ellipseNumber.
      Real element (size_t observation, int shellNumber, int ellipseNumber, int sectionNumber) const;
      //	calproj  from fortran code (calculates 'projection
      //	matrix' being matrix of fractional contributions from
      //	two shells).
      void defineMatrix (size_t observation);
      //	initialize ellipsoid descriptions. (major, minor,
      //	orientation and start/stop angles for sections).
      void createEllipsoidDescriptions (size_t observation, size_t spectrumNumber, size_t iShell);
      //	return shell number and semi-major axis length of volume
      //	interior to current.
      Real interiorVolume (size_t observation, int ellipseNumber, int& shellNumber) const;
      //	determines whether ellipsoid descriptions have been
      //	changed since last invocation, in which case the
      //	projection matrix needs to be recalculated.
      bool changedProjection () const;
      //	fortran style accessor for projection matrix array which
      //	is stored as a 1-d  array.
      Real projectionElement (size_t observation, int nshell, int mshell) const;
      //	fortran style accessor for projection matrix array which
      //	is stored as a 1-d  array.
      void setProjectionElement (size_t observation, int nshell, int mshell, Real value);
      void doPerform (const EnergyPointer& energy, GroupFluxContainer& fluxes);
      static Projection::Ellipsoid testEllipsoid (const std::map<string, Real>& xflt, int spectrumNumber);
      void orderEllipsoids (bool usingCenter);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      std::vector<std::vector<Real> > m_matrix;
      static const Real DEG2RAD;
      //	number of shells in the problem. Of course this is also
      //	the size of  the vector m_shell, but it will be called
      //	very frequently during the program so is stored
      //	separately.
      size_t m_numberOfShells;
      static const Real FOURPIBY3;
      size_t m_observations;
      // To keep track of gaps in dg numbering for this model:
      // Key = dg num, Val = 0-based order position of dg.
      std::map<size_t,size_t> m_dgOrder;
      bool m_includesCentreShell;

    // Data Members for Associations
      RealArray m_startWeight;
      RealArray m_endWeight;
      IntegerVector m_startBin;
      IntegerVector m_endBin;
      std::vector<std::vector<Ellipsoid> > m_shell;
      std::vector<std::vector<Ellipsoid> > m_previousShell;

    // Additional Implementation Declarations

};

// Class Projection::Ellipsoid 

// Class Projection 


#endif
