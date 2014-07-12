from __future__ import print_function

from wireworks.dispatcher import Dispatcher
from wireworks.util.callable_references import StrongCallableReference, WeakCallableReference
from wireworks.util.globbable_dict import GlobbableDict

__author__ = 'rob'

import inspect
import logging


class Registry(Dispatcher):
    _LOG = logging.getLogger("wireworks.registry")

    def __init__(self):
        self._glob_dict = GlobbableDict(default_factory=lambda: set())
        self._pending_instance_wiring = {}

        super(Registry, self).__init__(self._glob_dict)

    def wire_class_instances(self, cls):
        old_init = None
        if hasattr(cls, '__init__'):
            old_init = cls.__init__

        def new_init(inst_self, *args, **kwargs):
            old_rval = None
            if old_init:
                old_rval = old_init(inst_self, *args, **kwargs)

            for _, method in inspect.getmembers(inst_self, lambda mem: inspect.ismethod(mem)):
                method_func = method.im_func
                if method_func in self._pending_instance_wiring:
                    wiring_attrs = self._pending_instance_wiring[method_func]
                    self.register(fn=method, **wiring_attrs)

            return old_rval

        setattr(cls, '__init__', new_init)
        return cls

    def wire(self, pattern, strongly_reference=False):
        def decorator(fn):
            self.register(pattern, fn, strongly_reference)
            return fn
        return decorator

    def wire_instance_method(self, pattern, strongly_reference=False):
        def decorator(fn):
            self._pending_instance_wiring[fn] = {'pattern': pattern, 'strongly_reference': strongly_reference}
            return fn
        return decorator

    def register(self, pattern, fn, strongly_reference=False):
        if strongly_reference:
            p_callable_ref = StrongCallableReference(fn)
        else:
            p_callable_ref = WeakCallableReference(fn, lambda del_proxy: self._unregister_proxy(pattern, del_proxy))

        Registry._LOG.debug("Adding callable %s for pattern %s" % (p_callable_ref, pattern))
        self._glob_dict[pattern].add(p_callable_ref)

    def _unregister_proxy(self, pattern, callable_proxy):
        # in the common case, we should (obviously) always have a reference to both self and Registry. However,
        # if the vm is shutting down, then we may get a callback as stuff starts to get dereferenced, but
        # _our_ classes are not guarenteed to be around. if so, do the best we can given what we've got left.
        if Registry:
            Registry._LOG.debug("Unregistering proxy %s for pattern %s" % (callable_proxy, pattern))
        if self:
            self._glob_dict[pattern].remove(callable_proxy)


a = Registry()

logging.basicConfig(level=logging.DEBUG)


@a.wire("foo.bar")
def ca(aa, b):
        print("i sez: " + aa + b)

@a.wire("foo.baz")
def cb(aa, b):
    print("you sez: " + aa + b)

@a.wire_class_instances
class X(object):
    def __init__(self, name):
        self._name = name

    def __del__(self):
        print("going")

    @a.wire_instance_method("foo.inner", strongly_reference=False)
    def ina(self, aa, b):
        print("inst: " + aa + b + " from " + self._name)


def inner():
    @a.wire("foo.moo")
    def bla(aa, b):
        print("whatevs: " + aa + b)

    a.with_filter("foo.*").call("x", "y")


if __name__ == "__main__":
    x_ref = X('a')
    y_ref = X('b')
    x_ref.ina("For", " Dave")
    inner()

    dispatcher = a.with_filter("foo.*")
    dispatcher.call("hello", "world")

    print("done")