# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import multiprocessing
import sys
from .Context import singleton_decorator
from .base import AutoTestBase
from .ipython_extension import load_extension
from smoothtest.autotest.Master import Master

@singleton_decorator
class Main(AutoTestBase):
    def __init__(self, smoke=False):
        self._timeout = 1
        self.smoke = smoke
        
    def run(self, child_callback, embed_ipython=False):
        self.create_child(child_callback)
        #TODO: remove this below ??
#        def new_child(new_callback=None):
#            try:
#                self.kill_child
#            except Exception as e:
#                self.log.e(e)
#            if new_callback:
#                self.create_child(new_callback)
#            else:
#                self.create_child(child_callback)
#        self._new_child = new_child
        if embed_ipython:
            s = self # nice alias
            self.embed()
            self.kill_child
            raise SystemExit(0)
#        else:
#            #TODO: test it!
#            while self.parent_conn.poll(0):
#                self.log.i(self.parent_conn.recv())
    
    ishell = None
    def embed(self, **kwargs):
        """Call this to embed IPython at the current point in your program.
        """
        from IPython.terminal.ipapp import load_default_config
        from IPython.terminal.embed import InteractiveShellEmbed
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
        self._new_child()
    
    def send_test(self, **test_config):
        self.send_recv('new_test', **test_config)
        self.test_config = test_config

    def build_callback(self, **test_config):
        self.test_config = test_config

        def child_callback(child_conn):
            master = Master(child_conn)
            poll = master.io_loop(**test_config)            
            while 1:
                poll.next()
        
        return child_callback
    
    def create_child(self, child_callback):
        parent_conn, child_conn = multiprocessing.Pipe()
        self.parent_conn = parent_conn
        
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
        return self.parent_conn.poll()
    
    @property
    def test(self):
        answer = self.send_recv('parcial_callback')
        result, error = answer[0]
        if error:
            self.log.e(error)
        return result

    def send(self, cmd, *args, **kwargs):
        if self.poll():
            self.log.i('Remaining in buffer: %r'%self.parent_conn.recv())
        self.parent_conn.send(self.cmd(cmd, *args, **kwargs))
    
    def send_recv(self, cmd, *args, **kwargs):
        self.send(cmd, *args, **kwargs)
        return self.parent_conn.recv()
    
    @property
    def kill_child(self):
        if self.parent_conn and not self.parent_conn.closed: 
            self.log.i(self.send_recv(self._kill_command))
            self.parent_conn.close()
            self.parent_conn = None
        else:
            self.child_process.terminate()

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
