#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import nose
import logging
import appengine_config


# Setup logging before anything else can override it.
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-8s [%(filename)s:%(lineno)s] %(message)s')
# Setup paths.
current_path = os.path.abspath(os.path.dirname(__file__))
tests_path = os.path.join(current_path, 'tests')

PATHS = [
    current_path,
    tests_path,
]
for pth in PATHS:
  sys.path.insert(1, pth)


all_tests = [f[:-8] for f in os.listdir(tests_path) if f.endswith('_test.py')]


def get_suite(tests):
  tests = sorted(tests)
  suite = nose.suite.LazySuite()
  loader = nose.loader.TestLoader()
  for test in tests:
    suite.addTest(loader.loadTestsFromName(test))
  return suite


if __name__ == '__main__':
  tests = sys.argv[1:]
  if not tests:
    tests = all_tests
  tests = ['%s_test' % t for t in tests]
  suite = get_suite(tests)
  nose.core.TextTestRunner(verbosity=2).run(suite)
