import sys
import signal


class ProcessSafeExit(Exception):
    '''
    A safe sigterm exception to avoid deadlock in multiprocessing
    Example:
        lock.acquire()
        try:
            ... # if sigterm happens here
        except ProcessSafeExit:
            lock.release() # release the lock before process terminates
    '''
    pass


def process_safe_func(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except ProcessSafeExit:
        sys.exit(0)


def signal_handler(signum, frame):
    raise ProcessSafeExit()


signal.signal(signal.SIGTERM, signal_handler)
