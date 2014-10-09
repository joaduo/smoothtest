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
from types import FunctionType, TypeType
from argparse import ArgumentParser
import os
import importlib
import inspect
from ..autotest.base import ParentBase


class TestDiscoverBase(ParentBase):
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
    
    def discover_run(self, package, modules=[], argv=None, one_process=False):
        total = []
        failed = []
        for mod, attr in self._gather(package):
            if modules and mod not in modules:
                continue
            results = self._run_test(mod, attr, argv, one_process)
            if results.errors or results.failures:
                f = len(results.errors) + len(results.failures)
                failed.append((mod.__name__, f))
            total.append((mod.__name__, results.testsRun))
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

    def _run_test(self, mod, attr, argv, one_process):
        test_path = self._get_test_path(mod, attr)
        if one_process:
            results = self.run_test(test_path, argv)
        else:
            self.start_subprocess(self.dispatch_cmds, pre='Discover Runner')
            self.send(self.run_test, test_path, argv)
            results = self._get_answer(self.recv(), self.run_test).result
            self.kill(block=True, timeout=10)
        return results
    
    def dispatch_cmds(self, conn):
        while True:
            self._dispatch_cmds(conn)

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
        return results


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
        parser.add_argument('-o', '--one-process',
                    help='Run all tests inside 1 single process.',
                    default=False, action='store_true')
        if hasattr(self.test_discover, 'get_missing'):
            parser.add_argument('-i', '--ignore-missing',
                        help='Ignore missing smoke tests.',
                        default=False, action='store_true')
        return parser
    
    def _test_modules(self, tests, argv):
        for tst in tests:
            self.test_discover.run_test(self._path_to_modstr(tst), argv)
    
    def _discover_run(self, packages, argv=None, missing=True, one_process=False):
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
            t,f = tdisc.discover_run(pkg, argv=argv, one_process=one_process)
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
                               missing=not getattr(args,'ignore_missing', True),
                               one_process=args.one_process)
            sum_func = lambda x,y: x + y[1]
            t = reduce(sum_func, total, 0)
            f = reduce(sum_func, failed, 0)
            if failed:
                self.log.i('FAILURES + ERRORS={f} from {t}\n    '
                           'Problems detail:{failed}'.
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
