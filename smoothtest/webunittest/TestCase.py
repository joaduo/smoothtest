'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.settings.default import TEST_ROUND_LIFE
rel_imp.init()
from functools import wraps
from ..webunittest import unittest
from smoothtest.settings.solve_settings import solve_settings
from smoothtest.base import SmoothTestBase
from .WebdriverUtils import WebdriverUtils
import logging


class TestBase(WebdriverUtils):
    '''
    This base class takes care of Webdriver's initialization and shutdown.
    It also sets for webdriver parmeters like:
        implicit wait time, window size, log level
    '''
    def init_webdriver(self, settings=None):
        '''
        Initialize Webdriver and pass it to the WebdriverUtils._init_wedriver
        method, so its ready to be used from WebdriverUtils API.

        :param settings: smoothtest settings dictionary
        '''
        settings = self._settings = settings if settings else solve_settings()
        base_url = settings.get('web_server_url')
        self._level_mngr = WebdriverManager().enter_level(TEST_ROUND_LIFE,
                base_url, name=self.__class__.__name__)
        webdriver = self._level_mngr.acquire_driver()
        self.__setup_webdriver(webdriver, settings)
        self._init_webdriver(base_url, webdriver, settings)

    def __setup_webdriver(self, webdriver, settings):
        # Setup some webdriver parameters specified in smoothtest settings 
        if settings.get('webdriver_implicit_wait'):
            webdriver.implicitly_wait(settings.get('webdriver_implicit_wait'))
        if (settings.get('webdriver_window_size')
        and webdriver.get_window_size() != settings.get('webdriver_window_size')):
            webdriver.set_window_size(*settings.get('webdriver_window_size'))
        self.__set_webdriver_log_level(settings.get('webdriver_log_level'))

    def __set_webdriver_log_level(self, log_level):
        # Nicer method to setup webdriver's log level (too verbose by default)
        from selenium.webdriver.remote.remote_connection import LOGGER
        if log_level:
            LOGGER.setLevel(log_level)
        else:
            LOGGER.setLevel(logging.INFO)

    def shutdown_webdriver(self):
        '''
        Make sure we stop the webdriver correctly (if needed)
        '''
        self._level_mngr.exit_level()


class TestCase(unittest.TestCase, TestBase, SmoothTestBase):
    '''
    This class builds the common TestCase class to be inherit from while writing
    test cases.
    Aggregates:
        unittest.TestCase + TestBase + SmoothTestBase
    Each class gives a set of useful APIs available through methods.
    '''

    def __init__(self, *args, **kwargs):
        # Decorate methods who can fire screenshots on exceptoins
        self.decorate_exc_sshot()
        # Init parent class (unittest.TestCase, the other classed don't need initialization
        super(TestCase, self).__init__(*args, **kwargs)
        # Keep track of screenshots taken
        self._exc_screenshots = []

    def decorate_exc_sshot(self):
        '''
        Conditionally decorate methods according to the settings' screenshot_level.
        '''
        settings = solve_settings()
        # Decorate methods for taking screenshots upon exceptions
        if (settings.get('screenshot_level')
                and settings.get('screenshot_level') <= logging.ERROR):
            self._decorate_exc_sshot()

    def _exception_screenshot(self, name, exc):
        '''
        Overload WebdriverUtils._exception_screenshot method to keep track
        of screenshots taken. (for test reporting)

        :param name: Name of the exception screenshot
        :param exc: exception that fired the screenshot
        '''
        filename = super(TestCase, self)._exception_screenshot(name, exc)
        self._exc_screenshots.append(filename)
        return filename

    @staticmethod
    def disable_method(cls, meth, log_func=lambda msg: None):
        '''
        Disable class method. (to disable future calls)
        This method is useful when we want to make sure that a class' method is
        called only once. (because we want it to be called once per process)

        :param cls: class to disable the class method from
        :param meth: method to disable
        :param log_func: log function to use
        '''
        if not isinstance(meth, basestring):
            if not hasattr(meth, 'func_name'):
                meth = meth.im_func
            meth = meth.func_name
        func = getattr(cls, meth)
        func_types = [staticmethod, classmethod]
        for ftype in func_types:
            if isinstance(cls.__dict__[meth], ftype):
                @ftype
                @wraps(func)
                def no_op(*_, **__):
                    log_func('Ignoring call to {cls.__name__}.{meth}'
                             .format(cls=cls, meth=meth))
                setattr(cls, meth, no_op)
                return no_op

    def assert_text(self, xpath, value):
        '''
        Assert the text of the first node given by xpath is `value`
        (if xpath retrieves multiple nodes, only first node will be taken 
        in count)
        This is a nicer alias to extract_xsingle + assertEqual.

        :param xpath: xpath to extract text/html from
        :param value: value of the extracted text
        '''
        extracted = self.extract_xsingle(xpath)
        msg = (u'Expecting {value!r}, got {extracted!r} at {xpath!r}.'.
               format(**locals()))
        self.assertEqual(extracted, value, msg)
        self.screenshot('assert_text', xpath, value)


def smoke_test_module():
    pass


if __name__ == "__main__":
    smoke_test_module()
