# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import sys
#We want to use the new version of unittest in <= python 2.6
if sys.version_info < (2,7):
    import unittest2 as unittest
else:
    import unittest

unittest = unittest

#dummy function to avoid warnings inspecting this module
def smoke_test_module():
    from .Logger import Logger
    log = Logger('smoke')
    log.d([unittest.TestCase, unittest.TestLoader])

if __name__ == "__main__":
    smoke_test_module()
