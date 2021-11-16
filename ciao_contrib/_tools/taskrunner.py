#
# Copyright (C) 2012, 2015, 2016, 2019, 2020, 2021
# Smithsonian Astrophysical Observatory
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

Changes in multiprocessing in Python 3.8 means that on macOS the
spawn method is used by default. This gives subtly-different results
(e.g. screen output is different) so we attempt to force the fork
style approach, but this is dangerous.

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

        v3(f"TaskRunner: adding task {name}")

        if not hasattr(func, "__call__"):
            raise ValueError(f"The function for task {name} is not callable")

        if self._seen(name):
            raise ValueError(f"Task {name} has already been added to this runner")

        for pname in preconditions:
            if not self._seen(pname):
                raise ValueError(f"Precondition {pname} of task {name} has not been added to this runner")

        # Ideally this should not happen but just in case I forget
        # and use a data type that can't be serialized
        try:
            pickle.dumps(name)
            pickle.dumps(func)
            pickle.dumps(args)
            pickle.dumps(kwargs)
        except pickle.PicklingError:
            raise ValueError(f"Internal error: unable to serialize arguments for task={name}")

        self._torun[name] = (name, preconditions, func, args, kwargs)
        self._names.add(name)
        v3(f"TaskRunner: task {name} has been added to the queue.")

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

        v3(f"TaskRunner: adding barrier {name}")
        if self._seen(name):
            raise ValueError(f"Task {name} has already been added to this runner")

        for pname in preconditions:
            if not self._seen(pname):
                raise ValueError(f"Precondition {pname} of the barrier {name} has not been added to this runner")

        try:
            pickle.dumps(name)
            pickle.dumps(msg)
        except pickle.PicklingError:
            raise ValueError(f"Internal error: unable to serialize arguments for task={name}")

        self._torun[name] = (name, preconditions, msg)
        self._names.add(name)

    def run_tasks(self, processes=None, label=True, context='fork'):
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

        The context argument decides how, when multiprocessing is
        in use, the multiprocessing is run.
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
            f(f"Running tasks in parallel with {processes} processors.")
            self._run_parallel(processes, context=context)

        self._clean()

    def _run_parallel(self, processes, context='fork'):
        "Run the tasks in parallel"

        stime = time.localtime()
        v4(f"TaskRunner (parallel, processes={processes}): started {time.asctime(stime)}")

        ntasks = len(self._torun)
        finished = set()

        ctx = multiprocessing.get_context(context)

        class TaskHandler(ctx.Process):
            """A worker that waits for tasks from the
            task queue, runs it, then sends the name of
            the task to the results queue once finished.

            Does this need to be derived from ctx.Process>
            """

            def __init__(self, task_queue, result_queue):
                ctx.Process.__init__(self)
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
                        v3(f"TaskHandler {name} retrieved taskinfo={taskinfo}")

                        if taskinfo is None:
                            v3(f"TaskHandler {name} told to quit")
                            self.task_queue.task_done()
                            break

                        elif len(taskinfo) == 4:
                            v3(f"TaskHandler {name} running taskinfo={taskinfo}")
                            (taskname, func, args, kwargs) = taskinfo
                            try:
                                v3(f"TaskHandler {name} starting task {taskname}")
                                func(*args, **kwargs)
                                v3(f"TaskHandler {name} finshed task {taskname}")
                            except BaseException as be:
                                v3(f"TaskHandler {name} task {taskname} - caught exception {type(be)}/{be}")
                                self.task_queue.task_done()
                                self.result_queue.put((True, be))
                                break

                        elif len(taskinfo) == 2:
                            v3(f"TaskHandler {name} sent barrier: {taskinfo}")
                            (taskname, taskmsg) = taskinfo
                            if taskmsg is not None:
                                v1(taskmsg)

                        else:
                            v3(f"TaskHandler {name} sent invalid taskinfo={taskinfo}")
                            self.task_queue.task_done()
                            self.result_queue.put((True,
                                                   ValueError(f"Task queue argument: {taskinfo}")))
                            break

                        v3(f"TaskHandler {name} reporting that task={taskname} is finished.")
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
                    v3(f"TaskHandler {name} - caught exception {type(be)}/{be}")
                    self.result_queue.put((True, be))  # possibly excessive

                v3(f"TaskHandler {name} exiting.")

        queue = ctx.Queue()
        task_queue = ctx.JoinableQueue()

        # what tasks can be run now?
        deltasks = []
        for v in self._torun.values():
            name = v[0]
            preconditions = v[1]
            if len(preconditions) > 0:
                continue

            deltasks.append(name)
            if len(v) == 3:
                v3(f"TaskRunner: selected barrier {name}")
                taskarg = (name, v[2])
            elif len(v) == 5:
                v3(f"TaskRunner: selected task {name}")
                taskarg = (name, v[2], v[3], v[4])
            else:
                raise ValueError(f"Internal error: task info = {v}")

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
        v4(f"TaskRunner (parallel, processes={processes}): starting workers")
        workers = [TaskHandler(task_queue, queue)
                   for i in range(processes)]

        for w in workers:
            w.start()

        # Look for jobs that have finished and see
        # if any new ones can be started. Once all
        # the jobs have ended close down the workers.
        #
        v4(f"TaskRunner (parallel, processes={processes}): waiting for jobs")
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

            v4(f"TaskRunner: received result from task {taskout}")

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
                    v3(f"TaskRunner: selected barrier {name}")
                    taskarg = (name, v[2])
                elif len(v) == 5:
                    v3(f"TaskRunner: selected task {name}")
                    taskarg = (name, v[2], v[3], v[4])
                else:
                    raise ValueError(f"Internal error: task info = {v}")

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
        v4(f"TaskRunner (parallel, processes={processes}): stopped {time.asctime(etime)}")

    def _run_serial(self):
        "Run the tasks in serial"

        stime = time.localtime()
        v4(f"TaskRunner (serial): started {time.asctime(stime)}")

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
                    v3(f"TaskRunner (serial): running barrier {name}")
                    if v[2] is not None:
                        v1(v[2])

                elif len(v) == 5:
                    v3(f"TaskRunner (serial): running task {name}")
                    v[2](*v[3], **v[4])

                else:
                    raise ValueError(f"Internal error: task info={v}")

                deltask = name
                break

            if deltask is None:
                raise ValueError(f"Unable to find any task to run from {self._torun}")

            finished.add(deltask)
            del self._torun[deltask]

        etime = time.localtime()
        v4(f"TaskRunner (serial): stopped {time.asctime(etime)}")


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
            raise ValueError(f"nproc arument must be an integer, sent {nproc}")

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
