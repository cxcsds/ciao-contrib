//C++
#ifndef ASCACLUSTER_H
#define ASCACLUSTER_H

#include <xsTypes.h>
#include <XSUtil/FunctionUtils/XSModelFunction.h>

class MixUtility;

class AscaCluster
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
void XSCall<AscaCluster>::operator() (const EnergyPointer& energyArray, 
                        const std::vector<Real>& parameterValues, GroupFluxContainer& flux,
                        GroupFluxContainer& fluxError, MixUtility* mixGenerator, 
                        const string& modelName) const;

template <>
MixUtility* XSCall<AscaCluster>::getUtilityObject() const;


#endif
