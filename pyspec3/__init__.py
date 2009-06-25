# -*- coding: ascii -*-

"""PySpec - Behavior Driven Development Framework -.

This package have many items for BDD. For example, spec definition decorators
and spec verification tools, mock objects, CUI and GUI test runners and so on.

Simple usage (compare it with unittest module sample!):

    from pyspec import *

    class IntegerArithmentic_Behavior():
        @spec
        def integer_should_support_add(self):  ## test method have @spec decor
            About(1 + 2).should_equal(3)
            About(0 + 1).should_equal(1)
        @spec
        def integer_should_support_mul(self):
            About(0 * 10).should_equal(0)
            About(5 * 8).should_equal(40)

    if __name__ == '__main__':
        run_test()


This software is inspired by unittest module.
I thank Mr.Steve Purcell for his work.

And I must say 'thank you' to Mr. Masaru Ishii too.
He popularized unit test in Japan.

PySpec License
==============

Copyright (c) 2006-2007, Shibukawa Yoshiki<yoshiki at shibu.jp>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

  1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

"""

import pyspec3.compat_ironpython

__version__ = "0.44alpha"

__pyspec = 1
ignore_stack = False
__test_index = 0
__verifiers = []


__all__ = (
    "spec",
    "context",
    "class_context",
    "spec_finalize",
    "class_finalize",
    "ignore",
    "IgnoreTestCase",
    "value_of",
    "Verify",
    "run_test",
    "report_out",
    "regist_test_verifier")


report_out = None


def get_test_index():
    global __test_index
    __test_index += 1
    return __test_index


def regist_test_verifier(check_function, verifier):
    global __verifiers
    __verifiers.append((check_function, verifier))


class IgnoreTestCase(Exception):
    """Ignore notifier."""


def value_of(actual):
    global __verifiers
    for check_function, verifier in __verifiers:
        if check_function(actual):
            return verifier(actual)
    return StandardVerifier(actual)


class VerifierBase(object):
    __slots__ = ("actual",)
    def __init__(self, actual):
        self.actual = actual

    @staticmethod
    def _get_target():
        import re
        source = compat_ironpython.get_source_code(3)
        if source is None:
            return None
        match = re.search(r"About\((.*?)\).should", source)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _source(source, actual):
        if source is not None:
            return "%s" % source
        return "<%r>" % actual

    @classmethod
    def _value_with_source(cls, source, actual):
        if source is not None:
            value = cls._value(actual)
            if source == value:
                return value
            return "%s(=%s)" % (source, cls._value(actual))
        return "<%r>" % actual

    @staticmethod
    def _value(value):
        if isinstance(value, str):
            return '"%s"' % value
        return '%s' % str(value)

    @staticmethod
    def _write(value):
        if report_out:
            report_out.write(value)


