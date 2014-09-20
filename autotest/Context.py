# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
#parent_pipe, child_pipe = multiprocessing.Pipe()
import relative_import
from zmq.backend import zmq_poll
from .Master import Master
from .Slave import Slave
from .TestRunner import TestRunner
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
class Context(object):
    def __init__(self):
        self.master = None
        self.slave = None
        self.ipython_ipc = None
        
    def initialize(self, test_paths, parcial_reloads, full_reloads=[],
             parcial_decorator=lambda x:x, full_decorator=lambda x:x, 
             slave=None, ipython_pipe=None, wait_type='poll'):
        self.master = Master()
        self.slave = slave or Slave(TestRunner)
        poll = _select = None
        if wait_type == 'poll':
            poll = zmq_poll
        else:
            _select = select.select
        self.poll = self.master.test_all(test_paths, 
                                        parcial_reloads=parcial_reloads, 
                                        full_reloads=full_reloads,
                                        parcial_decorator=parcial_decorator,
                                        full_decorator=full_decorator,
                                        slave=self.slave,
                                        poll=poll, 
                                        select=_select,
                                        ipython_pipe=ipython_pipe,
                                        )

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
