#ifndef LSTATT_H
#define LSTATT_H

#include <XSFit/StatMethod/Cstat/CstatVariants.h>
#include <cmath>

template <typename T>
Real LorStat::lorSum (const Real S, const int C, const int B)
{
   // Calculate the log of the summation over 0 to C of 
   //             S^j (C+B-j)!/j!/(C-j)!             if flag = 0
   //             j S^(j-1) (C+B-j)!/j!/(C-j)!       if flag = 1
   //             j(j-1) S^(j-2) (C+B-j)!/j!/(C-j)!  if flag = 2
   // Avoids numerical overflows and speeds up calculation by first finding
   // the largest term, dividing it out of the sum, and then including only
   // those terms that are > exp(-20) times the largest term.
   // Arguments :
   //     S      d       i: the model rate times the sum of the exposure times
   //     C      i       i: the counts in the source observation
   //     B      i       i: the counts in the background observation
   //     Flag   i       i: indicates which of 3 summations is to be performed

   int flag = T::flag;
   Real result = .0;

   // First trap out the special case of C < flag. In this case the summation
   // is zero so we return -250 for the log. Also trap case of flag having an
   // unexpected value.
   if (C < flag || (flag != 0 && flag != 1 && flag != 2))
   {
      result = -250.0;
      return result;
   }

   // Now handle the easy case of S and C > 0
   int j = 0, jmax = 0;
   Real dtmax = 0.0;
   if (S > 0 && C > 0)
   {
      Real dlogS = std::log(S);

      // Find the maximum term in the summation from 0 to C
      if (C > flag)
      {
         int j1 = flag;
         int j2 = C;
         Real dt1 = T::calc(j1, dlogS) + lorTerm(C, B, j1);
         Real dt2 = T::calc(j2, dlogS) + lorTerm(C, B, j2);
         bool isDone = false;
         while (!isDone)
         {
            j = (j1+j2)/2;
            Real dtry1 = T::calc(j, dlogS) + lorTerm(C, B, j);
            Real dtry2 = T::calc(j+1, dlogS) + lorTerm(C, B, j+1);
            if (dtry2 > dtry1)
            {
               j1 = j+1;
               dt1 = dtry2;
            }
            else
            {
               j2 = j;
               dt2 = dtry1;
            }
            isDone = ((j1+1) == j2 || j1 == j2);
         }
         if (dt2 > dt1)
         {
            jmax = j2;
            dtmax = dt2;
         }
         else
         {
            jmax = j1;
            dtmax = dt1;
         }
      } // end if C > flag
      else if (C == flag)
      {
         jmax = flag;
         dtmax = T::calc(jmax, dlogS) + lorTerm(C, B, jmax);
      }

      // Now sum over all the terms bigger than EXP(-20) times the maximum.
      // Sum up from the maximum then down from the maximum using the fact
      // that the terms are decrease monotonically on both sides of the maximum.
      j = jmax - 1;
      Real dtemp = .0;
      while (j < C && dtemp > -20.0)
      {
         ++j;
	 dtemp = T::calc(j, dlogS) + lorTerm(C, B, j) - dtmax;
	 result += std::exp(dtemp);
      }
      j = jmax;
      dtemp = .0;
      while (j > flag && dtemp > -20.0)
      {
         --j;
	 dtemp = T::calc(j, dlogS) + lorTerm(C, B, j) - dtmax;
	 result += std::exp(dtemp);
      }
      result = std::log(result) + dtmax;
   } // end if S>0 && C>0
   else if (S == 0 && C > 0)
   {
      // Do the special cases for S = 0. If S = 0 then only the j=FLAG term 
      // contributes
      result = lorTerm(C, B, flag);
   }
   else if (C == 0)
   {
      // Do the special cases for C = 0. If C = 0 then only the j=0 term
      // contributes.
      result = lorTerm(0, B, 0);
   }
   return result;
}

#endif
