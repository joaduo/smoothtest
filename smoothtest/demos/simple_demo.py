# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest


class TestXpathBrowser(unittest.TestCase):
    def test_select(self):
        print '-select' * 10

    def test_foo(self):
        print '-foo' * 10

    def test_bar(self):
        print '-bar' * 10


if __name__ == "__main__":
    unittest.main()
