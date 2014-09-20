# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
from .Context import Context, singleton_decorator
from .base import AutoTestBase
import multiprocessing
import sys
import os

@singleton_decorator
class Main(AutoTestBase):
    def run(self, child_callback, embed_ipython=False):
        self.create_child(child_callback)
        def new_child():
            try:
                self.kill_child
            except Exception as e:
                self.log.e(e)
            self.create_child(child_callback)
        self._new_child = new_child
        if embed_ipython:
            from IPython import embed
            s = self #nice alias
            embed()
            self.kill_child
            raise SystemExit(0)
    
    @property
    def new_child(self):
        self._new_child()
        
    def new_test(self, test_path_regex, *test_path_regexes):
        pass
        
    def build_callback(self, test_paths, parcial_reloads, full_reloads=[],
             parcial_decorator=lambda x:x, full_decorator=lambda x:x, 
             slave=None, wait_type='poll'):
        
        def child_callback(child_pipe):
            ctx = Context()
            ctx.initialize(
                           test_paths=test_paths,
                           parcial_reloads=parcial_reloads,
                           full_reloads=full_reloads,
                           parcial_decorator=parcial_decorator,
                           full_decorator=full_decorator,
                           slave=slave,
                           #We are the child, so child_pipe is parent_pipe
                           #from this POV
                           child_conn=child_pipe,
                           wait_type=wait_type
                           )
            while 1:
                ctx.poll.next()
        
        return child_callback
    
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
        answer = self.send_recv('test_cmd')
        result, error = answer[0]
        if error:
            self.log.e(error)
        return result

    def send(self, cmd, *args, **kwargs):
        if self.poll():
            self.log.i('Remaining in buffer: %r'%self.parent_pipe.recv())
        self.parent_pipe.send(self.cmd(cmd, *args, **kwargs))
    
    def send_recv(self, cmd, *args, **kwargs):
        self.send(cmd, *args, **kwargs)
        return self.parent_pipe.recv()
    
    @property
    def kill_child(self):
        cmd = self.cmd(self._kill_command)
        if self.parent_pipe: #pipe is still open
            self.parent_pipe.send(cmd)
            self.log.i(self.parent_pipe.recv())
            self.parent_pipe.close()
            self.parent_pipe = None

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
