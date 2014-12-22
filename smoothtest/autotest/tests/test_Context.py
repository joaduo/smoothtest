# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.Context import Context
import unittest


class ContextTest(unittest.TestCase):

    def test_context(self):
        ctx = Context()
        ctx.initialize({})

if __name__ == "__main__":
    unittest.main()
