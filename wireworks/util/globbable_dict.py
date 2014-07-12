# -*- coding: utf-8 -*-
"""
Like a normal dict, but with additional glob superpowers.

In addition to the normal dict method, it also allows the retrieval of lists of values that match the given
glob pattern. As such, there are a few additional restrictions on the possible keys you can wedge in it:

  * Keys must be a string. The behaviour for non-strings is undefined (but probably explodey).
  * Keys must not contain the '*' character

This should be fairly threadsafe, assuming the reading threads are happy with the chance of slightly
out of date data being returned if you're unlucky.
"""

__author__ = 'rob'


import re

from collections import defaultdict
from threading import RLock


class GlobbableDict(defaultdict):
    """
    Make us a new GlobbableDict.

    By default, the separator used to split components is a ``.``.

    Args:
        separator (str, optinal): Single character separator to use to split components
        glob_return_type (callable, optional): A callable to pass the result of the glob to, which is then
            returned instead of a standard list
        default_factory (callable, optional): If missing, call this callable with no arguments to generate
            a new value for the key. If None or omitted, a KeyError is thrown on a missing key. See
            #defaultdict.
        allow_wildcard_keys (boolean, optional): Should we allow keys to be added to the dict with glob chars?
            If not, an AttributeError will be raised if attempted. If so, the glob chars are respected, and the key's
            value is returned if the key glob matches the filter value.
    """
    def __init__(self, separator='.', glob_return_type=None, default_factory=None, allow_wildcard_keys=False):
        super(GlobbableDict, self).__init__(default_factory)

        self._cachelock = RLock()
        if len(separator) != 1:
            raise AttributeError("Only single chars are supported as a separator")

        self._sep = separator
        self._glob_return_type = glob_return_type
        self._allow_wildcard_keys = allow_wildcard_keys

        self._empty_cache()

    def glob_intersection(self, glob_patterns):
        """
        As #glob(pattern), only ensures that the returned values have keys that match against *all* of
        the given glob patterns.

        Wildcard behaviour is the same as for glob().

        Args:
            glob_patterns (iterable): List of glob patterns to match against. Format and wildcards are as for
                the 'norma; glob patterns

        Returns:
            list: Any matches, as with the glob method

            If nothing matched the given glob, an empty list is returned.
        """
        # XXX: Should probably be cached too
        matches = set(self.glob("*"))

        for pattern in glob_patterns:
            matches.intersection_update(set(self.glob(pattern)))

        return list(matches)

    def glob(self, glob_pattern):
        """
        Performs a glob match against any registered keys.

        Two forms of wildcard may be used in the glob pattern:

          * ``*``: This matches a single component, and respects separators. If there is no match for exactly the
          components given, nothing is returned. For example::

              >> a = GlobbableDict()
              >> a['a.b'] = 1
              >> a['a.b.c'] = 2
              >> a.glob('a.*')
              [1]
              >> a.glob('*')
              []

          * ``**``: This matches any number of components, regardless of any separators. Given the previous definition::

              >> a.glob('a.**')
              [1, 2]
              >> a.glob('**')
              [1, 2]

        This method caches the result where possible, meaning subsequent calls for the same pattern should be faster.
        Sets or deletes on the dict cause the cache to be invalidated.

        Args:
            glob_pattern (str): Glob pattern, containing any number of `*` or `**` wildcards.

        Returns:
            list: Any matches

            If nothing matched the given glob, an empty list is returned.

            Note that the ordering of the list is undefined (as we iterate over the keys in the dict, which is
            itself undefined).
        """

        try:
            return self._cache[glob_pattern]
        except KeyError:
            with self._cachelock:
                return self._get_and_cache_glob_value(glob_pattern)

    def _empty_cache(self):
        """
        Truncate the cache, forcing subsequent calls to do a full lookup
        """

        with self._cachelock:
            self._cache = {}

    def _make_glob_re(self, glob_pattern):
        """
        Convert a glob with ``*`` and ``**`` wildcards into a valid regular expression to use for matching keys
        """

        n_parts = []
        for part in glob_pattern.split('**'):
            f_parts = [re.escape(p) for p in part.split("*")]
            n_parts.append(("[^" + self._sep + "]*").join(f_parts))
        str_re = "^" + ".*".join(n_parts) + "$"
        return re.compile(str_re)

    def _get_matching_items(self, glob_pattern):
        """
        Match the given glob_key against all registered keys in the dict (using ``self._make_glob_re(glob_pattern)``
        to build the regular expression), and return the result
        """

        collected_vals = []
        compiled_glob = self._make_glob_re(glob_pattern)

        for key in self.keys():
            # normal match
            if compiled_glob.match(key):
                collected_vals.append(self[key])
            # if no match, does the *reverse* work (ie treating the key as the glob)?
            elif '*' in key:
                # reverse search
                compiled_key_as_glob = self._make_glob_re(key)
                if compiled_key_as_glob.match(glob_pattern):
                    collected_vals.append(self[key])

        return collected_vals

    def _get_and_cache_glob_value(self, glob_pattern):
        """
        Match the given glob_key against all registered keys in the dict (using
        ``self._get_matching_items(glob_pattern)``), add the results to the cache, and return them
        """

        vals = self._get_matching_items(glob_pattern)

        if self._glob_return_type:
            vals = self._glob_return_type(vals)

        self._cache[glob_pattern] = vals

        return vals

    def __setitem__(self, key, value):
        if not self._allow_wildcard_keys and '*' in key:
            raise AttributeError("Keys may not contain glob chars if allow_wildcard_keys=False")

        with self._cachelock:
            super(GlobbableDict, self).__setitem__(str(key), value)
            self._empty_cache()

    def __delitem__(self, key):
        with self._cachelock:
            super(GlobbableDict, self).__delitem__(key)
            self._empty_cache()