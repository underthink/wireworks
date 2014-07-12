__author__ = 'rob'

import unittest

from ..callable_references import StrongCallableReference, WeakCallableReference


class TestCallableReferences(unittest.TestCase):
    def test_store_strong_ref_not_gcd(self):
        """Test that a strong reference to a method is not GC'd if the original goes out of scope"""
        called_ok = [False]
        reference = [None]

        def inner():
            def fn():
                called_ok[0] = True
            reference[0] = StrongCallableReference(fn)

        inner()
        self.assertFalse(called_ok[0], "Strongly-ref'd function called prematurely")
        fn_ref = reference[0].get_callable()
        self.assertIsNotNone(fn_ref, "Strongly-ref'd function was None")
        fn_ref()
        self.assertTrue(called_ok[0], "Strongly-ref'd function does not appear to have been called correctly")

    def test_function_calls_work(self):
        """Test that normal, non-class functions behave as expected for both Strong and Weak refs."""

        for ref_type in [StrongCallableReference, WeakCallableReference]:
            called_ok = [False]

            def fn():
                called_ok[0] = True

            ref = ref_type(fn)
            fn_ref = ref.get_callable()
            self.assertIsNotNone(fn_ref, "%s-based ref returned a None instead of a function" % ref_type)
            fn_ref()
            self.assertTrue(called_ok[0], "%s-based ref appears not to have correctly invoked function" % ref_type)

    def test_unbound_method_calls_work(self):
        """Test that unbound method calls behave as expected for both Strong and Weak refs."""

        for ref_type in [StrongCallableReference, WeakCallableReference]:
            called_ok = [False]

            class TestClass(object):
                def meth(self):
                    called_ok[0] = True
            inst = TestClass()
            ref = ref_type(TestClass.meth)
            fn_ref = ref.get_callable()
            self.assertIsNotNone(fn_ref, "%s-based ref returned a None instead of a function" % ref_type)
            fn_ref(inst)
            self.assertTrue(called_ok[0], "%s-based ref appears not to have correctly invoked unbound meth" % ref_type)

    def test_bound_method_calls_work(self):
        """Test that bound method calls behave as expected for both Strong and Weak refs."""

        for ref_type in [StrongCallableReference, WeakCallableReference]:
            called_ok = [False]

            class TestClass(object):
                def __init__(self):
                    self.called_ok = False

                def meth(self):
                    self.called_ok = True
                    called_ok[0] = True

            cls_ref = TestClass()
            ref = ref_type(cls_ref.meth)
            fn_ref = ref.get_callable()
            self.assertIsNotNone(fn_ref, "%s-based ref returned a None instead of a function" % ref_type)
            fn_ref()
            self.assertTrue(called_ok[0], "%s-based ref appears not to have correctly invoked bound meth" % ref_type)
            self.assertTrue(cls_ref.called_ok, "%s-based ref did not update class instance attr" % ref_type)

    def test_user_callables_work(self):
        """Test that user defined callables (__call__) behave as expected for both Strong and Weak refs."""

        for ref_type in [StrongCallableReference, WeakCallableReference]:
            called_ok = [False]

            class TestClass(object):
                def __init__(self):
                    self.called_ok = False

                def __call__(self):
                    self.called_ok = True
                    called_ok[0] = True

            cls_ref = TestClass()
            ref = ref_type(cls_ref)
            fn_ref = ref.get_callable()
            self.assertIsNotNone(fn_ref, "%s-based ref returned a None instead of a function" % ref_type)
            fn_ref()
            self.assertTrue(called_ok[0], "%s-based ref appears not to have correctly invoked user callable" % ref_type)
            self.assertTrue(cls_ref.called_ok, "%s-based ref did not update class instance attr" % ref_type)

    def test_normal_weak_ref_collected(self):
        """Test that a weak reference works with a function as long as it's not been collected"""
        called_ok = [False]
        notified_ok = [False]
        reference = [None]

        def update_notified(_):
            notified_ok[0] = True

        def inner():
            def fn():
                called_ok[0] = True
            reference[0] = WeakCallableReference(fn, dereference_callback=update_notified)

            self.assertFalse(called_ok[0], "Weakly-ref'd function called prematurely")
            fn_ref = reference[0].get_callable()
            self.assertIsNotNone(fn_ref, "Weakly-ref'd function was None")
            fn_ref()
            self.assertTrue(called_ok[0], "Weakly-ref'd function does not appear to have been called correctly")
            self.assertFalse(notified_ok[0], "Weak ref notified of deadness prematurely")

        inner()

        fn_ref = reference[0].get_callable()
        self.assertIsNone(fn_ref, "Weakly-ref'd function was not None after original function deleted")
        self.assertTrue(notified_ok[0], "Weak ref did not notify of deadness")

    def test_bound_method_weak_ref_collected(self):
        """Test that a weak reference works with a bound method as long as it's not been collected"""
        called_ok = [False]
        reference = [None]

        class TestClass(object):
            def __init__(self):
                self.called_ok = False

            def fn(self):
                self.called_ok = True
                called_ok[0] = True

        def inner():
            inst = TestClass()
            reference[0] = WeakCallableReference(inst.fn)

            self.assertFalse(called_ok[0], "Weakly-ref'd bound method called prematurely")
            fn_ref = reference[0].get_callable()
            self.assertIsNotNone(fn_ref, "Weakly-ref'd bound method was None")
            fn_ref()
            self.assertTrue(called_ok[0], "Weakly-ref'd bound method does not appear to have been called correctly")
            self.assertTrue(inst.called_ok, "Weakly-ref'd bound method did not update class instance attr")

        inner()

        fn_ref = reference[0].get_callable()
        self.assertIsNone(fn_ref, "Weakly-ref'd function was not None after original function deleted")

    def test_hashes(self):
        """Test that we generate the same hash for the same functions and methods."""

        for ref_type in [StrongCallableReference, WeakCallableReference]:
            class TestClass(object):
                def fn(self):
                    pass

            inst = TestClass()
            ref1 = ref_type(inst.fn)
            ref2 = ref_type(inst.fn)

            self.assertEqual(hash(ref1), hash(ref2), "%s bound method hashes do not match" % ref_type)

            fn = lambda: None

            ref3 = ref_type(inst.fn)
            ref4 = ref_type(inst.fn)

            self.assertEqual(hash(ref3), hash(ref4), "%s function hashes do not match" % ref_type)