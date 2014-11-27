# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from .ModuleAttrIterator import ModuleAttrIterator
from smoothtest.import_unittest import unittest
from types import FunctionType, TypeType
from argparse import ArgumentParser
import os
import importlib
import inspect
from smoothtest.autotest.base import ParentBase
from smoothtest.base import CommandBase, is_valid_file


class TestDiscoverBase(ParentBase):
    def __init__(self, filter_func):
        self.filter_func = filter_func
        self.inspector = ModuleAttrIterator()

    def _gather(self, package):
        iter_mod = self.inspector.iter_modules2
        for module, attrs in iter_mod(package, self.filter_func, reload_=False):
            for name, attr in attrs:
                yield module, name, attr

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
        for mod, attr_name, _ in self._gather(package):
            if modules and mod not in modules:
                continue
            result = self._run_test(mod, attr_name, argv, one_process)
            if result.errors or result.failures:
                f = len(result.errors) + len(result.failures)
                failed.append((mod.__name__, f))
            total.append((mod.__name__, result.testsRun))
        return total, failed

    #def get_missing(self, package):
    #    msg = 'You need to implement this method in a subclass'
    #    raise NotImplementedError(msg)

    def _get_class_file(self):
        module = importlib.import_module(self.__class__.__module__)
        return self.get_module_file(module)

    def _get_test_path(self, mod, attr_name):
        return '%s.%s' % (mod.__name__, attr_name)

    def _run_test(self, mod, attr_name, argv, one_process):
        test_path = self._get_test_path(mod, attr_name)
        if one_process:
            result = self.run_test(test_path, argv, one_process)
        else:
            self.start_subprocess(self.dispatch_cmds, pre='Discover Runner')
            self.send(self.run_test, test_path, argv, one_process)
            result = self._get_answer(self.recv(), self.run_test).result
            self.kill(block=True, timeout=10)
        return result
    
    def dispatch_cmds(self, conn):
        while True:
            self._dispatch_cmds(conn)

    def _get_test_class(self, test_path):
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
            raise TypeError('Tested object %r must be subclass of TestCase or'
                            ' a callable.' % func_cls)
        return TestClass

    def run_test(self, test_path, argv=None, one_process=False):
        self.log.d('Running %r' % test_path)
        TestClass = self._get_test_class(test_path)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
        if hasattr(TestClass, 'setUpProcess'):
            TestClass.setUpProcess(argv)
        result = unittest.TextTestRunner().run(suite)
        if not one_process:
            result = self.to_pickable_result(result)
        return result


class DiscoverCommandBase(CommandBase):
    #TODO:add same arguments as unittest
    def __init__(self, test_discover, description='Test discovery tool'):
        self.test_discover = test_discover
        self.description = description

    def get_parser(self):
        parser = ArgumentParser(description=self.description)
        parser.add_argument('tests', type=is_valid_file,
                    help='Specify the modules to run tests from.',
                    default=[], nargs='+')
        parser.add_argument('-p', '--packages', type=str,
                    help='Specify the packages to discover tests from.',
                    default=[], nargs='+')
        parser.add_argument('-o', '--one-process',
                    help='Run all tests inside 1 single process.',
                    default=False, action='store_true')
        if hasattr(self.test_discover, 'get_missing'):
            parser.add_argument('-i', '--ignore-missing',
                        help='Ignore missing smoke tests.',
                        default=False, action='store_true')
        self._add_smoothtest_common_args(parser)
        return parser
    
    def _test_modules(self, tests, argv):
        for tst in tests:
            if os.path.exists(tst):
                tst = self._path_to_test_path(tst)
            self.test_discover.run_test(tst, argv)

    def _path_to_test_path(self, path):
        mod = self._import(path)
        test_path = None
        for name, attr in inspect.getmembers(mod):
            if unittest_filter_func(attr, mod):
                test_path = self.test_discover._get_test_path(mod, name)
                break
        assert test_path, 'Could not find any test under %r' % path
        return test_path

    def _import(self, path):
        return importlib.import_module(self._path_to_modstr(path))

    def _discover_run(self, packages, argv=None, missing=True, one_process=False):
        #pydev friendly printing
        def formatPathPrint(path, line=None):
            if not line:
                line = 1
            path = os.path.realpath(path)
            return '  File "%r", line %d\n' % (path, line)
        total, failed = [], []
        # Nicer alias
        tdisc = self.test_discover
        for pkg_pth in packages:
            pkg = self._import(pkg_pth)
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
        self._process_common_args(args)
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


def unittest_filter_func(attr, mod):
    return (isinstance(attr, TypeType)
            and issubclass(attr, unittest.TestCase)
            and mod.__name__ != 'base')


class TestRunner(TestDiscoverBase):
    def __init__(self):
        super(TestRunner, self).__init__(filter_func=unittest_filter_func)


def smoke_test_module():
    pass

def main(argv=None):
    DiscoverCommandBase(TestRunner()).main(argv)

if __name__ == "__main__":
    main()
