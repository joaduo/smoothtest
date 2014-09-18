# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import tornado.web

from tornado.ioloop import IOLoop, PollIOLoop
from tornado.platform.select import _Select
from smoothtest.autotest.MasterAutoTest import MasterAutotest
from smoothtest.autotest.SlaveAutotest import SlaveAutotest
from smoothtest.autotest.ChildTestRunner import ChildTestRunner

import tornado.netutil
from tornado.httpserver import HTTPServer
import select
from zmq.eventloop.ioloop import PollIOLoop, IOLoop,tornado_version, Poller, ZMQPoller, ZMQIOLoop

#
#class AutoTestSelect(object):
#    def __init__(self):
#        self._sockets = []
#
#    def set_sockets(self, sockets):
#        self._sockets = sockets
#
#    def initialize(self):
#        test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
#        self._master = MasterAutotest()
#        self._slave = SlaveAutotest(ChildTestRunner)
##        self._generator = self._master.test_all(test_paths, 
##                                                ['fulcrum/views/sales/tests/about_us.py'], [],
##                                                select=select.select)
#        from zmq.backend import zmq_poll
#        self._generator = self._master.test_all(test_paths, 
#                                                ['fulcrum/views/sales/tests/about_us.py'], [],
#                                                poll=zmq_poll)
##        self._generator = self._master.test(test_paths, 
##                                                ['fulcrum/views/sales/tests/about_us.py'], [],
##                                                )
#        self.initialize = lambda:None
#
#    def __call__(self, *a, **kw):
#        return self.select(*a, **kw)
#
#    def poll(self, timeout=None):
#        if timeout is None or timeout < 0:
#            timeout = -1
#        elif isinstance(timeout, float):
#            timeout = int(timeout)
#        self._master.set_poll_args(self.sockets, timeout)
#        return self._generator.next()
#
#    def select(self, rlist, wlist, xlist, timeout=None):
#        self.initialize()
#        self._master.set_select_args(rlist=rlist,
#                                     wlist=wlist,
#                                     xlist=xlist,
#                                     timeout=timeout)
#        return self._generator.next()
    
class AtPoller(Poller):
    def initialize_autotest(self):
        test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
        self._master = MasterAutotest()
        self._slave = SlaveAutotest(ChildTestRunner)
        from zmq.backend import zmq_poll
        def parcial_decorator(parcial_callback):
            def wrapper(*a, **kw):
                print 'Should run %s' % parcial_callback
            return wrapper
        self._generator = self._master.test_all(test_paths, 
                                                ['fulcrum/views/sales/tests/about_us.py'], [],
                                                parcial_decorator=parcial_decorator,
                                                poll=zmq_poll)
        self.initialize_autotest = lambda:None

    def poll(self, timeout=None):
        self.initialize_autotest()
        if timeout is None or timeout < 0:
            timeout = -1
        elif isinstance(timeout, float):
            timeout = int(timeout)
        self._master.set_poll_args(self.sockets, timeout)
        return self._generator.next()

#class _UnblockSelect(_Select):
#    """A simple, select()-based IOLoop implementation for non-Linux systems"""
#    select = AutoTestSelect()
#    def poll(self, timeout):
#        readable, writeable, errors = self.select(
#            self.read_fds, self.write_fds, self.error_fds, timeout)
#        events = {}
#        for fd in readable:
#            events[fd] = events.get(fd, 0) | IOLoop.READ
#        for fd in writeable:
#            events[fd] = events.get(fd, 0) | IOLoop.WRITE
#        for fd in errors:
#            events[fd] = events.get(fd, 0) | IOLoop.ERROR
#        return events.items()

#AutoTest version
class AtZMQPoller(ZMQPoller):
    """A poller that can be used in the tornado IOLoop.
    
    This simply wraps a regular zmq.Poller, scaling the timeout
    by 1000, so that it is in seconds rather than milliseconds.
    """
    
    def __init__(self):
        self._poller = AtPoller()


class UnblockSelectIOLoop(PollIOLoop):
    def initialize(self, **kwargs):
        #super(UnblockSelectIOLoop, self).initialize(impl=_UnblockSelect(), **kwargs)
        super(UnblockSelectIOLoop, self).initialize(impl=AtZMQPoller(), **kwargs)

@classmethod
def configurable_default(cls):
    return UnblockSelectIOLoop

tornado.ioloop.IOLoop.configure(UnblockSelectIOLoop)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hi Sandeep, Welcome to Tornado Web Framework.")

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    sockets = tornado.netutil.bind_sockets(8888)
    #We need to close sockets in the child process just in case
#    _UnblockSelect.select.set_sockets(sockets)
    #tornado.process.fork_processes(1)
    server = HTTPServer(application)
    server.add_sockets(sockets)
    #import tornado.autoreload
    io_loop = tornado.ioloop.IOLoop.instance()
    #tornado.autoreload.start(io_loop, check_time=3600)
    io_loop.start()
