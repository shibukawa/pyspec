# -*- coding: utf-8 -*-

from __future__ import with_statement
from pyspec2.utils.mini_test import test
import pyspec2


with test("ignore", exception=pyspec2.IgnoreTestCase):
    pyspec2.ignore_spec()


with test("fail", exception=AssertionError):
    pyspec2.fail()


with test("should_equal success"):
    pyspec2.StandardVerifier(1).should_equal(1)


with test("should_equal fail", exception=AssertionError):
    pyspec2.StandardVerifier(1).should_equal(2)


with test("should_not_equal success"):
    pyspec2.StandardVerifier(1).should_not_equal(2)


with test("should_not_equal fail", exception=AssertionError):
    pyspec2.StandardVerifier(1).should_not_equal(1)


with test("spec decorator"):
    @pyspec2.spec
    def test_method():
        pass
    assert hasattr(test_method, "__pyspec_attribute")
