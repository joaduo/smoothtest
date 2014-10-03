# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import unittest
from ..Context import Context

class ContextTest(unittest.TestCase):
    def test_context(self):
        ctx = Context()
        ctx.initialize({})

if __name__ == "__main__":
    unittest.main()
