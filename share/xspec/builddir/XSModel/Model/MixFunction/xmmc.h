//C++
#ifndef XMMC_H
#define XMMC_H

#include <xsTypes.h>
#include <XSFunctions/Utilities/XSModelFunction.h>

class MixUtility;

class Xmmc
{
   public:
      static void modFunction(const EnergyPointer& energyArray,
                                  const std::vector<Real>& parameterValues,
                                  GroupFluxContainer& flux,
                                  GroupFluxContainer& fluxError,
                                  MixUtility* mixGenerator,
                                  const std::string& modelName);
      static MixUtility* createUtility();
};

template <>
void XSCall<Xmmc>::operator() (const EnergyPointer& energyArray, 
                        const std::vector<Real>& parameterValues, GroupFluxContainer& flux,
                        GroupFluxContainer& fluxError, MixUtility* mixGenerator, 
                        const string& modelName) const;

template <>
MixUtility* XSCall<Xmmc>::getUtilityObject() const;

#endif
