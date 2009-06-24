# -*- coding: utf-8 -*-

from pyspec3.support.tmini_test import test
import pyspec3


with test("ignore", exception=pyspec3.IgnoreTestCase):
    pyspec3.ignore_spec()


with test("fail", exception=AssertionError):
    pyspec3.fail()


with test("should_equal success"):
    pyspec3.StandardVerifier(1).should_equal(1)


with test("should_equal fail", exception=AssertionError):
    pyspec3.StandardVerifier(1).should_equal(2)


with test("should_not_equal success"):
    pyspec3.StandardVerifier(1).should_not_equal(2)


with test("should_not_equal fail", exception=AssertionError):
    pyspec3.StandardVerifier(1).should_not_equal(1)


with test("spec decorator"):
    @pyspec3.spec
    def test_method():
        pass
    assert hasattr(test_method, "__pyspec_attribute")