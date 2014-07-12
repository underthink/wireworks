from wireworks.util.synchronous_executor import SynchronousExecutor
from wireworks.event import Event

__author__ = 'rob'

_DEFAULT_SYNCHRONOUS_EXECUTOR = SynchronousExecutor()


class Dispatcher(object):
    def __init__(self, glob_dict, pattern="*", executor=_DEFAULT_SYNCHRONOUS_EXECUTOR):
        self._executor = executor
        self._pattern = pattern
        self._dispatcher_glob_dict = glob_dict

    def call(self, *args, **kwargs):
        event = Event(self._all_matching_callables(), self._executor)
        event.go(*args, **kwargs)

        return event

    def with_filter(self, pattern):
        return Dispatcher(self._dispatcher_glob_dict, pattern, self._executor)

    def with_executor(self, executor):
        return Dispatcher(self._dispatcher_glob_dict, self._pattern, executor)

    def _all_matching_callables(self):
        refs = [item for this_set in self._dispatcher_glob_dict.glob(self._pattern) for item in this_set]
        potential_callables = [item.get_callable() for item in refs]
        return [real_callable for real_callable in potential_callables if real_callable]