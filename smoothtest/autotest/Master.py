# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
import os
rel_imp.init()
from .base import ChildBase
from .Slave import Slave
from .TestRunner import TestRunner
from .SourceWatcher import SourceWatcher, realPath
import multiprocessing
import threading
import select as select_mod
from fnmatch import fnmatch


def lists_to_sockets(rlist, wlist, xlist):
    '''
    Convert select list arguments to sockets (used by ZMQ or Tornado)
    (rlist, wlist, xlist) -> list(sockets...)
    :param rlist:
    :param wlist:
    :param xlist:
    '''
    from zmq.sugar.constants import (POLLIN,  # @UnresolvedImport
                                     POLLOUT,  # @UnresolvedImport
                                     POLLERR)  # @UnresolvedImport
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
    from zmq.sugar.constants import (POLLIN,  # @UnresolvedImport
                                     POLLOUT,  # @UnresolvedImport
                                     POLLERR)  # @UnresolvedImport
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
            filtered_sockets.append((s, flags))
    return filtered_sockets, (rlist, wlist, xlist)


def get_zmq_poll():
    # avoid depending on zmq (only import if poll not present)
    from zmq.backend import zmq_poll  # @UnresolvedImport
    return zmq_poll


class Master(ChildBase):

    '''
    '''

    def __init__(self, parent_conn=None, slave=None):
        self._parent_conn = parent_conn
        self._watcher = SourceWatcher()
        self._slave = Slave(TestRunner) if not slave else slave
        master, watcher = multiprocessing.Pipe(duplex=False)
        self._m_w_conn = master
        self._w_m_conn = watcher

        # poll inputs
        self._poll_sockets = []
        self._poll_timeout = 0
        # select inputs
        self._select_args = {}
        self._restart_lock = threading.Lock()
        self._io_list = [self.parent_conn, self.slave_conn, self.m_w_conn]
        self._io_blacklist = set()
        if not self._parent_conn:
            self._io_blacklist.add(self.parent_conn)

    def parent_conn(self):
        # Since self._parent_conn can change, we use a method to refer to
        # it in set operations
        return self._parent_conn

    def slave_conn(self):
        # Since self._slave.get_conn() can change, we use a method to refer to
        # it in set operations
        return self._slave.get_conn()

    def m_w_conn(self):
        # Since self._m_w_conn can change, we use a method to refer to
        # it in set operations
        return self._m_w_conn

    def set_select_args(self, **select_args):
        self._select_args = select_args

    def set_poll_args(self, sockets, timeout=0):
        self._poll_sockets = sockets
        self._timeout = timeout

    def get_subprocess_pid(self):
        return self._slave.get_subprocess_pid()

    def io_loop(self, test_config, poll=None, select=None, block=True):
        # manager of the subprocesses
        self._slave.start_subprocess()

        # create callback for re-testing on changes/msgs
        self.new_test(**test_config)

        # build the block function listening to events
        get_event = self._build_get_event(poll, select)

        self.wait_input = True
        # loop listening events
        while self.wait_input:
            do_yield, yield_obj, rlist = get_event()
            self._dispatch(rlist)
            if do_yield:
                yield yield_obj
            self.wait_input = self.wait_input and block
        # We need to kill the child
        self._receive_kill()

    def new_test(self, test_paths=tuple(), partial_reloads=tuple(), full_reloads=tuple(),
                 partial_decorator=lambda x: x, full_decorator=lambda x: x,
                 full_filter=None,
                 smoke=False, force=False, argv=[]):
        # create callback for re-testing on changes/msgs
        def test_callback():
            self._slave.test(test_paths, argv, smoke=smoke)

        @partial_decorator
        def partial_callback(path=None):
            self.print_reload(path, test_paths, smoke, reload_type='Partial')
            if test_paths or smoke:
                test_callback()

        @full_decorator
        def full_callback(path=None):
            self.print_reload(path, test_paths, smoke, reload_type='Full')
            if test_paths or smoke:
                # to force reloading all modules we directly kill and restart
                # the process
                with self._restart_lock:  # locking is just in case of being bombed
                    self._watcher.unwatch_all()
                    self.restart_subprocess()
                    self._watcher.start_observer()
                    test_callback()

        # save for future dispatching
        self.partial_callback = partial_callback
        self.full_callback = full_callback

        def partial_msg(path):
            '''
            File _watcher thread -> master thread msg
            We use pipes to avoid race conditions on other IO mechanism
            (instead of calling the tests callbacks within the thread)
            '''
            self._w_m_conn.send(self.cmd(self.partial_callback, path))

        def full_msg(path):
            '''
            File _watcher thread -> master thread msg
            We use pipes to avoid race conditions on other IO mechanism
            (instead of calling the tests callbacks within the thread)
            '''
            self._w_m_conn.send(self.cmd(self.full_callback, path))

        self._watcher.unwatch_all(clear=True)
        for ppath in partial_reloads:
            self._watcher.watch_file(ppath, partial_msg)

        full_filter = self._build_path_filter(partial_reloads, full_filter)
        for fpath in full_reloads:
            self._watcher.watch_recursive(fpath, full_msg,
                                          path_filter=full_filter)

        if force:
            # Slave's subprocess where tests will be done
            self.restart_subprocess()

        # do first time test (for master)
        partial_callback('First test after setup')

        # Start inotify observer:
        self._watcher.start_observer()

    def print_reload(self, path, test_paths, smoke, reload_type):
        path = path if path else 'user'
        if len(test_paths) > 1:
            prefix = os.path.commonprefix([tp.split('.') for tp in test_paths])
            prefix = '.'.join(prefix)
            paths = [tp[len(prefix):].strip('.') for tp in test_paths]
        else:
            paths = [tp.split('.')[-1] for tp in test_paths]
        if test_paths or smoke:
            self.log.i('{reload_type} reload for: {paths}. '
                    'Triggered by {path}'.format(**locals()))
        else:
            self.log.i('No tests')

    def _build_path_filter(self, partial_reloads, path_filter):
        path_filter = path_filter if path_filter else lambda _: True

        if isinstance(path_filter, basestring):
            def pfilter(path):
                return fnmatch(path, path_filter)
        else:
            assert callable(path_filter)
            pfilter = path_filter

        partial_reloads = set(realPath(p) for p in partial_reloads)

        def _path_filter(path):
            return pfilter(path) and realPath(path) not in partial_reloads

        return _path_filter

    def restart_subprocess(self):
        def post_callback():
            # post-fork callback to close open fd
            self._watcher.unwatch_all(clear=True)
            self._m_w_conn.close()
            self._w_m_conn.close()
            if self._parent_conn:
                self._parent_conn.close()
        return self._slave.restart_subprocess(post_callback)

    def _build_get_event(self, poll=None, select=None):
        def local_rlist():
            rlist = set(self._io_list) - self._io_blacklist
            rlist = [conn().fileno() for conn in rlist]
            return rlist

        # If not set, set the io wait method
        select = select_mod.select if not(poll or select) else select

        if poll:
            def build_sockets():
                # in interactive mode we need to listen to stdin
                sockets = lists_to_sockets(local_rlist(), [], [])
                return sockets + self._poll_sockets

            def get_event():
                sockets = poll(build_sockets())
                sockets, (rlist, _, _) = filter_sockets(sockets, local_rlist())
                return bool(sockets), sockets, rlist

        elif select:
            def build_rlist():
                # in interactive mode we need to listen to stdin
                return local_rlist() + list(self._select_args.get('rlist', []))

            def get_event():
                rlist = build_rlist()
                lrlist = local_rlist()
                wlist = self._select_args.get('wlist', [])
                xlist = self._select_args.get('xlist', [])
                timeout = self._select_args.get('timeout')
                if timeout:
                    rlist, wlist, xlist = select(rlist, wlist, xlist, timeout)
                else:
                    rlist, wlist, xlist = select(rlist, wlist, xlist)
                # filter internal fds/sockets, don't yield them
                # and make a separated list
                yieldrlist = list(set(rlist) - set(lrlist))
                int_rlist = list(set(rlist) & set(lrlist))
                yield_obj = (yieldrlist, wlist, xlist)
                return any(yield_obj), yield_obj, int_rlist
        return get_event

    def _dispatch(self, rlist):
        # Build a dispatch dictionary
        # {conn_func:dispatch_lambda} dict
        fdict = {
            self.slave_conn: (lambda: self._recv_slave()),
            self.m_w_conn: (lambda: self._dispatch_cmds(self._m_w_conn, False)),
            self.parent_conn: (lambda: self._dispatch_cmds(self._parent_conn)), 
        }
        # Convert to {fileno:(dispatch_lambda, conn_func)...} dict
        fnodict = dict((f().fileno(), (lb, f)) for f, lb in fdict.items()
                       if f())
        # dispatch events
        for f in rlist:
            try:
                # depending on the input, dispatch actions
                # call lambda callback
                fnodict[f][0]()
            except Exception as e:
                self.log.e(self.reprex(e))
                conn_func = fnodict[f][1]
                self.log.e('Exception while dispatching to {conn!r}. {e!r}'
                           .format(conn=conn_func.func_name, e=e))
                self.log.e('Blacklisting {conn}. Restart Master to enable it.'
                           .format(conn=conn_func.func_name))
                # black list in future io
                self._io_blacklist.add(conn_func)

    def _receive_kill(self, *_args, **_kwargs):
        self._watcher.unwatch_all()
        self._slave.kill(block=True, timeout=3)

    def _recv_slave(self):
        first = self._slave._first_test
        answer = self._slave.recv_answer()
        if answer.error and not first:
            self.full_callback('Error on non-first run')


def smoke_test_module():
    test_paths = ['smoothtest.tests.example.test_Example.Example.test_example']
    partial_reloads = ['MasterAutoTest.py']
    mat = Master()
    poll = mat.io_loop(dict(test_paths=test_paths,
                            partial_reloads=partial_reloads, smoke=True),
                       block=False)
    for _ in poll:
        pass


if __name__ == "__main__":
    smoke_test_module()
