# -*- coding: utf-8 -*-

"""Mini Testing framework for PySpec

It have 2 purposes to develop PySpec.

* Internal testing
    Testing by itself is very beautiful as architecture, but it is nightmare
    for development. It separetes subject and object.

* Architecture sample
    PySpec is commitment base architecture, and it is first time to use it.

You can write test like following:

    with test("test name"):
        test_statements()

If you want to handle exceptions you can write it:

    with test("test name", exception=AssertionError):
        a = 2
        assert a == 1 # It's OK!

After running test, you must call show_result().
"""

import io
import sys
import traceback
import itertools
import pyspec3.tdfw as tdfw


def setup(method):
   test_manager._fook_methods[0] = method
   return method


def teardown(method):
   test_manager._fook_methods[1] = method
   return method


class test(object):
    _io = []
    def __init__(self, test_name="", exception=None):
        self.test_name = test_name
        self.exception = exception

    @tdfw.expose_method("test:start_recording")
    def __enter__(self):
        if not self._io:
            self._io = [sys.stdout, sys.stderr]
        output = io.StringIO()
        sys.stdout = output
        sys.stderr = output
        tdfw.twitter("test:start_recording")

    @tdfw.expose_method("test:stop_recording")
    @tdfw.expose_method("test:good_result")
    @tdfw.expose_method("test:bad_result")
    def __exit__(self, _type, _value, _traceback):
        result = ["TestCase: %s" % self.test_name, "-"*70]
        tdfw.twitter("test", "stop_recording")
        if self._io:
            console = sys.stdout.getvalue()
            sys.stdout = self._io[0]
            sys.stderr = self._io[1]
        else:
            console = ""
        if not self.exception:
            if _traceback is None:
                result.append("OK")
                tdfw.twitter("test:good_result", result=result)
            else:
                tb = "".join(traceback.format_exception(_type, _value, _traceback))
                result += [tb, "----console----", console]
                tdfw.twitter("test:bad_result", result=result)
        else:
            if _type is self.exception:
                result.append("OK")
                tdfw.twitter("test:good_result", result=result)
            elif _type is None:
                msg = "expected exception is '%s' but no exception raised" % \
                    self.exception.__name__
                result += [msg, "----console----", console]
                tdfw.twitter("test:bad_result", result=result)
            else:
                msg = "expected exception is '%s' but '%s' was raised" % \
                    (self.exception.__name__, _type.__name__)
                result += [msg, "----console----", console]
                tdfw.twitter("test:bad_result", result=result)
        return True


class test_manager(metaclass=tdfw.Follower):
    _good_results = []
    _bad_results = []
    _fook_methods = [None, None]

    @classmethod
    def show_result(cls):
        for result in itertools.chain(cls._good_results, cls._bad_results):
            print("="*70)
            print("\n".join(result))
        print("success: %d   error: %d" % \
            (len(cls._good_results), len(cls._bad_results)))

    @classmethod
    @tdfw.following_method("test:start_recording")
    def _start_recording(cls, ticket):
        if cls._fook_methods[0]:
            cls._fook_methods[0](self.result)

    @classmethod
    @tdfw.following_method("test:stop_recording")
    def _stop_recording(cls, ticket):
        if test_manager._fook_methods[1]:
            test_manager._fook_methods[1](self, _traceback is None)

    @classmethod
    @tdfw.following_method("test:good_result")
    def _good_result(cls, ticket):
        cls._good_results.append(ticket.result)

    @classmethod
    @tdfw.following_method("test:bad_result")
    def _bad_result(cls, ticket):
        cls._bad_results.append(ticket.result)


def show_result():
    test_manager.show_result()