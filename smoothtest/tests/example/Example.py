# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest


class Example(unittest.TestCase):
    def test_example(self):
        print 'Running test at %s!' % __file__

    def test_error(self):
        raise LookupError('Unexpected error!')
    
    def test_failure(self):
        self.assertTrue(False, 'On purpose!')


if __name__ == "__main__":
    unittest.main()
