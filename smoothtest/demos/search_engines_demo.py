# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.settings.default import SINGLE_TEST_LIFE


class SearchEnginesDemo(unittest.TestCase):
    def setUp(self):
        # We need to enter "single test level" of life for each test
        # It will initialize the webdriver if no webdriver is present from upper levels
        self._level_mngr = WebdriverManager().enter_level(level=SINGLE_TEST_LIFE)
        # Get Xpath browser
        self.browser = self._level_mngr.get_xpathbrowser(name=__name__)

    def tearDown(self):
        # Make sure we quit those webdrivers created in this specific level of life
        self._level_mngr.exit_level()

    def test_duckduckgo(self):
        # Load a local page for the demo
        self.browser.get_url('https://duckduckgo.com/')
        # Type smoothtest and press enter
        self.browser.fill(".//*[@id='search_form_input_homepage']", 'smoothtest\n')
        result_link = './/a[@title="smoothtest "]'
        # Wait for the result to be available
        self.browser.wait_condition(lambda brw: brw.select_xpath(result_link))
        # Click on result
        self.browser.click(result_link)
        # First result should point to github
        expected_url = 'https://github.com/joaduo/smoothtest'
        wait_url = lambda brw: brw.current_url() == expected_url
        # Make sure we end up in the right url
        self.assertTrue(self.browser.wait_condition(wait_url))

    def test_google(self):
        # go to google
        self.browser.get_url('https://www.google.com/')
        # search for smoothtest and press enter
        self.browser.fill(".//*[@id='lst-ib']", 'smoothtest\n')
        first_result = './/a[contains(text(),"smoothtest 0.1.3")]'
        # Wait for first result
        self.browser.wait_condition(lambda brw: brw.select_xpath(first_result))
        # Click first result
        self.browser.click(first_result)
        # Make sure we went to pypi
        wait_pypi_url = lambda brw: brw.current_url() == 'https://pypi.python.org/pypi/smoothtest/0.1.3'
        self.assertTrue(self.browser.wait_condition(wait_pypi_url))


if __name__ == "__main__":
    unittest.main()
