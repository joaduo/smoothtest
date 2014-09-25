# -*- coding: utf-8 -*-
'''
Simple RPC
Copyright (c) 2013, Joaquin G. Duo
'''
import rel_imp; rel_imp.init()
from unittest.loader import TestLoader
from unittest.case import TestCase
from unittest.runner import TextTestRunner
from unittest.suite import TestSuite
from types import FunctionType, TypeType, ModuleType
from importlib import import_module
from ..base import SmoothTestBase
import os
import pkgutil
import unittest
from argparse import ArgumentParser
import importlib
import subprocess
import shlex


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
        if (isinstance(package, ModuleType) 
        and not hasattr(package, '__path__')):
            yield package
        else:
            prefix = package.__name__ + '.'
            for _, modname, ispkg in pkgutil.walk_packages(package.__path__,
                                                           prefix):
                if not ispkg:
                    module = import_module(modname)
                    if reload_:
                        module = reload(module)
                    yield module


class SmokeTestDiscover(SmoothTestBase):
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
        for module, funcs in self.inspector.iter_modules(package, filter_func, 
                                                         reload_=False):
            if funcs:
                yield module, funcs[0]

    def get_missing(self, package):
        filter_ = lambda attr, module: isinstance(attr, (FunctionType,TypeType))

        func_dict = self.inspector.iter_modules(package, filter_, reload_=False)
        for module, funcs in func_dict:
            has_test = filter(lambda x: x.__name__ == self._func_name, funcs)
            unit_test = filter(lambda x: isinstance(x, TypeType) and issubclass(x, unittest.TestCase), funcs)
            #smokeTest exists, or is not this module
            if not (has_test or unit_test):
                yield module

    def discover_run(self, package, modules=[]):
        total = 0
        failed = 0
        for mod, func in self._gather(package):
            if modules and mod not in modules:
                continue
            if self._run_test(mod):
                failed += 1
            total +=1
        return total, failed

    def _run_test(self, mod):
        cmd = 'python %r -t %s' % (__file__, mod.__name__)
        return subprocess.call(shlex.split(cmd))

    def run_test(self, modstr):
        module = importlib.import_module(modstr)
        func = getattr(module, self._func_name)
        log = self.log
        class SmokeTest(TestCase):
            def test_func(self):
                log('Testing %s' % func.__module__)
                func()
        
        s = TestLoader().loadTestsFromTestCase(SmokeTest)
        big_suite = TestSuite([s])
        results = TextTestRunner().run(big_suite)
        raise SystemExit(len(results.errors))


class SmokeCommand(SmoothTestBase):
    def get_parser(self):
        parser = ArgumentParser(description='Start a local sales vs non-sales glidepath server')
        parser.add_argument('-t', '--tests', type=str,
                            help='Specify the modules to run smoke tests from.',
                            default=[], nargs='+')
        parser.add_argument('-p', '--packages', type=str,
                            help='Specify the packages to discover smoke tests from.',
                            default=[], nargs='+')
        parser.add_argument('-i', '--ignore-missing',
                            help='Ignore missing smoke tests.',
                            default=False, action='store_true')
        return parser
    
    def _test_modules(self, tests):
        s = SmokeTestDiscover()
        for tst in tests:
            s.run_test(tst)
    
    def _discover_run(self, packages, missing=True):
        #pydev friendly printing
        def formatPathPrint(path, line=None):
            if not line:
                line = 1
            path = os.path.realpath(path)
            return '  File "%s", line %d\n' % (path, line)
        total, failed = 0, 0
        s = SmokeTestDiscover()
        for pkg_str in packages:
            pkg = importlib.import_module(self._path_to_modstr(pkg_str))
            #run and count
            t,f = s.discover_run(pkg)
            total += t
            failed += f
            #Print missing
            if missing:
                for m in s.get_missing(pkg):
                    f = m.__file__
                    if f.endswith('.pyc'):
                        f = f[:-1]
                    s.log('Missing test in module %s' % m)
                    s.log(formatPathPrint(f))
        #return results
        return total, failed
    
    def main(self, argv=None):
        args = self.get_parser().parse_args(argv)
        if args.tests:
            self._test_modules(args.tests)
        elif args.packages:
            total, failed = self._discover_run(args.packages, missing=not args.ignore_missing)
            self.log.i('Total={total} Failed={failed}'.format(**locals()))


def smoke_test_module():
    pass

def main(argv=None):
    SmokeCommand().main(argv)

if __name__ == "__main__":
    main()
