# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import multiprocessing
import sys
from .base import AutoTestBase
from .Master import Master
from ..settings.solve_settings import solve_settings
from .Slave import Slave
from .TestRunner import TestRunner
from selenium import webdriver


class Main(AutoTestBase):
    def __init__(self, smoke=False):
        self._timeout = 1
        self.smoke = smoke
        self.ishell = None
        self.test_config = {}
        self._slave = None
        
    def run(self, test_config, embed_ipython=False, block=False):
        self.test_config = test_config
        self.create_child(self._build_callback())
        if embed_ipython:
            s = self # nice alias
            self.embed()
            self.kill_child
            raise SystemExit(0)
        elif block:
            self.log.i(self._parent_conn.recv())
    
    def get_conn(self):
        return self._parent_conn
    
    def embed(self, **kwargs):
        """Call this to embed IPython at the current point in your program.
        """
        from IPython.terminal.ipapp import load_default_config
        from IPython.terminal.embed import InteractiveShellEmbed
        from .ipython_extension import load_extension
        config = kwargs.get('config')
        header = kwargs.pop('header', u'')
        compile_flags = kwargs.pop('compile_flags', None)
        if config is None:
            config = load_default_config()
            config.InteractiveShellEmbed = config.TerminalInteractiveShell
            kwargs['config'] = config
        self.ishell = InteractiveShellEmbed.instance(**kwargs)
        load_extension(self.ishell, self)
        self.ishell(header=header, stack_depth=2, compile_flags=compile_flags)
    
    @property
    def new_child(self):
        self.kill_child
        self.create_child(self._build_callback())
    
    def send_test(self, **test_config):
        self.send_recv('new_test', **test_config)
        self.test_config = test_config

    def new_browser(self, browser=None):
        #Build the new slave
        if browser:
            m = dict(f='Firefox',
                     c='Chrome',
                     p='PhantomJS',
                     )
            browser = m.get(browser.lower()[0],m['f'])
        self._build_slave(force=True, browser=browser)
        self.new_child

    @property
    def ffox(self):
        self.new_browser('f')
    
    @property
    def chrome(self):
        self.new_browser('c')
        
    @property
    def phantomjs(self):
        self.new_browser('p')        

    def _build_slave(self, force=False, browser=None):
        if (not self._slave or force) and not self.smoke:
            settings = solve_settings()
            browser = browser or settings.webdriver_browser
            child_kwargs = {}
            if settings.webdriver_inmortal_pooling:
                wd = getattr(webdriver, browser)()
                child_kwargs.update(webdriver=wd)
            self._slave = Slave(TestRunner, child_kwargs=child_kwargs)
        return self._slave
        
    def _build_callback(self):
        #we need build it outside the child process
        slave = self._build_slave()
        
        def child_callback(child_conn):
            master = Master(child_conn, slave)
            poll = master.io_loop(self.test_config)
            while 1:
                poll.next()
        
        return child_callback
    
    def create_child(self, child_callback):
        parent_conn, child_conn = multiprocessing.Pipe()
        self._parent_conn = parent_conn
        
        def callback():
            self.log.i('Forking at %s.'%self.__class__.__name__)
            if self.ishell:
                self.ishell.exit_now = True
            sys.stdin.close()
            parent_conn.close()
            child_callback(child_conn)
        
        self.child_process = multiprocessing.Process(target=callback)
        self.child_process.start()
        child_conn.close()
    
    def poll(self):
        return self._parent_conn.poll()
    
    @property
    def test(self):
        answer = self.send_recv('parcial_callback')
        result, error = answer[0]
        if error:
            self.log.e(error)
        return result

    def send(self, cmd, *args, **kwargs):
        if self.poll():
            self.log.i('Remaining in buffer: %r'%self._parent_conn.recv())
        self._parent_conn.send(self.cmd(cmd, *args, **kwargs))
    
    def send_recv(self, cmd, *args, **kwargs):
        self.send(cmd, *args, **kwargs)
        return self._parent_conn.recv()
    
    @property
    def kill_child(self):
        answer = None
        if self._parent_conn and not self._parent_conn.closed:
            answer = self.send_recv(self._kill_command)
            self.log.i(answer)
            self._parent_conn.close()
            self._parent_conn = None
            self.child_process.join()
        else:
            self.child_process.terminate()
            self.child_process.join()
        self.child_process = None
        return answer


def smoke_test_module():
    main = Main(smoke=True)
    main.run({}, embed_ipython=False, block=False)
    main.kill_child

if __name__ == "__main__":
    smoke_test_module()
