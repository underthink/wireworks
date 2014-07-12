__author__ = 'rob'


class PatternSequence(object):
    def __init__(self, *include_patterns):


class Pattern(object):
    def __init__(self, *args):
        self._components = list(args)

    def __add__(self, other):
        if hasattr(other, self.get_components.__name__):
            return Pattern(self._components + other.get_components())

        self._components.append(str(other))
        return self

    def __str__(self):
        return ".".join(self._components)

    def get_components(self):
        return self._components