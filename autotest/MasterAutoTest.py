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

class MasterAutotest(AutoTestBase):
    '''
    create slave
    setup webserver?? Este requisito debería tenerlo el unittest?
    select pipe inotify ipython
    pass messages along them
    applies policies?
    '''
    
    def test(self, test_paths, parcial_reloads, full_reloads):
        slave = SlaveAutotest(ChildTestRunner)
        slave.start_subprocess()
        slave.test(test_paths)
        wait_input = True
        while wait_input:
            #print wait_input
            rlist, _, _ = select.select([slave._pipe_ipc], [], [])
            for f in rlist:
                if f is slave._pipe_ipc:
                    self._recv_slave(test_paths, slave)
            wait_input = False
        slave.kill(block=True, timeout=1)

    def _recv_slave(self, test_paths, slave):
        first = slave._first_test
        answer = slave.recv_answer(test_paths)
        if answer[0][0] and not first:
            self.log.i('Test import error, restarting process and repeating tests %r'%test_paths)
            slave.test(test_paths)

def smoke_test_module():
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    mat = MasterAutotest()
    mat.test(test_paths, [], [])
    

if __name__ == "__main__":
    smoke_test_module()
