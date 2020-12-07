//C++
#ifndef CSTATVARIANTS_H
#define CSTATVARIANTS_H 1

#include <xsTypes.h>
#include <cmath>

class StdCstat
{
   public:

      static const string cmdName;
      static const string rootName;
      static const Real FLOOR;

      static int specificPerform(const RealArray& s, const RealArray& ts, const RealArray& y,
				 const int n, const std::string& modstr, Real& stat);
      static int specificPerformB(const RealArray& s, const RealArray& b,
				  const RealArray& berr, const RealArray& ts,
				  const RealArray& tb, const RealArray& y, const int n,
				  const std::string& modstr, Real& stat);
      static int specificResetCalc(const RealArray& s, const RealArray& ts,
				   const RealArray& y, const int n,
				   const std::string& modstr, RealArray& diff1,
				   RealArray& diff2);
      static int specificResetCalcB(const RealArray& s, const RealArray& b,
				    const RealArray& berr, const RealArray& ts,
				    const RealArray& tb, const RealArray& y, const int n,
				    const std::string& modstr, RealArray& diff1,
				    RealArray& diff2);

      static bool specificValidStatistic(bool PoissonSource, bool PoissonBackground);

      static const string& fullName(const int n, const std::string& modstr);
      static const string& scriptName(const int n, const std::string& modstr);
      
   private:

      static string s_currentFullName;
      static string s_currentScriptName;
};

void cstatRebinNoB(const RealArray& s, const RealArray& ts, const RealArray& y,
		   const int n, const std::string& modstr, RealArray& sbin,
		   RealArray& tsbin, RealArray& ybin);

void cstatRebinB(const RealArray& s, const RealArray& b, const RealArray& ts, 
		 const RealArray& tb, const RealArray& y, const int n, 
		 const std::string& modstr, RealArray& sbin, RealArray& bbin,
		 RealArray& tsbin, RealArray& tbbin, RealArray& ybin);


class PGstat
{
   public:

      static const string cmdName;
      static const string rootName;
      static const Real FLOOR;

      static int specificPerform(const RealArray& s, const RealArray& ts, const RealArray& y,
				 const int n, const std::string& modstr, Real& stat);
      static int specificPerformB(const RealArray& s, const RealArray& b,
				  const RealArray& berr, const RealArray& ts,
				  const RealArray& tb, const RealArray& y, const int n,
				  const std::string& modstr, Real& stat);
      static int specificResetCalc(const RealArray& s, const RealArray& ts,
				   const RealArray& y, const int n,
				   const std::string& modstr, RealArray& diff1,
				   RealArray& diff2);
      static int specificResetCalcB(const RealArray& s, const RealArray& b,
				    const RealArray& berr, const RealArray& ts,
				    const RealArray& tb, const RealArray& y, const int n,
				    const std::string& modstr, RealArray& diff1,
				    RealArray& diff2);

      static bool specificValidStatistic(bool PoissonSource, bool PoissonBackground);

      static const string& fullName(const int n, const std::string& modstr);
      static const string& scriptName(const int n, const std::string& modstr);
      
};

class Pstat
{
   public:

      static const string cmdName;
      static const string rootName;
      static const Real FLOOR;

      static int specificPerform(const RealArray& s, const RealArray& ts, const RealArray& y,
				 const int n, const std::string& modstr, Real& stat);
      static int specificPerformB(const RealArray& s, const RealArray& b,
				  const RealArray& berr, const RealArray& ts,
				  const RealArray& tb, const RealArray& y, const int n,
				  const std::string& modstr, Real& stat);
      static int specificResetCalc(const RealArray& s, const RealArray& ts,
				   const RealArray& y, const int n,
				   const std::string& modstr, RealArray& diff1,
				   RealArray& diff2);
      static int specificResetCalcB(const RealArray& s, const RealArray& b,
				    const RealArray& berr, const RealArray& ts,
				    const RealArray& tb, const RealArray& y, const int n,
				    const std::string& modstr, RealArray& diff1,
				    RealArray& diff2);

      static bool specificValidStatistic(bool PoissonSource, bool PoissonBackground);

      static const string& fullName(const int n, const std::string& modstr);
      static const string& scriptName(const int n, const std::string& modstr);
      
};

class LorStat
{
   public:

      static const string cmdName;
      static const string rootName;
      static const Real FLOOR;
 
      static int specificPerform(const RealArray& s, const RealArray& ts, const RealArray& y,
				 const int n, const std::string& modstr, Real& stat);
      static int specificPerformB(const RealArray& s, const RealArray& b,
				  const RealArray& berr, const RealArray& ts,
				  const RealArray& tb, const RealArray& y, const int n,
				  const std::string& modstr, Real& stat);
      static int specificResetCalc(const RealArray& s, const RealArray& ts,
				   const RealArray& y, const int n,
				   const std::string& modstr, RealArray& diff1,
				   RealArray& diff2);
      static int specificResetCalcB(const RealArray& s, const RealArray& b,
				    const RealArray& berr, const RealArray& ts,
				    const RealArray& tb, const RealArray& y, const int n,
				    const std::string& modstr, RealArray& diff1,
				    RealArray& diff2);

      static bool specificValidStatistic(bool PoissonSource, bool PoissonBackground);

      static const string& fullName(const int n, const std::string& modstr);
      static const string& scriptName(const int n, const std::string& modstr);

   private:

      // calc functions are inlined below
      struct Dterm0
      {
         static const int flag;
         static Real calc(int j, Real dlogS);
      };
      struct Dterm1
      {
         static const int flag;
         static Real calc(int j, Real dlogS);
      };
      struct Dterm2
      {
         static const int flag;
         static Real calc(int j, Real dlogS);
      };

      static Real lorTerm(const int n1, const int n2, const int n3);

      template <typename T>
      static Real lorSum(const Real S, const int C, const int B);
};


inline Real LorStat::Dterm0::calc(int j, Real dlogS)
{
   return j*dlogS;
}

inline Real LorStat::Dterm1::calc(int j, Real dlogS)
{
   Real rj = static_cast<Real>(j);
   return std::log(rj) + (rj-1)*dlogS;
}

inline Real LorStat::Dterm2::calc(int j, Real dlogS)
{
   Real rj = static_cast<Real>(j);
   return std::log(rj) + std::log(rj-1) + (rj-2)*dlogS;
}

class WhittleStat
{
   public:

      static const string cmdName;
      static const string rootName;
      static const Real FLOOR;

      static int specificPerform(const RealArray& s, const RealArray& ts, const RealArray& y,
				 const int n, const std::string& modstr, Real& stat);
      static int specificPerformB(const RealArray& s, const RealArray& b,
				  const RealArray& berr, const RealArray& ts,
				  const RealArray& tb, const RealArray& y, const int n,
				  const std::string& modstr, Real& stat);
      static int specificResetCalc(const RealArray& s, const RealArray& ts,
				   const RealArray& y, const int n,
				   const std::string& modstr, RealArray& diff1,
				   RealArray& diff2);
      static int specificResetCalcB(const RealArray& s, const RealArray& b,
				    const RealArray& berr, const RealArray& ts,
				    const RealArray& tb, const RealArray& y, const int n,
				    const std::string& modstr, RealArray& diff1,
				    RealArray& diff2);

      static bool specificValidStatistic(bool PoissonSource, bool PoissonBackground);

      static const string& fullName(const int n, const std::string& modstr);
      static const string& scriptName(const int n, const std::string& modstr);
      
   private:

      static string s_currentFullName;
      static string s_currentScriptName;
};

#endif
