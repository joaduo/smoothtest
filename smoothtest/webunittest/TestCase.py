'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
import os
import tempfile
from smoothtest.webunittest.ImagesComparator import ImagesComparator
import shutil
from smoothtest.settings.default import SINGLE_TEST_LIFE
from smoothtest.settings.solve_settings import solve_settings
from smoothtest.base import SmoothTestBase
from .ScreenshotDecorator import ScreenshotDecorator
from .WebdriverManager import WebdriverManager
from ..webunittest import unittest
from functools import wraps
import logging


class TestCase(unittest.TestCase, SmoothTestBase):
    '''
    This class builds the common TestCase class to be inherit from while writing
    test cases.
    Aggregates:
        unittest.TestCase + TestBase + SmoothTestBase
    Each class gives a set of useful APIs available through methods.
    '''
    def __init__(self, *args, **kwargs):
        # Keep track of screenshots taken
        self._exc_screenshots = []
        # Decorate methods who can fire screenshots on exceptoins
        self._decorate_exc_sshot()
        # Temporary assert screenshots (for comparison)
        self._tmp_screenshots_dir = None
        # Init parent class (unittest.TestCase, the other classed don't need initialization
        super(TestCase, self).__init__(*args, **kwargs)

    def _decorate_exc_sshot(self):
        '''
        Conditionally decorate methods according to the settings' screenshot_level.
        '''
        settings = solve_settings()
        # Decorate methods for taking screenshots upon exceptions
        if (settings.get('screenshot_level')
                and settings.get('screenshot_level') <= logging.ERROR):
            def get_browser():
                return self.browser
            ScreenshotDecorator(get_browser, self, self._on_screenshot)

    def _on_screenshot(self, name, exc, filename):
        '''
        Exception screenshot callback definition.
        Keeps track of taken screenshots. (for test reporting)

        :param name: Name of the exception screenshot
        :param exc: exception that fired the screenshot
        :param filename: file name of the saved screenshot
        '''
        self._exc_screenshots.append(filename)

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

    def setUp_browser(self, settings=None):
        '''
        Common method to setup webdriver and return XpathBrower object.
        :param settings: smoothtest setttings wrapper/dictionary
        :returns: XpathBrower object.
        '''
        # Solve settings
        settings = settings or self.global_settings
        # Enter single test level
        self._level_mngr = WebdriverManager().enter_level(level=SINGLE_TEST_LIFE)
        # Build browser instance
        browser = self._level_mngr.get_xpathbrowser()
        # Setup webdriver parameters before doing the tets
        webdriver = self._level_mngr.get_locked_driver()
        # Setup some webdriver parameters specified in smoothtest settings 
        if settings.get('webdriver_implicit_wait'):
            webdriver.implicitly_wait(settings.get('webdriver_implicit_wait'))
        if (settings.get('webdriver_window_size')
        and webdriver.get_window_size() != settings.get('webdriver_window_size')):
            webdriver.set_window_size(*settings.get('webdriver_window_size'))
        self.__set_webdriver_log_level(settings.get('webdriver_log_level'))
        # Finally return the XpathBrowser instance
        return browser

    def __set_webdriver_log_level(self, log_level):
        # Nicer method to setup webdriver's log level (too verbose by default)
        from selenium.webdriver.remote.remote_connection import LOGGER
        if log_level:
            LOGGER.setLevel(log_level)
        else:
            LOGGER.setLevel(logging.INFO)

    def tearDown_browser(self):
        '''
        Common method to tearDown webdriver in case we called setUp_browser
        on setup
        '''
        # Make sure we leave webdriver clean
        self._level_mngr.exit_level()

    def assert_text(self, xpath, value):
        '''
        Assert the text of the first node given by xpath is `value`
        (if xpath retrieves multiple nodes, only first node will be taken 
        in count)
        This is a nicer alias to extract_xsingle + assertEqual.

        :param xpath: xpath to extract text/html from
        :param value: value of the extracted text
        '''
        extracted = self.browser.extract_xsingle(xpath)
        msg = (u'Expecting {value!r}, got {extracted!r} at {xpath!r}.'.
               format(**locals()))
        self.assertEqual(extracted, value, msg)

    def assert_screenshot(self, screenshot_id=None, threshold=100, crop_threshold=100):
        assert_dir = self.global_settings.get('assert_screenshots_dir')
        screenshot_id += '.png'
        ok_file = os.path.join(assert_dir, screenshot_id) 
        if not os.path.isfile(ok_file):
            if self.global_settings.get('assert_screenshots_learning'):
                self.log.d('Learning screenshot for %r' % screenshot_id)
                self.browser.save_screenshot(ok_file)
            else:
                raise LookupError('No reference screenshot file %r for '
                                  'screenshot id:%r' % (ok_file, screenshot_id))
        else:
            if not self._tmp_screenshots_dir:
                self._tmp_screenshots_dir = tempfile.mkdtemp()
            test_file = os.path.join(self._tmp_screenshots_dir, screenshot_id)
            self.browser.save_screenshot(test_file)
            assert os.path.isfile(test_file), ('The screenshot %r was not saved'
                                               % screenshot_id)
            comp = ImagesComparator()
            equal = comp.compare(ok_file, test_file, threshold)
            if not equal:
                self._save_failed_screenshot(ok_file, test_file, screenshot_id, crop_threshold)
            self.assert_(equal, 'Reference(%r) != Screenshot(%r), threshold=%s' % (ok_file, test_file, threshold))

    def _save_failed_screenshot(self, ok_file, test_file, screenshot_id, crop_threshold):
        save_dir = self.global_settings.get('assert_screenshots_failed_dir')
        assert os.path.isdir(save_dir), 'Inexistent directory %r' % save_dir
        failed = os.path.join(save_dir, 'failed_' + screenshot_id)
        # Create the diff
        diff = os.path.join(save_dir, 'failed_diff_' + screenshot_id)
        ImagesComparator().create_diff(ok_file, test_file, diff, crop_threshold)
        # Move the failing image
        shutil.move(test_file, failed)
        # Return the path to intercept them in reports
        return failed, diff


def smoke_test_module():
    pass


if __name__ == "__main__":
    smoke_test_module()
