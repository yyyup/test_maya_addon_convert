"""Python profiling tools"""
import cProfile
import os
import sys
import timeit
from zoo.core.util import zlogging
from zoo.core.util import filesystem
from functools import wraps

logger = zlogging.zooLogger


if sys.version_info[0] > 3:
    def _getFuncName(func):
        return func.func_name
else:
    def _getFuncName(func):
        return func.__name__


def profileit(name):
    """cProfile decorator to profile said function, must pass in a filename to write the information out to
    use RunSnakeRun to run the output

    :param name: The output file path
    :type name: str
    :return: Function
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            prof = cProfile.Profile()
            retval = prof.runcall(func, *args, **kwargs)
            absPath = os.path.expanduser(os.path.expandvars(name))
            filesystem.ensureFolderExists(os.path.dirname(absPath))
            # Note use of name from outer scope
            prof.dump_stats(absPath)
            return retval

        return wrapper

    return inner


def fnTimer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = timeit.default_timer()
        result = function(*args, **kwargs)
        t1 = timeit.default_timer()
        logger.debug("Total time running {}: {} seconds".format(".".join((function.__module__, _getFuncName(function))),
                                                                str(t1 - t0)))
        return result

    return function_timer
