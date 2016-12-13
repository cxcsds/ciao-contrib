//C++
#ifndef XSINTERFACE_H
#define XSINTERFACE_H

// Declarations of Xspec command-interface functions, with signatures 
// that are scripting-language independent.

#include <xsTypes.h>
class DataSet;

namespace XSGlobal {

// For generic command dispatch, it is helpful to group all the handler 
// functions with standard interface into a map with keys = function names.
// "Standard" interface is defined by the typedef below.
typedef int (*stdInterface)(const StringArray&);
extern std::map<string, stdInterface> stdInterfaceCmdMap;
void createStdInterfaceCmdMap();

// Unless stated otherwise, will handle all YellowAlerts.

int doAbund(const StringArray& rawArgs);

int doAddcomp(const StringArray& rawArgs);

int doAutosave(const StringArray& rawArgs);

// Return value: -1 = Error
//                0 = OK
int doArf(const StringArray& rawArgs);

// Return value: -1 = Error
//                0 = OK
int doBackgrnd(const StringArray& rawArgs);

int doBayes(const StringArray& rawArgs);

int doChain(const StringArray& rawArgs);

int doComsum(const StringArray& rawArgs);

int doCorfile(const StringArray& rawArgs);

int doCornorm(const StringArray& rawArgs);

int doCosmo(const StringArray& rawArgs);

int doCpd(const StringArray& rawArgs);

// Return value: -1 = Error occurred,
//               0 = OK  State changed, if calling autoSave don't empty trash.
//               1 = OK  If calling autoSave, empty trash.
//               2 = OK  Undo operation, do NOT call autoSave.
int doData(const StringArray& rawArgs, const bool handleUndo);

int doDelcomp(const StringArray& rawArgs);

int doDiagrsp(const StringArray& rawArgs);

int doDummyrsp(const StringArray& rawArgs);

int doEditmod(const StringArray& rawArgs);

int doEnergies(const StringArray& rawArgs);

int doEqwidth(const StringArray& rawArgs);

int doError(const StringArray& rawArgs);

int doFakeit(const StringArray& rawArgs);
void fakeitDataSetOrder(std::vector<DataSet*>& origDataSets);

int doFit(const StringArray& rawArgs);

int doFlux(const StringArray& rawArgs);

int doFreeze(const StringArray& rawArgs);

int doFtest(const StringArray& rawArgs);

int doGain(const StringArray& rawArgs);

int doGoodness(const StringArray& rawArgs);

int doHelp(const StringArray& rawArgs);

int doIdentify(const StringArray& rawArgs);

int doIgnore(const StringArray& rawArgs);

int doImprove(const StringArray& rawArgs);

int doInitpackage(const StringArray& rawArgs);

int doIplot(const StringArray& rawArgs);

int doLmod(const StringArray& rawArgs);

int doMargin(const StringArray& rawArgs);

int doMdefine(const StringArray& rawArgs);

int doMethod(const StringArray& rawArgs);

int doModel(const StringArray& rawArgs);

// This may throw YellowAlerts
void doNewpar(const string& input, const bool isRespPar, string& modelName, IntegerArray& paramRange);

int doNotice(const StringArray& rawArgs);

int doParallel(const StringArray& rawArgs);

int doRenorm(const StringArray& rawArgs);

int doResponse(const StringArray& rawArgs);

int doRmodel(const StringArray& rawArgs);

int doSave(const StringArray& rawArgs);

int doSetplot(const StringArray& rawArgs);

void doShow(const StringArray& rawArgs, string& prevOption);

int doStatistic(const StringArray& rawArgs);

int doSteppar(const StringArray& rawArgs);

int doSystematic(const StringArray& rawArgs);

int doTclout(const StringArray& rawArgs, bool& resultsEntered, string& results);

int doThaw(const StringArray& rawArgs);

int doTime(const StringArray& rawArgs);

int doUntie(const StringArray& rawArgs);

int doVersion(const StringArray& rawArgs);

int doWeight(const StringArray& rawArgs);

int doXsect(const StringArray& rawArgs);

int doXset(const StringArray& rawArgs);
}

#endif
