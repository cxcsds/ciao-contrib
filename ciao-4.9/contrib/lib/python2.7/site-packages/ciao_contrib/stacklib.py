
# Python35Support

#
#  Copyright (C) 2011, 2012, 2016  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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

"""Helper routines for using the stack module (see "ahelp stack"
for information on how stacks are used in CIAO tools).

The expand_stack() routine is deprecated; please use the build routine
from the stk module instead (in fact, expand_stack just calls this
routine for you).

The make_stackfile() is somewhat experimental, and may be removed.

"""

import os
import tempfile
import warnings

import stk

__all__ = ("expand_stack", "make_stackfile")


def expand_stack(pval):
    """***DEPRECATED*** use stk.build() instead.

    Expand out the contents of the parameter value
    treating it as a stack. So pval="@foo.lis" will
    examine the contents of the file foo.lis but
    pval="foo.lis" just has a single value (i.e.
    "foo.lis"). The input should be a string.

    The return value is an array of values, even if the input is not a
    stack.

    Examples of use:

        pval='foo.lis'
        return=['foo.lis']

        pval='foo.lis,bar.lis'
        return=['foo.lis', 'bar.lis']

        pval='foo.lis bar.lis'
        return=['foo.lis', 'bar.lis']

        pval='foo.lis[cols x,y]'
        return=['foo.lis[cols x,y]']

        pval='@foo.lis'
        return=[array of the contents of foo.lis]

        pval='@foo.lis[cols x,y]'
        return=[array of the contents of foo.lis with
                '[cols x,y]' appended to the end of each line]

    """

    warnings.warn("Use stk.build instead", DeprecationWarning)
    return stk.build(pval)


def make_stackfile(infiles, dir="/tmp/", suffix='', delete=True):
    """Create a temporary file object which points to a file listing
    the contents of infiles. So if

      tfh = make_stackfile(infiles)

    You can use '@' + tfh.name to use this as a stack and you should
    use tfh.close() to remove the temporary file when handling errors.

    The dir, suffix, and delete arguments are passed through to the
    NamedTemporaryFile constructor.

    The infile values are written to the stack file using their
    absolute location (on input they are taken to be relative to the
    current working directory and NOT the dir argument).
    """

    # Change the mode, since the default is 'wb+' which makes
    # Python 3.5 use byte strings. I could set the encoding, but
    # this argument isn't available in Python 2.7
    tfh = tempfile.NamedTemporaryFile(mode='w+', dir=dir,
                                      suffix=suffix,
                                      delete=delete)

    for infile in infiles:
        tfh.write(os.path.abspath(infile) + "\n")

    tfh.flush()
    return tfh

# End
