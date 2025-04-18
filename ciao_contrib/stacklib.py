#
#  Copyright (C) 2011, 2012, 2016, 2019, 2025
#  Smithsonian Astrophysical Observatory
#
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

"""Helper routines for using the stack module (see "ahelp stack"
for information on how stacks are used in CIAO tools).

The expand_stack() routine was removed in CIAO 4.12 since it was
just a renamed version of the build routine from the CIAO stk module.

The make_stackfile() is somewhat experimental, and may be removed.

"""

import os
import tempfile
import contextlib


__all__ = ("make_stackfile", "TemporaryStack")


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
    # this used to be used with Python 2.7 so leave as is.
    #
    tfh = tempfile.NamedTemporaryFile(mode='w+', dir=dir,
                                      suffix=suffix,
                                      delete=delete)

    for infile in infiles:
        tfh.write(os.path.abspath(infile) + "\n")

    tfh.flush()
    return tfh


class TemporaryStack(contextlib.AbstractContextManager):
    '''
    A context manager that will create a stack for a list of values.

    If abspath=True, then it will save the values in the tempfile
    with the full path name. If false then it will save the values
    with a preceeding "!" so as not to append the path to the satck
    file onto the values.
    '''

    def __init__(self, values, abspath=False, *args, **kwargs):
        'Create temp stack and populate it with values'

        # use ASCDS_WORK_PATH for tmpdir if not set
        if 'dir' not in kwargs:
            kwargs['dir'] = os.environ["ASCDS_WORK_PATH"]

        # use ".lis" for suffix if not set
        if 'suffix' not in kwargs:
            kwargs['suffix'] = ".lis"

        # Use 'w' so stack is always overwritten
        self.tfh = tempfile.NamedTemporaryFile(mode='w', *args,**kwargs)

        for val in values:
            if abspath:
                putstr = os.path.abspath(str(val))
            else:
                putstr = "!"+str(val)
            self.tfh.write(putstr+"\n")

        self.tfh.flush()
        self.name = self.tfh.name

    def __exit__(self, exc_type, exc_value, traceback):
        'Close the stack and delete file'
        self.tfh.close()

# End
