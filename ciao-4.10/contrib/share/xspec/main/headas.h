/******************************************************************************
 *   File name: headas.h                                                      *
 *                                                                            *
 * Description: Declarations for functions used to set up and shut down       *
 *     standard HEASoft tools (Ftools). This includes initializing I/O        *
 *     facilities, parameter file access, and the processing of standard      *
 *     parameters.                                                            *
 *                                                                            *
 *    Language: C or C++                                                      *
 *                                                                            *
 *      Author: Mike Tripicco, for HEASARC/GSFC/NASA                          *
 *                                                                            *
 *  Change log: see CVS Change log at the end of the file.                    *
 ******************************************************************************/
#ifndef headas_headas_H
#define headas_headas_H

/* Declarations for HEASoft I/O facilities, modeled on stdio.h. */
#include "headas_stdio.h"

/* Declarations for HEASoft I/O facilities, modeled on stdio.h. */
#include "headas_utils.h"

#ifdef __cplusplus
extern "C" {
#endif

/*******************************************************************************
The following functions are the original interface developed for HEADas along
with software for Swift mission. Used by swift, suzaku, and other Ftools
developed since 2005. START HERE: CHECK THE DATE.
*******************************************************************************/
/* Perform standard initialization for tools that use HEASoft facilities
   in heaio, heautils, and PIL. Normally this is not called directly, but
   rather is called by all HEASoft tools that use the standard "main"
   function from headas_main.c. This includes setting up the following:
     * HEADASNOQUERY (PIL): if this environment variable is set, no prompts
       will be issued, even for "automatic" or "queried" parameters.

     * Standard Parameters Read (PIL):
         chatter (int): this parameter, if present, establishes a
           threshold for displaying optional output messages (warnings
           and informational messages). Messages written to heaio
           streams with this chatter level or higher will be displayed.

         clobber (bool): this parameter, if present, controls whether
           or not a "clobber" flag is set. This may be used by client
           code to determine whether to overwrite existing files. This
           setting is used by heautils.

         history (bool): this parameter, if present, controls whether
           or not parameters are written into HISTORY keywords in output
           FITS extensions by functions in heautils.
*/
int headas_init(int argc, char * argv[]);

/* Perform closing operations complementary to headas_init. Writes
   final status messages. Closes PIL parameter file. */
int headas_close(int taskStatus);

#ifdef AHLOG_INTEGRATION_COMPLETE_REMOVE_THIS_IF
/*******************************************************************************
The following functions were developed along with software for the
Astro-H mission. They perform a superset of the headas initializations
declared above?
*******************************************************************************/
/** Perform the same initializations as headas_init, but in addition:
      * Set up logging facilities in the ahlog library.
    \param[in] argc The number of command line arguments.
    \param[in] argv The command line arguments.
    \param[in] tooltag String describing version or other identifying tag
      for the tool being run (used in output messages by ahlog).
*/
int headas_start_up(int argc, char * argv[], const char * tooltag);

int headas_shut_down(void);
#endif

#ifdef __cplusplus
} /* End extern "C" { */
#endif

#endif

/*
 * $Log$
 * Revision 1.6  2014/01/03 22:31:47  peachey
 * Add and test new functionality headas_start_up.
 *
*/
