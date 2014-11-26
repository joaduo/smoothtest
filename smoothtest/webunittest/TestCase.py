'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from functools import wraps
from ..webunittest import unittest
from smoothtest.settings.solve_settings import solve_settings
from smoothtest.base import SmoothTestBase
from .WebdriverUtils import WebdriverUtils, new_driver


class TestBase(WebdriverUtils):
    _global_webdriver = None
    @staticmethod
    def set_webdriver(webdriver):
        TestBase._global_webdriver = webdriver
    
    @staticmethod
    def _new_webdriver(settings):
        #TODO: passing a webdriver factory, so we can cycle them
        #locking and releasing them
        browser = settings.get('webdriver_browser')
        if settings.get('webdriver_pooling'):
            if not TestBase._global_webdriver:
                TestBase._global_webdriver = new_driver(browser)
            driver = TestBase._global_webdriver
        else:
            driver = new_driver(browser)
        return driver

    def _init_webserver_webdriver(self, settings=None, webdriver=None):
        settings = self._settings = settings if settings else solve_settings()
        base_url = settings.get('web_server_url')
        browser = settings.get('webdriver_browser')
        webdriver = webdriver if webdriver else TestBase._new_webdriver(settings)
        self._set_webdriver_log_level(settings.get('webdriver_log_level'))
        self._init_webdriver(base_url, browser=browser, webdriver=webdriver,
                             screenshot_level=self._settings.screenshot_level)

    def _set_webdriver_log_level(self, log_level):
        from selenium.webdriver.remote.remote_connection import LOGGER
        LOGGER.setLevel(log_level)

    def _shutdown_webserver_webdriver(self):
        if (not self._settings.get('webdriver_keep_open') and
            not self._settings.get('webdriver_pooling')):
            self._quit_webdriver()


class TestCase(unittest.TestCase, TestBase, SmoothTestBase):
    @staticmethod
    def disable_method(cls, meth, log_func=lambda msg:None):
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
                def no_op(*_,  **__):
                    log_func('Ignoring call to {cls.__name__}.{meth}'
                              .format(cls=cls, meth=meth))
                setattr(cls, meth, no_op)
                return no_op

    def assert_text(self, xpath, value):
        extracted = self.extract_xpath(xpath)
        msg = (u'Expecting {value!r}, got {extracted!r} at {xpath!r}.'.
               format(**locals()))
        self.assertEqual(extracted, value, msg)
        self.screenshot('assert_text', xpath, value)


def smoke_test_module():
    pass


if __name__ == "__main__":
    smoke_test_module()
