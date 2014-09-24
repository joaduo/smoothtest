# -*- coding: utf-8 -*-
'''
Simple RPC
Copyright (c) 2013, Joaquin G. Duo
'''
import relative_import
from unittest.loader import TestLoader
from unittest.case import TestCase
from unittest.runner import TextTestRunner
from unittest.suite import TestSuite
from types import FunctionType, TypeType
from importlib import import_module
from ..base import SmoothTestBase
import os
import pkgutil
import unittest
import multiprocessing


class ModulesAttributesIterator(SmoothTestBase):
    def iter_modules(self, package, filter_func, reload_=False):
        for module in self._gatherModules(package, reload_):
            yield module, list(self._filterModule(module, filter_func))

    def _filterModule(self, module, filter_func):
        for attr in module.__dict__.values():
            if (getattr(attr, '__module__', None) == module.__name__
            and filter_func(attr, module)):
                yield attr

    def _gatherModules(self, package, reload_):
        prefix = package.__name__ + '.'
        for _, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
            if not ispkg:
                module = import_module(modname)
                if reload_:
                    module = reload(module)
                yield module


class SmokeTestRunner(SmoothTestBase):
    '''
    Inspect in all simplerpc modules for a smokeTestModule function.
    Then create a test for each class and runs it.
    '''
    def __init__(self):
        self.inspector = ModulesAttributesIterator()
        self._func_name = 'smoke_test_module'

    def _gather(self, package):
        filter_func = lambda attr, module: (isinstance(attr, FunctionType) 
                                          and hasattr(attr, '__name__') 
                                          and attr.__name__ == self._func_name)
        for _, funcs in self.inspector.iter_modules(package, filter_func, 
                                                         reload_=False):
            if funcs:
                yield funcs[0]

    def get_missing(self, package):
        filter_ = lambda attr, module: isinstance(attr, (FunctionType,TypeType))

        func_dict = self.inspector.iter_modules(package, filter_, reload_=False)
        for module, funcs in func_dict:
            has_test = filter(lambda x: x.__name__ == self._func_name, funcs)
            unit_test = filter(lambda x: isinstance(x, TypeType) and issubclass(x, unittest.TestCase), funcs)
            #smokeTest exists, or is not this module
            if not (has_test or unit_test):
                yield module

    def run_tests(self, package):
        suites = []
        for func in self._gather(package):
            s = TestLoader().loadTestsFromTestCase(self._create_test(func))
            suites.append(s)
        big_suite = TestSuite(suites)
        TextTestRunner().run(big_suite)

    def _create_test(self, func, timeout=10):
        log = self.log
        reprex = self.reprex
        class SmokeTest(TestCase):
            def test_func(self):
                log('Testing %s' % func.__module__)
                parent, child = multiprocessing.Pipe(duplex=False)
                def wrapper():
                    parent.close()
                    msg = False, None
                    try: 
                        func()
                        msg = True, None
                    except Exception as e:
                        msg = False, reprex(e)
                    child.send(msg)
                    child.recv()
                    #child.close()
                    #raise SystemExit(0)
                
                p = multiprocessing.Process(target=wrapper)
                p.start()
                child.close()
                success, exc = False, None
                #success on first param
                #if parent.poll(timeout):
                success, exc = parent.recv()
                p.terminate()
                parent.close()
                p.join()
                if not success:
                    raise Exception(exc)
        return SmokeTest


def smoke_test_module():
    pass


def formatPathPrint(path, line=None, error=False):
    if not line:
        line = 1
    path = os.path.realpath(path)
    return '  File "%s", line %d\n' % (path, line)


def main(argv=None):
    import smoothtest
    s = SmokeTestRunner()
    s.run_tests(smoothtest)
    for m in s.get_missing(smoothtest):
        f = m.__file__
        if f.endswith('.pyc'):
            f = f[:-1]
        s.log('Missing test in module %s' % m)
        s.log(formatPathPrint(f))


if __name__ == "__main__":
    main()
