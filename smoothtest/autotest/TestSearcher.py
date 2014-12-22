# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
rel_imp.init()
from multiprocessing import Process, Pipe
from inspect import isclass
from .base import AutoTestBase
from ..import_unittest import unittest
import re
import importlib
import traceback

# TODO: optionally use TestLoader.loadTestsFromNames from unittest
# inheriting and replacing TestLoader.suiteClass = suite.TestSuite to extract
# the found classes


class TestSearcher(AutoTestBase):
    # TODO: rename test_path_regex to test_path

    def _build_solve_paths(
            self,
            test_path_regex,
            *test_path_regexes,
            **kwargs):
        def solve_paths(conn):
            specific_class = kwargs.get('specific_class')
            test_class = kwargs.get('test_class', unittest.TestCase)
            tst_regex = list(test_path_regexes) + [test_path_regex]
            test_paths = set()
            partial_reloads = set()
            valid = re.search if kwargs.get('search', True) else re.match
            for tst_pth, regex in tst_regex:
                try:
                    if specific_class:
                        # We are looking for a specific class
                        modstr, clsstr = self.split_test_path(tst_pth)
                        mod = importlib.import_module(modstr)
                        cls = getattr(mod, clsstr)
                        self.append_methods(test_paths, partial_reloads, mod,
                                            cls, regex, valid, modstr, clsstr)
                    else:
                        # Nicer alias
                        modstr = tst_pth
                        mod = importlib.import_module(modstr)
                        for _, cls in vars(mod).iteritems():
                            if (not isclass(cls)
                                    or not issubclass(cls, test_class)):
                                continue
                            clsstr = cls.__name__
                            self.append_methods(
                                test_paths,
                                partial_reloads,
                                mod,
                                cls,
                                regex,
                                valid,
                                modstr,
                                clsstr)

                except Exception:
                    traceback.print_exc()
            conn.send([test_paths, partial_reloads])
        return solve_paths

    def append_methods(self, test_paths, partial_reloads, mod, cls, regex,
                       valid, modstr, clsstr):
        for mthstr, _ in vars(cls).iteritems():
            if (mthstr.startswith('test')
                    and (not regex or valid(regex, mthstr))):
                path = '.'.join([modstr, clsstr, mthstr])
                test_paths.add(path)
                partial_reloads.add(self.get_module_file(mod))

    def get_module_file(self, module):
        return module.__file__.replace('.pyc', '.py')

    def solve_paths(self, test_path_regex, *test_path_regexes, **kwargs):
        # We need to create a new process to avoid importing the modules
        # in the parent process
        solve = self._build_solve_paths(test_path_regex, *test_path_regexes,
                                        **kwargs)
        parent_conn, child_conn = Pipe(duplex=False)
        p = Process(target=solve, args=(child_conn,))
        p.start()
        test_paths, partial_reloads = parent_conn.recv()
        parent_conn.close()
        p.join()
        return test_paths, partial_reloads


def smoke_test_module():
    from pprint import pprint
    ts = TestSearcher()
    test_paths, partial_reloads = ts.solve_paths(
        ('smoothtest.tests.example.test_Example', ''))
    pprint(test_paths)
    pprint(partial_reloads)

if __name__ == "__main__":
    smoke_test_module()
