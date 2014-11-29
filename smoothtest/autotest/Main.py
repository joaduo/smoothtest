# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import sys
from .base import ParentBase
from .Master import Master
from smoothtest.settings.solve_settings import solve_settings
from .Slave import Slave
from .TestRunner import TestRunner
from smoothtest.webunittest.WebdriverManager import WebdriverManager


class Main(ParentBase):
    def __init__(self, smoke=False):
        self._timeout = 1
        self.smoke = smoke
        self.ishell = None
        self.test_config = {}
        self._slave = None
        
    def run(self, test_config, embed_ipython=False, block=False):
        self.log.set_pre_post(pre='Main ')
        self.test_config = test_config
        self.create_child()
        if embed_ipython:
            s = self # nice alias
            self.embed()
            self.kill_child
            raise SystemExit(0)
        elif block:
            self.log.i(self._subprocess_conn.recv())
        WebdriverManager().stop_display()
    
    def embed(self, **kwargs):
        """Call this to embed IPython at the current point in your program.
        """
        iptyhon_msg = ('Could not embed Ipython, falling back to ipdb'
                       ' shell. Exception: %r')
        ipdb_msg = ('Could not embed ipdb, falling back to pdb'
                       ' shell. Exception: %r')
        try:
            self._embed_ipython(**kwargs)
        except Exception as e:
            self.log.w(iptyhon_msg % e)
            try:
                import ipdb; ipdb.set_trace()
            except Exception as e:
                self.log.e(ipdb_msg % e)
                import pdb ; pdb.set_trace()

    def _embed_ipython(self, **kwargs):
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
        kwargs.setdefault('display_banner', False)
        self.ishell = InteractiveShellEmbed.instance(**kwargs)
        load_extension(self.ishell, self)
        #Stack depth is 3 because we use self.embed first
        self.ishell(header=header, stack_depth=3, compile_flags=compile_flags)
            
    @property
    def new_child(self):
        self.kill_child
        self.create_child()
    
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
        if (not self._slave or force):
            settings = solve_settings()
            child_kwargs = {}
            if settings.get('webdriver_inmortal_pooling') and not self.smoke:
                wd = WebdriverManager().new_webdriver(browser)
                child_kwargs.update(webdriver=wd)
            self._slave = Slave(TestRunner, child_kwargs=child_kwargs)
        return self._slave

    def create_child(self):
        slave = self._build_slave()
        
        def callback(conn):
            if self.ishell:
                self.ishell.exit_now = True
            sys.stdin.close()
            master = Master(conn, slave)
            poll = master.io_loop(self.test_config)
            while 1:
                poll.next()
        
        super(Main, self).start_subprocess(callback, pre='Master')
    
    @property
    def test(self):
        cmd = 'partial_callback'
        answers = self.send_recv(cmd)
        ans = self._get_answer(answers, cmd)
        if ans.error:
            self.log.e(ans.error)
        return ans

    def send(self, cmd, *args, **kwargs):
        while self.poll():
            self.log.i('Remaining in buffer: %r'%self.recv())
        return super(Main, self).send(cmd, *args, **kwargs)
    
    @property
    def kill_child(self):
        return self.kill(block=True, timeout=3)


def smoke_test_module():
    main = Main(smoke=True)
    main.run({}, embed_ipython=False, block=False)
    import time
    time.sleep(0.5)
    main.kill_child

if __name__ == "__main__":
    smoke_test_module()
