# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
from .base import AutoTestBase
from multiprocessing import Process, Pipe
import re
import importlib
import traceback
from unittest import TestCase
from inspect import isclass


class TestSearcher(AutoTestBase):
    def _build_solve_paths(self, test_path_regex, *test_path_regexes, **kwargs):
        def solve_paths(conn):
            #return test paths
            #return parcial reloads paths
            specific_class = kwargs.get('specific_class')
            test_class = kwargs.get('test_class', TestCase)
            tst_regex = list(test_path_regexes) + [test_path_regex]
            test_paths = set()
            parcial_reloads = set()
            valid = re.search if kwargs.get('search', True) else re.match
            for tst_pth, regex in tst_regex:
                try:
                    if specific_class:
                        modstr, clsstr = self.split_test_path(tst_pth)
                        mod = importlib.import_module(modstr)
                        cls = getattr(mod, clsstr)
                        self.append_methods(test_paths, parcial_reloads, 
                                            mod, cls, regex, valid, modstr, clsstr)
                    else:
                        modstr = tst_pth
                        mod = importlib.import_module(tst_pth)
                        for _, cls in vars(mod).iteritems():
                            if not isclass(cls) or not issubclass(cls, test_class):
                                continue
                            clsstr = cls.__name__
                            self.append_methods(test_paths, parcial_reloads, 
                                       mod, cls, regex, valid, modstr, clsstr)
                                
                except Exception:
                    traceback.print_exc()
            conn.send([test_paths, parcial_reloads])
        return solve_paths
    
    def append_methods(self, test_paths, parcial_reloads, mod, cls, regex, valid, modstr, clsstr):
        for mthstr, _ in vars(cls).iteritems():
            if (mthstr.startswith('test') 
            and (not regex or valid(regex, mthstr))):
                path = '.'.join([modstr, clsstr, mthstr])
                test_paths.add(path)
                parcial_reloads.add(self.get_module_file(mod))        
                
    def get_module_file(self, module):
        return module.__file__.replace('.pyc','.py')
    
    def solve_paths(self, test_path_regex, *test_path_regexes, **kwargs):
        #We need to create a new process to avoid importing the modules
        #in the parent process
        solve = self._build_solve_paths(test_path_regex, *test_path_regexes,  **kwargs)
        parent_conn, child_conn = Pipe(duplex=False)
        p = Process(target=solve, args=(child_conn,))
        p.start()
        test_paths, parcial_reloads = parent_conn.recv()   # prints "[42, None, 'hello']"
        parent_conn.close()
        p.join()
        return test_paths, parcial_reloads


def smoke_test_module():
    from pprint import pprint
    ts = TestSearcher()
    test_paths, parcial_reloads = ts.solve_paths(('smoothtest.tests.example.Example', ''))
    pprint(test_paths)
    pprint(parcial_reloads)

if __name__ == "__main__":
    smoke_test_module()
