'''
'''
import unittest
from smoothtest.webunittest.WebdriverUtils import WebdriverUtils,\
    zero_screenshot, screenshot, no_screenshot
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.Logger import Logger
import os
from selenium.common.exceptions import UnexpectedAlertPresentException


def setUp():
    mngr = WebdriverManager()
    mngr.setup_display()
    webdriver = mngr.new_webdriver()
    logger = Logger(__name__)
    #settings = dict(webdriver_pooling = True)
    TestWebdriverUtils.browser = WebdriverUtils('', webdriver, logger, settings={})
    return mngr


def tearDown(mngr):
    mngr.close_webdrivers()
    mngr.stop_display()


class TestWebdriverUtils(unittest.TestCase):
    browser = None

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

    def test_screenshots(self):
        class WDU(WebdriverUtils):
    
            def __init__(self, base):
                self.log = Logger(self.__class__.__name__)
                self._decorate_exc_sshot()
                # Test twice
                self._decorate_exc_sshot()
    
            def get_driver(self, *args, **kwargs):
                class Driver(object):
    
                    def save_screenshot(self, path):
                        print('Would save to: %r' % path)
                return Driver()
    
            @zero_screenshot
            def extract_xpath(self, xpath, ret='text'):
                self.select_xpath(xpath, ret)
    
            @screenshot
            def _example(self, bar):
                try:
                    self.select_xpath(bar)
                finally:
                    raise LookupError('With screenshot')
    
            def _example2(self, bar):
                raise LookupError('Without screenshot')
    
            def _example3(self, bar):
                try:
                    self.select_xpath(bar)
                finally:
                    raise LookupError('Without screenshot')
    
            @no_screenshot
            def example4(self, bar):
                try:
                    self.select_xpath(bar)
                finally:
                    raise LookupError('Without screenshot')
    
        wdu = WDU('http://www.juju.com/',
                  # browser='Chrome'
                  )
        # wdu.get_page('/')
        #import traceback
        for m in [
            wdu.select_xpath,  # select_xpath
            wdu.extract_xpath,
            wdu._example,  # select_xpath + _example
            wdu._example2,
            wdu._example3,  # select_xpath
            wdu.example4,  # select_xpath
        ]:
            try:
                m('bar')
            except Exception as e:
                pass
                # traceback.print_exc()

if __name__ == "__main__":
    mngr = setUp()
    try:
        unittest.main()
    except SystemExit:
        pass
    tearDown(mngr)
