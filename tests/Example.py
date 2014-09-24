# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import unittest

class ContextTest(unittest.TestCase):
    def test_example(self):
        print 'Running test at %s!' % __file__.replace('.pyc','.py')

if __name__ == "__main__":
    unittest.main()
