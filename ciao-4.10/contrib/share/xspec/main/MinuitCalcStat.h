// the class to calculate the statistic used in Minuit2
// a derived class of FCNBase

#ifndef MINUITCALCSTAT_H
#define MINUITCALCSTAT_H 1

#include "Minuit2/FCNBase.h"
#include "Minuit2/FCNGradientBase.h"

class MinuitCalcStat : public ROOT::Minuit2::FCNGradientBase {

 public:

  MinuitCalcStat();
  ~MinuitCalcStat();

  virtual double Up() const {return theErrorDef;}
  virtual double operator()(const std::vector<double>&) const;
  virtual bool CheckGradient() const {return false;}
  virtual std::vector<double> Gradient(const std::vector<double>&) const;

  void setErrorDef(double def) {theErrorDef = def;}

 private:

  double theErrorDef;

};

#endif
