# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
import multiprocessing
import select
import signal
import relative_import
from .base import AutoTestBase
from .ChildTestRunner import ChildTestRunner

class SlaveAutotest(AutoTestBase):
    def __init__(self, child_cls, child_args=[], child_kwargs={}, timeout=1):
        self._timeout = timeout
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self._child_pid = None
        self._pipe_ipc = None
        self._first_test = True

    def start_subprocess(self):
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
        self.kill(block=True, timeout=self._timeout)
        if self._pipe_ipc:
            self._pipe_ipc.close()
        self._first_test = True
        self.start_subprocess()

    def recv(self):
        return self._pipe_ipc.recv()

    def send(self, msg):
        return self._pipe_ipc.send(msg)

    def get_pipe(self):
        return self._pipe_ipc

    def kill(self, block=False, timeout=None):
        #TODO: make multiplatform Mac OS works?
        pid, status = os.waitpid(self._child_pid, os.WNOHANG)
        if pid:
            self.log.i('Child with pid {pid} terminated by himself with'
                       ' exit status {status}.'.format(pid=pid, status=status))
            return

        self.send([
                    (self._child_cls._kill_command, [0], {}),
                    ])

        if not block:
            return

        if timeout:
            rlist, _, _ = select.select([self._pipe_ipc], [], [], timeout)
        else:
            rlist, _, _ = select.select([self._pipe_ipc], [], [])

        if rlist:
            msg = self.recv()
            #assert msg == ChildTestRunner._kill_answer
            pid, status = os.waitpid(self._child_pid, 0)
            self.log.i('Child with pid {pid} gently terminated with exit '
                       'status {status}.'.format(pid=pid, status=status))
            return

        os.kill(self._child_pid, signal.SIGKILL)
        pid, status = os.waitpid(self._child_pid, 0)
        self.log.i('Child pid {pid} killed by force with exit status {status}.'
                   ''.format(pid=pid, status=status))

    def test(self, test_paths, block=False, repeat=True):
        msg = [('test', [test_paths], {})]
        self.send(msg)
        if not block:
            return
        else:
            return self.recv_answer(test_paths, repeat)

    def recv_answer(self, test_paths, repeat=False):
        msg = [('test', [test_paths], {})]
        answer = self.recv()
        testing_errors = answer[0][0]
        if not self._first_test and testing_errors and repeat:
            self.log.i('Test import error, restarting process and repeating tests %r'%test_paths)
            self.restart_subprocess()
            self.send(msg)
            answer = self.recv()
        self._first_test = False
        return answer

def smoke_test_module():
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    sat = SlaveAutotest(ChildTestRunner, [], {})
    sat.start_subprocess()
    print sat.test(test_paths, block=True)
    print sat.test(test_paths, block=True)
    sat.kill()
    sat.kill(block=True)
    print 'parent ended'

if __name__ == "__main__":
    smoke_test_module()
