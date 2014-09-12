# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
from smoothtest.Logger import Logger

class AutoTestBase(object):
    log = Logger('at')

def smoke_test_module():
    base = AutoTestBase()
    base.log.d('Debug')
    base.log.i('Info')

if __name__ == "__main__":
    smoke_test_module()
