# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
from .AutotestContext import singleton_decorator
import multiprocessing
import sys
from smoothtest.autotest.base import AutoTestBase
from IPython import embed

@singleton_decorator
class AutotestNotebook(AutoTestBase):
    def init_notebook(self, child_callback):
        self.create_child(child_callback)
        def new_child():
            try:
                self.kill_child
            except Exception as e:
                self.log.e(e)
            self.create_child(child_callback)
        self._new_child = new_child
        s = self #nice alias
        embed()
        self.kill_child
        raise SystemExit(0)
    
    @property
    def new_child(self):
        self._new_child()
    
    def create_child(self, child_callback):
        parent_pipe, child_pipe = multiprocessing.Pipe()
        self.parent_pipe = parent_pipe
        pid = os.fork()
        if pid: #parent
            #Child will use this pipe
            child_pipe.close()
            #return to ipython
            return pid
        else: #child
            #Setup IO #not yet needed
            #from cStringIO import StringIO
            #keep old stdout and stderr
            #self._stdout,  self._stderr = sys.stdout, sys.stderr
            #sys.stdout = StringIO()
            #sys.stderr = StringIO()
            #Close input, parent will listen to it
            sys.stdin.close()
            #This pipe is not needed (parent will use it)
            parent_pipe.close()
            child_callback(child_pipe)
        
    def poll(self):
        return self.parent_pipe.poll()
    
    @property
    def test(self):
        print self.sendb('test')

    def send(self, cmd, *args, **kwargs):
        if self.poll():
            self.log.i('Remaining in buffer: %r'%self.parent_pipe.recv())
        self.parent_pipe.send(self.cmd(cmd, *args, **kwargs))
    
    def sendb(self, cmd, *args, **kwargs):
        self.send(cmd, *args, **kwargs)
        return self.parent_pipe.recv()
    
    @property
    def kill_child(self):
        cmd = self.cmd(self._kill_command)
        self.parent_pipe.send(cmd)
        self.log.i(self.parent_pipe.recv())
        self.parent_pipe.close()
        self.parent_pipe = None

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
