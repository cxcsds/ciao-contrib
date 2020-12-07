//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef INTEGPROBGRID_H
#define INTEGPROBGRID_H 1

// Grid
#include <XSFit/Fit/Grid.h>
#include <XSFit/MCMC/MarginGrid.h>


class IntegProbGrid : public Grid  //## Inherits: <unnamed>%41F9450D0201
{

  public:

      IntegProbGrid (MarginGrid* marginGrid);
      virtual ~IntegProbGrid();

      virtual void doGrid ();
      virtual void report (bool title = false) const;

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      IntegProbGrid(const IntegProbGrid &right);
      IntegProbGrid & operator=(const IntegProbGrid &right);

      void calcBinCenters ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes

    // Data Members for Associations
      // Non-owning.  (MarginGrid owns IntegProbGrid)
      MarginGrid* m_marginGrid;

    // Additional Implementation Declarations

};

// Class IntegProbGrid 

#endif
