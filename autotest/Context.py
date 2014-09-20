# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
#parent_pipe, child_pipe = multiprocessing.Pipe()
import relative_import
from .Master import Master
from .Slave import Slave
from .TestRunner import TestRunner

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
             slave=None, poll=None, select=None, child_conn=None):
        self.master = Master()
        self.slave = slave or Slave(TestRunner)
        self.poll = self.master.test(test_paths, 
                                        parcial_reloads=parcial_reloads, 
                                        full_reloads=full_reloads,
                                        parcial_decorator=parcial_decorator,
                                        full_decorator=full_decorator,
                                        slave=self.slave,
                                        poll=poll, 
                                        select=select,
                                        child_conn=child_conn,
                                        )

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
