__author__ = 'rob'

from functools import partial
from weakref import ref


class StrongCallableReference(object):
    """A class to represent a strong ref to a callable. The callable can't be gc'd while this class is still referenced.

    A strong reference to some kind of callable object. This class is exactly as simple as you'd expect it to be;
    it exists largely to provide a consistent interface to other parts of the application that have to deal
    with these things.

    The docs for get_callable() say this may return None. That needs to be true to provide a consistent contract,
    but practially the only way you'll a None out is if you put a None in, and that's your own fault really.
    """
    def __init__(self, callable_fn):
        """Make a new StrongCallableReference for some callable.

        :param callable_fn:     The function to store a strong reference to
        """
        self._callable_fn = callable_fn

    def __hash__(self):
        return hash(self._callable_fn)

    def get_callable(self):
        """Returns the stored callable.

        Well, I say that. In most cases, you will get out the exact callable you put in. In some cases however, you'll
        be returned a _different_ callable that should behave as the one passed to the constructor.

        :return:    A callable like the callable you wedged in, or None if the callable is no longer valid for calling
        """
        return self._callable_fn


class WeakCallableReference(object):
    """A class to store a weak reference to a callable. If the callable has no other references, it'll be gc'd."""

    def __init__(self, callable_fn, dereference_callback=None):
        """Make a new WeakCallableReference for some callable.

        :param callable_fn:     The function to store a strong reference to
        :param dereference_callback:    Optional callback that will be notified if this reference dies.
        """
        self._dereference_callback = dereference_callback
        self._class_inst_ref = None
        self._hash = hash(callable_fn)
        self._callable_ref = ref(callable_fn, self._dereference)

        # maybe clobber some of those if we've been given a class method
        self._set_properties_for_class_method(callable_fn, self._dereference)

    def __hash__(self):
        return self._hash

    def _set_properties_for_class_method(self, callable_fn, dereference_fn):
        """Tweak properties of `self` as necessary to support a class method.

        Weak references are a pain in the arse for class methods.

        When you reference a class member method (eg MyClass().some_method), python will create a new instance for
        every retrieval ("Note that the transformation from function object to instance method object happens each time
        the attribute is retrieved from the instance." [1]). This means that you've been given a new object that
        (unless you keep a reference around to it) will immediately be dereferenced when you leave the scope.

        This means that naively storing a weakref to the class method we've been given is a bit futile, as that
        particular method will most likely immediately be dereferenced, killing our weakref. Instead, in this
        case, we store a weakref to both the class instance and the underlying function. You'll be doing well to
        cause the function to be dereferenced, but you never know.

        With this, we can then build a partial that behaves as a class method would.

        This method attempts to naively detect whether it's been given a class method. If not, nothing happens.
        If so, the weakref instance attributes are created/updated (and the hash attr tweaked too).

          [1]: https://docs.python.org/3/reference/datamodel.html

        :param callable_fn:     The maybe-class-method callable you want to store a weak reference to
        :param dereference_fn:  The function you want to notify of weakref death (if we create weakrefs)
        """
        if not hasattr(callable_fn, '__func__') or not hasattr(callable_fn, '__self__'):
            # non-class function (or some other kind of callable); no more work required
            return

        class_inst = getattr(callable_fn, '__self__')
        raw_func = getattr(callable_fn, '__func__')

        # class method; we need to store a weakref to the class instance as well so we can build a partial later.
        # override the generic properties we set earlier.
        self._callable_ref = ref(raw_func, dereference_fn)
        if class_inst:
            self._class_inst_ref = ref(class_inst, dereference_fn)
        self._hash = hash(class_inst) ^ hash(raw_func)

    def _dereference(self, _):
        """Handle any weakrefs dying (noop atm), then notify any callbacks we got"""
        if self._dereference_callback:
            self._dereference_callback(self)

    def get_callable(self):
        """ Returns the stored callable.

        In most cases this will actually be the callable, in a few cases it'll be a
        callable that

        Returns:
            Callable: That callable you wedged in, or None if the callable is no longer valid for calling
        """

        # We jump through a few hooks here to return a usable partial if we were initially given a bound method.
        callable_fn = self._callable_ref()
        if not callable_fn:
            return None

        if not self._class_inst_ref:
            return callable_fn

        class_inst = self._class_inst_ref()
        if not class_inst:
            return None

        return partial(callable_fn, class_inst)
