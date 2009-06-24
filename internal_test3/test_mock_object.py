# -*- coding: utf-8 -*-

from pyspec3.support.tmini_test import test
from pyspec3.mockobject import (MockResult, MockMethod, MockObject,
                                MockFile, MockSocket)
from pyspec3.support.dprint import enable_debug_print


with test("mock method"):
    enable_debug_print()
    add = MockMethod("add")
    add(1, 2) == 3
    add.is_recording = False
    assert add(1, 2) == 3


with test("mock method: fail", exception=AssertionError):
    enable_debug_print()
    add = MockMethod("add")
    add(1, 2) == 3
    add.is_recording = False
    add(2, 2) # bud argument


with test("mock method with kwargs"):
    enable_debug_print()
    range2 = MockMethod("range2")
    range2(start=1, to=4) == [1, 2, 3]
    range2.is_recording = False
    assert range2(start=1, to=4) == [1, 2, 3]


with test("mock method with kwargs: fail", exception=AssertionError):
    enable_debug_print()
    range2 = MockMethod("range2")
    range2(start=1, to=4) == [1, 2, 3]
    range2.is_recording = False
    assert range2(start=1, to=5)


with test("mock object: recording mode test"):
    enable_debug_print()
    mock = MockObject()
    assert mock._is_recording
    mock.end_record()
    assert not mock._is_recording


with test("mock object: recording method call"):
    enable_debug_print()
    mock = MockObject()
    mock.add(1, 2) == 3 # recording
    mock.end_record()
    assert mock.add(1, 2) == 3 # replay


with test("mock object: recording method call fail",
        exception=AssertionError):
    enable_debug_print()
    mock = MockObject()
    mock.add(1, 2) == 3 # recording
    mock.end_record()
    mock.add(1, 4) # error


with test("mock object: recording method call with kwargs"):
    enable_debug_print()
    mock = MockObject()
    mock.add(v1=1, v2=2) == 3 # recording
    mock.end_record()
    assert mock.add(v1=1, v2=2) == 3 # replay


with test("mock object: recording method call with kwargs fail",
        exception=AssertionError):
    enable_debug_print()
    mock = MockObject()
    mock.add(v1=1, v2=2) == 3 # recording
    mock.end_record()
    mock.add(1, 2) # error: no kwargs


with test("mock method: dump"):
    enable_debug_print()
    range2 = MockMethod("range2")
    range2(start=1, to=4) == [1, 2, 3]
    range2.is_recording = False
    assert str(range2) == "range2(start=1, to=4) == [1, 2, 3]"


with test("mock object: dump"):
    enable_debug_print()
    mock = MockObject(class_name="Calculator")
    mock.add(v1=1, v2=2) == 3 # recording
    mock.end_record()
    mock.add(1, 2) # error: no kwargs
    print(mock)
    assert str(range2) == "MockObject of Calculator\n  add(1, 2) == 3\n"
