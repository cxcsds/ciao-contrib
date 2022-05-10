#  Copyright (C) 2022  Smithsonian Astrophysical Observatory
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

__all__ = [ 'xpaget', 'xpaset', 'xpaset_p', ]

import subprocess as sp

def xpaget(xpa, args):
    'Run xpaget, return output as str'
    cmd = ["xpaget", xpa]
    cmd.extend(args.split())
    retval = sp.run(cmd, check=True, stdout=sp.PIPE).stdout
    retval = retval.decode()
    return retval


def xpaset_p(xpa, args):
    'Run xpaset -p (nothing return)'
    cmd = ["xpaset", "-p", xpa]
    cmd.extend(args)
    sp.run(cmd, check=True)


def xpaset(xpa, command, args):
    'Run xpaset (pipe in via stdin)'
    cmd = ["xpaset",  xpa]
    cmd.extend(command.split())
    stdin_str = args
    doit = sp.Popen(cmd, stdin=sp.PIPE)
    doit.stdin.write(stdin_str.encode())
    doit.communicate()

