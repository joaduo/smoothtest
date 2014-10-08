# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from ..base import SmoothTestBase
from .ModuleAttrIterator import ModuleAttrIterator
from ..import_unittest import unittest
import importlib
import subprocess
import shlex
from types import FunctionType, TypeType
import inspect
from argparse import ArgumentParser
import os


class TestDiscoverBase(SmoothTestBase):
    def __init__(self, filter_func):
        self.filter_func = filter_func
        self.inspector = ModuleAttrIterator()

    def _gather(self, package):
        iter_mod = self.inspector.iter_modules
        for module, attrs in iter_mod(package, self.filter_func, reload_=False):
            for attr in attrs:
                yield module, attr

    def _get_attr_name(self, mod, attr):
        if isinstance(attr, FunctionType):
            return attr.func_name
        elif issubclass(attr, object):
            return attr.__name__
        else:
            for name, val in inspect.getmembers(mod):
                if val is attr:
                    return name
    
    def discover_run(self, package, modules=[], argv=None):
        total = []
        failed = []
        for mod, attr in self._gather(package):
            if modules and mod not in modules:
                continue
            failed_amount = self._run_test(mod, attr, argv)
            if failed_amount:
                failed.append((mod.__name__, failed_amount))
            #count total tests per TestClass
            _, suite = self._get_test_suite(self._get_test_path(mod, attr))
            total.append((mod.__name__, suite.countTestCases()))
        return total, failed

    #def get_missing(self, package):
    #    msg = 'You need to implement this method in a subclass'
    #    raise NotImplementedError(msg)

    def _get_class_file(self):
        module = importlib.import_module(self.__class__.__module__)
        return self.get_module_file(module)

    def _get_test_path(self, mod, attr):
        attr_name = self._get_attr_name(mod, attr)
        return '%s.%s' % (mod.__name__, attr_name)        

    def _run_test(self, mod, attr, argv):
        #call this same script with a different argument
        #we need to test them in another process to avoid concurrency
        #between tests
        prog = self._get_class_file()
        cmd = 'python %r -t %s' % (prog, self._get_test_path(mod, attr))
        cmd = shlex.split(cmd) + argv
        self.log.d('Running test with: %r'%(cmd,))
        return subprocess.call(cmd)

    def _get_test_suite(self, test_path):
        modstr, attr_name = self.split_test_path(test_path)
        module = importlib.import_module(modstr)
        func_cls = getattr(module, attr_name)
        log = self.log
        if (isinstance(func_cls, TypeType) 
        and issubclass(func_cls, unittest.TestCase)):
            #Its already a test class
            TestClass = func_cls
        elif callable(func_cls):
            class TestClass(unittest.TestCase):
                def test_func(self):
                    log('Testing %s at %s' % (func_cls, modstr))
                    func_cls()
        else:
            raise TypeError('Tested object %r muset be subclass of TestCase or'
                            ' a callable.' % func_cls)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
        return TestClass, suite

    def run_test(self, test_path, argv=None):
        self.log.d('Running %r' % test_path)
        TestClass, suite = self._get_test_suite(test_path)
        if hasattr(TestClass, 'setUpProcess'):
            TestClass.setUpProcess(argv)
        results = unittest.TextTestRunner().run(suite)
        raise SystemExit(len(results.errors))


class DiscoverCommandBase(SmoothTestBase):
    def __init__(self, test_discover, description='Test discovery tool'):
        self.test_discover = test_discover
        self.description = description

    def get_parser(self):
        parser = ArgumentParser(description=self.description)
        parser.add_argument('-t', '--tests', type=str,
                    help='Specify the modules to run smoke tests from.',
                    default=[], nargs='+')
        parser.add_argument('-p', '--packages', type=str,
                    help='Specify the packages to discover smoke tests from.',
                    default=[], nargs='+')
        if hasattr(self.test_discover, 'get_missing'):
            parser.add_argument('-i', '--ignore-missing',
                        help='Ignore missing smoke tests.',
                        default=False, action='store_true')
        return parser
    
    def _test_modules(self, tests, argv):
        for tst in tests:
            self.test_discover.run_test(tst, argv)
    
    def _discover_run(self, packages, argv=None, missing=True):
        #pydev friendly printing
        def formatPathPrint(path, line=None):
            if not line:
                line = 1
            path = os.path.realpath(path)
            return '  File "%tdisc", line %d\n' % (path, line)
        total, failed = [], []
        tdisc = self.test_discover
        for pkg_pth in packages:
            pkg = importlib.import_module(self._path_to_modstr(pkg_pth))
            #run and count
            t,f = tdisc.discover_run(pkg, argv=argv)
            total += t
            failed += f
            #Print missing
            if missing:
                for m in tdisc.get_missing(pkg):
                    pth = self.get_module_file(m)
                    tdisc.log('Missing test in module %s' % m)
                    tdisc.log(formatPathPrint(pth))
        #return results
        return total, failed

    def main(self, argv=None):
        args, unknown = self.get_parser().parse_known_args(argv)
        if args.tests:
            self._test_modules(args.tests, unknown)
        elif args.packages:
            total, failed = self._discover_run(args.packages, argv=unknown,
                               missing=not getattr(args,'ignore_missing', True))
            sum_func = lambda x,y: x + y[1]
            t = reduce(sum_func, total, 0)
            f = reduce(sum_func, failed, 0)
            if failed:
                self.log.i('FAILED {f} from {t}\n  Detail:{failed}'.
                           format(f=f, t=t, failed=failed))
            else:
                self.log.i('All {t} tests OK'.format(t=t))


class TestRunner(TestDiscoverBase):
    def __init__(self):
        filter_func = lambda attr, mod: (isinstance(attr, TypeType)
                                         and issubclass(attr, unittest.TestCase)
                                         and mod.__name__ != 'base')
        super(TestRunner, self).__init__(filter_func)


def smoke_test_module():
    pass    

def main(argv=None):
    DiscoverCommandBase(TestRunner()).main(argv)

if __name__ == "__main__":
    main()
