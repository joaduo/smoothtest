# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import multiprocessing
import sys
import os
from .Context import singleton_decorator
from .base import AutoTestBase
from .TestSearcher import TestSearcher
from .ipython_extension import load_extension
from smoothtest.autotest.Master import Master

@singleton_decorator
class Main(AutoTestBase):
    def __init__(self, smoke=False):
        self.smoke = smoke
        
    def run(self, child_callback, embed_ipython=False):
        self.create_child(child_callback)
        def new_child(new_callback=None):
            try:
                self.kill_child
            except Exception as e:
                self.log.e(e)
            if new_callback:
                self.create_child(new_callback)
            else:
                self.create_child(child_callback)
        self._new_child = new_child
        if embed_ipython:
            s = self # nice alias
            self.embed()
            self.kill_child
            raise SystemExit(0)
    
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
        
    def new_test(self, class_path, regex=None, search=True, force=False):
        test_paths, parcial_reloads = TestSearcher().solve_paths((class_path, regex), search=search)
        test_config = dict(test_paths=test_paths, parcial_reloads=parcial_reloads, 
                      smoke=self.smoke)
        if not force:
            self.send('new_test', **test_config)
        else:
            child_callback = self.build_callback(**test_config)
            self._new_child(child_callback)
        return test_paths, parcial_reloads
    
    def send_tests(self, **test_config):
        self.send('new_test', **test_config)

    def build_callback(self, **test_config):
        
        def child_callback(child_conn):
            master = Master()
            poll = master.test(child_conn=child_conn, **test_config)            
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
        answer = self.send_recv('test_cmd')
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
        self.child_process.terminate()
        if self.parent_conn and not self.parent_conn.closed: #pipe is still open
            self.log.i(self.send_recv(self._kill_command))
            self.parent_conn.close()
            self.parent_conn = None

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()
