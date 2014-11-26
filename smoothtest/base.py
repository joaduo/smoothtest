# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
from smoothtest.Logger import Logger
import re
import os
from smoothtest.settings.solve_settings import solve_settings


class SmoothTestBase(object):
    log = Logger('autotest')
    
    @property
    def global_settings(self):
        return solve_settings()

    def _path_to_modstr(self, tst):
        tst = tst.replace(os.path.sep, '.')
        tst = re.sub(r'\.(pyc)|(py)$', '', tst).strip('.')
        return tst

    def split_test_path(self, test_path, meth=False):
        test_path = test_path.split('.')
        if meth:
            offset = -2
            module = '.'.join(test_path[:offset])
            class_ = test_path[offset]
            method = test_path[offset+1]
            return module, class_, method
        else: #only module+class
            offset = -1
            module = '.'.join(test_path[:offset])
            class_ = test_path[offset]
            return module, class_

    def get_module_file(self, module):
        pth = module.__file__
        if pth.endswith('.pyc'):
            pth = pth[:-1]
        return pth

class CommandBase(SmoothTestBase):
    pass

def smoke_test_module():
    s = SmoothTestBase()
    s.log.i(__file__)


if __name__ == "__main__":
    smoke_test_module()
