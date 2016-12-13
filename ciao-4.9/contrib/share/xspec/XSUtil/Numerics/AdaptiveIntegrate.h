//C++

#ifndef ADAPTIVEINTEGRATE_H
#define ADAPTIVEINTEGRATE_H

#include <xsTypes.h>
#include <utility>
#include <XSUtil/Utils/XSutility.h>

namespace Numerics {

  // Adaptive integration based on Gauss-Kronrod on subsections
  // Uses function pointer as a template parameter for efficiency.
	
  template<RealArray Integrand(const RealArray& x, void *p)> 
    int AdaptiveIntegrate(const Real LowerLimit, const Real UpperLimit, 
			  void *p, const Real Precision, Real& Integral, 
			  Real& IntegralError);
  template<RealArray Integrand(const RealArray& x, void *p)> 
    void GaussKronrodIntegrate(const Real LowerLimit, const Real UpperLimit, 
			       void *p, Real& Integral, Real& IntegralError);


  template<RealArray Integrand(const RealArray& x, void *p)> 
  int AdaptiveIntegrate(const Real LowerLimit, const Real UpperLimit, void *p, 
			const Real Precision, Real& Integral, 
			Real& IntegralError)
  {
    std::vector<Real> partValue, partError, partLower, partUpper;
    
    // do an initial G-K integration over the entire range to set the adaptive
    // integral up

    GaussKronrodIntegrate<Integrand>(LowerLimit, UpperLimit, p, 
				     Integral, IntegralError);

    partValue.push_back(Integral);
    partError.push_back(IntegralError);
    partLower.push_back(LowerLimit);
    partUpper.push_back(UpperLimit);

    // adaptive integration loop. Continue till the total error is below some
    // fractional value

    int MaxIter = 100;
    int next = 0;

    int iter = 0;
    while ( IntegralError/Integral > Precision && iter < MaxIter ) {

      iter++;
      
      // find part of integral with largest error

      Real error = 0.0;

      for (size_t i=0; i<partValue.size(); i++) {
	if ( partError[i] > error ) {
	  error = partError[i];
	  next = i;
	}
      }

      // split it in two and do a G-K integration on each half

      Real lower = partLower[next];
      Real upper = partUpper[next];
      Real midpoint = (lower+upper)/2.0;

      Real I1,I2,E1,E2;

      GaussKronrodIntegrate<Integrand>(lower, midpoint, p, I1, E1);
      GaussKronrodIntegrate<Integrand>(midpoint, upper, p, I2, E2);

      // put results in vector

      partValue[next] = I1;
      partError[next] = E1;
      partLower[next] = lower;
      partUpper[next] = midpoint;

      partValue.push_back(I2);
      partError.push_back(E2);
      partLower.push_back(midpoint);
      partUpper.push_back(upper);

      // evaluate total integral and error

      Integral = 0.0;
      IntegralError = 0.0;

      for (size_t i=0; i<partValue.size(); i++) {
	Integral += partValue[i];
	IntegralError += partError[i]*partError[i];
      }
      IntegralError = sqrt(IntegralError);

    }

    return(iter);

  }

  template<RealArray Integrand(const RealArray& x, void *p)>
  void GaussKronrodIntegrate(const Real LowerLimit, const Real UpperLimit, 
			     void *p, Real& Integral, Real& IntegralError)
  {
    // Gauss-Kronrod integration of function Integrand

    static const Real xgk[8] =    // abscissae of the 15-point kronrod rule */
      {
	0.991455371120812639206854697526329,
	0.949107912342758524526189684047851,
	0.864864423359769072789712788640926,
	0.741531185599394439863864773280788,
	0.586087235467691130294144838258730,
	0.405845151377397166906606412076961,
	0.207784955007898467600689403773245,
	0.000000000000000000000000000000000
      };

    // xgk[1], xgk[3], ... abscissae of the 7-point gauss rule. 
    //   xgk[0], xgk[2], ... abscissae to optimally extend the 7-point gauss rule

    static const Real wg[4] =     // weights of the 7-point gauss rule
      {
	0.129484966168869693270611432679082,
	0.279705391489276667901467771423780,
	0.381830050505118944950369775488975,
	0.417959183673469387755102040816327
      };

    static const Real wgk[8] =    // weights of the 15-point kronrod rule
      {
	0.022935322010529224963732008058970,
	0.063092092629978553290700663189204,
	0.104790010322250183839876322541518,
	0.140653259715525918745189590510238,
	0.169004726639267902826583426598550,
	0.190350578064785409913256402421014,
	0.204432940075298892414161999234649,
	0.209482141084727828012999174891714
      };

    Real midpoint = 0.5 * (UpperLimit + LowerLimit);
    Real halfrange = 0.5 * (UpperLimit - LowerLimit);
    
    RealArray x(15);
    for (size_t i=0; i<7; i++) {
      x[i] = midpoint - xgk[i]*halfrange;
      x[14-i] = midpoint + xgk[i]*halfrange;
    }
    x[7] = midpoint;
    
    RealArray out(15);

    out = Integrand(x, p);

    Real GaussResults(out[7]*wg[3]);
    for (size_t i=0; i<3; i++) GaussResults += wg[i]*(out[2*i+1]+out[13-2*i]);

    Real KronrodResults(out[7]*wgk[7]);
    Real AbsResults(abs(out[7])*wgk[7]);
    for (size_t i=0; i<7; i++) {
      KronrodResults += wgk[i]*(out[i]+out[14-i]);
      AbsResults += wgk[i]*(abs(out[i])+abs(out[14-i]));
    }

    Real Mean = KronrodResults * 0.5;

    Real AscResults = wgk[7] * abs (out[7] - Mean);

    for (size_t i=0; i<7; i++) AscResults += wgk[i] * (abs(out[i]-Mean) + abs(out[14-i]-Mean));

    // scale by the width of the integration region

    IntegralError = (KronrodResults - GaussResults) * halfrange;

    Integral = KronrodResults * halfrange;

    AbsResults *= abs(halfrange);
    AscResults *= abs(halfrange);

    IntegralError = abs(IntegralError);

    if (AscResults != 0.0 && IntegralError != 0.0) {
      Real scale = pow((200 * IntegralError / AscResults), 1.5) ;
      if (scale < 1.0) {
	IntegralError = AscResults * scale;
      } else {
	IntegralError = AscResults;
      }
    }
    if (AbsResults > 2.2250738585072014e-308 / (50 * 2.2204460492503131e-16)) {
      Real min_err = 50 * 2.2204460492503131e-16 * AbsResults;
      if (min_err > IntegralError) IntegralError = min_err;
    }

    return;

  }

}


#endif
