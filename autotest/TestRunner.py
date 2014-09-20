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
    def __init__(self, webdriver=None, sockets=[]):
        super(TestRunner, self).__init__()
        self._webdriver = webdriver
        self.after_fork(sockets)

    def after_fork(self, sockets):
        for s in sockets:
            s.close()

    def test(self, test_paths):
        '''
        :param test_paths: iterable like ['package.module.test_class.test_method', ...]
        '''
        errors = []
        pusherror = lambda err: err and errors.append(err)
        for tpath in test_paths:
            pusherror = lambda err: err and errors.append((tpath, err))
            objects = self._import_test(pusherror, tpath)
            if not objects:
                continue
            self._run_test(pusherror, tpath, *objects)
        return errors

    def wait_io(self, pipe):
        while True:
            self._dispatch_cmds(pipe)

    def _run_test(self, pusherror, test_path, module, class_, method):
        try:
            #assert issubclass(class_, TestCase), 'The class must be subclass of unittest.TestCase'
            _, _, methstr = self._split_path(test_path)
            suite = unittest.TestSuite()
            suite.addTest(class_(methstr))
            runner = unittest.TextTestRunner()
            runner.run(suite)
        except Exception as e:
            pusherror(self.reprex(e))

    def _import_test(self, pusherror, test_path):
        modstr, clsstr, methstr = self._split_path(test_path)
        try:
            module = importlib.import_module(modstr)
            module = reload(module)
            class_ = getattr(module, clsstr)
            method = getattr(class_, methstr)
        except Exception as e:
            pusherror(self.reprex(e))
            return None
        return module, class_, method

    def _split_path(self, test_path):
        test_path = test_path.split('.')
        module = '.'.join(test_path[:-2])
        class_ = test_path[-2]
        method = test_path[-1]
        return module, class_, method


def smoke_test_module():
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    sr = TestRunner()
    class DummyIpc(object):
        def recv(self):
            cmds = [
                    ('test', (test_paths,), {}),
                    ]
            self.recv = self.recv2
            return cmds

        def recv2(self):
            cmds = [
                    ('raise SystemExit', (0,), {}),
                    ]
            self.read = lambda : []
            return cmds

        def send(self, msg):
            print msg
            return 1

        def close(self):
            pass

    sr.wait_io(DummyIpc())

if __name__ == "__main__":
    smoke_test_module()
