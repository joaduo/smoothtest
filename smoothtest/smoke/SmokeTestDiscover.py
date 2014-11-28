# -*- coding: utf-8 -*-
'''
Simple RPC
Copyright (c) 2013, Joaquin G. Duo
'''
import rel_imp; rel_imp.init()
from types import FunctionType, TypeType
from ..import_unittest import unittest
from ..discover.TestDiscover import TestDiscoverBase, DiscoverCommandBase


class SmokeTestDiscover(TestDiscoverBase):
    '''
    Inspect in all modules for a smoke_test_module function.
    Then create a test for each module and run it.
    '''
    def __init__(self, func_name='smoke_test_module'):
        self._func_name = func_name
        filter_func = lambda attr, _: (isinstance(attr, FunctionType) 
                                      and hasattr(attr, '__name__') 
                                      and attr.__name__ == self._func_name)
        super(SmokeTestDiscover, self).__init__(filter_func)

    def get_missing(self, package):
        filter_ = lambda attr, _: isinstance(attr, (FunctionType, TypeType))

        func_dict = self.inspector.iter_modules(package, filter_, reload_=False)
        for module, funcs in func_dict:
            has_test = filter(lambda x: x.__name__ == self._func_name, funcs)
            unit_test = filter(lambda x: isinstance(x, TypeType) 
                               and issubclass(x, unittest.TestCase), funcs)
            #smokeTest exists, or is not this module
            if not (has_test or unit_test):
                yield module


class SmokeCommand(DiscoverCommandBase):
    def __init__(self):
        super(SmokeCommand, self).__init__(desc='Smoke test discovery tool')


#dummy function to avoid warnings inspecting this module
def smoke_test_module():
    pass


def main(argv=None):
    SmokeCommand().main(argv)

if __name__ == "__main__":
    main()
