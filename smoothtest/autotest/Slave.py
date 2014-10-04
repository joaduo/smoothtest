# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from .base import ParentBase


class Slave(ParentBase):
    def __init__(self, child_cls, child_args=[], child_kwargs={}, timeout=3):
        self._timeout = timeout
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self._subprocess = None
        self._subprocess_conn = None
        self._first_test = True
        
    def start_subprocess(self, post_callback=None):
        def callback(conn):
            if post_callback:
                post_callback()
            child = self._child_cls(*self._child_args, **self._child_kwargs)
            #wait for io
            child.io_loop(conn, stdin=None, stdout=None, stderr=None)
        
        super(Slave, self).start_subprocess(callback, pre='TestRunner')

    def restart_subprocess(self, post_callback):
        self.kill(block=True, timeout=self._timeout)
        self._first_test = True
        self.start_subprocess(post_callback)

    def test(self, test_paths, smoke=False, block=False):
        self.send(self._child_cls.test, test_paths, smoke=smoke)
        if block:
            return self.recv_answer()

    def _fmt_answer(self, ans):
        result = ans.result
        error = ans.error
        if ans.sent_cmd.cmd == 'test':
            if not ans.error and ans.result:
                error = '\n'
                error += ''.join('\n%s\n%s'% (m,e) for m,e in ans.result)
                result = 'Exceptions'
        return 'result: %r, errors: %s' % (result, error)

    def recv_answer(self):
        answers = self.recv()
        self.log.d('Received TestRunner\'s answer: ' + 
                   self.fmt_answers(answers))
        kans = self._get_answer(answers, self._kill_command)
        if kans and kans.result == self._kill_answer:
            self.log.w('Answer is %r. Perhaps 2 kill commands sent?' % 
                       answers)
        self._first_test = False
        return self._get_answer(answers, self._child_cls.test)


def smoke_test_module():
    from .TestRunner import TestRunner
    test_paths = ['smoothtest.tests.example.Example.Example.test_example']
    sat = Slave(TestRunner, [], {})
    sat.start_subprocess()
    sat.log.i(sat.test(test_paths, block=True))
    sat.log.i(sat.test(test_paths, block=True))
    sat.kill(block=True)

if __name__ == "__main__":
    smoke_test_module()
