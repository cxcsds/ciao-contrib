# 
# Copyright (C) 2013 Smithsonian Astrophysical Observatory
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 

# KJG checked P3 2016-09-13, no changes required


__all__ = [ 'get_params' ]


def __check_musthave( pars, musthave, fname ):
    """
    check for the must have parameters
    """

    if not musthave:
        return

    missing = []
    for must in musthave:
        if must not in pars:
            missing.append( must )
    
    if missing:
        raise RuntimeError("ERROR: The parameter file '{1}' is missing the following parameters: {0}".format( ", ".join(missing), fname ))


def get_params( tool, mode="rw", args=None, verbose=None, musthave=None ):
    """
    Load all the parameters from a .par file.
    
    All values are stored as strings which is fine since most
    are going to be str()'ed to be passed back to system
    commands.
    
    The value returned is a dictionary with par='value'

    tool is the tool name used to open par file (if no @@ given)

    mode is the specialised parameter file open mode, usually "rw"

    args is the list of comamnd line arguments, usually sys.args

    verbose is a dictionary with 2 elements

        verbose["set"] should be a function pointer to routine
          to set the verbosity level, eg lw.set_verbosity 

        verbose["cmd"] should be a function pointer to routine
          to print a string, eg verb1 or v1, etc.

    musthave is a list (iterable) of parameter values that
        must exist.  A parameter file may have more parameters
        than are actually needed (eg dmcoords, dmimgfilt, etc)
    """

    import paramio as pio

    if not hasattr( pio, "plist" ):
        raise Exception( "This script requires CIAO 4.5" )
    
    from ciao_contrib.param_wrapper import open_param_file as opf
    
    # open param file using contrib wrappers (tracebackdebug)
    pf = opf( args, toolname=tool)["fp"]

    # get list of all parameters
    pars = pio.plist( pf )
    __check_musthave( pars, musthave, pio.paramgetpath( pf ) )
    
    # load all params
    values = [ pio.pget(pf, pp) for pp in pars ]

    # close param
    pio.paramclose(pf)
    
    # create dictionary 
    all_pars = dict(zip(pars,values))

    if verbose:
        verbstr="\n"
        for pp in pars:
            verbstr += "{0:>16s} = {1}\n".format( pp,all_pars[pp] )
        # set verbose
        if "verbose" in all_pars:
            verbose["set"]( int(all_pars["verbose"]))
        else:
            verbose["set"](0)
        verbose["cmd"]( tool + verbstr)
        
    return all_pars
