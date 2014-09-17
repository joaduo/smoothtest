# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
from smoothtest.autotest.base import AutoTestBase
import multiprocessing

class SlaveAutotest(AutoTestBase):
    def __init__(self, child_cls, child_args, child_kwargs):
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self._child_pid = None
        self._pipe_ipc = None
        self._first_test = True
    
    def start_subprocess(self):
        '''
        pipes
        fork
        close pipes
        test
        '''
        parent_pipe, child_pipe = multiprocessing.Pipe()

        pid = os.fork()
        if pid:
            self._child_pid = pid
            self._pipe_ipc = parent_pipe
            return pid
        else:
            self._child_cls(*self._child_args, **self._child_kwargs
                            ).wait_io(child_pipe)

    def restart_subprocess(self):
        self.kill(force=True)
        if self._pipe_ipc:
            self._pipe_ipc.close()
        self._first_test = True
        self.start_subprocess()
    
    def recv(self):
        return self._pipe_ipc.recv()
    
    def send(self, msg):
        return self._pipe_ipc.send(msg)
    
    def get_in_fd(self):
        return self._pipe_ipc.fileno()

    def kill(self, force=False):
        self.send([
                    (self._child_cls._kill_command, ('Gently killing the process',), {}),
                    ])
        if force:
            print NotImplementedError()

    def test(self, test_paths, block=False, repeat=True):
        msg = [('test', [test_paths], {})] 
        self.send(msg)
        if not block:
            answer = None
        else:
            answer = self.recv()
            testing_errors = answer[0][0]
            if not self._first_test and testing_errors and repeat:
                self.log.i('Test lookup error, restarting process and repeating tests %r'%test_paths)
                self.restart_subprocess()
                self.send(msg)
                answer = self.recv()
        #Tested at least once
        self._first_test = False
        #ok, return the answer
        return answer

def smoke_test_module():
    from smoothtest.autotest.ChildTestRunner import ChildTestRunner
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    sat = SlaveAutotest(ChildTestRunner, [], {})
    sat.start_subprocess()
    print sat.test(test_paths, block=True)
    sat.test(test_paths)
    print sat.recv()
    print sat.test(test_paths, block=True)
    print sat.test(test_paths, block=True, repeat=False)
    sat.kill()

if __name__ == "__main__":
    smoke_test_module()
