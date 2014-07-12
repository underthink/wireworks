__author__ = 'rob'

from threading import local


_event_threadlocal = local()


def set_current_event(event):
    _event_threadlocal.event = event


def clear_current_event():
    del _event_threadlocal.event


def current_event():
    try:
        return _event_threadlocal.event
    except AttributeError:
        raise ValueError("No event is currently available. current_event() should only be used from a method that "
                         "has been invoked as part of an event dispatch.")