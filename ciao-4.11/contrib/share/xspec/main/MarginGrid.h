//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MARGINGRID_H
#define MARGINGRID_H 1

// Histogram
#include <XSUtil/Numerics/Histogram.h>
// Grid
#include <XSFit/Fit/Grid.h>
// Chain
#include <XSFit/MCMC/Chain.h>

class ChainManager;
class IntegProbGrid;




class MarginGrid : public Grid  //## Inherits: <unnamed>%41F9450D0201
{

  public:



    struct MarginInfo 
    {
        // Data Members for Class Attributes
          std::vector<Real> minRanges;
          std::vector<Real> maxRanges;
          IntegerArray nSteps;
          BoolArray isLog;

      public:
      protected:
      private:
      private: //## implementation
    };



    typedef Numerics::Histogram< Real , Numerics::MixedBinning  > ProbabilityHist;
      MarginGrid (ChainManager* chainManager);
      virtual ~MarginGrid();

      virtual void doGrid ();
      virtual void report (bool title = false) const;
      const MarginInfo& marginInfo () const;
      const std::vector<Chain::ParamID>& paramIDs () const;
      const RealArray& getFractionValues () const;
      IntegProbGrid* integProbGrid () const;
      void integProbGrid (IntegProbGrid* value);

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations
      RealArray& fraction();

  private:
      MarginGrid(const MarginGrid &right);
      MarginGrid & operator=(const MarginGrid &right);

      void setMarginInfo ();
      static void makePoint (const std::vector<size_t>& indices, std::vector<Real>& point);
      void calcBinCenters ();

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_isSimple;

    // Data Members for Associations
      MarginInfo m_marginInfo;
      ChainManager* m_chainManager;
      std::vector<Chain::ParamID> m_paramIDs;
      RealArray m_fraction;
      // MarginGrid owns m_integProbGrid.
      IntegProbGrid* m_integProbGrid;

    // Additional Implementation Declarations

};

// Class MarginGrid::MarginInfo 

// Class MarginGrid 

inline RealArray& MarginGrid::fraction ()
{
  return m_fraction;
}

inline const MarginGrid::MarginInfo& MarginGrid::marginInfo () const
{
  return m_marginInfo;
}

inline const std::vector<Chain::ParamID>& MarginGrid::paramIDs () const
{
  return m_paramIDs;
}

inline const RealArray& MarginGrid::getFractionValues () const
{
  return m_fraction;
}

inline IntegProbGrid* MarginGrid::integProbGrid () const
{
  return m_integProbGrid;
}

inline void MarginGrid::integProbGrid (IntegProbGrid* value)
{
  m_integProbGrid = value;
}

#endif
