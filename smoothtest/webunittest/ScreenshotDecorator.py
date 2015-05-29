# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import re
import inspect
from functools import wraps
from types import MethodType
from threading import Lock
import os
from smoothtest.base import SmoothTestBase


_with_screenshot = '_with_screenshot'
_zero_screenshot = '_zero_screenshot'


def zero_screenshot(method):
    '''
    Decorated method won't have any exception screenshot until we leave the method
    (means no screenshot on other methods called too)

    :param method: decorated method
    '''
    setattr(method, _zero_screenshot, True)
    return method


def screenshot(method):
    '''
    If the method raises an exception, take a screenshot.

    :param method: decorated method
    '''
    setattr(method, _with_screenshot, True)
    return method


def no_screenshot(method):
    '''
    No screenshot for exceptions at this decorated method.
    But any other method is free to take screenshots for any exception.

    :param method: decorated method
    '''
    setattr(method, _with_screenshot, False)
    return method


class ScreenshotDecorator(SmoothTestBase):
    def __init__(self, get_browser, test, on_screenshot=None, meth_filter=None):
        self._get_browser = get_browser
        self._test = test
        self._meth_filter = meth_filter
        self._on_screenshot = on_screenshot
        # Gather all exceptions seen (to avoid repeating screenshots)
        self._seen_exceptions = set()
        # Lock for avoiding taking screenshots
        self._sshot_lock = Lock()
        self._decorate_exc_sshot()

    def _decorate_exc_sshot(self):
        fltr = lambda n, method: (getattr(method, _with_screenshot, False)
                                  or n.startswith('test'))
        meth_filter = self._meth_filter or fltr
        decorated = self._test
        # Decorate our own methods, if None provided #TODO: remove later
        for name, method in inspect.getmembers(decorated):
            if (getattr(method, '_screenshot_decorated', False)
                or not (isinstance(method, MethodType)
                        and getattr(method, _with_screenshot, True))):
                # Do not decorate if:
                # - already decorated
                # - its not a method
                # - attribute _with_screenshot = False
                continue
            if getattr(method, _zero_screenshot, False):
                # Decorate to avoid excs screenshots on this method, neither
                # on deeper levels
                method = self._decorate(name, method, zero_screeshot=True)
                setattr(decorated, name, method)
            elif(name != 'screenshot'
                 and meth_filter(name, method)):
                # We want to decorate this method to capture screenshots
                self.log.debug('Decorating %r for screenshot' % name)
                method = self._decorate(name, method)
                setattr(decorated, name, method)

    def _decorate(self, name, method, zero_screeshot=False):
        if not zero_screeshot:
            # Capture sreenshot
            @wraps(method)
            def dec(*args, **kwargs):
                self.log.i('-'*20 + 'entering %s' % method + '-'*20)
                try:
                    return method(*args, **kwargs)
                except Exception as e:
                    if (e not in self._seen_exceptions
                            and self._sshot_lock.acquire(False)):
                        self._seen_exceptions.add(e)
                        self._exception_screenshot(name, e)
                        self._sshot_lock.release()
                    raise
        else:
            # No excs screenshot at any deeper level decorator
            @wraps(method)
            def dec(*args, **kwargs):
                # block any further exception screenshot, until
                # we return from this call
                locked = self._sshot_lock.acquire(False)
                try:
                    return method(*args, **kwargs)
                finally:
                    if locked:
                        self._sshot_lock.release()
        dec._screenshot_decorated = True
        return dec

    def _string_to_filename(self, str_, max_size=150):
        '''
        For example:
          'My Super Company' into 'my_super_company'
        It will became like a python variable name, although it will accept
          starting with a number
        2-Will collect alphanumeric characters and ignore the rest
        3-Will join collected groups of alphanumeric characters with "_"
        :param str_:
        '''
        str_ = str_.strip()
        words = re.findall(r'[a-zA-Z0-9][a-zA-Z0-9]*', str_)
        str_ = '_'.join(words)
        if max_size:
            return str_[:max_size]
        else:
            return str_

    _exc_sshot_count = 0

    def _exception_screenshot(self, name, exc, exc_dir=None):
        self._exc_sshot_count += 1
        exc = self._string_to_filename(repr(exc))
        count = self._exc_sshot_count
        test = self._test.__class__.__name__
        filename = '{count:03d}.{test}.{name}.{exc}.png'.format(**locals())
        self.log.e('Saving exception screenshot to: %r' % filename)
        exc_dir = exc_dir or self.global_settings.get('screenshot_exceptions_dir')
        self._get_browser().save_screenshot(os.path.join(exc_dir, filename))
        if self._on_screenshot:
            self._on_screenshot(name, exc, filename)
        return filename



def smoke_test_module():
    from smoothtest.webunittest.WebdriverManager import WebdriverManager
    from smoothtest.settings.default import SINGLE_TEST_LIFE
    mngr = WebdriverManager()
    mngr.set_browser('Firefox')
    lvl = mngr.enter_level(level=SINGLE_TEST_LIFE)
    class ExampleTest(object):
        def test_something(self):
            raise LookupError('Example Exception')
    test = ExampleTest()
    browser = lvl.get_xpathbrowser(name='test')
    get_browser = lambda : browser
    dec = ScreenshotDecorator(get_browser, test)
    dec._decorate_exc_sshot()
    lvl.get_locked_driver().get('http://www.example.com')
    try:
        test.test_something()
    except Exception as e:
        pass
        #print e
    lvl.exit_level()


if __name__ == "__main__":
    smoke_test_module()

