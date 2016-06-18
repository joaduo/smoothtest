# -*- coding: utf-8 -*-
'''
Simple RPC
Copyright (c) 2013, Joaquin G. Duo
'''
import rel_imp
rel_imp.init()
from types import FunctionType, TypeType
from ..import_unittest import unittest
from ..discover.TestDiscover import TestDiscoverBase, DiscoverCommandBase
from fnmatch import fnmatch
import re


def fake_init(class_, instance=True):
    '''
    Fake initialization of a class to avoid calling it's real __init__
    method. (replacing with a dummy one that does nothing)
    BEWARE!!: this is only useful for testing methods independent from
    calling the real __init__
    :param class_: class_ to be instanced or __init__'s replaced
    :param instance: if False the new fake class is returned, if True
        an instance of the fake class is returned
    '''
    class fake_init(class_):

        def __init__(self):
            pass
    if instance:
        return fake_init()
    else:
        return fake_init


class SmokeTestDiscover(TestDiscoverBase):

    '''
    Inspect in all modules for a smoke_test_module function.
    Then create a test for each module and run it.
    '''

    def __init__(self, func_regex, *args, **kwargs):
        self._func_regex = func_regex
        super(SmokeTestDiscover, self).__init__( *args, **kwargs)

    def get_missing(self, package):
        filter_ = lambda attr, _: isinstance(attr, (FunctionType, TypeType))

        func_dict = self.inspector.iter_modules(
            package, filter_, reload_=False)
        for module, funcs in func_dict:
            has_test = filter(
                lambda x: self._func_regex.match(x[1].__name__), funcs)
            unit_test = filter(lambda x: isinstance(x[1], TypeType)
                               and issubclass(x[1], unittest.TestCase), funcs)
            # smokeTest exists, or is not this module
            if not (has_test or unit_test):
                yield module


class SmokeCommand(DiscoverCommandBase):

    def __init__(self):
        super(SmokeCommand, self).__init__(desc='Smoke test discovery tool',
                                           print_missing=True)

    def get_parser(self):
        parser = super(SmokeCommand, self).get_parser()
        parser.add_argument('--function-regex', type=str,
                            help='Regex pattern to match smoke function name.',
                            default='^smoke_test_module$', nargs=1)
        return parser

    def _get_args_defaults(self):
        defaults = super(SmokeCommand, self)._get_args_defaults()
        defaults.update(pattern='*')
        return defaults

    def _set_test_discover(self, args):
        func_regex = re.compile(args.function_regex)
        pattern = args.pattern

        def filter_func(attr, mod):
            name = mod.__name__.split('.')[-1]
            return (isinstance(attr, FunctionType)
                    and hasattr(attr, '__name__')
                    and func_regex.match(attr.__name__)
                    and fnmatch(name, pattern))
        self.test_discover = SmokeTestDiscover(func_regex, filter_func, quiet=args.quiet)


# dummy function to avoid warnings inspecting this module
def smoke_test_module():
    main(
        ['-t', 'smoothtest.tests.example.smoke_test_example.smoke_test_module'])


def main(argv=None):
    SmokeCommand().main(argv)

if __name__ == "__main__":
    main()
