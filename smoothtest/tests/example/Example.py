# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest

class Example(unittest.TestCase):
    def __init__(self, methodName='example'):
        methodName='example'
        unittest.TestCase.__init__(self, methodName=methodName)
    def test_example(self):
        print 'Running test at %s!' % __file__
        
#    def test_example2(self):
#        print 'Running test2 at %s!' % __file__

if __name__ == "__main__":
    unittest.main()
