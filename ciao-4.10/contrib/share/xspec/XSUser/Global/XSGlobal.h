

// namespace definition for XSGlobal functions

#ifndef XSGLOBAL_H
#define XSGLOBAL_H

#       include <string>
#       include <list>
#       include <map>
#       include <XSUser/UserInterface/xstcl.h>

#include "xsTypes.h"

class Fit;
class Model;
class SpectralData;
class XSstream;

namespace XSGlobal {

  class GlobalData;

   extern  std::map <string,Tcl_ObjCmdProc*> commandMap;
   extern  std::map <string,string> summaryMap;        

   bool printDocs(const char* command, const char* firstArgument);

        extern GlobalData* globalData;

        void createCommandMap();

        void xsNotImplemented(const string& commandName);

        void registerNativeFitMethods();

        void registerNativeStatMethods();

	void registerNativeTables();

        void registerFunctionUtility();

        void registerNativePlotCommands();

        void registerNativeLineLists();

        void registerNativeRandomizingStrategies(Fit* fit);

        void commonPlotHandler(const StringArray& args, bool isInteractive);

        void saveAll(const string& outFile);

        void saveData(std::ofstream& outStream);

        void saveModel(std::ofstream& outStream);

        string refreshFitMethodNames();

        void startUp(bool displayVersion=true);

	void cleanUp();

        void initializeGUILibraries( Tcl_Interp* xsInterp);

        // note that the compiler ignores namespace qualifiers for
        // functions that are declared extern "C".

        extern "C"          
        {
          Tcl_ObjCmdProc  xsModel;
          Tcl_ObjCmdProc  xsUnknown;
          Tcl_ObjCmdProc  xsLog;
          Tcl_ObjCmdProc  xsExit;
          Tcl_ObjCmdProc  xsScript;
          Tcl_ObjCmdProc  xsAddcomp; 
          Tcl_ObjCmdProc  xsEditmod;
          Tcl_ObjCmdProc  xsNewpar;
          Tcl_ObjCmdProc  xsComsum;
          Tcl_ObjCmdProc  xsDiagrsp;
          Tcl_ObjCmdProc  xsImprove;
          Tcl_ObjCmdProc  xsSuggest;
          Tcl_ObjCmdProc  xsTime;
          Tcl_ObjCmdProc  xsMdefine; 
          Tcl_ObjCmdProc  xsChatter;
          Tcl_ObjCmdProc  xsAutosave;
          Tcl_ObjCmdProc  xsAbund;
          Tcl_ObjCmdProc  xsArf;
          Tcl_ObjCmdProc  xsBackgrnd;
          Tcl_ObjCmdProc  xsBayes;
          Tcl_ObjCmdProc  xsChain;
          Tcl_ObjCmdProc  xsCorfile;
          Tcl_ObjCmdProc  xsCornorm;
          Tcl_ObjCmdProc  xsCosmo;
          Tcl_ObjCmdProc  xsCpd;
          Tcl_ObjCmdProc  xsData;
          Tcl_ObjCmdProc  xsDelcomp;
          Tcl_ObjCmdProc  xsDummyrsp;
          Tcl_ObjCmdProc  xsEnergies;
          Tcl_ObjCmdProc  xsError;
          Tcl_ObjCmdProc  xsEqwidth;
          Tcl_ObjCmdProc  xsFakeit;
          Tcl_ObjCmdProc  xsFit;
          Tcl_ObjCmdProc  xsFlux;
          Tcl_ObjCmdProc  xsFreeze;
          Tcl_ObjCmdProc  xsFtest;
          Tcl_ObjCmdProc  xsGain;
          Tcl_ObjCmdProc  xsGenetic;
          Tcl_ObjCmdProc  xsGoodness;
          Tcl_ObjCmdProc  xsHelp;
          Tcl_ObjCmdProc  xsIdentify;
          Tcl_ObjCmdProc  xsIgnore;
	  Tcl_ObjCmdProc  xsInitpackage;
	  Tcl_ObjCmdProc  xsIplot;
          Tcl_ObjCmdProc  xsLmod;
          Tcl_ObjCmdProc  xsMargin;
          Tcl_ObjCmdProc  xsMethod;
          Tcl_ObjCmdProc  xsNotice;
          Tcl_ObjCmdProc  xsParallel;
          Tcl_ObjCmdProc  xsPlot;
          Tcl_ObjCmdProc  xsQuery;
          Tcl_ObjCmdProc  xsRecornrm;
          Tcl_ObjCmdProc  xsRenorm;
          Tcl_ObjCmdProc  xsResponse;
          Tcl_ObjCmdProc  xsRmodel;
          Tcl_ObjCmdProc  xsSave;
          Tcl_ObjCmdProc  xsSetplot;
          Tcl_ObjCmdProc  xsShow;
          Tcl_ObjCmdProc  xsStatistic;
          Tcl_ObjCmdProc  xsSteppar;
          Tcl_ObjCmdProc  xsSystematic;
          Tcl_ObjCmdProc  xsTclout;
          Tcl_ObjCmdProc  xsThaw;
          Tcl_ObjCmdProc  xsThleqw;
	  Tcl_ObjCmdProc  xsUndo;
          Tcl_ObjCmdProc  xsUntie;
          Tcl_ObjCmdProc  xsXsect;
          Tcl_ObjCmdProc  xsVersion;
          Tcl_ObjCmdProc  xsWeight;
          Tcl_ObjCmdProc  xsNull;
          Tcl_ObjCmdProc  xsXset;

        }



}
#endif
