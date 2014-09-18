# -*- coding: utf-8 -*-
'''

'''

import errno
#import logging
import os
#import random
#import select
#import signal
import socket
#import sys
import threading
#import time
import webbrowser

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop.ioloop import PollIOLoop, IOLoop,tornado_version, Poller, ZMQPoller, ZMQIOLoop
from zmq.sugar.constants import POLLIN, POLLOUT, POLLERR
from zmq.backend import zmq_poll
import tornado.httpserver as httpserver
from IPython.html.notebookapp import random_ports, NotebookApp, NotebookWebApplication, \
    LOCALHOST
from smoothtest.autotest.MasterAutoTest import MasterAutotest
from smoothtest.autotest.SlaveAutotest import SlaveAutotest
from smoothtest.autotest.ChildTestRunner import ChildTestRunner

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
    
    assert tornado_version >= (3,)
    # tornado 3 has an official API for registering new defaults
    ioloop.IOLoop.configure(IOLoop_cls)

#AutoTest version
class AtPoller(Poller):
    def _initialize_autotest(self):
        test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
        self._master = MasterAutotest()
        self._slave = SlaveAutotest(ChildTestRunner)
        self._generator = self._master.test_poll(zmq_poll, test_paths, ['fulcrum/views/sales/tests/about_us.py'], [])
        self._initialize_autotest = lambda:None

    def poll(self, timeout=None):
        if timeout is None or timeout < 0:
            timeout = -1
        elif isinstance(timeout, float):
            timeout = int(timeout)
        self._master.set_poll_args(self.sockets, timeout)
        return self._generator.next()

#AutoTest version
class AtZMQPoller(ZMQPoller):
    """A poller that can be used in the tornado IOLoop.
    
    This simply wraps a regular zmq.Poller, scaling the timeout
    by 1000, so that it is in seconds rather than milliseconds.
    """
    
    def __init__(self):
        self._poller = AtPoller()

#AutoTest version
class AtZMQIOLoop(ZMQIOLoop):
    """ZMQ subclass of tornado's IOLoop"""
    def initialize(self, **kwargs):
        super(AtZMQIOLoop, self).initialize(impl=AtZMQPoller(), **kwargs)
    
    @staticmethod
    def instance():
        """Returns a global `IOLoop` instance.
        
        Most applications have a single, global `IOLoop` running on the
        main thread.  Use this method to get this instance from
        another thread.  To get the current thread's `IOLoop`, use `current()`.
        """
        # install ZMQIOLoop as the active IOLoop implementation
        # when using tornado 3
        if tornado_version >= (3,):
            PollIOLoop.configure(AtZMQIOLoop)
        return PollIOLoop.instance()

install(AtZMQIOLoop)

class AutotestNotebookApp(NotebookApp):
    pass
#    def init_webapp(self):
#        """initialize tornado webapp and httpserver"""
#        self.web_app = NotebookWebApplication(
#            self, self.kernel_manager, self.notebook_manager, 
#            self.cluster_manager, self.log,
#            self.base_project_url, self.webapp_settings
#        )
#        if self.certfile:
#            ssl_options = dict(certfile=self.certfile)
#            if self.keyfile:
#                ssl_options['keyfile'] = self.keyfile
#        else:
#            ssl_options = None
#        self.web_app.password = self.password
#        self.http_server = httpserver.HTTPServer(self.web_app, ssl_options=ssl_options,
#                                                 xheaders=self.trust_xheaders)
#        if not self.ip:
#            warning = "WARNING: The notebook server is listening on all IP addresses"
#            if ssl_options is None:
#                self.log.critical(warning + " and not using encryption. This "
#                    "is not recommended.")
#            if not self.password:
#                self.log.critical(warning + " and not using authentication. "
#                    "This is highly insecure and not recommended.")
#        success = None
#        for port in random_ports(self.port, self.port_retries+1):
#            try:
#                self.http_server.listen(port, self.ip)
#            except socket.error as e:
#                # XXX: remove the e.errno == -9 block when we require
#                # tornado >= 3.0
#                if e.errno == -9 and tornado.version_info[0] < 3:
#                    # The flags passed to socket.getaddrinfo from
#                    # tornado.netutils.bind_sockets can cause "gaierror:
#                    # [Errno -9] Address family for hostname not supported"
#                    # when the interface is not associated, for example.
#                    # Changing the flags to exclude socket.AI_ADDRCONFIG does
#                    # not cause this error, but the only way to do this is to
#                    # monkeypatch socket to remove the AI_ADDRCONFIG attribute
#                    saved_AI_ADDRCONFIG = socket.AI_ADDRCONFIG
#                    self.log.warn('Monkeypatching socket to fix tornado bug')
#                    del(socket.AI_ADDRCONFIG)
#                    try:
#                        # retry the tornado call without AI_ADDRCONFIG flags
#                        self.http_server.listen(port, self.ip)
#                    except socket.error as e2:
#                        e = e2
#                    else:
#                        self.port = port
#                        success = True
#                        break
#                    # restore the monekypatch
#                    socket.AI_ADDRCONFIG = saved_AI_ADDRCONFIG
#                if e.errno != errno.EADDRINUSE:
#                    raise
#                self.log.info('The port %i is already in use, trying another random port.' % port)
#            else:
#                self.port = port
#                success = True
#                break
#        if not success:
#            self.log.critical('ERROR: the notebook server could not be started because '
#                              'no available port could be found.')
#            self.exit(1)
#
#
#    def start(self, io_loop=None, open_browser=True, ):
#        """ Start the IPython Notebook server app, after initialization
#        
#        This method takes no arguments so all configuration and initialization
#        must be done prior to calling this method."""
#        ip = self.ip if self.ip else '[all ip addresses on your system]'
#        proto = 'https' if self.certfile else 'http'
#        info = self.log.info
#        self._url = "%s://%s:%i%s" % (proto, ip, self.port,
#                                      self.base_project_url)
#        for line in self.notebook_info().split("\n"):
#            info(line)
#        info("Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).")
#
#        if self.open_browser or self.file_to_run:
#            ip = self.ip or LOCALHOST
#            try:
#                browser = webbrowser.get(self.browser or None)
#            except webbrowser.Error as e:
#                self.log.warn('No web browser found: %s.' % e)
#                browser = None
#
#            if self.file_to_run:
#                name, _ = os.path.splitext(os.path.basename(self.file_to_run))
#                url = self.notebook_manager.rev_mapping.get(name, '')
#            else:
#                url = ''
#            if browser:
#                b = lambda : browser.open("%s://%s:%i%s%s" % (proto, ip,
#                    self.port, self.base_project_url, url), new=2)
#                threading.Thread(target=b).start()
#        try:
#            ioloop.IOLoop.instance().start()
#        except KeyboardInterrupt:
#            info("Interrupted...")
#        finally:
#            self.cleanup_kernels()
