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
    def test(self, test_paths, parcial_reloads, full_reloads, 
             full_decorator=lambda x:x):
        #nice alias useful for callbacks
        #master = self
        #manager of the subprocesses
        slave = SlaveAutotest(ChildTestRunner)
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
        #setup variable to control loop escape
        self.wait_input = True
        #Start the main test-and-wait loop
        while self.wait_input:
            #TODO: add stdin for receiving user's commands
            #Wait for any of the inputs to be ready
            rlist, _, _ = select.select([slave._pipe_ipc, watcher.get_fd()], [], [])
            #depending on the input, dispatch actions
            for f in rlist:
                if f is slave._pipe_ipc:
                    self._recv_slave(full_callback, test_paths, slave)
                if f is watcher.get_fd():
                    watcher.dispatch(timeout=1)
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
    mat.test(test_paths, ['MasterAutoTest.py'], [])
    

if __name__ == "__main__":
    smoke_test_module()
