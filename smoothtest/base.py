# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
from smoothtest.Logger import Logger
import traceback

class SmoothTestBase(object):
    log = Logger('autotest')
    
    def reprex(self, e):
        #TODO: shuoldn't format lat exception,but passed one
        return traceback.format_exc()

def smoke_test_module():
    s = SmoothTestBase()
    s.log.i(__file__)


if __name__ == "__main__":
    smoke_test_module()