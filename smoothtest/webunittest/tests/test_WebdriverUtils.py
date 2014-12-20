'''
Created on Dec 18, 2014

@author: jduo
'''
import unittest
from smoothtest.webunittest.WebdriverUtils import WebdriverUtils
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.Logger import Logger
import os
from selenium.common.exceptions import UnexpectedAlertPresentException

class TestWebdriverUtils(unittest.TestCase):
    def setUp(self):
        self._mngr = WebdriverManager()
        self._mngr.setup_display()
        webdriver = self._mngr.new_webdriver()
        logger = Logger(self.__class__.__name__)
        self.browser = WebdriverUtils('', webdriver, logger, settings={})
        
    def tearDown(self):
        self._mngr.close_webdrivers()
        self._mngr.stop_display()

    def _get_page_path(self, filename):
        join = os.path.join
        path = join(os.path.dirname(__file__), 'html', filename)
        return 'file://' + path

    def test_dismiss_alert(self):
        path = self._get_page_path('test_dismiss_alert.html')
        try:
            self.browser.get_page(path)
        except UnexpectedAlertPresentException:
            self.browser.wipe_alerts()

if __name__ == "__main__":
    unittest.main()
