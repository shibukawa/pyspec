# -*- encoding: utf-8 -*-

"""
need to support multiprocessing, threading
"""


from __future__ import with_statement


from logging import (getLevelName, CRITICAL, DEBUG, ERROR,
                     FATAL, INFO, NOTSET, WARN, WARNING)

import os
import re
import sys
import inspect
import threading
import collections

try:
    from multiprocessing import Queue
    from multiprocessing import Lock
except ImportError:
    from Queue import Queue
    from threading import Lock


_variable_name_splitter = re.compile("ddump\((.*)\)")
_output_queue = Queue()
_dprint_flag = {}

class _lock(object):
    _lock_obj = Lock()
    def __enter__(self):
        _lock_obj.acquire()

    def __exit__(self, _type, _value, _traceback):
        _lock_obj.release()
        return _type is None


class _basic_config_type(object):
    __slots__ = ("level", "filename", "_file")
    def __init__(self):
        self.level = DEBUG
        self.filename = None
        self._file = None


_basic_config = _basic_config_type()


class _LogStore(object):
    _records = []
    def append(record):
        with _lock():
            record.index = len(self._records)
            self._records.append(record)


class _LogRecord(object):
    def __init__(self, message, filename, funcname, linono, level):
        self.message = message
        self.filename = filename
        self.funcname = funcname
        self.lineno = lineno
        self.index = None


def set_config(level=None, filename=None):
    if level is not None:
        _basic_config["level"] = level
    if filename is not None:
        _basic_config["filename"] = filename
        logfile = _basic_config.get("_file")
        if logfile:
            logfile.close()
        _basic_config["_file"] = file(filename, "w")


def debug(msg):
    if _basic_config < DEBUG:
        return


def info(msg):
    if _basic_config < INFO:
        return


def warning(msg):
    if _basic_config < WARNING:
        return


def error(msg):
    if _basic_config < ERROR:
        return


def critical(msg):
    if _basic_config < CRITICAL:
        return


def ddump(obj):
    debug_status = _debug_info()
    if not debug_status[0]:
        return
    _dprint_function_info(debug_status)
    match = _variable_name_splitter.search("".join(inspect.stack()[1][4]))
    if match:
        if match.group(1) != str(obj):
            print("%s = %s" % (match.group(1), str(obj)))
        else:
            print(obj)
    else:
        print(obj)


def dprint(*messages):
    """Debug print function"""
    debug_status = _debug_info()
    if not debug_status[0]:
        return
    _dprint_function_info(debug_status)
    print(" ".join(messages))


def dprint_for_lib(*messages):
    """Debug print function for internal use

    This function won't show function information.
    """
    is_debug = _debug_info()[0]
    if not is_debug:
        return
    print(" ".join(messages))


def enable_debug_print():
    sys._getframe(1).f_locals["_debug_print_enabler_object"] = \
        _debug_print_enabler()


def _key():
    return (os.getpid(), threading.currentThread().getName())


def _set_debug(value=True):
    """"""
    flag = _dprint_flag.setdefault(_key(), [0, -1])
    if value:
        flag[0] += 1
    else:
        flag[0] -= 1


def _debug_info():
    """"""
    return _dprint_flag.setdefault(_key(), [0, -1])


def _dprint_function_info(debug_status):
    frame_obj = sys._getframe(2)
    frame_id = id(frame_obj)
    code_obj = frame_obj.f_code
    if debug_status[1] == frame_id:
        return
    print("%s() in '%s'(%d)" % (code_obj.co_name,
        os.path.basename(code_obj.co_filename), code_obj.co_firstlineno))
    del frame_obj
    debug_status[1] = frame_id


class _debug_print_enabler(object):
    """"""
    def __init__(self):
        _set_debug(True)

    def __del__(self):
        _set_debug(False)


def test_main():
    test1()
    test2()
    dprint("not print")

def test1():
    a = 1
    b = 2
    ddump(a)
    enable_debug_print()
    ddump(b)
    test1_1()
    test1_2()

def test1_1():
    dprint("from test1_1")

def test1_2():
    dprint("from test2_1")

def test2():
    enable_debug_print()
    dprint("from test2")
    test2_2()


def test2_2():
    enable_debug_print()
    dprint("from test2_2")


def test_with():
    with lock():
        print("ok")


if __name__ == "__main__":
    #test_main()
    test_with()