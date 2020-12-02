//C++
#ifndef PROJECT_H
#define PROJECT_H

#include <xsTypes.h>
#include <XSFunctions/Utilities/XSModelFunction.h>

class MixUtility;

class Project
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
void XSCall<Project>::operator() (const EnergyPointer& energyArray, 
                        const std::vector<Real>& parameterValues, GroupFluxContainer& flux,
                        GroupFluxContainer& fluxError, MixUtility* mixGenerator, 
                        const string& modelName) const;

template <>
MixUtility* XSCall<Project>::getUtilityObject() const;

#endif
