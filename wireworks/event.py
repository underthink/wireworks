__author__ = 'rob'

from wireworks.static_utilities import set_current_event, clear_current_event

from concurrent.futures import wait as futures_wait, FIRST_COMPLETED, ALL_COMPLETED


class Event(object):
    """An object representing a dispatched Event.

    Essentially, this class generates normal Python `Futures`, so any of the standard utilities and approaching them
    are valid (concurrent.futures.wait, etc). The raw futures are accessable using the `get_all_futures` method.

    Alternatively, there are various convienience methods to handle some of the common cases. Unless otherwise
    specified, these methods will filter out cancelled methods.
    """
    def __init__(self, calls, executor):
        self._calls = calls
        self._executor = executor
        self._cancelled = False
        self._dispatch_started = False
        self._futures = []
        self._completed_futures = []
        self._unexecuted = []

    def go(self, *args, **kwargs):
        """Starts all pending calls for the registered event.

        Largely for internal use. If called more than once, subsequent invocations will cause a ValueError to happen.

        :param args:    The set of args to pass to each callable
        :param kwargs:  The set of kwargs to pass to each callable.
        """
        if self._dispatch_started:
            raise ValueError("The dispatch has already started.")

        self._dispatch_started = True

        for one_callable in self._calls:
            if self._cancelled:
                self._unexecuted.append(one_callable)
                continue

            def shim():
                set_current_event(self)
                try:
                    return one_callable(*args, **kwargs)
                finally:
                    clear_current_event()

            future = self._executor.submit(shim)
            future.add_done_callback(self._handle_complete)
            self._futures.append(future)

    def try_cancel_pending_calls(self, future):
        """Attempt to cancel all pending calls, where possible.

        Attempts to cancel calls by indicating that no further executor submissions should happen (which may be
        optimistic if they're going to a threadpool), and by attempting to cancel all thrown Futures. As those
        comments imply, there's no guarantee that anything will *actually* be cancelled when calling this.
        """
        self._cancelled = True

        [future.cancel() for future in self._futures]

    def get_all_futures(self):
        """Get a list of all Futures known to this Event.

        :return:    The list of Futures
        """
        return self._futures

    def get_completed_futures(self):
        """Get all Futures that have currently completed, one way or another.

        :return:    The list of completed Futures
        """
        return self._completed_futures

    def first_result(self, timeout=None):
        """Await, and return, the first result from the set of known futures.

        If an Exception was thrown by the completed Future, this will be thrown instead.

        :param timeout: Amount of time to wait in seconds before giving up and returning what we got until then
        :return:        The value returned by the first future to finish, or None if no futures completed successfully
        """
        possible = self._futures
        while possible:
            (done, possible) = futures_wait(self._futures, timeout=timeout, return_when=FIRST_COMPLETED)
            for future in done:
                if not future.cancelled():
                    return future.result(0)

        return None

    def await_all(self, timeout=None):
        """Await all known futures completion.

        All completed futures are then returned. Unlike `first_result`, this method doesn't try to return
        the result or throw any exceptions.

        :param timeout: Amount of time to wait in seconds before giving up and returning what we got until then
        :return:        All futures that have completed and were not cancelled
        """
        (done, possible) = futures_wait(self._futures, timeout=timeout, return_when=ALL_COMPLETED)
        return [future for future in done if not future.cancelled()]

    def _handle_complete(self, future):
        self._completed_futures.append(future)