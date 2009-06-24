# -*- coding: utf-8 -*-


import io
import sys
import traceback
import itertools
import pyspec3.support.tdfw as tdfw


def setup(method):
   test_manager._fook_methods[0] = method
   return method


def teardown(method):
   test_manager._fook_methods[1] = method
   return method


class test:
    _io = []
    def __init__(self, test_name="", exception=None):
        self.test_name = test_name
        self.exception = exception

    @tdfw.expose_method("test", "start_recording")
    def __enter__(self):
        if not self._io:
            self._io = [sys.stdout, sys.stderr]
        output = io.StringIO()
        sys.stdout = output
        sys.stderr = output
        tdfw.notify("test", "start_recording")

    @tdfw.expose_method("test", "stop_recording")
    @tdfw.expose_method("test", "good_result")
    @tdfw.expose_method("test", "bad_result")
    def __exit__(self, _type, _value, _traceback):
        result = ["TestCase: %s" % self.test_name, "-"*70]
        tdfw.notify("test", "stop_recording")
        if self._io:
            console = sys.stdout.getvalue()
            sys.stdout = self._io[0]
            sys.stderr = self._io[1]
        else:
            console = ""
        console = ""
        if not self.exception:
            if _traceback is None:
                result.append("OK")
                tdfw.notify("test", "good_result", result=result)
            else:
                tb = "".join(traceback.format_exception(_type, _value, _traceback))
                result += [tb, "----console----", console]
                tdfw.notify("test", "bad_result", result=result)
        else:
            if _type is self.exception:
                result.append("OK")
                tdfw.notify("test", "good_result", result=result)
            elif _type is None:
                msg = "expected exception is '%s' but no exception raised" % \
                    self.exception.__name__
                result += [msg, "----console----", console]
                tdfw.notify("test", "bad_result", result=result)
            else:
                msg = "expected exception is '%s' but '%s' was raised" % \
                    (self.exception.__name__, _type.__name__)
                result += [msg, "----console----", console]
                tdfw.notify("test", "bad_result", result=result)
        return True


class test_manager(metaclass=tdfw.Commitable):
    _good_results = []
    _bad_results = []
    _fook_methods = [None, None]

    @classmethod
    def show_result(cls):
        for result in itertools.chain(cls._good_results, cls._bad_results):
            print("="*70)
            print("\n".join(result), "\n\n")
        print("success: %d   error: %d" % \
            (len(cls._good_results), len(cls._bad_results)))

    @classmethod
    @tdfw.commit_method("test", "start_recording")
    def _start_recording(cls, ticket):
        if cls._fook_methods[0]:
            cls._fook_methods[0](self.result)

    @classmethod
    @tdfw.commit_method("test", "stop_recording")
    def _stop_recording(cls, ticket):
        if test_manager._fook_methods[1]:
            test_manager._fook_methods[1](self, _traceback is None)

    @classmethod
    @tdfw.commit_method("test", "good_result")
    def _good_result(cls, ticket):
        cls._good_results.append(ticket.result)

    @classmethod
    @tdfw.commit_method("test", "bad_result")
    def _good_result(cls, ticket):
        cls._bad_results.append(ticket.result)
