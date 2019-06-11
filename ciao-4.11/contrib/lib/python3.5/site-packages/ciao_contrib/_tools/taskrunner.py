from __future__ import absolute_import

#
# Copyright (C) 2012, 2015, 2016, 2019
#           Smithsonian Astrophysical Observatory
#
#
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

"""
An attempt at a simple task runner, supporting a pool-style
system where tasks wait for preconditions to be passed
before being run.

"""

import time
import multiprocessing
from queue import Empty

import pickle

from ..logger_wrapper import initialize_module_logger

"""
Very lmited testing and it feels a little clunky to use.

TODO:

  - tasks should signal their type via a string/name
    rather than the length of the tuple

"""

__all__ = ("TaskRunner", )

lgr = initialize_module_logger('taskrunner')
v1 = lgr.verbose1
v2 = lgr.verbose2
v3 = lgr.verbose3
v4 = lgr.verbose4


class TaskHandler(multiprocessing.Process):
    """A worker that waits for tasks from the
    task queue, runs it, then sends the name of
    the task to the results queue once finished.
    """

    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        """Remove a task from the task queue, call
        it, and once finished add the task name to
        the result queue.
        """

        name = self.name
        try:
            while True:
                taskinfo = self.task_queue.get()
                v3("TaskHandler {} retrieved taskinfo={}".format(name, taskinfo))

                if taskinfo is None:
                    v3("TaskHandler {} told to quit".format(name))
                    self.task_queue.task_done()
                    break

                elif len(taskinfo) == 4:
                    v3("TaskHandler {} running taskinfo={}".format(name, taskinfo))
                    (taskname, func, args, kwargs) = taskinfo
                    try:
                        v3("TaskHandler {} starting task {}".format(name, taskname))
                        func(*args, **kwargs)
                        v3("TaskHandler {} finshed task {}".format(name, taskname))
                    except BaseException as be:
                        v3("TaskHandler {} task {} - caught exception {}/{}".format(name, taskname, type(be), be))
                        self.task_queue.task_done()
                        self.result_queue.put((True, be))
                        break

                elif len(taskinfo) == 2:
                    v3("TaskHandler {} sent barrier: {}".format(name, taskinfo))
                    (taskname, taskmsg) = taskinfo
                    if taskmsg is not None:
                        v1(taskmsg)

                else:
                    v3("TaskHandler {} sent invalid taskinfo={}".format(name, taskinfo))
                    self.task_queue.task_done()
                    self.result_queue.put((True,
                                           ValueError("Task queue argument: {}".format(taskinfo))))
                    break

                v3("TaskHandler {} reporting that task={} is finished.".format(name, taskname))
                self.task_queue.task_done()
                self.result_queue.put((False, taskname))

        except BaseException as be:
            # This was added whilst tracking down an error with send/receive
            # as it was found to reduce the trace backs when a control-c
            # was needed after the system had essentially hung.
            #
            # I do not send a task_done message to self.task_queue
            # as I no idea what the state is here.
            #
            v3("TaskHandler {} - caught exception {}/{}".format(name, type(be), be))
            self.result_queue.put((True, be))  # possibly excessive

        v3("TaskHandler {} exiting.".format(name))


