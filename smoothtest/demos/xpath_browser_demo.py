# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest
import rel_imp; rel_imp.init()
from .base import WebUnitTestBase
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.Logger import Logger
from smoothtest.webunittest.XpathBrowser import XpathBrowser
from smoothtest.settings.default import SINGLE_TEST_LIFE
import os


class TestXpathBrowser(WebUnitTestBase):
    def setUp(self):
        # We need to enter "single test level" of life for each test
        # It will initialize the webdriver if no webdriver is present from upper levels
        self.__level_mngr = WebdriverManager().enter_level(level=SINGLE_TEST_LIFE)
        # Once we make sure there is a webdriver available, we acquire it
        # and block usage from other possible users
        webdriver = self.__level_mngr.acquire_driver()
        # Initialize the XpathBrowser class
        logger = Logger(__name__)
        self.browser = XpathBrowser('', webdriver, logger, settings={})

    def tearDown(self):
        # Make sure we quit those webdrivers created in this specific level of life
        self.__level_mngr.leave_level()

    def test_demo(self):
        # Load a local page for the demo
        self.get_local_page('xpath_browser_demo.html')
        # Do 2 type of selection
        self.browser.select_xpath('//div') # Xpath must be present, but no inner element may be returned
        self.browser.select_xsingle('//div') # Xpath must be present and at least 1 element must be present

    def get_local_page(self, file_name):
        # Auxiliary method
        url = 'file://' + os.path.join(os.path.dirname(__file__), 'html', file_name)
        self.browser.get_url(url)


if __name__ == "__main__":
    unittest.main()
