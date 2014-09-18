# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import select
import relative_import
from .base import AutoTestBase
from .SlaveAutotest import SlaveAutotest
from .ChildTestRunner import ChildTestRunner
from .SourceWatcher import SourceWatcher

class MasterAutotest(AutoTestBase):
    '''
    '''
    _select_args = {}
    def set_select_args(self, **select_args):
        self._select_args = select_args
    
    def test(self, test_paths, parcial_reloads, full_reloads=[], 
             full_decorator=lambda x:x, slave=None):
        #nice alias useful for callbacks
        #master = self
        #manager of the subprocesses
        slave = slave or SlaveAutotest(ChildTestRunner)
        
        #create callback for re-testing on changes/msgs
        @full_decorator
        def full_callback(path=None):
            slave.test(test_paths)
        #Monitor changes in files
        watcher = SourceWatcher()
        watcher.watch_file(parcial_reloads[0], full_callback)
        
        #slave's subprocess where tests will be done
        slave.start_subprocess()
        #do first time test (for master)
        full_callback()
        
        def build_rlist():
            #in interactive mode we need to listen to stdin
            rlist = [slave._pipe_ipc, watcher.get_fd()] + list(self._select_args.get('rlist',[]))
            return rlist
        
        def _select(rlist, wlist, xlist, timeout=None):
            if timeout:
                return select.select(rlist, wlist, xlist, timeout)
            return select.select(rlist, wlist, xlist)
        
        #setup variable to control loop escape
        self.wait_input = True
        while self.wait_input:
            #Wait for any of the inputs to be ready
            rlist, wlist, xlist = _select(build_rlist(), 
                                          self._select_args.get('wlist',[]), 
                                          self._select_args.get('xlist',[]),
                                          self._select_args.get('timeout'),
                                          )
            #depending on the input, dispatch actions
            for f in rlist:
                #Receive input from child process
                if f is slave._pipe_ipc:
                    rlist.remove(f)
                    self._recv_slave(full_callback, test_paths, slave)
                if f is watcher.get_fd():
                    rlist.remove(f)
                    watcher.dispatch(timeout=1)
            if rlist or wlist or xlist:
                yield rlist, wlist, xlist
        #We need to kill the child
        slave.kill(block=True, timeout=1)

    def _recv_slave(self, callback, test_paths, slave):
        #keep value, since it will be changed in slave.recv_answer
        first = slave._first_test
        #read the answer sent by the subprocess
        answer = slave.recv_answer(test_paths)
        #unpack from (testing_errors, exception_errors) tuple
        testing_errors, error = answer[0]
        if (testing_errors or error) and not first:
            self.log.w('Test\'s import errors, restarting process and repeating '
                       'tests.')
            #to force reloading all modules we directly kill and restart
            #the process
            slave.restart_subprocess()
            #Now, lets test if reloading all worked
            callback()
        #Notify unexpected errors
        if testing_errors:
            self.log.e(testing_errors)
        if error:
            self.log.e(error)


def smoke_test_module():
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    mat = MasterAutotest()
    mat.test(test_paths, ['MasterAutoTest.py'], []).next()
    

if __name__ == "__main__":
    smoke_test_module()