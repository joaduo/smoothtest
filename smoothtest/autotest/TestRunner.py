# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import importlib
import unittest
import rel_imp
rel_imp.init()
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.settings.default import TEST_RUNNER_LIFE, TEST_ROUND_LIFE
from .base import ChildBase
from smoothtest.TestResults import TestResults, TestException
from smoothtest.base import TestRunnerBase


class TestRunner(ChildBase, TestRunnerBase):

    '''
    Responsabilities
        - Import the Test Class
        - Run test over all methods or specific methods
        - Report any errors
    '''

    def __init__(self):
        super(TestRunner, self).__init__()
        self._level_mngr = WebdriverManager().enter_level(level=TEST_RUNNER_LIFE)

    def test(self, test_paths, argv=[], smoke=False):
        '''
        :param test_paths: iterable like ['package.module.test_class.test_method', ...]
        '''
        results = TestResults()
        if smoke or not test_paths:
            if not test_paths:
                self.log.i('Empty tests')
            else:
                self.log.i('Smoke mode. No test ran.')
            return results
        level_mngr = WebdriverManager().enter_level(level=TEST_ROUND_LIFE)
        for tpath in test_paths:
            class_ = self._import_test(tpath)
            if isinstance(class_, TestException):
                results.append_result(tpath, class_)
            else:
                result = self._run_test(tpath, argv, class_)
                results.append_result(tpath, result)
        level_mngr.exit_level()
        return results

    def io_loop(self, conn, stdin=None, stdout=None, stderr=None):
        while True:
            self._dispatch_cmds(conn)

    def _receive_kill(self, *args, **kwargs):
        self._tear_down_process()
        self._level_mngr.exit_level()

    def _run_test(self, test_path, argv, class_):
        try:
            _, _, methstr = self._split_path(test_path)
            suite = unittest.TestSuite()
            suite.addTest(class_(methstr))
            runner = unittest.TextTestRunner()
            self._setup_process(class_, test_path, argv)
            return runner.run(suite)
        except Exception as e:
            return self.reprex(e)

    def _split_path(self, test_path):
        return self.split_test_path(test_path, meth=True)

    def _import_test(self, test_path):
        modstr, clsstr, _ = self._split_path(test_path)
        try:
            module = importlib.import_module(modstr)
            module = reload(module)
            class_ = getattr(module, clsstr)
            return class_
        except Exception as e:
            return self.reprex(e)


def smoke_test_module():
    from .base import AutotestCmd
    test_paths = ['smoothtest.tests.example.test_Example']
    tr = TestRunner()

    class DummyIpc(object):

        def recv(self):
            cmds = [
                AutotestCmd('test', (test_paths,), dict(smoke=True)),
            ]
            self.recv = self.recv2
            return cmds

        def recv2(self):
            cmds = [
                AutotestCmd(TestRunner._kill_command, (0,), {}),
            ]
            self.recv = lambda: []
            return cmds

        def send(self, msg):
            print 'Sending:', msg
            return 1

        def close(self):
            pass
    try:
        tr.io_loop(DummyIpc())
    except SystemExit as e:
        tr.log.i(e)


if __name__ == "__main__":
    smoke_test_module()
