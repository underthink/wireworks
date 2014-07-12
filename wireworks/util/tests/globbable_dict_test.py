__author__ = 'rob'

import unittest

from wireworks.util.globbable_dict import GlobbableDict


class TestGlobbableDict(unittest.TestCase):
    def test_basic_dict_functionality(self):
        """
        Test that the basic dict functionality still works. I'd be doing well if I broke it, but still...
        """

        d = GlobbableDict()

        d['a'] = 1
        d['b'] = 'z'

        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 'z')
        self.assertRaises(KeyError, lambda: d['c'])

    def test_no_wildcard_glob_all(self):
        """
        Test that a call to glob() with no wildcards returns the single row (or empty list) we'd expect
        """
        d = GlobbableDict()

        d[''] = 1
        d['aa'] = 2
        d['a.a'] = 3
        d['aa.aa'] = 4

        self.assertListEqual(sorted(d.glob("")), [1])
        self.assertListEqual(sorted(d.glob("aa")), [2])
        self.assertListEqual(sorted(d.glob("a.a")), [3])
        self.assertListEqual(sorted(d.glob("aa.aa")), [4])
        self.assertListEqual(sorted(d.glob("a")), [])

    def test_single_asterisk_glob_all(self):
        """
        Test that globs containing one or more of the '*' single-component wildcard match what's expected, when used
        as the entire component
        """
        d = GlobbableDict()

        d['a.b'] = 1
        d['a.c'] = 2
        d['b'] = 3
        d['a.b.c'] = 4
        d['d.e'] = 5

        self.assertListEqual(sorted(d.glob("a.*")), [1, 2])
        self.assertListEqual(sorted(d.glob("*")), [3])
        self.assertListEqual(sorted(d.glob("*.*")), [1, 2, 5])
        self.assertListEqual(sorted(d.glob("")), [])
        self.assertListEqual(sorted(d.glob("*.*.c")), [4])
        self.assertListEqual(sorted(d.glob("*.b.*")), [4])
        self.assertListEqual(sorted(d.glob("a.b.c.*")), [])

    def test_single_asterisk_glob_in_key(self):
        """
        Test that globs containing one or more of the '*' single-component wildcard match what's expected, when used
        in a key
        """
        d = GlobbableDict(allow_wildcard_keys=True)

        d['a.*'] = 1
        d['a.c'] = 2
        d['b'] = 3
        d['a.b.c'] = 4
        d['d.e'] = 5
        d['*'] = 6

        self.assertListEqual(sorted(d.glob("a.b")), [1])
        self.assertListEqual(sorted(d.glob("*")), [3, 6])
        self.assertListEqual(sorted(d.glob("*.*")), [1, 2, 5])
        self.assertListEqual(sorted(d.glob("")), [6])
        self.assertListEqual(sorted(d.glob("a.c")), [1, 2])
        self.assertListEqual(sorted(d.glob("*.b")), [])

    def test_partial_single_asterisk_glob_all(self):
        """
        Test that globs containing one or more of the '*' single-component wildcard match what's expected, when used
        as part of a component combined with regular chars
        """
        d = GlobbableDict()

        d['longer.keys'] = 1
        d['longer.keys.too'] = 2

        self.assertListEqual(sorted(d.glob("longer.key*")), [1])
        self.assertListEqual(sorted(d.glob("lo*.key*")), [1])
        self.assertListEqual(sorted(d.glob("lo*r.keys")), [1])
        self.assertListEqual(sorted(d.glob("*o*.*")), [1])
        self.assertListEqual(sorted(d.glob("*f*.*")), [])

    def test_double_asterisk_glob_all(self):
        """
        Test that globs containing one or more of the '**' any-component wildcard match what's expected, when used
        as an entire component
        """
        d = GlobbableDict()

        d['a.b'] = 1
        d['a.c'] = 2
        d['b'] = 3
        d['a.b.c'] = 4
        d['d.e'] = 5
        d['a.b.c.d.e.f.g'] = 6
        d['a.b.g'] = 7

        self.assertListEqual(sorted(d.glob("a.**")), [1, 2, 4, 6, 7])
        self.assertListEqual(sorted(d.glob("**")), [1, 2, 3, 4, 5, 6, 7])
        self.assertListEqual(sorted(d.glob("**.g")), [6, 7])
        self.assertListEqual(sorted(d.glob("**.c.**")), [6])
        self.assertListEqual(sorted(d.glob("a.**.g")), [6, 7])

    def test_double_asterisk_glob_in_key(self):
        """
        Test that globs containing one or more of the '**' any-component wildcard match what's expected, when used
        in a key
        """
        d = GlobbableDict(allow_wildcard_keys=True)

        d['a.**'] = 1
        d['a.c'] = 2
        d['b'] = 3
        d['a.b.c'] = 4
        d['d.e'] = 5
        d['a.b.c.d.e.f.g'] = 6
        d['a.b.g'] = 7
        d['a'] = 8
        d['**'] = 9

        # NB a pair of 'a.**' -> '**.x' don't match. I don't think this would practically be useful. Also it makes
        # me head hurt. So not supported. Them's the breaks.

        self.assertListEqual(sorted(d.glob("a")), [8, 9])
        self.assertListEqual(sorted(d.glob("a.b.c")), [1, 4, 9])
        self.assertListEqual(sorted(d.glob("a.b.**")), [1, 4, 6, 7, 9])
        self.assertListEqual(sorted(d.glob("**.g")), [6, 7, 9])
        self.assertListEqual(sorted(d.glob("**.c.**")), [6, 9])
        self.assertListEqual(sorted(d.glob("a.**.g")), [1, 6, 7, 9])

    def test_partial_double_asterisk_glob_all(self):
        """
        Test that globs containing one or more of the '**' any-component wildcard match what's expected, when used
        as part of a component combined with regular chars
        """
        d = GlobbableDict()

        d['a.b.c.d.e.f.g'] = 1
        d['a.b.g'] = 2
        d['agog'] = 3

        self.assertListEqual(sorted(d.glob("a**g")), [1, 2, 3])
        self.assertListEqual(sorted(d.glob("a**.g")), [1, 2])
        self.assertListEqual(sorted(d.glob("ag**")), [3])

    def test_mixed_single_double_asterisk_glob_all(self):
        """
        Test that a combination of '*' and '**' wildcards match what's expected
        """
        d = GlobbableDict()

        d['a.b'] = 1
        d['a.c'] = 2
        d['b'] = 3
        d['a.b.c'] = 4
        d['d.e'] = 5
        d['a.b.c.d.e.f.g'] = 6

        self.assertListEqual(sorted(d.glob("a.*.**")), [4, 6])
        self.assertListEqual(sorted(d.glob("**")), [1, 2, 3, 4, 5, 6])
        self.assertListEqual(sorted(d.glob("**.d.*.f.g")), [6])
        self.assertListEqual(sorted(d.glob("*.**.*.d.**")), [6])
        self.assertListEqual(sorted(d.glob("**.*")), [1, 2, 4, 5, 6])

    def test_put_changes_results(self):
        """
        Test that putting a new value invalidates the cache enough to return the correct list on next glob
        """
        d = GlobbableDict()

        d['a.b'] = 1

        self.assertListEqual(sorted(d.glob("a.*")), [1])

        d['a.c'] = 2

        self.assertListEqual(sorted(d.glob("a.*")), [1, 2])

    def test_del_changes_results(self):
        """
        Test that putting a new value invalidates the cache enough to return the correct list on next glob
        """
        d = GlobbableDict()

        d['a.b'] = 1
        d['a.c'] = 2

        self.assertListEqual(sorted(d.glob("a.*")), [1, 2])

        del d['a.c']

        self.assertListEqual(sorted(d.glob("a.*")), [1])

    def test_invalid_separator_rejected(self):
        """
        Test that we do not allow invalid separator chars
        """
        self.assertRaises(AttributeError, GlobbableDict, "abc")
        self.assertRaises(AttributeError, GlobbableDict, "")

    def test_put_with_wildcard_rejected(self):
        """
        Test that we cannot put a key with a wildcard in if allow_wildcard_keys is False (the default).
        """
        d = GlobbableDict()

        def test_putter():
            d['a.*'] = 1

        self.assertRaises(AttributeError, test_putter)

    def test_put_with_wildcard_allowed_with_param(self):
        """
        Test that we *can* put a key with a wildcard in if allow_wildcard_keys is True
        """
        d = GlobbableDict(allow_wildcard_keys=True)
        d['a.*'] = 1  # nothing thrown is a success

    def test_return_custom_type(self):
        """
        Test that custom types are correctly returned
        """

        def test_type_converter(val):
            self.assertListEqual(sorted(val), [1, 2])
            return "OK"

        d = GlobbableDict(glob_return_type=test_type_converter)

        d['a.b'] = 1
        d['a.c'] = 2

        self.assertEquals("OK", d.glob("a.*"))

    def test_custom_separator(self):
        """
        Test that custom separators are correctly honoured
        """

        d = GlobbableDict(separator="/")

        d['a.b'] = 1
        d['a.c'] = 2
        d['a.b/c.d'] = 3
        d['a.c/c.d'] = 4

        self.assertListEqual(sorted(d.glob("a.*")), [1, 2])
        self.assertListEqual(sorted(d.glob("a.b/*")), [3])
        self.assertListEqual(sorted(d.glob("*")), [1, 2])