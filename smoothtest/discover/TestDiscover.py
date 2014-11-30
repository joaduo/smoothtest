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
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
import importlib
import inspect
from smoothtest.autotest.base import ParentBase
from smoothtest.base import CommandBase, is_valid_file, TestRunnerBase
from smoothtest.webunittest.WebdriverManager import stop_display
from fnmatch import fnmatch
from smoothtest.TestResults import TestResults


class TestFunction(unittest.TestCase):
    def __init__(self, function, modstr, log, methodName='runTest'):
        self.function = function
        self.modstr = modstr
        self.log = log
        unittest.TestCase.__init__(self, methodName=methodName)

    def runTest(self):
        self.log('Testing %s at %s' % (self.function, self.modstr))
        self.function()


class TestDiscoverBase(ParentBase, TestRunnerBase):
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
    
    def test_package(self, package, modules=[], argv=None, one_process=False):
        results = TestResults()
        for mod, attr_name, _ in self._gather(package):
            if modules and mod not in modules:
                continue
            test_path = self._get_test_path(mod, attr_name)
            result = self._run_test(test_path, argv, one_process)
            results.append_unittest(mod.__name__, result)
        return results

    def test_modules(self, mod_paths, argv=None, one_process=False):
        results = TestResults()
        for test_path in mod_paths:
            if os.path.exists(test_path):
                test_path = self._path_to_test_path(test_path)
            res = self._run_test(test_path, argv, one_process)
            results.append_unittest(test_path, res)
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

    def _run_test(self, test_path, argv, one_process):
        if one_process:
            result = self.run_test(test_path, argv, one_process)
        else:
            self.start_subprocess(self.dispatch_cmds, pre='Discover Runner')
            result = self.call_remote(self.run_test, test_path, argv, one_process)
            self.kill(block=True, timeout=10)
            self.stop_display()
        return result
    
    def stop_display(self):
        '''
        Stop display if there is a virtual screen running
        '''
        stop_display()

    def dispatch_cmds(self, conn):
        while True:
            self._dispatch_cmds(conn)

    def _get_test_class(self, test_path, argv):
        modstr, attr_name = self.split_test_path(test_path)
        module = importlib.import_module(modstr)
        func_cls = getattr(module, attr_name)
        log = self.log
        if (isinstance(func_cls, TypeType) 
        and issubclass(func_cls, unittest.TestCase)):
            # Its already a test class, lets instance it
            self._setup_process(func_cls, test_path, argv)
            suite = unittest.TestLoader().loadTestsFromTestCase(func_cls)
        elif callable(func_cls):
            # Its a callable, we wrap it around a test
            test = TestFunction(func_cls, modstr, log)
            suite = unittest.TestSuite([test])
        else:
            raise TypeError('Tested object %r must be subclass of TestCase or'
                            ' a callable.' % func_cls)
        return suite

    def run_test(self, test_path, argv=None, one_process=False):
        self.log.d('Running %r' % test_path)
        suite = self._get_test_class(test_path, argv)
        result = unittest.TextTestRunner().run(suite)
        self._tear_down_process()
        if not one_process and not self._is_pickable(result):
            result = self.to_pickable_result(result)
        return result


class DiscoverCommandBase(CommandBase):
    '''
    Common class to build test discovery tools. Base classes can filter
    modules arbitrarily for specific classes or functions.
    '''
    #TODO:add similar arguments as unittest
    def __init__(self, desc='Test discovery tool'):
        self.description = desc
        self.test_discover = None

    def _get_args_defaults(self):
        return {}

    def get_parser(self):
        defaults = self._get_args_defaults()
        parser = ArgumentParser(description=self.description,
                                formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument('-t', '--tests', type=is_valid_file,
                    help='Specify the modules to run tests from (path or python'
                    ' namespace). If specified, no discovery is done.',
                    default=defaults.get('tests',[]), nargs='+')
        parser.add_argument('-p', '--pattern', type=str,
                    help='Fnmatch pattern to match test module names, not files.',
                    default=defaults.get('pattern','test*'), nargs=1)
        parser.add_argument('-P', '--packages', type=str,
                    help='Specify the packages to discover tests from. (path or python namespace)',
                    default=defaults.get('packages',[]), nargs='+')
        parser.add_argument('-o', '--one-process',
                    help='Run all tests inside 1 single process.',
                    default=defaults.get('one_process', False), action='store_true')
        if hasattr(self.test_discover, 'get_missing'):
            parser.add_argument('-i', '--ignore-missing',
                        help='Ignore missing smoke tests.',
                        default=defaults.get('ignore_missing', False), action='store_true')
        self._add_smoothtest_common_args(parser)
        return parser
    
    def _import(self, path):
        return self.test_discover._import(path)

    def _discover_run(self, packages, argv=None, missing=True, one_process=False):
        #pydev friendly printing
        def formatPathPrint(path, line=None):
            if not line:
                line = 1
            path = os.path.realpath(path)
            return '  File "%r", line %d\n' % (path, line)
        #total, failed = [], []
        results = TestResults()
        # Nicer alias
        tdisc = self.test_discover
        for pkg_pth in packages:
            pkg = self._import(pkg_pth)
            #run and count
            res = tdisc.test_package(pkg, argv=argv, one_process=one_process)
            results.append_results(res)
            #Print missing
            if missing and tdisc.get_missing:
                for m in tdisc.get_missing(pkg):
                    pth = self.get_module_file(m)
                    tdisc.log('Missing test in module %s' % m)
                    tdisc.log(formatPathPrint(pth))
        #return results
        return results

    def _set_test_discover(self, args):
        raise NotImplementedError('Implement this method in concrete class.')

    def main(self, argv=None):
        args, unknown = self.get_parser().parse_known_args(argv)
        self._process_common_args(args)
        self._set_test_discover(args)
        assert self.test_discover, 'Value self.test_discover not set.'
        results = None
        if args.tests:
            results = self.test_discover.test_modules(args.tests,
                                                  argv=unknown,
                                                  one_process=args.one_process)
        elif args.packages:
            results = self._discover_run(args.packages, argv=unknown,
                               missing=not getattr(args,'ignore_missing', True),
                               one_process=args.one_process)
        # Stop display in case we have a virtual display
        self.test_discover.stop_display()
        # Report status
        if results:
            self.log.i(str(results))


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
    main(['-t','smoothtest.tests.example.test_Example.Example'])

def main(argv=None):
    DiscoverCommand().main(argv)

if __name__ == "__main__":
    main()
