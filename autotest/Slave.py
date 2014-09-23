# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import multiprocessing
from .base import AutoTestBase
from .TestRunner import TestRunner
    

class Slave(AutoTestBase):
    def __init__(self, child_cls, child_args=[], child_kwargs={}, timeout=3):
        self._timeout = timeout
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self._process = None
        self._parent_conn = None
        self._first_test = True
        parent, child = multiprocessing.Pipe()
        self._parent_conn = parent
        self._child_conn = child

    def start_subprocess(self, post_callback=lambda: None):
        def target():
            post_callback()
            self.log.i('Forking at %s.'%self.__class__.__name__)
            self._parent_conn.close()
            self._child_cls(*self._child_args, **self._child_kwargs
                            ).wait_io(self._child_conn, 
                                    stdin=None, stdout=None, stderr=None
                                      )
        
        self._process = multiprocessing.Process(target=target)
        self._process.start()

    def restart_subprocess(self, post_callback):
        self.kill(block=True, timeout=self._timeout)
        self._first_test = True
        self.start_subprocess(post_callback)

    def recv(self):
        return self._parent_conn.recv()

    def send(self, msg):
        return self._parent_conn.send(msg)

    def get_conn(self):
        return self._parent_conn

    def kill(self, block=False, timeout=None):
        if not self._process:
            return
        
        if not self._process.is_alive():
            self.log.w('Child terminated by himself.'
                       ' Exitcode:' % self._process.exitcode)
            return
        
        self.send(self.cmd(self._child_cls._kill_command))

        if not block:
            return

        if self._parent_conn.poll(timeout):
            msg = self.recv()
            assert msg == TestRunner._kill_answer
            pid, status = self._process.ident, self._process.exitcode
            self.log.i('Child with pid {pid} gently terminated with exit '
                       'status {status}.'.format(pid=pid, status=status))
            return

        self._process.terminate()
        pid, status = self._process.ident, self._process.exitcode
        self.log.i('Child pid {pid} killed by force with exit status {status}.'
                   ''.format(pid=pid, status=status))
        self._process.join(timeout)

    def test(self, test_paths, smoke=False, block=False, repeat=True):
        self.send(self.cmd('test', test_paths, smoke=smoke))
        if not block:
            return
        else:
            return self.recv_answer(test_paths, repeat)

    def recv_answer(self, test_paths=[], repeat=False):
        answer = self.recv()
        if answer == self._kill_answer:
            answer = self.recv()
        self._first_test = False
        return answer[0]

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
