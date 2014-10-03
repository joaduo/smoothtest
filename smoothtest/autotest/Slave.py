# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import multiprocessing
from .base import AutoTestBase
from .TestRunner import TestRunner


class Slave(AutoTestBase):
    def __init__(self, child_cls, child_args=[], child_kwargs={}, timeout=3):
        self._timeout = timeout
        self._child_args = child_args
        self._child_kwargs = child_kwargs
        self._child_cls = child_cls
        self._subprocess = None
        self._subprocess_conn = None
        self._first_test = True
        self._runner_cmd = 'test'
        
    def start_subprocess(self, post_callback=lambda: None):
        parent, child = multiprocessing.Pipe()
        def target():
            self.log.set_pre_post(pre='TestRunner ')
            post_callback()
            self.log.d('Forked process')
            parent.close()
            self._child_cls(*self._child_args, **self._child_kwargs
                            ).io_loop(child, 
                                    stdin=None, stdout=None, stderr=None
                                      )
        
        self._subprocess = multiprocessing.Process(target=target)
        self._subprocess.start()
        self._subprocess_conn = parent
        child.close()

    def restart_subprocess(self, post_callback):
        self.kill(block=True, timeout=self._timeout)
        self._first_test = True
        self.start_subprocess(post_callback)

    def get_conn(self):
        return self._subprocess_conn

    def kill(self, block=False, timeout=None):
        self._kill_subprocess(block, timeout)

    def test(self, test_paths, smoke=False, block=False):
        self._subprocess_conn.send(self.cmd(self._runner_cmd, test_paths, 
                                            smoke=smoke))
        if not block:
            return
        else:
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
        answers = self._subprocess_conn.recv()
        self.log.d('Received TestRunner\'s answer: ' + 
                   self.fmt_answers(answers))
        if self._get_answer(answers, self._kill_answer) == self._kill_answer:
            self.log.w('Answer is %r. Perhaps two kill commands sent?' % 
                       answers)
        self._first_test = False
        return self._get_answer(answers, self._runner_cmd)


def smoke_test_module():
    test_paths = ['smoothtest.tests.example.Example.Example.test_example']
    sat = Slave(TestRunner, [], {})
    sat.start_subprocess()
    sat.log.i(sat.test(test_paths, block=True))
    sat.log.i(sat.test(test_paths, block=True))
    sat.kill(block=True)

if __name__ == "__main__":
    smoke_test_module()
