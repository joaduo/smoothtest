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
from .chat_example import default_port

class TestChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # It will initialize the webdriver if no webdriver is present from upper levels
        # Since we don't want to initialize a webdriver for each single test
        # we create the webdriver one level upper SINGLE_TEST_LIFE
        cls.cls_level_mngr = WebdriverManager().enter_level(level=TEST_ROUND_LIFE)

    @classmethod
    def tearDownClass(cls):
        cls.cls_level_mngr.exit_level()

    def setUp(self):
        # The webdriver is already initialized on previous level
        # We simply manage it's context with this new _level_mngr
        self._level_mngr = WebdriverManager().enter_level(level=SINGLE_TEST_LIFE)
        # Lock webdriver and build XpathBrowser API
        self.browser = self._level_mngr.get_xpathbrowser(name=__name__)
        self.base_url = 'http://localhost:%s' % default_port
        self.browser.set_base_url(self.base_url)

    def tearDown(self):
        # Release webdriver, we are not longer using it.
        self._level_mngr.exit_level()

#    def test_loaded(self):
#        b = self.browser
#        b.get_page('/')
#        # Make sure there is at least 1 element
#        b.select_xsingle(".//*[@id='input_area']")

    def test_send_msg(self):
        browser1 = self.browser
        path = '/'
        with WebdriverManager().enter_level(level=SINGLE_TEST_LIFE, name='Browser2') \
        as browser2:
            browser1.get_page(path)
            browser2.set_base_url(self.base_url)
            browser2.get_page(path)
            username = 'my name'
            message = 'my message'
            browser1.fill(".//*[@id='username']", username)
            browser1.fill(".//*[@id='message']", message)
            browser1.click(".//*[@id='input_area']/button")
            msgs_xpath = ".//*[@id='chat']/div[3]/*/text()"
            browser1.wait(1)
            msg_recv = ''.join(browser1.select_xpath(msgs_xpath))
            self.assertEqual(msg_recv, '%s: %s' % (username, message))
            msg_recv2 = ''.join(browser2.select_xpath(msgs_xpath))
            self.assertEqual(msg_recv, msg_recv2)


if __name__ == "__main__":
    unittest.main()
