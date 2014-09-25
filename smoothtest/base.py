# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
from smoothtest.Logger import Logger
import traceback
import re
import os

class SmoothTestBase(object):
    log = Logger('autotest')
    
    def _path_to_modstr(self, tst):
        tst = tst.replace(os.path.sep, '.')
        tst = re.sub(r'\.(pyc)|(py)$', '', tst).strip('.')
        return tst

    def reprex(self, e):
        #TODO: shuoldn't format lat exception,but passed one
        return traceback.format_exc()

def smoke_test_module():
    s = SmoothTestBase()
    s.log.i(__file__)


if __name__ == "__main__":
    smoke_test_module()