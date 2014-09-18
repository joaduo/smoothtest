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



class AutoTestSelect(object):
    def __init__(self):
        self._sockets = []

    def set_sockets(self, sockets):
        self._sockets = sockets

    def initialize(self):
        test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
        self._master = MasterAutotest()
        self._slave = SlaveAutotest(ChildTestRunner, [], dict(sockets=self._sockets))
        self._generator = self._master.test(test_paths, ['fulcrum/views/sales/tests/about_us.py'], [])
        self.initialize = lambda:None

    def __call__(self, *a, **kw):
        return self._select(*a, **kw)

    def _select(self, rlist, wlist, xlist, timeout=None):
        self.initialize()
        self._master.set_select_args(rlist=rlist,
                                     wlist=wlist,
                                     xlist=xlist,
                                     timeout=timeout)
        return self._generator.next()

class _UnblockSelect(_Select):
    """A simple, select()-based IOLoop implementation for non-Linux systems"""
    _select = AutoTestSelect()
    def poll(self, timeout):
        readable, writeable, errors = self._select(
            self.read_fds, self.write_fds, self.error_fds, timeout)
        events = {}
        for fd in readable:
            events[fd] = events.get(fd, 0) | IOLoop.READ
        for fd in writeable:
            events[fd] = events.get(fd, 0) | IOLoop.WRITE
        for fd in errors:
            events[fd] = events.get(fd, 0) | IOLoop.ERROR
        return events.items()

class UnblockSelectIOLoop(PollIOLoop):
    def initialize(self, **kwargs):
        super(UnblockSelectIOLoop, self).initialize(impl=_UnblockSelect(), **kwargs)

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
    _UnblockSelect._select.set_sockets(sockets)
    #tornado.process.fork_processes(1)
    server = HTTPServer(application)
    server.add_sockets(sockets)
    #import tornado.autoreload
    io_loop = tornado.ioloop.IOLoop.instance()
    #tornado.autoreload.start(io_loop, check_time=3600)
    io_loop.start()
