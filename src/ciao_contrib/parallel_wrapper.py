#
#  Copyright (C) 2011, 2015, 2016, 2019-2024
#                Smithsonian Astrophysical Observatory
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

"""
Test routines for taking advantage of multiple processors.
This is a slightly different approach to that provided by
sherpa.utils.parallel_map and is provided for testing. Please
be aware that at present this code has seen limited testing and
has no guarantee of stability.

Sherpa's parallel_map splits up the work load at creation time and
farms off a set of tasks to each processor. Here we use a pool of jobs,
with each worker extracting the next job when it is free.

See, amongst others:

http://docs.python.org/library/multiprocessing.html

http://www.bryceboe.com/2010/08/26/python-multiprocessing-and-keyboardinterrupt/

"""

import time
import signal
import multiprocessing
from queue import Empty

import concurrent.futures, os, sys, shutil, itertools, curses # for parallel_pool_futures and progress bars

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


def parallel_pool(func, args, ncores=None, context='fork'):
    """Process func in parallel, once for each argument in args.

    func takes a single parameter, so you will normally need to write
    a wrapper routine something like the following, and use it as an
    argument to parallel_pool.

      def wrapper(arg):
          actual_func(*arg)

    One issue with this design is that it does not support keyword
    arguments.

    If ncores is None then uses multiprocessing.cpu_count().

    The context argument decides how, when multiprocessing is in use,
    the multiprocessing is run.

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

    v3(f"# Parallel processing: {narg} processes with {nc} cores")
    v3(f"#   with multiprocessing context: {context}")
    ctx = multiprocessing.get_context(context)

    job_queue = ctx.Queue()
    result_queue = ctx.Queue()

    for i, arg in enumerate(args):
        job_queue.put((i, arg))

    stime = time.localtime()
    v4("# Parallel start time: {0}".format(time.asctime(stime)))

    workers = []
    for i in range(nc):
        v5("# Starting parallel worker: {0}".format(i + 1))
        w = ctx.Process(target=task,
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



def parallel_pool_futures(func, args, ncores=None, maxitersize=512, chunksize=None, context='fork', progress=False, progress_prefix=""):
    """
    Process func in parallel asynchronously, with pool managed by
    'concurrent.futures'.  Usage is essentially identical to 'parallel_map'
    and 'parallel_futures'.  A function that runs with parallel_pool_futures
    will run with parallel_pool and parallel_map, but the reverse is not
    necessarily true, since concurrent.futures cannot support passing
    non-picklable objects.

    For example, a tempfile.NamedTemporaryFile file object or curses window
    cannot be directly referenced through parallel_pool_futures as an argument
    variable, but a tempfile.NamedTemporaryFile.name() string can be referenced.

    Another issue is that concurrent.futures executor 'submit' cannot handle
    inner/nested functions, and scripts should be written accordingly.

    If 'ncores' is None then uses multiprocessing.cpu_count().

    The 'context' argument decides how, when multiprocessing is in use,
    the multiprocessing is run.

    The 'maxitersize' is the maximum number of processes to execute and
    let concurrent.futures to automatically manage before letting
    parallel_pool_futures take over management to help avoid using up
    system memory; the default is 512. 'chunksize' is number of processes
    to manage at a time, when 'chunksize=None', the value is then
    multiprocessing.cpu_count()**2; a poor 'maxitersize' and 'chunksize'
    combination can lead to significantly poorer performance than running
    the function in serial through a loop.

    The 'progress' argument will print a progress bar showing as the list
    of processes are completed and the 'progress_prefix' can be a string
    displayed before the progress bar describing the task being handled.

    The return value is an array of the return values of func,
    in the order of the args array.

    """

    ### based on https://alexwlchan.net/2019/10/adventures-with-concurrent-futures/ ###

    ctx = multiprocessing.get_context(context)

    if ncores is None:
        nc = ctx.cpu_count()
    else:
        nc = ncores

    if nc < 1 and ctx.get_context()._name == "fork":
        context = "spawn"
        ctx = multiprocessing.get_context(context)
        nc = ctx.cpu_count()


    narg = len(args)
    if nc > narg:
        nc = narg

    out = [None] * narg


    v3(f"# Parallel processing: {narg} processes with {nc} cores")
    v3(f"#   with multiprocessing context: {context}")


    # setup ProcessPoolExecutor arguments
    executor_kw = {"mp_context" : ctx}

    # https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor
    if nc > 61:
        executor_kw["max_workers"] = nc

    if chunksize is None:
        chunksize = nc**2


    # check character type to use with progressbar if it will be used
    if progress:
        stat_unicode = _use_unicode()


    ### Note: do not pass an unpickle-able object as an input argument (e.g. tempfile object) ###
    ### Note: this approach does not always handle local functions defined within a function well ###

    with concurrent.futures.ProcessPoolExecutor(**executor_kw) as executor:
        try:
            if narg <= maxitersize:
                future_task = {executor.submit(func,arg): (i,arg) for i,arg in enumerate(args)}

                if progress:
                    for future in progressbar_mp(concurrent.futures.as_completed(future_task),
                                                 narg,prefix=progress_prefix,isfutures=False,
                                                 use_unicode=stat_unicode):
                        i,arg = future_task[future]
                        out[i] = future.result()

                else:
                    for future in concurrent.futures.as_completed(future_task):
                        i,arg = future_task[future]
                        out[i] = future.result()

            else:
                args_enum_gen = ((i,arg) for i,arg in enumerate(args))

                future_task = {executor.submit(func,arg): (i,arg) for i,arg in itertools.islice(args_enum_gen, chunksize)}

                donelen = []

                while future_task:
                    done,_ = concurrent.futures.wait(future_task,return_when=concurrent.futures.FIRST_COMPLETED)

                    for future in done:
                        i,arg = future_task.pop(future)
                        out[i] = future.result()

                    if progress:
                        donelen.append(len(done))

                        [*progressbar_mp(donelen,
                                         narg,prefix=progress_prefix,isfutures=True,
                                         use_unicode=stat_unicode)]

                    # re-fill processor executor queue as jobs are completed
                    for i,arg in itertools.islice(args_enum_gen, len(done)):
                        future = executor.submit(func,arg)
                        future_task[future] = (i,arg)

        except Exception as emsg:
            raise(emsg)

    return out



def _check_tty():
    # ### python throws NameError; ipython returns "TerminalInteractiveShell'; ###
    # ### Jupyter Notebook returns "ZMQIteractiveShell"                        ###
    #
    # try:
    #     check_ipython = get_ipython().__class__.__name__
    #     tty = os.itatty()
    # except NameError:
    #     tty = os.itatty()

    try:
        tty = os.isatty(sys.stdout.fileno())

    except (IOError,NameError,AttributeError):
        # Jupyter notebooks does not use TTY, but can
        # be printed to, but will throw a warning and print
        # to new line if data stream rate exceeded.  Some
        # newer versions of Jupyter will return True with os.isatty
        # rather than throwing an exception

        tty = True

    return tty



def _use_unicode():
    """
    determine whether or not unicode symbols can be used in
    the terminal shell.  This is especially problematic if
    using XQuartz directly (rather than the Terminal app) on
    MacOS, since while unicode is supported, the necessary
    environment variables are not set to correctly use the
    symbols.

    For example, using `locale` to determine the associated
    variables, (don't explicitly set $LC_ALL), unicode support
    can be activated in XQuartz by setting:

    (t)csh:
    setenv LANG 'en_US.UTF-8'
    setenv LC_CTYPE 'en_US.UTF-8'
    setenv LC_COLLATE 'en_US.UTF-8'
    setenv LC_MESSAGES 'en_US.UTF-8'
    setenv LC_MONETARY 'en_US.UTF-8'
    setenv LC_NUMERIC 'en_US.UTF-8'
    setenv LC_TIME 'en_US.UTF-8'
    setenv LC_ALL ''

    bash/zsh:
    export LANG='en_US.UTF-8'
    export LC_CTYPE='en_US.UTF-8'
    export LC_COLLATE='en_US.UTF-8'
    export LC_MESSAGES='en_US.UTF-8'
    export LC_MONETARY='en_US.UTF-8'
    export LC_NUMERIC='en_US.UTF-8'
    export LC_TIME='en_US.UTF-8'
    export LC_ALL=''
    """

    status = []

    try:
        ctype = os.environ["LC_CTYPE"]

        if "." and "_" in ctype:
            status.append(True)

    except KeyError:
        status.append(False)

    try:
        lang = os.environ["LANG"]

        if lang.upper() not in ["C","POSIX"]:
            status.append(True)

    except KeyError:
        status.append(False)

    if True not in status:
        return False

    return True



def _show(j, count, size, prefix="", out=sys.stdout, use_unicode=False,
          use_curses=False, curses_pbarnum=1, printqueue=None, curses_win=None):
    ### based on https://stackoverflow.com/a/34482761 ###

    if not use_curses:
        x = int(size*j/count)

        if use_unicode:
            print("{0}[{1}{2}] {3}/{4}".format(prefix, u"\N{Full block}"*x, "."*(size-x), j, count), end='\r', file=out, flush=True) # print unicode "Full block"=u"\u2588"
        else:
            print(f"{prefix}[{'#'*x}{('.'*(size-x))}] {j}/{count}", end='\r', file=out, flush=True) # print '#'

    else:
        # curses windowcoordinates have (0,0) at the upper-left corner
        # of the terminal, max number of rows and lines are the terminal
        # values-1.
        #
        # curses.newwin(nrows, ncols, begin_y, begin_x)

        count_strlen = len(str(count))

        size -= 1
        x = int(size*j/count)

        ## pad j with 0 by either: f"{j:0{count_strlen}}" or f"{j}".rjust(count_strlen,"0") ##
        j = f"{j}".rjust(count_strlen," ")

        str_y = 2*(curses_pbarnum-1) + 1
        str_x = 0

        if use_unicode:
            pbarstr = (str_y,str_x,"{0}[{1}{2}] {3}/{4}\r".format(prefix, u"\N{Full block}"*x, "."*(size-x), j, count)) # print unicode "Full block"=u"\u2588"
        else:
            pbarstr = (str_y,str_x,f"{prefix}[{'#'*x}{('.'*(size-x))}] {j}/{count}\r") # print '#'

        printqueue.put(pbarstr,block=True)

        if use_curses and curses_pbarnum == 1 and int(j) > 0:
            while not printqueue.empty():
                try:
                    curses_win.addstr(*printqueue.get(block=True))
                except Empty:
                    pass

            curses_win.refresh()



def progressbar_iter(iterfunc, count=None, prefix="", size=60, out=sys.stdout, use_unicode=False,
                     use_curses=False, curses_pbarnum=1, printqueue=None): # Python3.6+
    """
    Display progress bar when used with an iterator; generators will need to listed, for example:

    for i in progressbar_iter(range(100), count=100, prefix="calculating func:"):
        func(i)

    #########################################################################

    Making use of curses, for example when running chunks of stacks of image arithemetic in parallel
    and want to monitor to progress of each chunk, will want to take advantage of curses_wrapper and
    requires multiple wrapper functions that will be executed in main().

    def func_with_progressbar(args):
        n,imgstk,printqueue,prefix = args

        img_stklen = len(imgstk)
        stat_unicode = _use_unicode()

        for i in progressbar_iter(range(img_stklen),img_stklen,prefix=f"{prefix} {n+1}:",
                                  use_unicode=stat_unicode,use_curses=True,
                                  curses_pbarnum=n+1,printqueue=printqueue):
            try:
                cr = pcr.read_file(imgstk[i])

                if i > 0:
                    combine_imgvals += pcr.copy_piximgvals(cr)
                else:
                    combine_imgvals = pcr.copy_piximgvals(cr)

            except Exception as emsg:
                raise RuntimeError(emsg)

        return combine_imgvals


    def func(curses_screen,stklist):
        if curses_screen is None or not isinstance(curses_screen,curses.window):
            raise AttributeError("A curses screen needs to be defined.")

        ncore = multiprocessing.cpu_count()
        datachunks = [*enumerate([stklist[i::ncore] for i in range(ncore)])]
        curses_prefix = "stacking image chunk"

        curses_screen.erase()

        for i in range(ncore):
            # provide label for each progress bar
            curses_screen.addstr(2*i+1,0,f"{curses_prefix} {i+1}:\r")

        curses_screen.refresh()

        printqueue = multiprocessing.Manager().Queue()
        datachunks = [(i,v,printqueue,curses_prefix) for i,v in datachunks]

        try:
            image_chunks = parallel_pool_futures(func_with_progressbar,datachunks,progress=False)

        except Exception as emsg:
            raise RuntimeError(emsg)

        out_arr = numpy.sum(image_chunks, axis=0)

        return out_arr


    def func_wrapper(stdscr,stklist):
        stdscr = curses.initscr()
        stdscr.erase()
        stdscr.refresh()

        out = func(stdscr,stklist)

        return out


    def main(...):

        ...

        cr = curses.wrapper(func_wrapper,stklist)

        ...

    """

    status_tty = _check_tty()

    if status_tty:
        termwidth = shutil.get_terminal_size().columns
        termlines = shutil.get_terminal_size().lines
        nwin = None

        if count is None:
            count = len(iterfunc)

        if use_curses:
            if not isinstance(printqueue,multiprocessing.managers.BaseProxy):
                raise ValueError("'printqueue' requires a multiprocessing.Manager().Queue()")

            termwidth -= 1
            termlines -= 1

            if curses_pbarnum == 1:
                nwin = curses.newwin(termlines,termwidth)

        if termwidth <= size + 4 + len(prefix) + 2*len(str(count)):
            size = int(termwidth - 4 - len(prefix) - 2*len(str(count)))

        _show(0,count,size,prefix=prefix,use_unicode=use_unicode,
              use_curses=use_curses,curses_pbarnum=curses_pbarnum,
              printqueue=printqueue)

        for i, item in enumerate(iterfunc):
            yield item

            _show(i+1,count,size,prefix=prefix,use_unicode=use_unicode,
                  use_curses=use_curses,curses_pbarnum=curses_pbarnum,
                  printqueue=printqueue,curses_win=nwin)

        if not use_curses:
            print("\n", flush=True, file=out)

    else:
        for i, item in enumerate(iterfunc):
            yield item



def progressbar_futures(setfunc, count=None, prefix="", size=60, out=sys.stdout, use_unicode=False,
                        use_curses=False, curses_pbarnum=1,  printqueue=None): # Python3.6+
    """
    display progress bar when used in tandem with concurrent.futures.wait in 'parallel_pool_futures'
    as the pool gets repopulated by the function if 'maxitersize' is exceeded.
    """

    iterset = list(setfunc)

    status_tty = _check_tty()

    if status_tty:

        termwidth = shutil.get_terminal_size().columns
        termlines = shutil.get_terminal_size().lines
        nwin = None

        if count is None:
            count = len(iterset)

        if use_curses:
            if not isinstance(printqueue,multiprocessing.managers.BaseProxy):
                raise ValueError("'printqueue' requires a multiprocessing.Manager().Queue()")

            termwidth -= 1
            termlines -= 1

            if curses_pbarnum == 1:
                nwin = curses.newwin(termlines,termwidth)

        if termwidth <= size + 4 + len(prefix) + 2*len(str(count)):
            size = int(termwidth - 4 - len(prefix) - 2*len(str(count)))

        complete = 0
        #show(complete)

        while complete < count:
            complete = sum(setfunc)

            _show(complete,count,size,prefix=prefix,use_unicode=use_unicode,
                  use_curses=use_curses,curses_pbarnum=curses_pbarnum,
                  printqueue=printqueue,curses_win=nwin)

            return setfunc

        if not use_curses:
            print("\n", flush=True, file=out)

    else:
        return setfunc



def progressbar_mp(arr, count=None, prefix="", size=60, out=sys.stdout,
                   isfutures=False, use_unicode=False,
                   use_curses=False, curses_pbarnum=1, printqueue=None):

    """
    generalized progressbar function based on 'progressbar_iter' and
    'progressbar_futures'.  If 'isfutures=True', then this function should
    be called as `[*progressbar_mp(...)]` in script.
    """

    status_tty = _check_tty()

    if status_tty:
        if count is None:
            if isfutures:
                count = len(list(arr))
            else:
                count = len(arr)

        termwidth = shutil.get_terminal_size().columns
        termlines = shutil.get_terminal_size().lines
        nwin = None

        if use_curses:
            if not isinstance(printqueue,multiprocessing.managers.BaseProxy):
                raise ValueError("'printqueue' requires a multiprocessing.Manager().Queue()")

            termwidth -= 1
            termlines -= 1

            if curses_pbarnum == 1:
                nwin = curses.newwin(termlines,termwidth)

        if termwidth <= size + 4 + len(prefix) + 2*len(str(count)):
            size = int(termwidth - 4 - len(prefix) - 2*len(str(count)))

        if not isfutures:
            ### https://stackoverflow.com/a/34482761 ###

            _show(0,count,size,prefix=prefix,use_unicode=use_unicode,
                  use_curses=use_curses,curses_pbarnum=curses_pbarnum,
                  printqueue=printqueue)

            for i,item in enumerate(arr):
                yield item

                _show(i+1,count,size,prefix=prefix,use_unicode=use_unicode,
                      use_curses=use_curses,curses_pbarnum=curses_pbarnum,
                      printqueue=printqueue,curses_win=nwin)

        else:
            ### will need to call as `[*progressbar_mp(...)]` in script ###
            ### since the 'yield' above causes this to be a generator   ###

            complete = 0

            while complete < count:
                complete = sum(arr)

                _show(complete,count,size,prefix=prefix,use_unicode=use_unicode,
                      use_curses=use_curses,curses_pbarnum=curses_pbarnum,
                      printqueue=printqueue,curses_win=nwin)

                return arr

        if not use_curses:
            print("\n", flush=True, file=out)

    else:
        if not isfutures:
            for i,item in enumerate(arr):
                yield item
        else:
            return arr
