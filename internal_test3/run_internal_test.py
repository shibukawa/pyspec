# -*- coding: utf-8 -*-

import os
import sys

dirname = os.path.dirname(os.path.abspath(os.path.join(".", __file__)))
parent_dir = os.path.split(dirname)[0]
sys.path.insert(0, parent_dir)

from pyspec3.utils.mini_test import show_result


def show_usage():
    print("""PySpec internal test launcher
  for Python 3.0, 3.1 (current interpreter: %d.%d.%d)

  run_internal_test.py target:

  *target
    --all:         run all test
    --verifier:    test basic verifier
    --mockobject:  test mockobject
""" % sys.version_info[:3])
    sys.exit()

def main():
    is_run = False

    if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
        show_usage()

    if "--verifier" in sys.argv or "--all" in sys.argv:
        import test_verify_methods
        is_run = True

    if "--mockobject" in sys.argv or "--all" in sys.argv:
        import test_mock_object
        is_run = True

    if not is_run:
        show_usage()
    show_result()


if __name__ == "__main__":
    main()


