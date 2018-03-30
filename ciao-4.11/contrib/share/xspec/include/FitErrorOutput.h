//C++
#ifndef FITERROROUTPUT_H
#define FITERROROUTPUT_H

#include <xsTypes.h>

class FitErrorCalc;

// Abstract base class to encompass the differences in handling the output
//  (ie. results, diagnostic error messages)  of the 'error' command
//  in single vs. parallel-processing modes.  Basically a strategy pattern.

class FitErrorOutput
{
   public:
      virtual ~FitErrorOutput();
      virtual void reportParameter(FitErrorCalc* context, int verbose=10) const = 0;
      virtual void writeMsg(FitErrorCalc* context, const string& msg, int verbose=10) const = 0;
      virtual void reportException(FitErrorCalc* context, const string& msg) const = 0;
      
   protected:
      FitErrorOutput();
      
   private:
      FitErrorOutput(const FitErrorOutput& right);
      FitErrorOutput & operator=(const FitErrorOutput &right);
      
};


inline FitErrorOutput::FitErrorOutput()
{
}

inline FitErrorOutput::~FitErrorOutput()
{
}

class SingleErrorOutput : public FitErrorOutput
{
   public:
      SingleErrorOutput();
      virtual ~SingleErrorOutput(); 
      virtual void reportParameter(FitErrorCalc* context, int verbose=10) const;
      virtual void writeMsg(FitErrorCalc* context, const string& msg, int verbose=10) const;
      virtual void reportException(FitErrorCalc* context, const string& msg) const;
};

class ParallelErrorOutput : public FitErrorOutput
{
   public:
      ParallelErrorOutput();
      virtual ~ParallelErrorOutput();
      virtual void reportParameter(FitErrorCalc* context, int verbose=10) const;
      virtual void writeMsg(FitErrorCalc* context, const string& msg, int verbose=10) const;
      virtual void reportException(FitErrorCalc* context, const string& msg) const;
};

#endif
