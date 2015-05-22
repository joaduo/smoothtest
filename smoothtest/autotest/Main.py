# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
from smoothtest.settings.default import PROCESS_LIFE
rel_imp.init()
import os
import signal
import sys
from .base import ParentBase
from .Master import Master
from .Slave import Slave
from .TestRunner import TestRunner
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.IpythonEmbedder import IpythonEmbedder


class Main(ParentBase):

    def __init__(self):
        self._timeout = 1
        self.ishell = None
        self.test_config = {}
        self._slave = None
        self._child_pids = []
        self._wdriver_mngr = WebdriverManager()
        self._level_mngr = None

    def run(self, test_config, embed_ipython=False, block=False):
        self.log.set_pre_post(pre='Autotest CLI')
        self.test_config = test_config
        self.create_child()
        if embed_ipython:
            from .ipython_extension import load_extension
            def extension(ipython):
                return load_extension(ipython, self)
            self._run_ipython(extension)
            self.kill_child()
            self.end_main()
            raise SystemExit(0)
        elif block:
            self.log.i(self.recv())
        self._wdriver_mngr.stop_display()

    def _run_ipython(self, extension):
        test_config = self.test_config
        IpythonEmbedder().embed(extension)

    def reset(self):
        self.kill_child()
        self.create_child()

    def send_test(self, **test_config):
        if self._healthy_webdriver():
            self.send_recv('new_test', **test_config)
            self.test_config = test_config

    def new_browser(self, browser=None):
        # Build the new slave
        if browser:
            m = dict(f='Firefox',
                     c='Chrome',
                     p='PhantomJS',
                     )
            browser = m.get(browser.lower()[0], m['f'])
            self.global_settings.set('webdriver_browser', browser)
        self._build_slave(force=True)
        self.reset()

    def _build_slave(self, force=False):
        if (not self._slave or force):
            child_kwargs = {}
            # Release no longer used webdriver
            if self._level_mngr:
                self._level_mngr.release_driver()
            # Quit those drivers not responding
            self._wdriver_mngr.quit_all_failed_webdrivers()
            # Enter the level again
            self._level_mngr = self._wdriver_mngr.enter_level(level=PROCESS_LIFE)
            self._slave = Slave(TestRunner, child_kwargs=child_kwargs)
        return self._slave

    def _healthy_webdriver(self):
        if self._wdriver_mngr.quit_all_failed_webdrivers():
            self.log.w('Webdriver failed. Restarting subprocesses...')
            self.new_browser()
            return False
        return True

    def create_child(self):
        slave = self._build_slave()

        def callback(conn):
            if self.ishell:
                self.ishell.exit_now = True
            sys.stdin.close()
            master = Master(conn, slave)
            poll = master.io_loop(self.test_config)
            while True:
                poll.next()

        self.start_subprocess(callback, pre='Master')
        slave_pid = self.call_remote(Master.get_subprocess_pid)
        self._child_pids.append(('slave_pid', slave_pid))
        self._child_pids.append(('master_pid', self.get_subprocess_pid()))

    def test(self):
        if self._healthy_webdriver():
            cmd = 'partial_callback'
            ans = self.send_recv(cmd)
            self.log.e(ans.error)
            return ans

    def send(self, cmd, *args, **kwargs):
        while self.poll():
            self.log.i('Remaining in buffer: %r' % self.recv())
        return super(Main, self).send(cmd, *args, **kwargs)

    def kill_child(self):
        answer = self.kill(block=True, timeout=3)
        self._force_kill(self._child_pids)
        self._child_pids = []
        return answer

    def _force_kill(self, child_pids):
        '''
        Fallback mechanism that sends SIGKILL signal if any subprocess is still up.
        :param child_pids: iterable of subprocesses pids
        '''
        def process_running(pid):
            # Check For the existence of a unix pid.
            try:
                # Why not use signal.SIG_DFL ? (= 0)
                # Seems 0 will kill a process on Windows
                # http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
                os.kill(pid, 0)
                return True
            except OSError:
                return False
        for name, pid in child_pids:
            if process_running(pid):
                self.log.w('Pid (%r,%r) still up. Sending SIGKILL...' % (name, pid))
                os.kill(pid, signal.SIGKILL)

    def end_main(self):
        if self._level_mngr:
            self._level_mngr.leave_level()


def smoke_test_module():
    import time
    def get_main():
        main = Main(smoke=True)
        main.run({}, embed_ipython=False, block=False)
        return main
    main = get_main()
    time.sleep(0.5)
    main.kill_child
    # Test forcing kills
    main = get_main()
    main._force_kill(main._child_pids)
    # TODO: build a master and _slave that need to be killed

if __name__ == "__main__":
    smoke_test_module()
