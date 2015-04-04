# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
rel_imp.init()
from argparse import ArgumentParser
from smoothtest.base import CommandBase
from smoothtest.IpythonEmbedder import IpythonEmbedder
from .TestCase import TestBase

class XpathShell(TestBase):
    def __init__(self):
        pass

    def run_shell(self, url=None):
        self.init_webdriver()
        self.set_base_url(None)
        #Aliases #TODO: add ipython extension
        dr = driver = self.get_driver()
        ex  = extract = self.extract_xpath
        xs = xsingle = self.extract_xsingle
        if url:
            driver.get(url)
        IpythonEmbedder().embed()
        self.shutdown_webdriver()

class XpathShellCommand(CommandBase):

    def get_parser(self):
        parser = ArgumentParser(description='Test XPaths via Selenium.')
        self._add_smoothtest_common_args(parser)
        return parser

    def main(self, argv=None):
        args = self.get_parser().parse_args(argv)
        XpathShell().run_shell()

def smoke_test_module():
    c = XpathShellCommand()

def main(argv=None):
    XpathShellCommand().main(argv)

if __name__ == "__main__":
    main()
