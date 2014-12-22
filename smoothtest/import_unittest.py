# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import sys
# We want to use the new version of unittest in <= python 2.6
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

unittest = unittest


def smoke_test_module():
    import rel_imp
    rel_imp.init()
    from .Logger import Logger
    log = Logger('smoke')
    # If we are in old unittest some of this classes are missing
    log.d([unittest.TestCase, unittest.TestLoader, unittest.TestSuite,
           unittest.TextTestRunner])

if __name__ == "__main__":
    smoke_test_module()