class TaskRunner:
    """Given a set of tasks with pre-conditions,
    run them in order. The tasks can be added to
    at any time before the run_tasks method is
    called.

    The task names and preconditions just need to
    be objects that can be displayed, compared
    for equality/used in a set, and can be pickled
    (although strings are primarily used/tested).
    """

    def __init__(self):
        """Set up the task runner."""

        self._clean()

    def _clean(self):
        "Prepare for a new set of tasks"

        self._torun = {}
        self._names = set()

    def _seen(self, name):
        """Returns True if the runner has already been
        sent a task called name."""

        return name in self._names

    def add_task(self, name, preconditions, func,
                 *args, **kwargs):
        """Add a task to be run.

        The name of the task must not have been used
        before with this runner.

        The preconditions are a list of task names that
        must have been completed before the task can be
        run. The preconditions must have been added to
        the runner by addtask otherwise an error is
        raised (this is a simple method to try and avoid
        cyclical dependencies).
        """

        v3("TaskRunner: adding task {}".format(name))

        if not hasattr(func, "__call__"):
            raise ValueError("The function for task {} is not callable".format(name))

        if self._seen(name):
            raise ValueError("Task {} has already been added to this runner".format(name))

        for pname in preconditions:
            if not self._seen(pname):
                raise ValueError("Precondition {} of task {} has not been added to this runner".format(pname, name))

        # Ideally this should not happen but just in case I forget
        # and use a data type that can't be serialized
        try:
            pickle.dumps(name)
            pickle.dumps(func)
            pickle.dumps(args)
            pickle.dumps(kwargs)
        except pickle.PicklingError:
            raise ValueError("Internal error: unable to serialize arguments for task={}".format(name))

        self._torun[name] = (name, preconditions, func, args, kwargs)
        self._names.add(name)
        v3("TaskRunner: task {} has been added to the queue.".format(name))

    def add_barrier(self, name, preconditions, msg=None):
        """Add a barrier which ensures that all the
        preconditions have been met and then inserts
        name into the list of completed jobs.

        If msg is not None then the value will be
        displayed to the user (so in this case it
        acts like a simple task that just prints a
        message rather than being a no-op).

        As with add_task, name must be unique and
        all the preconditions must be known to the
        runner. The preconditions list can be
        empty.
        """

        v3("TaskRunner: adding barrier {}".format(name))
        if self._seen(name):
            raise ValueError("Task {} has already been added to this runner".format(name))

        for pname in preconditions:
            if not self._seen(pname):
                raise ValueError("Precondition {} of the barrier {} has not been added to this runner".format(pname, name))

        try:
            pickle.dumps(name)
            pickle.dumps(msg)
        except pickle.PicklingError:
            raise ValueError("Internal error: unable to serialize arguments for task={}".format(name))

        self._torun[name] = (name, preconditions, msg)
        self._names.add(name)

    def run_tasks(self, processes=None, label=True):
        """Run the tasks, waiting until all the tasks have finished.

        The processes argument
        indicates the number of processes that should be run
        in parallel; a value of None uses the value of
        multiprocessing.cpu_count(). 0 is invalid; negative values are
        added on to the number of processes (so that -1 means use
        all-but-one processor). The result is clamped to the
        range 1 to cpu_count (inclusive).

        The label lag indicates if the informational message
        describing the number of processors used to run the tasks
        is displayed at verbose=1 (True) or verbose=2 (False).
        """

        if len(self._torun) == 0:
            raise ValueError("No tasks have been added to this runner")

        if label:
            f = v1
        else:
            f = v2

        processes = get_nproc(processes)
        if processes == 1:
            f("Running tasks in serial.")
            self._run_serial()
        else:
            f("Running tasks in parallel with {} processors.".format(processes))
            self._run_parallel(processes)

        self._clean()

    def _run_parallel(self, processes):
        "Run the tasks in parallel"

        stime = time.localtime()
        v4("TaskRunner (parallel, processes={}): started {}".format(processes, time.asctime(stime)))

        ntasks = len(self._torun)

        finished = set()
        queue = multiprocessing.Queue()
        task_queue = multiprocessing.JoinableQueue()

        # what tasks can be run now?
        deltasks = []
        for v in self._torun.values():
            name = v[0]
            preconditions = v[1]
            if len(preconditions) > 0:
                continue

            deltasks.append(name)
            if len(v) == 3:
                v3("TaskRunner: selected barrier {}".format(name))
                taskarg = (name, v[2])
            elif len(v) == 5:
                v3("TaskRunner: selected task {}".format(name))
                taskarg = (name, v[2], v[3], v[4])
            else:
                raise ValueError("Internal error: task info = {}".format(v))

            task_queue.put(taskarg)

        if len(deltasks) == 0:
            raise ValueError("Unable to start since all the tasks have at least one precondition")

        for deltask in deltasks:
            del self._torun[deltask]

        # If this process is starved of time then it may not
        # add a task to a queue, even if a process is idle.
        #
        # I am not sure how much of a problem that is here;
        # if the system is bogged down enough that this is
        # happening then not adding to the load is probably
        # a good idea anyway.
        #
        v4("TaskRunner (parallel, processes={}): starting workers".format(processes))
        workers = [TaskHandler(task_queue, queue)
                   for i in range(processes)]

        for w in workers:
            w.start()

        # Look for jobs that have finished and see
        # if any new ones can be started. Once all
        # the jobs have ended close down the workers.
        #
        v4("TaskRunner (parallel, processes={}): waiting for jobs".format(processes))
        while True:
            (errflag, taskout) = queue.get()

            if errflag:
                # Should we try to kill the other tasks?
                # It is possible that the user will see screen output
                # from these other tasks after the error message
                # we raise here.
                #
                # From some simple tests it looks like explicitly calling
                # terminate on these tasks does not really help, and may
                # avoid some of the clean up of tmp files we have.
                #
                v4("TaskRunner: received error condition; exiting")
                while True:
                    # try to remove any jobs that have not been run yet
                    try:
                        task_queue.get_nowait()
                    except Empty:
                        break

                for i in range(processes):
                    task_queue.put(None)

                raise taskout

            v4("TaskRunner: received result from task {}".format(taskout))

            # Can we stop the workers?
            finished.add(taskout)
            if len(finished) == ntasks:
                v4("TaskRunner: all tasks completed; stopping.")
                for i in range(processes):
                    task_queue.put(None)

                break

            # Can we run any new tasks?
            deltasks = []
            for v in self._torun.values():
                name = v[0]
                preconditions = v[1]
                flag = True
                for pname in preconditions:
                    if pname not in finished:
                        flag = False
                        break

                if not flag:
                    continue

                deltasks.append(name)

                if len(v) == 3:
                    v3("TaskRunner: selected barrier {}".format(name))
                    taskarg = (name, v[2])
                elif len(v) == 5:
                    v3("TaskRunner: selected task {}".format(name))
                    taskarg = (name, v[2], v[3], v[4])
                else:
                    raise ValueError("Internal error: task info = {}".format(v))

                task_queue.put(taskarg)

            for deltask in deltasks:
                del self._torun[deltask]

        # Wait for everything to finish.
        #
        # Attempts at calling join on the worker processes
        # leads to occasional errors, presumably because
        # they are already in the process of exiting due
        # to the None signal above (or some other related issue).
        #
        task_queue.join()

        etime = time.localtime()
        v4("TaskRunner (parallel, processes={}): stopped {}".format(processes, time.asctime(etime)))

    def _run_serial(self):
        "Run the tasks in serial"

        stime = time.localtime()
        v4("TaskRunner (serial): started {}".format(time.asctime(stime)))

        ntasks = len(self._torun)
        finished = set()

        while len(finished) < ntasks:

            deltask = None
            for v in self._torun.values():
                name = v[0]
                preconditions = v[1]
                flag = True
                for pname in preconditions:
                    if pname not in finished:
                        flag = False
                        break

                if not flag:
                    continue

                if len(v) == 3:
                    v3("TaskRunner (serial): running barrier {}".format(name))
                    if v[2] is not None:
                        v1(v[2])

                elif len(v) == 5:
                    v3("TaskRunner (serial): running task {}".format(name))
                    v[2](*v[3], **v[4])

                else:
                    raise ValueError("Internal error: task info={}".format(v))

                deltask = name
                break

            if deltask is None:
                raise ValueError("Unable to find any task to run from {}".format(self._torun))

            finished.add(deltask)
            del self._torun[deltask]

        etime = time.localtime()
        v4("TaskRunner (serial): stopped {}".format(time.asctime(etime)))


def get_nproc(nproc=None):
    """Convert the nproc command-line argument into the
    actual number of processors for this machine.

    maxproc is the number of processors available.

    A value of nproc=0 is invalid, None means use all
    the processors, an integer > 1 means use that number,
    and < 0 means add to maxproc. All values are clamped
    at 1 and maxproc.
    """

    # If we took processes=0 to mean use all the processors,
    # ie rather than None, then the following code would be nicer.
    # However, it strikes me as more confusing for the user.

    maxproc = multiprocessing.cpu_count()
    if nproc is None:
        nproc = maxproc
    else:
        try:
            if int(nproc) != nproc:
                raise ValueError("dummy")
        except ValueError:
            raise ValueError("nproc arument must be an integer, sent {}".format(nproc))

        if nproc == 0:
            raise ValueError("nproc argument can not be 0")

        if nproc > maxproc:
            nproc = maxproc
        elif nproc < 0:
            nproc = maxproc + nproc
            if nproc < 1:
                nproc = 1

    return nproc

# End
