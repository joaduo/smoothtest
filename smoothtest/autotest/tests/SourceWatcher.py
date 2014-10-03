# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import unittest
from ..SourceWatcher import SourceWatcher

class SourceWatcherTest(unittest.TestCase):
    def test_source_watcher(self):
        sw = SourceWatcher()
        #Start fork to watch files
        #create/modify them
        #record changes
        

if __name__ == "__main__":
    unittest.main()
