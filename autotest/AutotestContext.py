# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
#parent_pipe, child_pipe = multiprocessing.Pipe()
import relative_import
from zmq.backend import zmq_poll
from .MasterAutoTest import MasterAutotest
from .SlaveAutotest import SlaveAutotest
from .ChildTestRunner import ChildTestRunner
import select

class singleton_decorator(object):
    '''
      Singleton pattern decorator.
      There will be only one instance of the decorated class.
      Decorator always returns same instance.
    '''
    def __init__(self, class_):
        self.class_ = class_
        self.instance = None
    def __call__(self, *a, **ad):
        if self.instance == None:
            self.instance = self.class_(*a,**ad)
        return self.instance

@singleton_decorator
class AutotestContext(object):
    def __init__(self):
        self.master = None
        self.slave = None
        self.ipython_ipc = None
        
    def initialize(self, wait_type='poll', parcial_decorator=None, ipython_pipe=None):
        test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
        parcial_loads, full_loads =['fulcrum/views/sales/tests/about_us.py'], []
        ########
        self.master = MasterAutotest()
        self.slave = SlaveAutotest(ChildTestRunner)
        poll = _select = None
        if wait_type == 'poll':
            poll = zmq_poll
        else:
            _select = select.select
        self.poll = self.master.test_all(test_paths, 
                                        parcial_loads, full_loads,
                                        parcial_decorator=parcial_decorator,
                                        slave=self.slave,
                                        poll=poll, 
                                        select=_select,
                                        ipython_pipe=ipython_pipe,
                                        )

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
