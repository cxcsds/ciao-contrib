from __future__ import absolute_import

#
#  Copyright (C) 2011, 2015, 2016, 2019
#                Smithsonian Astrophysical Observatory
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

"""
Test routines for taking advantage of multiple processors.
This is a slightly different approach to that provided by
sherpa.utils.parallel_map and is provided for testing. Please
be aware that at present this code has seen limited testing and
has no guarantee of stability.

Sherpa's parallel_map splits up the work load at creation time and
farms off a set of tasks to each processor. Here we use a pool of jobs,
with each worker extracting the next job when it is free.

See, amongt others:

http://docs.python.org/library/multiprocessing.html

http://www.bryceboe.com/2010/08/26/python-multiprocessing-and-keyboardinterrupt/

"""

import time
import signal
import multiprocessing
from queue import Empty

from .logger_wrapper import initialize_module_logger

__all__ = ("parallel_pool", )

logger = initialize_module_logger("parallel_wrapper")
v3 = logger.verbose3
v4 = logger.verbose4
v5 = logger.verbose4


def task(func, arg_queue, result_queue):
    """Remove a task from the arg_queue (ie the next argument to use)
    and call func. Store the result in result_queue.
    Repeat until arg_queue is empty.
    """

    # note we block control-c handling here
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    while not arg_queue.empty():

        try:
            (i, arg) = arg_queue.get(block=False)
            v5("# Parallel worker starting task #{0}".format(i + 1))
            ans = func(arg)
            result_queue.put((i, ans))

        except Empty:
            pass


def parallel_pool(func, args, ncores=None):
    """Process func in parallel, once for each argument in args.

    func takes a single parameter, so you will normally need to write
    a wrapper routine something like the following, and use it as an
    argument to parallel_pool.

      def wrapper(arg):
          actual_func(*arg)

    One issue with this design is that it does not support keyword
    arguments.

    If ncores is None then uses multiprocessing.cpu_count().

    The return value is an array of the return values of func,
    in the order of the args array.

    """

    if ncores is None:
        nc = multiprocessing.cpu_count()
    else:
        nc = ncores

    narg = len(args)
    if nc > narg:
        nc = narg

    v3("# Parallel processing: {0} processes with {1} cores".format(narg, nc))

    job_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    for i, arg in enumerate(args):
        job_queue.put((i, arg))

    stime = time.localtime()
    v4("# Parallel start time: {0}".format(time.asctime(stime)))

    workers = []
    for i in range(nc):
        v5("# Starting parallel worker: {0}".format(i + 1))
        w = multiprocessing.Process(target=task,
                                    args=(func, job_queue, result_queue))
        w.start()
        workers.append(w)

    try:
        for w in workers:
            v5("# Joining worker to parallel queue")
            w.join()

    except KeyboardInterrupt:
        v5("# Parallel execution aborted by control c")
        for w in workers:
            w.terminate()
            w.join()

    etime = time.localtime()
    v4("# Parallel end time: {0}".format(time.asctime(etime)))

    dtime = time.mktime(etime) - time.mktime(stime)
    v3("# Parallel run took: {0} seconds".format(dtime))

    out = [None] * narg
    while not result_queue.empty():
        (n, v) = result_queue.get(block=False)
        out[n] = v

    return out

# End
