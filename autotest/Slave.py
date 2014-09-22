# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import os
import multiprocessing
import signal
from .base import AutoTestBase
from .TestRunner import TestRunner

class Slave(AutoTestBase):
    def __init__(self, child_cls, child_args=[], child_kwargs={}, timeout=1):
        self._timeout = timeout
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self.child_process = None
        self._parent_conn = None
        self._first_test = True

    def start_subprocess(self, watcher=None):
        parent_pipe, child_pipe = multiprocessing.Pipe()
#        parent_stdin, child_stdin = multiprocessing.Pipe()
#        parent_stdout, child_stdout = multiprocessing.Pipe()
#        parent_stderr, child_stderr = multiprocessing.Pipe()
        
        def callback():
            if watcher:
                watcher.unwatch_all()
            self.log.i('Forking at %s.'%self.__class__.__name__)
            for pp in [parent_pipe, 
#                       parent_stdin, parent_stdout, parent_stderr
                       ]:
                pp.close()
            self._child_cls(*self._child_args, **self._child_kwargs
                            ).wait_io(child_pipe, 
                                    stdin=None, stdout=None, stderr=None
                                      )
        
        self.child_process = multiprocessing.Process(target=callback)
        self.child_process.start()
        self._parent_conn = parent_pipe
#        self._stdin = parent_stdin
#        self._stdout = parent_stdout
#        self._stderr = parent_stderr
        for pp in [child_pipe, 
#                child_stdin, child_stdout, child_stderr
                   ]:
            pp.close()

#        else: #child
#            if watcher:
#                watcher.unwatch_all()
#            self.log.i('Forking at %s.'%self.__class__.__name__)
#            for pp in [parent_pipe, 
##                       parent_stdin, parent_stdout, parent_stderr
#                       ]:
#                pp.close()
#            self._child_cls(*self._child_args, **self._child_kwargs
#                            ).wait_io(child_pipe, 
#                                    stdin=None, stdout=None, stderr=None
#                                      )

    def restart_subprocess(self, watcher):
        self.kill(block=True, timeout=self._timeout)
        if self._parent_conn:
            self._parent_conn.close()
        self._first_test = True
        self.start_subprocess(watcher)

    def recv(self):
        return self._parent_conn.recv()

    def send(self, msg):
        return self._parent_conn.send(msg)

    def get_conn(self):
        return self._parent_conn

    def kill(self, block=False, timeout=None):
        if not self.child_process:
            return
        
        if not self.child_process.is_alive():
            self.log.w('Child terminated by himself.'
                       ' Exitcode:' % self.child_process.exitcode)
            return
        
        self.send(self.cmd(self._child_cls._kill_command))

        if not block:
            return

        if self._parent_conn.poll(timeout):
            msg = self.recv()
            #assert msg == TestRunner._kill_answer
            pid, status = self.child_process.ident, self.child_process.exitcode
            self.log.i('Child with pid {pid} gently terminated with exit '
                       'status {status}.'.format(pid=pid, status=status))
            return

        self.child_process.terminate()
        pid, status = self.child_process.ident, self.child_process.exitcode
        self.log.i('Child pid {pid} killed by force with exit status {status}.'
                   ''.format(pid=pid, status=status))

    def test(self, test_paths, smoke=False, block=False, repeat=True):
        self.send(self.cmd('test', test_paths, smoke=smoke))
        if not block:
            return
        else:
            return self.recv_answer(test_paths, repeat)

    def recv_answer(self, test_paths=[], repeat=False):
        answer = self.recv()
        testing_errors = answer[0][0]
        if not self._first_test and testing_errors and repeat:
            assert test_paths, 'If repeating where you need to provide test_paths'
            msg = [('test', [test_paths], {})]
            self.log.i('Test import error, restarting process and repeating tests %r'%test_paths)
            self.restart_subprocess()
            self.send(msg)
            answer = self.recv()
        self._first_test = False
        return answer

def smoke_test_module():
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    sat = Slave(TestRunner, [], {})
    sat.start_subprocess()
    print sat.test(test_paths, block=True)
    print sat.test(test_paths, block=True)
    sat.kill()
    sat.kill(block=True)
    print 'parent ended'

if __name__ == "__main__":
    smoke_test_module()
