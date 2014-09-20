# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
from zmq.eventloop.ioloop import PollIOLoop, IOLoop,tornado_version, Poller, ZMQPoller, ZMQIOLoop
from zmq.sugar.constants import POLLIN, POLLOUT, POLLERR
from zmq.backend import zmq_poll
from tornado.platform.select import _Select
from smoothtest.autotest.Context import Context

def install(IOLoop_cls):
    """set the tornado IOLoop instance with the pyzmq IOLoop.
    
    After calling this function, tornado's IOLoop.instance() and pyzmq's
    IOLoop.instance() will return the same object.
    
    An assertion error will be raised if tornado's IOLoop has been initialized
    prior to calling this function.
    """
    from tornado import ioloop
    # check if tornado's IOLoop is already initialized to something other
    # than the pyzmq IOLoop instance:
    assert (not ioloop.IOLoop.initialized()) or \
        ioloop.IOLoop.instance() is IOLoop.instance(), "tornado IOLoop already initialized"

    if tornado_version >= (3,):
        # tornado 3 has an official API for registering new defaults, yay!
        ioloop.IOLoop.configure(IOLoop_cls)
    else:
        # we have to set the global instance explicitly
        ioloop.IOLoop._instance = IOLoop_cls.instance()

class AtPollerBase(object):
    def initialize_autotest(self, wait_type):
        ctx = Context()
        ctx.initialize(wait_type)
        self._master = ctx.master
        self._slave = ctx.slave
        self._generator = ctx.poll
        self.initialize_autotest = lambda:None

###### Using select.select

class AtSelectPoller(_Select, AtPollerBase):
    def initialize_autotest(self):
        AtPollerBase.initialize_autotest(self, wait_type='select')
    
    def poll(self, timeout):
        self.initialize_autotest()
        self._master.set_select_args(rlist=self.read_fds,
                                     wlist=self.write_fds,
                                     xlist=self.error_fds,
                                     timeout=timeout)
        readable, writeable, errors = self._generator.next()
        events = {}
        for fd in readable:
            events[fd] = events.get(fd, 0) | IOLoop.READ
        for fd in writeable:
            events[fd] = events.get(fd, 0) | IOLoop.WRITE
        for fd in errors:
            events[fd] = events.get(fd, 0) | IOLoop.ERROR
        return events.items()    


class AtSelectIOLoop(PollIOLoop):
    def initialize(self, **kwargs):
        super(AtSelectIOLoop, self).initialize(impl=AtSelectPoller(), **kwargs)
    
    @staticmethod
    def instance():
        if tornado_version >= (3,):
            PollIOLoop.configure(AtSelectIOLoop)
        return PollIOLoop.instance()

######## Using ZMQ Poller

class AtPoller(Poller, AtPollerBase):
    def initialize_autotest(self):
        AtPollerBase.initialize_autotest(self, wait_type='poll')

    def poll(self, timeout=None):
        self.initialize_autotest()
        if timeout is None or timeout < 0:
            timeout = -1
        elif isinstance(timeout, float):
            timeout = int(timeout)
        self._master.set_poll_args(self.sockets, timeout)
        return self._generator.next()

class AtPollZMQIOLoop(ZMQIOLoop):
    class AtZMQPoller(ZMQPoller):
        def __init__(self):
            self._poller = AtPoller()
    
    def initialize(self, **kwargs):
        super(ZMQIOLoop, self).initialize(impl=self.AtZMQPoller(), **kwargs)
    
    @staticmethod
    def instance():
        if tornado_version >= (3,):
            PollIOLoop.configure(AtPollZMQIOLoop)
        return PollIOLoop.instance()


def smoke_test_module():
    install(AtSelectIOLoop)
    install(AtPollZMQIOLoop)

if __name__ == "__main__":
    smoke_test_module()
