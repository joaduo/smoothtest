# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
#parent_pipe, child_pipe = multiprocessing.Pipe()
import relative_import
from .Master import Master

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
        
    def initialize(self, **test_config):
        self.master = Master()
        self.poll = self.master.test(**test_config)

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
