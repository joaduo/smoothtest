# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.base import AutoTestBase

class MasterAutotest(AutoTestBase):
    '''
    create slave
    setup webserver?? Este requisito debería tenerlo el unittest?
    select pipe inotify ipython
    pass messages along them
    applies policies?
    '''
    
    def test(self, test_class, methods, parcial_reloads, full_reloads):
        pass
    
#    def _

class PipeMessenger(object):
    def __init__(self, in_pipe, out_pipe):
        self._in_pipe = in_pipe
        self._out_pipe = out_pipe
    
    def send_message(self, msg):
        pass
    
    def receive_message(self, block=False):
        pass

class SlaveAutotest(AutoTestBase):
    def __init__(self, subprocess_mngr):
        pass
    
    def start_subprocess(self, test_paths):
        '''
        pipes
        fork
        close pipes
        test
        '''
        pass

    def restart_subprocess(self, test_paths):
        pass
    
    def receive_message(self, block=False):
        pass
    
    def send_message(self, payload):
        pass
    
    def get_in_fd(self):
        pass

    def kill(self, force=False):
        pass

    def test(self, changed_paths, test_paths, reload_all=False):
        pass
        
class SubprocessTestRunner(AutoTestBase):
    '''
    Responsabilities
        - import the Test Class
        - Run test over all methods or specific methods
        - report any error. Inside tests and outside
            - Specifically
    '''
    def test(self, test_paths):
        '''
        test_paths = ['package.module.class.method']
        check existence
            report if down
        do test
            report if down
        
        report import errors
        
        :param test_class:
        :param methods:
        '''
        
    def receive_message(self, block=False):
        pass
    
    def send_message(self, payload):
        pass

#    def send(self, msg):
#        pass
#    
#    def recieve(self):
#        pass

def smoke_test_module():
    pass    

if __name__ == "__main__":
    smoke_test_module()

  