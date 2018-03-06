//
#ifndef XSTCL_H
#define XSTCL_H
/*
 * Include file for TCL/XSPEC interface
 * Revised 2/99 B. Dorman
 * Revisions have moved all global function declarations to .h file and given the
 * EXTERN keyword ( compatibility with C++ and Win32 - see tcl.h for details).
 * Since C declares global functions as extern it is less confusing to do it this
 * way than to prototype in each separate file (prototyping is a requirement for C++).
 */

#include <fstream>

#include <string>
#include <map>
#include <set>

class TkGUI;

#include <tcl.h>
// defines Tclreadline_Init etc and version strings.
#include <tclreadline.h>

extern "C" {

// tcl interpreter.
extern Tcl_Interp *interp;

}

namespace xstcl
{
        // map containers for command function pointers and one line syntax summaries.
        using std::string;


/*
 * Values for the TCL prompt, both the default and the one
 * for prompting for parameters.
 */
        extern  char xsTclPrompt[];
        extern  char xsLogOut[];
        extern  char xsLogErr[];
        extern  char cPrompt[];  // continuation prompt 
        extern  const size_t NORM_OUTPUT;

        extern TkGUI* GUIdata;

        /*
        * String to hold the value of the current prompt for xspec.  Linked
        * to a corresponding TCL variable.
        */
        extern char *xs_tcl_prompt;


        /*
        * Token for command tracer which echoes the commands.
        */
        extern Tcl_Trace XS_Echo_Trace;

        /*
        * Tcl and linked C variable as to whether to echo commands from a script.
        */
        extern int xs_echo_script;


        /*
        * Variable to turn off writing of commands to log files or scripts.
        */
        extern int xs_noecho_command;

        /*
        * Tcl and linked C variable to control whether or not XSPEC commands return
        * Tcl results - only included for backwards compatibility with v10.0
        */
        extern int xs_return_result;

 /*
 * TCL Channels used for implementing log and script files
 */
        extern Tcl_Channel XS_Stdout_Chan;
        extern Tcl_Channel XS_Stderr_Chan;
        extern Tcl_Channel XS_Logfile_Chan;
        extern Tcl_Channel XS_Script_Chan;

/*
 * Names for the TCL scripting channel.
 */
        extern string xsScriptFile;

// extern "C" linkage block. All calls from/to tcl need C linkage  

#ifdef __cplusplus
extern "C" {
#endif

// All functions that are used by Tcl need to be global and declared with C linkage
        int xs_execute_script(Tcl_Interp* interp, char* command);



    // utility for querying tcl about string. Used by execscript but may be useful elsewhere.
        /* returns 1 if the string is a valid command, 0 else */

        int isCommand(Tcl_Interp* interp, const char* astring, std::set<string>& userProcs);


        void returnCommand(std::ifstream& stream, Tcl_Interp* interp, std::string& buffer, 
                unsigned int* location, std::set<string>& userProcs);

/* function of type Tcl_CmdObjTraceProc */

        Tcl_CmdObjTraceProc xs_echo_command;

/* tcl procedures for handling log channel */

        int xsInputLog(ClientData, char*, int, int*);
        int xsCloseLog(ClientData, Tcl_Interp*);
        int xsOutputLog(ClientData, char*,int,int*);
        void xsWatchLog(ClientData, int);
        int xsHandleLog(ClientData,int,ClientData*);

/* tcl command function definitions */

/* tcl appendresult handling */

        int xs_reset_result(void);
        int xs_append_old_result(char* );
        int xs_append_result(char* );
#ifdef __cplusplus
}  // extern "C" linkage block
#endif

/* signal handler related functions */

        void Sig_Setup(Tcl_Interp *);
        void Sig_Throw(Tcl_Interp *);

}   // namespace xstcl //



extern const int MAXLEN;

/*
 * maximum command length
 */
#define XS_COM_LEN 16

/*
 * Max TCL level for logging commands
 */
#define XS_MAX_LEV 100


#endif
