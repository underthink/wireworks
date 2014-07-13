__author__ = 'rob'

import time
import unittest

from collections import namedtuple
from concurrent.futures import Executor, Future

from wireworks.event import Event


class TestExecutor(Executor):
    SeenSubmission = namedtuple("SeenSubmission", ['id', 'args', 'kwargs'])

    def __init__(self):
        self._seen = []
        self._count = 0
        self._futures = []

    def get_seen_submissions(self):
        return self._seen

    def set_futures_to_return(self, futures):
        self._futures = list(futures)

    def make_expected_function_call(self, future=None):
        this_id = self._count

        def exc_fn(*args, **kwargs):
            self._seen.append({'id': this_id, 'args': list(args), 'kwargs': kwargs})

        if not future:
            future = Future()

        self._futures.append(future)
        self._count += 1

        return exc_fn

    def verify_calls(self, testcase, expected_args, expected_kwargs):
        testcase.assertEqual(len(self._seen), self._count, "Unexpected number of calls")

        for i in range(0, self._count):
            call = self._seen[i]
            testcase.assertEqual(i, call['id'], "Function appears to have been submitted out of order")
            testcase.assertListEqual(expected_args, call['args'], "Function args do not match expected")
            testcase.assertDictEqual(expected_kwargs, call['kwargs'], "Function kwargs do not match expected")

    def submit(self, fn, *args, **kwargs):
        fn(*args, **kwargs)
        return self._futures.pop(0) if self._futures else Future()


class EventTests(unittest.TestCase):
    def setUp(self):
        self._exec = TestExecutor()

    def _make_event(self, callables):
        return Event(callables, self._exec)

    def test_submit_calls_using_executor(self):
        """Check that multiple functions are passed to the associated executor correctly, and in order."""

        fn1 = self._exec.make_expected_function_call()
        fn2 = self._exec.make_expected_function_call()
        args = [1, 'a', 2, None]
        kwargs = {'one': 2, 'three': 'four'}

        self._make_event([fn1, fn2]).go(*args, **kwargs)
        self._exec.verify_calls(self, args, kwargs)

    def test_try_cancel(self):
        """Check that a cancel call will cancel all pending tasks if possible. """

        event_prx = [None]

        def first():
            event_prx[0].try_cancel_pending_calls()

        def second():
            self.fail("Second call should have been cancelled")

        event_prx[0] = self._make_event([first, second])
        event_prx[0].go()

    def test_get_all_futures(self):
        """Test that 'get all futures' does what the name heavily implies"""

        futures = [Future(), Future()]

        fn1 = self._exec.make_expected_function_call()
        fn2 = self._exec.make_expected_function_call()

        self._exec.set_futures_to_return(futures)
        evt = self._make_event([fn1, fn2]).go()

        self.assertListEqual(futures, evt.get_all_futures(), "Not all futures were returned")

    def test_multiple_gos_not_allowed(self):
        """Test that an event dispatch can't be started twice"""

        evt = self._make_event([])
        evt.go()
        self.assertRaises(ValueError, evt.go)

    def test_first_return_value(self):
        """Test that the value from the first returned non-cancelled future is returned"""

        future1 = Future()
        future2 = Future()
        future3 = Future()

        evt = self._make_event([self._exec.make_expected_function_call(future1),
                                self._exec.make_expected_function_call(future2),
                                self._exec.make_expected_function_call(future3)])
        evt.go()

        start = time.time()
        self.assertIsNone(evt.first_result(1), "No completed futures, yet something returned")
        duration = time.time() - start
        # This one might be a bit too dependent on where the test is running. let's see how it goes...
        self.assertAlmostEqual(1.0, duration, msg="Incorrect timeout duration", delta=0.5)

        future1.cancel()

        self.assertIsNone(evt.first_result(0), "One (ignored) cancelled future, yet something returned")

        future3.set_result("WOOT")

        self.assertEquals("WOOT", evt.first_result(0), "Future completed, yet value not returned")

    def test_first_returned_value_raises_exceptions(self):
        """Test that if an exception is raised by the first future to complete, that is re-thrown"""

        future1 = Future()

        evt = self._make_event([self._exec.make_expected_function_call(future1)])
        evt.go()

        future1.set_exception(KeyError())

        self.assertRaises(KeyError, lambda: evt.first_result(0))

    def test_await_all_futures(self):
        """Test that the await_all_futures call will return all complete, non-cancelled futures"""

        future1 = Future()
        future2 = Future()

        evt = self._make_event([self._exec.make_expected_function_call(future1),
                                self._exec.make_expected_function_call(future2)])
        evt.go()

        self.assertListEqual([], evt.await_all(0), "No ready futures, but something returned")

        future1.cancel()
        future2.set_result("WOOT")

        self.assertListEqual([future2], evt.await_all(0), "Single future was not returned after cancel/complete")
