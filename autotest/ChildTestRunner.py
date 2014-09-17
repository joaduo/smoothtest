# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.base import AutoTestBase
import importlib
import unittest

class ChildTestRunner(AutoTestBase):
    '''
    Responsabilities
        - Import the Test Class
        - Run test over all methods or specific methods
        - Report any errors
    '''
    _kill_command = 'raise SystemExit'
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
        msg = pipe.recv()
        answer = []
        while True:
            for params in msg:
                cmd, args, kwargs = params 
                if cmd == self._kill_command:
                    raise SystemExit(*args, **kwargs)
                try:
                    result = getattr(self, cmd)(*args, **kwargs)
                    answer.append((result, None))
                except Exception as e:
                    answer.append((None, self.reprex(e)))
                
                pipe.send(answer)
                msg = pipe.recv()
    
    def reprex(self, e):
        return repr(e)
    
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
    sr = ChildTestRunner()
    class DummyIpc(object):
        def read(self):
            cmds = [
                    ('test', (test_paths,), {}),
                    ]
            self.read = self.read2
            return cmds
        
        def read2(self):
            cmds = [
                    ('raise SystemExit', ('Gently killing the process',), {}),
                    ]
            self.read = lambda : []
            return cmds

        def write(self, msg):
            print msg
            return 1
    
    sr.wait_io(DummyIpc())

if __name__ == "__main__":
    smoke_test_module()

  