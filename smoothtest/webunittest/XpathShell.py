# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
import urlparse
rel_imp.init()
from argparse import ArgumentParser
from smoothtest.base import CommandBase
from smoothtest.IpythonEmbedder import IpythonEmbedder
from smoothtest.Logger import Logger
from .TestCase import TestBase

class XpathShell(TestBase):
    def __init__(self, logger=None):
        self.log = logger or Logger('xpath shell')

    def get(self, url):
        u = urlparse.urlparse(url)
        if not u.scheme:
            u = ('http', u.netloc, u.path, u.params, u.query, u.fragment)
            url = urlparse.urlunparse(u)
        self.get_driver().get(url)
        self.log.i('Current url: %r' % self.current_url())

    def run_shell(self, url=None):
        self.init_webdriver()
        self.set_base_url(None)
        #Aliases #TODO: add ipython extension
        dr = driver = self.get_driver()
        ex  = extract = self.extract_xpath
        xs = xsingle = self.extract_xsingle
        if url:
            self.get(url)
        IpythonEmbedder().embed()
        self.shutdown_webdriver()

class XpathShellCommand(CommandBase):

    def get_parser(self):
        parser = ArgumentParser(description='Test XPaths via Selenium.')
        parser.add_argument('url', nargs='?')
        self._add_smoothtest_common_args(parser)
        return parser

    def main(self, argv=None):
        args = self.get_parser().parse_args(argv)
        url = args.url
        XpathShell().run_shell(url=url)

def smoke_test_module():
    c = XpathShellCommand()

def main(argv=None):
    XpathShellCommand().main(argv)

if __name__ == "__main__":
    main()
