# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest
import rel_imp; rel_imp.init()
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.settings.default import TEST_ROUND_LIFE, SINGLE_TEST_LIFE
from .chat_example import port

base_url = 'http://localhost:%s' % port

class TestXpathBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to enter "single test level" of life for each test
        # It will initialize the webdriver if no webdriver is present from upper levels
        cls._level_mngr = WebdriverManager().enter_level(level=TEST_ROUND_LIFE)
        # Get Xpath browser
        cls.browser = cls._level_mngr.get_xpathbrowser(name=__name__)
        cls.browser.set_base_url(base_url)
    
    @classmethod
    def tearDownClass(cls):
        cls._level_mngr.exit_level()

    def test_loaded(self):
        b = self.browser
        b.get_page('/')
        # Make sure there is at least 1 element
        b.select_xsingle(".//*[@id='input_area']")

    def test_send_msg(self):
        browser1 = self.browser
        path = '/'
        with WebdriverManager().enter_level(level=SINGLE_TEST_LIFE, name='Browser2') \
        as browser2:
            browser1.get_page(path)
            browser2.set_base_url(base_url)
            browser2.get_page(path)
            username = 'my name'
            message = 'my message'
            browser1.fill_input(".//*[@id='username']", username)
            browser1.fill_input(".//*[@id='message']", message)
            browser1.click(".//*[@id='input_area']/button")
            msgs_xpath = ".//*[@id='chat']/div"
            msg_recv = browser1.extract_xpath(msgs_xpath)[-1]
            self.assertEqual(msg_recv, '%s: %s' % (username, message))
            msg_recv2 = browser2.extract_xpath(msgs_xpath)[-1]
            self.assertEqual(msg_recv, msg_recv2)


if __name__ == "__main__":
    unittest.main()
