__author__ = 'rob'

from concurrent.futures import Executor, Future


class SynchronousExecutor(Executor):
    """
    Basic Executor implementation that executes tasks synchronously. This lets us use a consistent interface
    to invoke callables and handle the result.

    It does seem a bit silly though.
    """
    def submit(self, fn, *args, **kwargs):
        """
        Submits and immediately executes (in the same thread) the function call

        Returns:
            A Future representing the given call.
        """
        future = Future()

        try:
            result = fn(*args, **kwargs)
        except BaseException as e:
            future.set_exception(e)
        else:
            future.set_result(result)

        return future