class StandardVerifier(VerifierBase):
    """Verification tool class.

    This class have many verification methods to define behavior.

    usage:
        a = 100
        About(a).should_equal(10)
    """
    def should_equal(self, expected):
        """Test the value is equal to a target.

        Fail if the two objects are unequal as determined by the '=='
        operator.

        usage:
            a = 2
            About(a).should_equal(2) # OK!
            About(a).should_equal(3) # Fail!

        @param expected: target value
        """
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if not expected == self.actual:
            msg = "%s should equal %s, but was %s." % \
                (self._source(source, self.actual),
                 self._value(expected), self._value(self.actual))
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should equal %s." % \
            (self._source(source, self.actual), self._value(expected))
        self._write((source, msg))
        ignore_stack = False
        return msg

    def should_not_equal(self, expected, msg = None):
        """Test the value is unequal to a target.

        Fail if the two objects are equal as determined by the '=='
        operator.

        usage:
            a = 2
            About(a).should_not_equal(3) # OK!
            About(a).should_not_equal(2) # Fail!

        @param expected: target value
        """
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if expected == self.actual:
            msg = "%s should not equal %s, but equal." % \
                (self._source(source, self.actual), self._value(expected))
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should not equal %s." % \
            (self._value_with_source(source, self.actual),
             self._value(expected))
        self._write((source, msg))
        ignroe_stack = False
        return msg

    def should_equal_nearly(self, expected, tolerance=None):
        """Test the value is near to a target value.

        Fail if the difference of two floating point number is
        more than 'tolerance'.

        usage:
            a = 2
            About(a).should_not_equal(3) # OK!
            About(a).should_not_equal(2) # Fail!

        @param expected: target value
        @type  expected: float
        @param tolerance: allowable margin of error(default=expected*0.01)
        @type  tolerance: float

        """
        global ignore_stack
        ignore_stack = True
        if tolerance is None:
            tolerance = expected * 0.01
        source = self._get_target()
        if abs(expected - self.actual) > tolerance:
            msg = "%s should equal nearly %f(within %f), but was %f." % \
                (self._source(source, self.actual), expected, tolerance, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should not equal %f(more than %f)." % \
            (self._value_with_source(source, self.actual), expected, tolerance)
        self._write((source, msg))
        ignore_stack = False

    def should_not_equal_nearly(self, expected, tolerance=None):
        """Test the value is far from a target value.

        Fail if the difference of two floating point number is
        less than 'tolerance'.

        usage:
            a = 2
            About(a).should_not_equal(3) # OK!
            About(a).should_not_equal(2) # Fail!

        @param expected: target value
        @type  expected: float
        @param tolerance: disallowable margin of error(default=expected*0.01)
        @type  tolerance: float

        """
        global ignore_stack
        ignore_stack = True
        if tolerance is None:
            tolerance = expected * 0.01
        source = self._get_target()
        if abs(expected - self.actual) < tolerance:
            msg = "%s should not equal %f(more than %f), but was." % \
                (self._source(source, self.actual), expected, tolerance)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should not equal nearly %f(within %f)." % \
            (self._value_with_source(source, self.actual), expected, tolerance)
        self._write((source, msg))
        ignore_stack = False

    def should_be_true(self, msg=""):
        """Fail if value is not True."""
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if not self.actual:
            msg = "%s should be True, but was False." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should be True." % \
            self._source(source, self.actual)
        self._write((source, msg))
        ignore_stack = False

    def should_be_false(self, msg=""):
        """Fail if value is not False."""
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if self.actual:
            msg = "%s should be False, but was True." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should be False." % \
            self._source(source, self.actual)
        self._write((source, msg))
        ignore_stack = False

    def should_be_none(self, msg=""):
        """Fail if value is not None."""
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if self.actual is not None:
            msg = "%s should be None, but was not." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should be None." % \
            self._source(source, self.actual)
        self._write((source, msg))
        ignore_stack = False

    def should_not_be_none(self, msg=""):
        """Fail if value is None."""
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if self.actual is None:
            msg = "%s should not be None, but was." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should not be None." % \
            self._source(source, self.actual)
        self._write((source, msg))
        ignore_stack = False

    def should_be_same(self, expected, msg = None):
        """Fail if the two objects are different as determined by the 'is'
             operator.
        """
        import re
        global ignore_stack
        ignore_stack = True
        source = compat_ironpython.get_source_code()
        if source is None:
            match1 = None
            match2 = None
        else:
            m = re.search(r"About\((.*?)\).should_be_same\((.*?)\)", source)
            match1 = m.group(1)
            match2 = m.group(2)
        if not expected is self.actual:
            try:
                msg = "%s(id=%d) should be same %s(id=%d), but was not." % \
                    (self._source(match1, self.actual), id(self.actual), \
                     self._source(match2, expected), id(expected))
            except:
                msg = "%s(id=%d) should be same %s(id=%d), but was not." % \
                    (self.actual, id(self.actual), expected, id(expected))
            ignore_stack = False
            raise AssertionError(msg)
        try:
            msg = "%s should be same %s." % \
                (self._source(match1, self.actual), \
                 self._source(match2, expected))
        except:
            msg = "%s should not equal %s." % \
                (self.actual, expected)
        self._write((source, msg))
        ignore_stack = False

    def should_not_be_same(self, expected, msg = None):
        """Fail if the two objects are different as determined by the 'is'
             operator.
        """
        from re import search
        global ignore_stack
        ignore_stack = True
        source = compat_ironpython.get_source_code()
        if source is None:
             match1 = None
             match2 = None
        else:
             m = search(r"About\((.*?)\).should_not_be_same\((.*?)\)", source)
             match1 = m.group(1)
             match2 = m.group(2)
        if expected is self.actual:
            try:
                msg = "%s should not be same %s, but equal." % \
                    (self._source(match1, self.actual), \
                     self._source(match2, expected))
            except:
                msg = "%s should not be same %s, but equal." % \
                    (self.actual, expected)
            ignore_stack = False
            raise AssertionError(msg)
        try:
            msg = "%s(id=%d) should not be same %s(id=%d)." % \
                (self._source(match1, self.actual), id(self.actual), \
                 self._source(match2, expected), id(expected))
        except:
            msg = "%s(id=%d) should not be same %s(id=%d)." % \
                (self.actual, id(self.actual), expected, id(expected))
        self._write((source, msg))
        ignore_stack = False

    def should_include(self, expected, msg = None):
        from re import search
        global ignore_stack
        ignore_stack = True
        source = compat_ironpython.get_source_code()
        if source is None:
             match1 = None
             match2 = None
        else:
             m = search(r"About\((.*?)\).should_include\((.*?)\)", source)
             match1 = m.group(1)
             match2 = m.group(2)
        if (not hasattr(self.actual, "__contains__")
            and not hasattr(self.actual, "__iter__")):
            msg = "%s should have __contains__ or __iter__ method." % \
                self._value_with_source(match1, self.actual)
            ignore_stack = False
            raise TypeError(msg)
        elif not expected in self.actual:
            msg = "%s should include %s, but didn't." % \
                (self._value_with_source(match1, self.actual), \
                 self._value_with_source(match2, expected))
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should include %s." % \
            (self._value_with_source(match1, self.actual), \
             self._value_with_source(match2, expected))
        self._write((source, msg))
        ignore_stack = False

    def should_not_include(self, expected, msg = None):
        from re import search
        global ignore_stack
        ignore_stack = True
        source = compat_ironpython.get_source_code()
        if source is None:
             match1 = None
             match2 = None
        else:
             m = search(r"About\((.*?)\).should_not_include\((.*?)\)", source)
             match1 = m.group(1)
             match2 = m.group(2)
        if (not hasattr(self.actual, "__contains__")
            and not hasattr(self.actual, "__iter__")):
            msg = "%s should have __contains__ or __iter__ method." % \
                self._value_with_source(match1, self.actual)
            ignore_stack = False
            raise TypeError(msg)
        elif expected in self.actual:
            try:
                msg = "%s should not include %s, but include." % \
                    (self._value_with_source(match1, self.actual), \
                     self._value_with_source(match2, expected))
            except:
                msg = "%s should not include %s, but include." % \
                    (self.actual, expected)
            ignore_stack = False
            raise AssertionError(msg)
        try:
            msg = "%s should not include %s." % \
                (self._value_with_source(match1, self.actual), \
                 self._value_with_source(match2, expected))
        except:
            msg = "%s should not include %s." % \
                (self.actual, expected)
        self._write((source, msg))
        ignore_stack = False

    def should_be_empty(self, msg = None):
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if not hasattr(self.actual, "__len__"):
            msg = "%s should have __len__ method." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        if len(self.actual) != 0:
            msg = "%s should be empty, but was not." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should be empty." % \
            self._source(source, self.actual)
        self._write((source, msg))
        ignore_stack = False

    def should_not_be_empty(self, msg = None):
        global ignore_stack
        ignore_stack = True
        source = self._get_target()
        if not hasattr(self.actual, "__len__"):
            msg = "%s should have __len__ method." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        if len(self.actual) == 0:
            msg = "%s should not be empty, but was empty." % \
                self._source(source, self.actual)
            ignore_stack = False
            raise AssertionError(msg)
        msg = "%s should not be empty." % \
            self._source(source, self.actual)
        self._write((source, msg))
        ignore_stack = False


def fail(msg="Stop by user"):
    """Fail always."""
    raise AssertionError(msg)


def ignore_spec(msg="This spec was ignored"):
    """Ignore always."""
    raise IgnoreTestCase(msg)


def spec(method = None, group=None, expected=None):
    """Set BDD method flag."""
    if method is not None:
        append_pyspec_attribute(method, SpecMethodAttribute)
        return method
    return BDDDecorator(group, SpecMethodAttribute, expected)


internal_spec = spec


def context(method = None, group=None):
    """Set BDD context method flag.

    If you add group, you can make group of context and spec.

    usage:
        @context
        def context_method():

        @context(group=1)
        def context_method_that_have_group()
    """
    if method is not None:
        append_pyspec_attribute(method, ContextMethodAttribute)
        return method
    return BDDDecorator(group, ContextMethodAttribute)


def class_context(method):
    """Set class context method flag."""
    attr = append_pyspec_attribute(method, ContextMethodAttribute)
    attr.is_class = True
    return method


def spec_finalize(method):
    """Set finalize method flag."""
    append_pyspec_attribute(method, FinalizeMethodAttribute)
    return method


def class_finalize(method):
    """Set class finalize method flag."""
    attr = append_pyspec_attribute(method, FinalizeMethodAttribute)
    attr.is_class = True
    return method


def ignore(method):
    """Set spec method ignored flag."""
    attr = append_pyspec_attribute(method, SpecMethodAttribute)
    attr.ignored = True
    return method

# -------------
# Spec Register

def append_pyspec_attribute(method, AttributeClass):
    if not hasattr(method, "__pyspec_attribute"):
        method.__pyspec_attribute = AttributeClass(method)
    return getattr(method, "__pyspec_attribute")


class PySpecAttribute(object):
    def __init__(self):
        """set test decorator.
        @category load.registmethod
        """
        self.is_context = False
        self.is_finalize = False
        self.index = get_test_index()


class SpecMethodAttribute(PySpecAttribute):
    def __init__(self, method):
        super(SpecMethodAttribute, self).__init__()
        self.timeout = 100.0
        self.ignored = False
        self.groups = None
        self.expected = None

    def set_group(self, group):
        """group attribute is used by BDD.
        Spec method uses same group contexts.
        """
        if type(group) in (list, tuple):
            self.groups = group
        else:
            self.groups = (group,)

    def set_expected(self, expected):
        self.expected = expected


class ContextMethodAttribute(PySpecAttribute):
    def __init__(self, method):
        super(ContextMethodAttribute, self).__init__()
        self.is_context = True
        self.is_class = False
        self.group = None

    def context(self, test_fixture, context_method):
        method = getattr(test_fixture, context_method.name())
        method()

    def set_group(self, group):
        if type(group) in (list, tuple):
            raise TypeError("context's group argument cannot accept list, tuple.")
        else:
            self.group = group


class FinalizeMethodAttribute(PySpecAttribute):
    def __init__(self, method):
        super(FinalizeMethodAttribute, self).__init__()
        self.is_finalize = True
        self.is_class = False

    def finalize(self, test_fixture, finalize_method):
        method = getattr(test_fixture, finalize_method.name())
        method()


class BDDDecorator(object):
    """BDD method decorator.
    This object contains grouping types.
    """
    def __init__(self, group, Attribute, expected=None):
        self.group = group
        self.expected = expected
        self.Attribute = Attribute

    def __call__(self, method):
        """Decorate spec options."""
        attr = append_pyspec_attribute(method, self.Attribute)
        attr.set_group(self.group)
        if self.expected is not None:
           attr.set_expected(self.expected)
        return method


def run_test():
    """Easy test launcher method.

    usage:
        from pyspec import *

        @spec
        def easy_test():
            About(2 + 1).should_equal(2) # wrong

        if __name__ == "__main__":
            run_test()
    """
    import pyspec.textui
    pyspec.textui.TextSpecTestRunner(auto=True).run()
