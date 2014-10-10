# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from .base import ParentBase
from smoothtest.autotest.base import TestException


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

    def test(self, test_paths, argv=[], smoke=False, block=False):
        self.send(self._child_cls.test, test_paths, argv, smoke)
        if block:
            return self.recv_answer()

    def _collect_stats(self, ans):
        exceptions = errored = failed = total = 0
        exlist = []
        errlist = []
        faillist = []
        for tst_pth, result in ans.result:
            if isinstance(result, TestException):
                #exception running test
                exceptions += 1
                exlist.append(tst_pth)
                continue
            #TestResult with failures or errors
            result.errors and errlist.append(tst_pth)
            result.failures and faillist.append(tst_pth)
            errored += len(result.errors)
            failed += len(result.failures)
            total += result.testsRun
        if not (failed and errored and exceptions):
            msg = 'All %s OK' % total
        else:
            msg = ('EXCEPT:{exceptions} FAILED:{failed} ERROR:{errored}'
                   ' TOTAL:{total}'.format(**locals()))
        for typ, lst in [('exceptions', exlist), ('erros', errlist), 
                    ('failures', faillist)]:
            msg += '\n  with %s: %s' % (typ, lst)
        return msg

    def _fmt_answer(self, ans):
        if ans.sent_cmd.cmd == self._get_cmd_str(self._child_cls.test):
            if ans.error:
                return 'Exception importing initializing test: %r' % ans.error
            return self._collect_stats(ans)
        else:
            return super(Slave, self)._fmt_answer(ans)

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
    pre = 'smoothtest.tests.example.Example.'
    test_paths = [pre+'Example.test_example',
                  pre+'Example.test_error',
                  pre+'Example.test_failure',
                  pre+'NonExistingExample.test',
      'smoothtest.tests.example.ErroringExample.ErroringExample.test_example',
                  ]
    sat = Slave(TestRunner, [], {})
    sat.start_subprocess()
    for i in range(1,len(test_paths)+1):
        sat.log.i(sat.test(test_paths[:i], block=True))
    sat.kill(block=True)

if __name__ == "__main__":
    smoke_test_module()
