//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef STEP_H
#define STEP_H 1

// memory
#include <memory>
// Grid
#include <XSFit/Fit/Grid.h>
#include <XSUtil/Utils/ProcessManager.h>

class Fit;




class Step : public Grid  //## Inherits: <unnamed>%41F91DBD034D
{

  public:
      Step (Fit* fit);
      virtual ~Step();

      virtual void doGrid ();
      static void retrieveParameter (const Fit* fit, const string& paramIDStr, ModParam*& parameter, int& paramIndex, int& fullIndex, string& paramName);
      virtual void report (bool title) const;
      bool best () const;
      void best (bool value);
      //	bestFit is the fit statistic value at the start of the
      //	steppar run.  Its name is misleading if the user runs
      //	steppar when the fit is not up-to-date (which wasn't
      //	allowed in the original steppar implementation).
      Real bestFit () const;
      void bestFit (Real value);
      //	This is the saved value of the minimum fit statistic
      //	found during the most recent steppar run.
      Real minStatFound () const;
      //	These are the values of ALL the variable fit parameters
      //	at the time of minStatFound, keyed by parameter index.
      //	Both the frozen stepped parameters and non-frozen other
      //	fit parameters are included here.  Use CAUTION if
      //	accessing this sometime after the last steppar, as
      //	parameter indices may no longer be valid.
      const std::map<int,Real>& minStatParams () const;
      void doPoint(const IntegerArray& coordinates);
      
      bool isFirstProc() const;
      void isFirstProc(bool flag);
      
      const std::map<string,RealArray>& freeParVals () const;

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
     
      class ParallelGrid : public ParallelFunc
      {
         public:
           ParallelGrid(const IntegerArray& nSteps);
           virtual void execute(const bool isParallel, const TransferStruct& input,
                        TransferStruct& output);
                        
         private:
            
            const IntegerArray m_nSteps;
      };
     
      Step(const Step &right);
      Step & operator=(const Step &right);

      void restoreFit ();
      // The elemRanges vector must be sized to the number of processes
      //   prior to calling this.  It will be filled with the 0-based
      //   stopping array index of the step-tree node for each process.
      void divideIntoProcs(IntegerArray& elemRanges) const;
      void reportPoint(const IntegerArray& coordinates) const;
      void reportProcess(const IntegerArray& nSteps, int startingElem, const std::vector<Real>& vals) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      bool m_best;
      Real m_bestFit;
      Fit* m_fit;
      Real m_minStatFound;
      std::map<int,Real> m_minStatParams;
      // For parallel processing, distinguish the first process
      //  for purposes of real-time reporting of output.
      bool m_isFirstProc;
      // For storage of the free parameter values at each grid point.
      //  The string key is the [<modName>:]<parNum>.
      std::map<string, RealArray> m_freeParVals;
    // Additional Implementation Declarations

};

// Class Step 

inline bool Step::best () const
{
  return m_best;
}

inline void Step::best (bool value)
{
  m_best = value;
}

inline Real Step::bestFit () const
{
  return m_bestFit;
}

inline void Step::bestFit (Real value)
{
  m_bestFit = value;
}

inline Real Step::minStatFound () const
{
  return m_minStatFound;
}

inline const std::map<int,Real>& Step::minStatParams () const
{
  return m_minStatParams;
}

inline bool Step::isFirstProc() const
{
   return m_isFirstProc;
}

inline void Step::isFirstProc(bool flag)
{
   m_isFirstProc = flag;
}

inline const std::map<string,RealArray>& Step::freeParVals () const
{
   return m_freeParVals;
}

#endif
