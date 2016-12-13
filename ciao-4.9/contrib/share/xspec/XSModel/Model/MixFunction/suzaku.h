//C++
#ifndef SUZAKU_H
#define SUZAKU_H

#include <xsTypes.h>
#include <XSUtil/FunctionUtils/XSModelFunction.h>

class MixUtility;

class SuzakuMix
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
void XSCall<SuzakuMix>::operator() (const EnergyPointer& energyArray, 
                        const std::vector<Real>& parameterValues, GroupFluxContainer& flux,
                        GroupFluxContainer& fluxError, MixUtility* mixGenerator, 
                        const string& modelName) const;

template <>
MixUtility* XSCall<SuzakuMix>::getUtilityObject() const;

#endif
