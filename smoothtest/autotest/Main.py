# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
rel_imp.init()
from smoothtest.settings.default import PROCESS_LIFE, INMORTAL_LIFE
from smoothtest.webunittest.XpathBrowser import XpathBrowser
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
    '''
    This class contains the "main loop" logic of the autotest command
    It will create 2 forked subprocess as:
        Main Process (this one)
          Master Subprocess (Child)
            TestRunner Subprocess (Grand Child)

    Roles are as:
        Main: where the CLI loop is done, sending commands to Master.
        Master: where file watching happens; events from Main and TestRunner are integrated
            decides whether to: trigger tests, kill TestRunner and recreate it.
        TestRunner: where tests are loaded and ran, test results are sent back to Master.
    '''

    def __init__(self):
        '''
        Initialize attributes
        '''
        self._timeout = 1
        self._ishell = None   # Ipython Shell instance
        self.test_config = {} # Configuration parameters sent for each test round
        self._slave = None    # Slave instance (configures how tests are ran)
        self._child_pids = [] # Store pids of children, in case we need to kill them
        self._wdriver_mngr = WebdriverManager() # common WebdriverManager instance
        self._browser_name = None # Current selected browser name
        self._level_mngr = None # WebdriverLevelManager for each time we enter/leave a "webdriver life level" 

    def run(self, test_config, embed_ipython=False, block=False):
        '''
        Runs the main CLI loop.
        If ipython is not present it will fallback to gdb as CLI.

        :param test_config: initial configuration parameters
        :param embed_ipython: if True, it will embed a interactive shell.
        :param block: block waiting for events (in case no shell was enabled)
        '''
        self.log.set_pre_post(pre='Shell UI')
        self.test_config = test_config
        self.create_child()
        if embed_ipython:
            from .ipython_extension import load_extension
            def extension(ipython):
                return load_extension(ipython, self)
            self._ishell = IpythonEmbedder().embed(extension)
            self.kill_child()
            self.end_main()
            self._wdriver_mngr.stop_display()
            raise SystemExit(0)
        elif block:
            self.log.i(self.recv())

    def create_child(self):
        '''
        Create Master role subprocess
        '''
        slave = self._build_slave()

        def callback(conn):
            if self._ishell:
                self._ishell.exit_now = True
            sys.stdin.close()
            master = Master(conn, slave)
            poll = master.io_loop(self.test_config)
            while True:
                poll.next()

        self.start_subprocess(callback, pre='Master')
        slave_pid = self.call_remote(Master.get_subprocess_pid)
        self._child_pids.append(('slave_pid', slave_pid))
        self._child_pids.append(('master_pid', self.get_subprocess_pid()))

    def _build_slave(self):
        # Build the Slave class instance (used to control how tests are ran)
        if not self._slave:
            # Release no longer used webdriver
            if self._level_mngr:
                self._level_mngr.release_driver()
            # Quit those drivers not responding
            self._wdriver_mngr.quit_all_failed_webdrivers()
            self._wdriver_mngr.set_browser(self._get_browser_name())
            # Enter the level again
            self._level_mngr = self._wdriver_mngr.enter_level(level=PROCESS_LIFE)
            self._slave = Slave(TestRunner)
        return self._slave

    def _set_browser_name(self, browser):
        # Set the default browser to use from now on
        self._browser_name = browser or self._browser_name
        
    def _get_browser_name(self):
        # Get the name of the current browser in use
        return self._browser_name or self.global_settings.get('webdriver_browser')

    def reset(self):
        '''
        Reset as if we were from a fresh start.
        '''
        self.end_main()
        self._wdriver_mngr.quit_all_failed_webdrivers()
        self.kill_child()
        self.create_child()

    def new_browser(self, browser=None):
        '''
        Select a new current browser to run tests with. (will create if missing else reuse)
        :param browser: browser's name string. Eg:'Firefox', 'Chrome', 'PhantomJS'
        '''
        self._set_browser_name(browser)
        self.kill_child()
        self.create_child()

    def send_test(self, test_config, temp=False):
        '''
        Send tests config parameters to the Master process.
        (which in turn will send to TestRunner)
        '''
        if self._healthy_webdriver():
            self.send_recv('new_test', **test_config)
            if not temp:
                self.test_config = test_config

    def test(self):
        '''
        Send parcial reload testing command.
        Means testing without recreating TestRunner subprocess
        '''
        if self._healthy_webdriver():
            cmd = 'partial_callback'
            ans = self.send_recv(cmd)
            if ans.error:
                self.log.e(ans.error)
            return ans

    def _healthy_webdriver(self):
        # Check if used webdrivers are in healthy status
        if self._wdriver_mngr.quit_all_failed_webdrivers():
            self.log.w('Webdriver failed. Restarting subprocesses...')
            # Restart browser if needed
            self.new_browser()
            return False
        return True

    def send(self, cmd, *args, **kwargs):
        '''
        Send arbitrary commands to the Master subprocess.
        Also make sure no remaining incoming data is in the pipe buffer
        before sending.
        
        :param cmd: method name of Master class
        :param args: variable args matching the signature of the remote method
        :param kwargs: variable keyword args matching the signature of the remote method
        '''
        while self.poll():
            self.log.i('Remaining in buffer: %r' % self.recv())
        return super(Main, self).send(cmd, *args, **kwargs)

    def kill_child(self):
        '''
        Send a kill command to the Master subprocess.
        If unable to gently die, we force killing Master subprocess.
        '''
        answer = self.kill(block=True, timeout=3)
        self._force_kill(self._child_pids)
        self._slave = None
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
        '''
        Function we call when leaving the main loop or when resetting 
        the testing.
        '''
        if self._level_mngr:
            self._level_mngr.exit_level()
            self._level_mngr = None

    def steal_xpathbrowser(self, browser):
        '''
        Get an XpathBrowser instance bypassing any locking mechanism. (debugging purposes)
        :param browser: browser's name string
        '''
        browser = self._wdriver_mngr.expand_browser_name(browser)
        webdrivers = self._wdriver_mngr.list_webdrivers(which='all')
        for wd, (brwsr, _) in webdrivers.iteritems():
            if browser == brwsr:
                return XpathBrowser(wd)


def smoke_test_module():
    import time
    from smoothtest.settings.solve_settings import solve_settings
    solve_settings().set('webdriver_browser_life', INMORTAL_LIFE)
    def get_main():
        main = Main()
        main.run({}, embed_ipython=False, block=False)
        return main
    main = get_main()
    time.sleep(0.5)
    main.kill_child()
    # Test forcing kills
    main = get_main()
    main._force_kill(main._child_pids)
    # TODO: build a master and _slave that need to be killed

if __name__ == "__main__":
    smoke_test_module()
