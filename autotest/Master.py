# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
from .base import AutoTestBase
from .Slave import Slave
from .TestRunner import TestRunner
from .SourceWatcher import SourceWatcher

class Master(AutoTestBase):
    '''
    '''
    _select_args = {}
    def set_select_args(self, **select_args):
        self._select_args = select_args
        
    _poll_sockets = []
    _poll_timeout = 0
    def set_poll_args(self, sockets, timeout=0):
        self._poll_sockets = sockets
        self._timeout = timeout

    def lists_to_sockets(self, rlist, wlist, xlist):
        '''
        Convert select list arguments to sockets (used by ZMQ or Tornado)
        (rlist, wlist, xlist) -> list(sockets...)
        :param rlist:
        :param wlist:
        :param xlist:
        '''
        from zmq.sugar.constants import POLLIN, POLLOUT, POLLERR
        sockets = []
        for s in set(rlist + wlist + xlist):
            flags = 0
            if s in rlist:
                flags |= POLLIN
            if s in wlist:
                flags |= POLLOUT
            if s in xlist:
                flags |= POLLERR
            sockets.append((s, flags))
        return sockets
    
    def filter_sockets(self, sockets, exclude):
        '''
        Exclude internal Autotest Sockets from yielded external sockets
        :param sockets: sockets returned by poll
        :param exclude: fds/sockets to be excluded
        '''
        from zmq.sugar.constants import POLLIN, POLLOUT, POLLERR
        rlist, wlist, xlist = [], [], []
        filtered_sockets = []
        for s, flags in sockets:
            if s in exclude:
                if flags & POLLIN:
                    rlist.append(s)
                if flags & POLLOUT:
                    wlist.append(s)
                if flags & POLLERR:
                    xlist.append(s)
            else:
                filtered_sockets.append((s,flags))
        return filtered_sockets, (rlist, wlist, xlist)
    
    def test(self, test_paths, parcial_reloads, full_reloads=[],
             parcial_decorator=lambda x:x, full_decorator=lambda x:x, 
             slave=None, poll=None, select=None,
             child_conn=None, block=True):
        #manager of the subprocesses
        self._slave = slave = slave or Slave(TestRunner)
        #create callback for re-testing on changes/msgs
        @parcial_decorator
        def parcial_callback(path=None):
            slave.test(test_paths)
            
        #Monitor changes in files
        self.watcher = watcher = SourceWatcher()
        for fpath in parcial_reloads:
            watcher.watch_file(fpath, parcial_callback)
        
        def local_rlist():
            rlist = [slave.get_conn().fileno(), watcher.get_fd()]
            if child_conn:
                rlist.append(child_conn.fileno())
            return rlist
        
        def get_zmq_poll():
            #avoid depending on zmq (only import if poll not present)
            from zmq.backend import zmq_poll
            return zmq_poll
        
        poll = get_zmq_poll() if not(poll or select) else poll
        
        if poll:
            def build_sockets():
                #in interactive mode we need to listen to stdin
                sockets = self.lists_to_sockets(local_rlist(), [], [])
                return sockets + self._poll_sockets
            
            def get_event():
                sockets = poll(build_sockets())
                sockets, (rlist, _, _) = self.filter_sockets(sockets, local_rlist())
                return bool(sockets), sockets, rlist
            
        elif select:
            def build_rlist():
                #in interactive mode we need to listen to stdin
                return local_rlist() + list(self._select_args.get('rlist',[]))
    
            def get_event():
                rlist = build_rlist()
                wlist = self._select_args.get('wlist',[])
                xlist = self._select_args.get('xlist',[])
                timeout = self._select_args.get('timeout')
                if timeout:
                    rlist, wlist, xlist = select(rlist, wlist, xlist, timeout)
                else:
                    rlist, wlist, xlist = select(rlist, wlist, xlist)
                #filter internal fds/sockets, don't yield them
                #and make a separated list
                yieldrlist = list(set(rlist) - set(local_rlist()))
                int_rlist = list(set(rlist) & set(local_rlist()))
                yield_obj = (yieldrlist, wlist, xlist)
                return any(yield_obj), yield_obj, int_rlist
        
        #slave's subprocess where tests will be done
        slave.start_subprocess()
        #do first time test (for master)
        parcial_callback()
        
        self.wait_input = True
        while self.wait_input:
            do_yield, yield_obj, rlist = get_event()
            self._dispatch(rlist, slave, watcher, child_conn, locals())
            if do_yield:
                yield yield_obj
            self.wait_input = self.wait_input & block
        #We need to kill the child
        slave.kill(block=True, timeout=1)
        
    def new_test(self, test_paths, parcial_reloads, full_reloads=[], 
             child_conn=None, block=True):
        #TODO: parcial_decorator=lambda x:x, full_decorator=lambda x:x,
        pass

    def _dispatch(self, rlist, slave, watcher, child_conn, _locals):
        #depending on the input, dispatch actions
        for f in rlist:
            #Receive input from child process
            if f is slave.get_conn().fileno():
                rlist.remove(f)
                self._recv_slave(_locals['parcial_callback'], slave)
            if f is watcher.get_fd():
                rlist.remove(f)
                watcher.dispatch()
            if child_conn and f is child_conn.fileno():
                self._dispatch_cmds(child_conn, self._cmds_handler, _locals)
    
    def _cmds_handler(self, params, _locals):
        cmd, args, kw = params
        if cmd == 'test_cmd':
            _locals['parcial_callback']()
    
    def _receive_kill(self, *args, **kwargs):
        self._slave.kill(block=True, timeout=3)
    
    def _recv_slave(self, callback, slave):
        #keep value, since it will be changed in slave.recv_answer
        first = slave._first_test
        #read the answer sent by the subprocess
        #We do not repeat inside slave since its a blocking operation
        answer = slave.recv_answer()
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
        return answer


def smoke_test_module():
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    mat = Master()
    mat.test(test_paths, ['MasterAutoTest.py'], block=False).next()


if __name__ == "__main__":
    smoke_test_module()
