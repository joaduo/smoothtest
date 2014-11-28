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
from smoothtest.webunittest.WebdriverManager import stop_display
from fnmatch import fnmatch


class TestResults(object):
    def __init__(self):
        self.total = []
        self.failures = []
        self.errors = []

    def append_unittest(self, mod_name, result):
        if result.errors:
            self.errors.append((mod_name, len(result.errors)))
        if result.failures:
            self.failures.append((mod_name, len(result.failures)))
        self.total.append((mod_name, result.testsRun))


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
        results = TestResults()
        for mod, attr_name, _ in self._gather(package):
            if modules and mod not in modules:
                continue
            result = self._run_test(mod, attr_name, argv, one_process)
            results.append_unittest(mod.__name__, result)
        return results

    def test_modules(self, tests, argv):
        results = TestResults()
        for tst in tests:
            if os.path.exists(tst):
                tst = self._path_to_test_path(tst)
            res = self.run_test(tst, argv)
            results.append_unittest(tst, res)
        return results

    def _path_to_test_path(self, path):
        mod = self._import(path)
        test_path = None
        for name, attr in inspect.getmembers(mod):
            if self.filter_func(attr, mod):
                test_path = self._get_test_path(mod, name)
                break
        assert test_path, 'Could not find any test under %r' % path
        return test_path

    def _import(self, path):
        return importlib.import_module(self._path_to_modstr(path))

    #Implement if you want to print missing attrs in modules
    get_missing = None

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
    #TODO:add similar arguments as unittest
    def __init__(self, desc='Test discovery tool'):
        self.description = desc
        self.test_discover = None

    def get_parser(self):
        parser = ArgumentParser(description=self.description)
        parser.add_argument('-t', '--tests', type=is_valid_file,
                    help='Specify the modules to run tests from (path or python'
                    ' namespace). If specified, no discovery is done.',
                    default=[], nargs='+')
        parser.add_argument('-p', '--pattern', type=str,
                    help='Pattern to match test module names -not files- '
                    '(\'test*\' default)',
                    default='test*', nargs=1)
        parser.add_argument('-P', '--packages', type=str,
                    help='Specify the packages to discover tests from. (path or python namespace)',
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
    
    def _import(self, path):
        self.test_discover._import(path)

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
            if missing and tdisc.get_missing:
                for m in tdisc.get_missing(pkg):
                    pth = self.get_module_file(m)
                    tdisc.log('Missing test in module %s' % m)
                    tdisc.log(formatPathPrint(pth))
        #return results
        return total, failed

    def _set_test_discover(self, args):
        raise NotImplementedError('Implement this method in concrete class.')

    def main(self, argv=None):
        args, unknown = self.get_parser().parse_known_args(argv)
        self._process_common_args(args)
        self._set_test_discover(args)
        assert self.test_discover, 'Value self.test_discover not set.'
        results = None
        if args.tests:
            results = self.test_discover.test_modules(args.tests, unknown)
        elif args.packages:
            results = self._discover_run(args.packages, argv=unknown,
                               missing=not getattr(args,'ignore_missing', True),
                               one_process=args.one_process)
        # Stop display in case we have a virtual display
        stop_display()
        # Report status
        if results:
            sum_func = lambda x,y: x + y[1]
            t = reduce(sum_func, results.total, 0)
            f = reduce(sum_func, results.failures, 0)
            e = reduce(sum_func, results.errors, 0)
            if f or e:
                last_msg = ('FAILURES={f} ERRORS={e} from a TOTAL={t}\n'
                           'Details:\n  Failed:{failed}\n  Erred:{erred}'.
                           format(f=f, e=e, t=t, failed=results.failures,
                                  erred=results.errors))
            else:
                last_msg = 'All {t} tests OK'.format(t=t)
            self.log.i(last_msg)


class DiscoverCommand(DiscoverCommandBase):
    '''
    Unittest discovering concrete class
    '''
    def _set_test_discover(self, args):
        # Unpack just in case args changes later
        pattern = args.pattern
        def unittest_filter_func(attr, mod):
            name = mod.__name__.split('.')[-1]
            return (isinstance(attr, TypeType)
                    and issubclass(attr, unittest.TestCase)
                    and fnmatch(name, pattern))
        self.test_discover = TestDiscoverBase(filter_func=unittest_filter_func)


def smoke_test_module():
    pass

def main(argv=None):
    DiscoverCommand().main(argv)

if __name__ == "__main__":
    main()
