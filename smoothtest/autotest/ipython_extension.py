# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import urlparse
from IPython.core.magic import Magics, magics_class, line_magic
import shlex
from argparse import ArgumentParser
from smoothtest.Logger import Logger
import re
import sys
from smoothtest.settings.solve_settings import solve_settings
from xpathwebdriver.webdriver_manager import WebdriverManager


@magics_class
class AutotestMagics(Magics):
    '''
    Mainly add some "magic" commands to the autotest's Ipython shell.
    '''
    main = None
    log = Logger(name='Ipython Extension')

    def get_test_config(self):
        return self.main.test_config

    def __common(self, line):
        from .Command import Command
        command = Command()
        parser = command.get_extension_parser()
        try:
            args, unknown = parser.parse_known_args(shlex.split(line))
            test_config = command.get_test_config(args, unknown)
            test_config.update(force=args.force)
            return args, test_config
        except SystemExit:
            # Ignore SystemExit exception since ipython will ignore it anyway
            # (happens when passing --help or on error)
            pass

    def _send(self, test_config, temp=False):
        self.main.send_test(test_config, temp)

    def _test_magic_cmd_parser(self):
        parser = ArgumentParser(description='Manually trigger a test.')
        parser.add_argument('method', help='Test case method regex',
                            default='', type=str, nargs='?')
        parser.add_argument('-l', '--list', help='Display test cases list',
                            default=False, action='store_true')
        parser.add_argument('-f', '--force', help='Trigger full reload',
                            default=False, action='store_true')
        return parser

    @line_magic
    def help(self, line):
        print('Check https://github.com/joaduo/smoothtest/blob/master/smoothtest/autotest/AutotestGuide.md')

    @line_magic
    def test_m(self, line):
        line = ' -r {regex} -u'.format(regex=line)
        self._autotest(line)

    @line_magic
    def test(self, line):
        parser = self._test_magic_cmd_parser()
        try:
            test_config = self.get_test_config().copy()
            if line.strip():
                args = parser.parse_args(shlex.split(line))
                paths = test_config['test_paths']
                if args.list:
                    sys.stdout.write('\n'.join(paths) + '\n')
                    return
                if args.force:
                    # Force full reload
                    test_config.update(force=True)
                if args.method:
                    paths = [p for p in paths if re.search(args.method, p.split('.')[-1])]
                test_config['test_paths'] = paths
            self._send(test_config, temp=True)
        except SystemExit:
            pass

    @line_magic
    def smoothtest(self, line):
        return self._autotest(line)

    @line_magic
    def smtest(self, line):
        return self._autotest(line)

    @line_magic
    def autotest(self, line):
        self.log.w('Deprecated autotest command, use smoothtest instead')
        return self._autotest(line)

    def _autotest(self, line):
        res = self.__common(line)
        if not res:
            return
        args, test_config = res
        if args.update:
            # Update set values
            for k, v in self.get_test_config().iteritems():
                if not test_config.get(k):
                    test_config[k] = v
            if args.smoke is not None:
                test_config['smoke'] = True
            if args.nosmoke is not None:
                test_config['smoke'] = False
            test_config.update(force=args.force)
        self.log.i('Parsing arguments and sending new test config. Check children processes output below...')
        self._send(test_config)
        return 'Done sending new test_config=%r' % test_config

    @line_magic
    def steal_xpathbrowser(self, line):
        parser = ArgumentParser(prog='Steal XpathBrowser', 
                       description='Get an XpathBrowser instance bypassing any locking mechanism. (debugging purposes)')
        parser.add_argument('browser', type=str, default=self.main._get_browser_name(), nargs='?',
                            help='The browser we want the XpathBrowser object from.')
        try:
            args = parser.parse_args(shlex.split(line))
        except SystemExit:
            return
        xbrowser = self.main.steal_xpathbrowser(args.browser)
        if not xbrowser:
            self.log.w('No webdriver for browser %r' % args.browser)
        return xbrowser
    
    @line_magic
    def get(self, line):
        parser = ArgumentParser(prog='Get page at URL',
                       description='Fetch a URL using the current selected browser.')
        parser.add_argument('url', type=str,
                            help='Url we would like to open.')
        parser.add_argument('browser', type=str, default=self.main._get_browser_name(), nargs='?',
                            help='The browser name we want to open the Url with.')
        try:
            args = parser.parse_args(shlex.split(line))
        except SystemExit:
            return
        xbrowser = self.main.steal_xpathbrowser(args.browser)
        if not xbrowser:
            return
        u = urlparse.urlparse(args.url)
        if not u.scheme:
            u = ('http', u.netloc, u.path, u.params, u.query, u.fragment)
            url = urlparse.urlunparse(u)
        xbrowser.get_url(url)
        self.log.i('Current url: %r' % xbrowser.current_url())
        return xbrowser

    def _new_browser(self, browser):
        self.log.i('Setting browser to: %s' % browser)
        self.main.new_browser(browser)

    @line_magic
    def firefox(self, line):
        self._new_browser('Firefox')

    @line_magic
    def chrome(self, line):
        self._new_browser('Chrome')

    @line_magic
    def phantomjs(self, line):
        self._new_browser('PhantomJS')

    @line_magic
    def reset(self, line):
        self.main.reset()

    @line_magic
    def test_config(self, line):
        return self.get_test_config()

    @line_magic
    def enable_browser(self, line):
        if not solve_settings().get('webdriver_enabled'):
            solve_settings().set('webdriver_enabled', True)
            #WebdriverManager().init_level(level)


def load_extension(ipython, main):
    AutotestMagics.main = main
    ipython.register_magics(AutotestMagics)


def load_ipython_extension(ipython):
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ipython.register_magics(AutotestMagics)


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass


def smoke_test_module():
    am = AutotestMagics(None)


if __name__ == "__main__":
    smoke_test_module()
