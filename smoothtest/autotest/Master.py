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
from .SourceWatcher import SourceWatcher, realPath
import re
import multiprocessing
import threading


def lists_to_sockets(rlist, wlist, xlist):
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


def filter_sockets(sockets, exclude):
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


class Master(AutoTestBase):
    '''
    '''
    def __init__(self, child_conn=None):
        self._child_conn = child_conn
        self._watcher = SourceWatcher()
        self._slave = Slave(TestRunner)
        master, watcher = multiprocessing.Pipe(duplex=False)
        self._m_w_conn = master
        self._w_m_conn = watcher
        
        #poll inputs
        self._poll_sockets = []
        self._poll_timeout = 0        
        #select inputs
        self._select_args = {}
        
    def set_select_args(self, **select_args):
        self._select_args = select_args

    def set_poll_args(self, sockets, timeout=0):
        self._poll_sockets = sockets
        self._timeout = timeout
    
    def io_loop(self, test_config, poll=None, select=None, block=True):
        #manager of the subprocesses
        self._slave.start_subprocess()

        #create callback for re-testing on changes/msgs
        self.new_test(**test_config)
        
        #build the block function listening to events
        get_event = self._build_get_event(poll, select)
        
        self.wait_input = True
        #loop listening events
        while self.wait_input:
            do_yield, yield_obj, rlist = get_event()
            self._dispatch(rlist)
            if do_yield:
                yield yield_obj
            self.wait_input = self.wait_input & block
        #We need to kill the child
        self._receive_kill()

    lock = threading.Lock()
    def new_test(self, test_paths=[], parcial_reloads=[], full_reloads=[],
             parcial_decorator=lambda x: x, full_decorator=lambda x: x,
             full_filter=None,
             smoke=False, force=False):
        #create callback for re-testing on changes/msgs
        def test_callback():
            self._slave.test(test_paths, smoke=smoke)

        @parcial_decorator
        def parcial_callback(path=None):
            self.log.i('Partial reload for: %r. Triggered by %r' %
                       (list(test_paths), path))
            test_callback()

        @full_decorator
        def full_callback(path=None):
            self.log.i('Full reload for: %r. Triggered by %r' %
                       (list(test_paths), path))
            #to force reloading all modules we directly kill and restart
            #the process
            with self.lock: #locking is just in case of being bombed
                self._watcher.unwatch_all()
                self.restart_subprocess()
                self._watcher.start_observer()
                test_callback()

        #save for future dispatching
        self.parcial_callback = parcial_callback
        self.full_callback = full_callback

        def parcial_msg(path):
            '''
            File _watcher thread -> master thread msg
            We use pipes to avoid race conditions on other IO mechanism
            (instead of calling the tests callbacks within the thread)
            '''
            self._w_m_conn.send(self.cmd('parcial_callback', path))
        
        def full_msg(path):
            '''
            File _watcher thread -> master thread msg
            We use pipes to avoid race conditions on other IO mechanism
            (instead of calling the tests callbacks within the thread)
            '''        
            self._w_m_conn.send(self.cmd('full_callback', path))

        self._watcher.unwatch_all(clear=True)
        for ppath in parcial_reloads:
            self._watcher.watch_file(ppath, parcial_msg)
            
        full_filter = self._build_path_filter(parcial_reloads, full_filter)
        for fpath in full_reloads:
            self._watcher.watch_recursive(fpath, full_msg,
                                         path_filter=full_filter)

        if force:
            #_slave's subprocess where tests will be done
            self.restart_subprocess()

        #do first time test (for master)
        parcial_callback()

        #Start inotify observer:
        self._watcher.start_observer()

    def _build_path_filter(self, parcial_reloads, path_filter):
        path_filter = path_filter if path_filter else lambda x: True

        if isinstance(path_filter, basestring):
            def pfilter(path):
                return re.match(path_filter, path)
        else:
            assert callable(path_filter)
            pfilter = path_filter

        parcial_reloads = set(realPath(p) for p in parcial_reloads)
        def _path_filter(path):
            return pfilter(path) and realPath(path) not in parcial_reloads
        
        return _path_filter

    def restart_subprocess(self):
        def post_callback():
            self._watcher.unwatch_all(clear=True)
            self._m_w_conn.close()
            self._w_m_conn.close()
            if self._child_conn:
                self._child_conn.close()
        return self._slave.restart_subprocess(post_callback)

    def _build_get_event(self, poll=None, select=None):
        def local_rlist():
            rlist = [self._slave.get_conn().fileno(), 
                     self._m_w_conn.fileno()]
            if self._child_conn:
                rlist.append(self._child_conn.fileno())
            return rlist
        
        def get_zmq_poll():
            #avoid depending on zmq (only import if poll not present)
            from zmq.backend import zmq_poll
            return zmq_poll
        
        poll = get_zmq_poll() if not(poll or select) else poll
        
        if poll:
            def build_sockets():
                #in interactive mode we need to listen to stdin
                sockets = lists_to_sockets(local_rlist(), [], [])
                return sockets + self._poll_sockets
            
            def get_event():
                sockets = poll(build_sockets())
                sockets, (rlist, _, _) = filter_sockets(sockets, local_rlist())
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
        return get_event

    def _dispatch(self, rlist):
        #depending on the input, dispatch actions
        for f in rlist:
            #Receive input from child process
            if f is self._slave.get_conn().fileno():
                self._recv_slave(self.parcial_callback)
            if self._child_conn and f is self._child_conn.fileno():
                self._dispatch_cmds(self._child_conn)
            if f is self._m_w_conn.fileno():
                self._dispatch_cmds(self._m_w_conn, duplex=False)

    def _receive_kill(self, *args, **kwargs):
        self._slave.kill(block=True, timeout=3)
        self._watcher.unwatch_all()

    def _recv_slave(self, callback):
        #keep value, since it will be changed in _slave.recv_answer
        first = self._slave._first_test
        #read the answer sent by the subprocess
        #We do not repeat inside _slave since its a blocking operation
        answer = self._slave.recv_answer()
        #unpack from (testing_errors, exception_errors) tuple
        testing_errors, error = answer
        if (testing_errors or error) and not first:
            self.log.w('Test\'s import errors, restarting process and repeating '
                       'tests.')
            #to force reloading all modules we directly kill and restart
            #the process
            self.restart_subprocess()
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
    parcial_reloads = ['MasterAutoTest.py']
    mat = Master()
    poll = mat.io_loop(dict(test_paths=test_paths, parcial_reloads=parcial_reloads, smoke=True),
                    block=False)
    for s in poll:
        pass


if __name__ == "__main__":
    smoke_test_module()
