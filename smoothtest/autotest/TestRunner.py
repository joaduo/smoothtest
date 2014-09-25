# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import importlib
import unittest
import relative_import
from .base import AutoTestBase

class TestRunner(AutoTestBase):
    '''
    Responsabilities
        - Import the Test Class
        - Run test over all methods or specific methods
        - Report any errors
    '''
    def __init__(self, webdriver=None):
        super(TestRunner, self).__init__()
        self._webdriver = webdriver

    def test(self, test_paths, smoke=False):
        '''
        :param test_paths: iterable like ['package.module.test_class.test_method', ...]
        '''
        errors = []
        if smoke or not test_paths:
            self.log.i('Ignoring %r \n  (smoke mode or no tests found)'%list(test_paths))
            return errors
        pusherror = lambda err: err and errors.append(err)
        for tpath in test_paths:
            pusherror = lambda err: err and errors.append((tpath, err))
            class_ = self._import_test(pusherror, tpath)
            if not class_:
                continue
            self._run_test(pusherror, tpath, class_)
        return errors

    def io_loop(self, conn, stdin=None, stdout=None, stderr=None):
        while True:
            self._dispatch_cmds(conn)

    def _run_test(self, pusherror, test_path, class_):
        try:
            _, _, methstr = self._split_path(test_path)
            suite = unittest.TestSuite()
            suite.addTest(class_(methstr))
            runner = unittest.TextTestRunner()
            runner.run(suite)
        except Exception as e:
            pusherror(self.reprex(e))

    def _split_path(self, test_path):
        return self.split_test_path(test_path, meth=True)

    def _import_test(self, pusherror, test_path):
        modstr, clsstr, _ = self._split_path(test_path)
        try:
            module = importlib.import_module(modstr)
            module = reload(module)
            class_ = getattr(module, clsstr) 
        except Exception as e:
            pusherror(self.reprex(e))
            return None
        return class_


def smoke_test_module():
    test_paths = ['smoothtest.tests.example.Example']
    tr = TestRunner()
    class DummyIpc(object):
        def recv(self):
            cmds = [
                    ('test', (test_paths,), dict(smoke=True)),
                    ]
            self.recv = self.recv2
            return cmds

        def recv2(self):
            cmds = [
                    (TestRunner._kill_command, (0,), {}),
                    ]
            self.recv = lambda : []
            return cmds

        def send(self, msg):
            print msg
            return 1

        def close(self):
            pass
    try:
        tr.io_loop(DummyIpc())
    except SystemExit as e:
        tr.log.i(e)


if __name__ == "__main__":
    smoke_test_module()
