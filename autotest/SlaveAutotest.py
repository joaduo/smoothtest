# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
from smoothtest.autotest.base import AutoTestBase
from smoothtest.autotest.PipeIpc import PipeIpc

class SlaveAutotest(AutoTestBase):
    def __init__(self, child_cls, child_args, child_kwargs):
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self._in_fd = None
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
        parent_in = os.pipe()
        parent_out = os.pipe()
        self._in_fd = parent_in[0]
        pid = os.fork()
        if pid:
            self._child_pid = pid
            self._pipe_ipc = PipeIpc(parent_in, parent_out)
            return pid
        else:
            self._child_cls(*self._child_args, **self._child_kwargs
                            ).wait_io(PipeIpc(parent_out, parent_in))

    def restart_subprocess(self):
        self.kill(force=True)
        if self._pipe_ipc:
            self._pipe_ipc.close()
        self._first_test = True
        self.start_subprocess()
    
    def read(self):
        return self._pipe_ipc.read()
    
    def write(self, msg):
        return self._pipe_ipc.write(msg)
    
    def get_in_fd(self):
        return self._in_fd

    def kill(self, force=False):
        self.write([
                    (self._child_cls._kill_command, ('Gently killing the process',), {}),
                    ])
        if force:
            print NotImplementedError()

    def test(self, test_paths, repeat=True):
        msg = [('test', [test_paths], {})]
        answer = self.write(msg)
        assert answer
        _, err = answer[0]
        
        if not self._first_test and err and repeat:
            self.log.i('Repeating tests %r'%test_paths)
            self.restart_subprocess()
            answer = self.write(msg)
        #Tested at least once
        self._first_test = False
        #ok, return the answer
        return answer

def smoke_test_module():
    from smoothtest.autotest.ChildTestRunner import ChildTestRunner
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    sat = SlaveAutotest(ChildTestRunner, [], {})
    sat.start_subprocess()
#    sat.test(test_paths)
#    sr = ChildTestRunner()
#    class DummyIpc(object):
#        def read(self):
#            cmds = [
#                    ('test', (test_paths,), {}),
#                    ]
#            self.read = self.read2
#            return cmds
#        
#        def read2(self):
#            cmds = [
#                    ('raise SystemExit', ('Gently killing the process',), {}),
#                    ]
#            self.read = lambda : []
#            return cmds
#
#        def write(self, msg):
#            print msg
#            return 1
#    
#    sr.wait_io(DummyIpc())

if __name__ == "__main__":
    smoke_test_module()
