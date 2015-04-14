# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import urlparse
import time
import re
import inspect
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.common.exceptions import WebDriverException,\
    TimeoutException
from functools import wraps
from types import MethodType
from threading import Lock
from smoothtest.Logger import Logger
import urllib
import os
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions


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


class Url(object):

    '''A url object that can be compared with other url orbjects
    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings.
    from http://stackoverflow.com/questions/5371992/comparing-two-urls-in-python
    '''

    def __init__(self, url):
        if not isinstance(url, Url):
            self._orig = parts = urlparse.urlparse(url)
            _query = frozenset(urlparse.parse_qsl(parts.query))
            _path = urllib.unquote_plus(parts.path).rstrip('/')
            parts = parts._replace(query=_query, path=_path)
            self.parts = parts
        else:
            self._orig = url._orig
            self.parts = url.parts

    def get_original(self):
        '''
        Get original url.
        '''
        return urlparse.urlunparse(self._orig)

    def get_path_and_on(self):
        '''
        Get (path + params + query + fragment) as string from original url.
        '''
        return urlparse.urlunparse(self._orig._replace(scheme='', netloc=''))

    @staticmethod
    def are_equal(url_a, url_b):
        return Url(url_a) == Url(url_b)

    def __eq__(self, other):
        if not isinstance(other, Url):
            raise ValueError('Cannot compare %r against %r. Wrong type:%r' %
                             (self, other, type(other)))
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)


class WebdriverUtils(object):

    '''
    Utilities for making Webdriver more xpath-friendly.
    This class is designed to be framework independent, to be reused by other
    testing frameworks.

    #TODO:
        * finish screenshot logging
    '''
    Url = Url

    def __init__(self, base_url, webdriver, logger=None, settings=None):
        '''
        If you don't ignore __init__, arguments 
        :param base_url: like in _init_webdriver method
        :param webdriver: like in _init_webdriver method
        :param logger: You can optionally pass a smoothtest.Logger instance (or a child class's instance) 
        :param settings: like in _init_webdriver method
        '''
        settings = settings or {}
        self._init_webdriver(base_url, webdriver, settings=settings)
        self.log = logger or Logger(self.__class__.__name__)

    def _init_webdriver(self, base_url, webdriver, settings={}):
        '''
        Use this method when you want to ignore __init__ and call this method
        when when setting up a test (in setUp method on unittest class for example)
        
        :param base_url: common base url (e.g: http://example.com, http://example.com/some/common/path) 
            Used to build URL for all methods accepting the "path" argument. 
        :param webdriver: selenium's webdriver object (connected to Firefox, Chrome, etc...)  
        :param settings: smoothtest settings object.
        '''
        assert webdriver, 'You must provide a webdriver'
        self._driver = webdriver
        self.settings = settings
        # Initialize values
        self._base_url = base_url
        self._wait_timeout = self.settings.get('wait_timeout', 2)

    def set_base_url(self, base_url):
        self._base_url = base_url

    def _decorate_exc_sshot(self, meth_filter=None, inspected=None):
        fltr = lambda n, method: (getattr(method, _with_screenshot, False)
                                  or n.startswith('test'))
        meth_filter = meth_filter or fltr
        # Gather all exceptions seen (to avoid repeating screenshots)
        self._seen_exceptions = set()
        # Lock for avoiding taking screenshots
        self._sshot_lock = Lock()
        # Decorate our own methods, if None provided #TODO: remove later
        inspected = inspected or self
        for name, method in inspect.getmembers(self):
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
                setattr(self, name, method)
            elif(name != 'screenshot'
                 and meth_filter(name, method)):
                # We want to decorate this method to capture screenshots
                self.log.debug('Decorating %r for screenshot' % name)
                method = self._decorate(name, method)
                setattr(self, name, method)

    def _decorate(self, name, method, zero_screeshot=False):
        if not zero_screeshot:
            # Capture sreenshot
            @wraps(method)
            def dec(*args, **kwargs):
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

    def _quit_webdriver(self):
        self._driver.quit()
        self._driver = None

    def get_driver(self):
        assert self._driver, 'driver was not initialized'
        return self._driver

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
        dr = self.get_driver()
        exc = self._string_to_filename(repr(exc))
        count = self._exc_sshot_count
        test = self.__class__.__name__
        filename = '{count:03d}.{test}.{name}.{exc}.png'.format(**locals())
        self.log.e('Saving exception screenshot to: %r' % filename)
        exc_dir = exc_dir or self.settings.get('screenshot_exceptions_dir')
        dr.save_screenshot(os.path.join(exc_dir, filename))
        return filename

    _quick_sshot_count = 0

    def _quick_screenshot(self):
        self._quick_sshot_count += 1
        filename = '{count:03d}.quick_screenshot.png'.format(**locals())
        self.log.i('Saving exception screenshot to: %r' % filename)
        self.get_driver().save_screenshot(filename)

    def screenshot(self, *args, **kwargs):
        #self.log.w('WebdriverUtils.screenshot not yet implemented.')
        pass

    def assert_screenshot(self, name, valid=None):
        #self.log.w('WebdriverUtils.assert_screenshot not yet implemented.')
        pass

    def current_path(self):
        '''
        Get (path + params + query + fragment) as string from current url.
        '''
        return self.Url(self.current_url()).get_path_and_on()

    def current_url(self):
        return self.get_driver().current_url

    def build_url(self, path):
        assert self._base_url, 'No base_url set for building urls'
        return urlparse.urljoin(self._base_url, path)

    def get_url(self, url, condition=None):
        '''
        Open a page in the browser controlled by webdriver.
        
        :param path: path or url we want to get the page from.
        :param base: If we provide a base, the final url will be base+bath joined.
        :param condition: condition script or functor passed to the `wait_condition` method
        '''
        driver = self.get_driver()
        if url.startswith('https') and isinstance(driver, webdriver.PhantomJS):
            self.log.d('PhantomJS may fail with https if you don\'t pass '
                       'service_args=[\'--ignore-ssl-errors=true\']'
                       ' Trying to fetch {url!r}'.format(url=url))
        self.log.d('Fetching page at {url!r}'.format(url=url))
        driver.get(url)
        # Errors
        msg = 'Couldn\'t load page at {url!r}'.format(url=url)
        if condition and not self.wait_condition(condition):
            raise LookupError(msg)
        if self.current_url() == u'about:blank':
            raise LookupError(msg + '. Url is u"about:blank"')
        if not self.Url.are_equal(url, self.current_url()):
            self.log.d('For {url!r} we got {current!r}.'
                       .format(url=url, current=self.current_url()))

    def get_page(self, path, condition=None):
        '''
        Open a page in the browser controlled by webdriver.
        
        :param path: path or url we want to get the page from.
        :param base: If we provide a base, the final url will be base+bath joined.
        :param condition: condition script or functor passed to the `wait_condition` method
        '''
        self.get_url(self.build_url(path), condition)

    def get_page_once(self, path, condition=None):
        if not self.Url.are_equal(self.build_url(path), self.current_url()):
            self.get_page(path, condition)
        else:
            self.log.d('Pare already loaded once: %r' % self.build_url(path))

    _max_wait = 2
    _default_condition = 'return "complete" == document.readyState;'

    def wait_condition(self, condition=None, max_wait=None, print_msg=True):
        '''
        Active wait (polling) function, for a specific condition inside a page.
        '''
        condition = condition if condition else self._default_condition
        if isinstance(condition, basestring):
            # Its a javascript script
            def condition_func(driver):
                return driver.execute_script(condition)
            condtn = condition_func
        else:
            condtn = condition
        # first start waiting a tenth of the max time
        parts = 10
        max_wait = max_wait or self._max_wait
        top = int(parts * max_wait)
        for i in range(1, top + 1):
            loaded = condtn(self.get_driver())
            if loaded:
                self.log.d('Condition "%s" is True.' % condition)
                break
            self.log.d('Waiting condition "%s" to be True.' % condition)
            time.sleep(float(i) / parts)
        if not loaded and print_msg:
            msg = ('Page took too long to load. Increase max_wait (secs) class'
                   ' attr. Or override _wait_script method.')
            self.log.d(msg)
        return loaded

    def _get_xpath_script(self, xpath, single=True):
        common_func = '''
function extract_elem(elem){
    var elem = elem
    //elem.noteType == 1 //web element
    if(elem.nodeType == 2){
      //attribute
      elem = elem.value;
    }
    if(elem.nodeType == 3){
      //text()
      elem = elem.wholeText;
    }
    return elem;
}
        '''
        if single:
            script_single = '''
var xpath = %(xpath)r;
//XPathResult.FIRST_ORDERED_NODE_TYPE = 9
var e = document.evaluate(xpath, document, null,9, null).singleNodeValue;
return extract_elem(e);
            '''
        else:
            script_list = '''
var xpath = %(xpath)r;
//XPathResult.ORDERED_NODE_ITERATOR_TYPE = 5
var es = document.evaluate(xpath, document, null, 5, null);
var r = es.iterateNext();
var eslist = [];
while(r){
    eslist.push(extract_elem(r));
    r = es.iterateNext();
}
return eslist;
        '''
        script = script_single if single else script_list
        return common_func + script % locals()

    def select_xpath(self, xpath):
        return self._select_xpath(xpath, single=False)

    def select_xsingle(self, xpath):
        return self._select_xpath(xpath, single=True)

    def _select_xpath(self, xpath, single):
        dr = self.get_driver()
        try:
            e = dr.execute_script(self._get_xpath_script(xpath, single))
        except WebDriverException as e:
            msg = (
                'WebDriverException: Could not select xpath {xpath!r} '
                'for page {dr.current_url!r}\n Error:\n {e}'.format(
                    **locals()))
            raise LookupError(msg)
        return e

    def has_xpath(self, xpath):
        return self._has_xpath(xpath, single=False)

    def has_xsingle(self, xpath):
        return self._has_xpath(xpath, single=True)

    def _has_xpath(self, xpath, single):
        try:
            self._extract_xpath(xpath, single)
            return True
        except LookupError:
            return False

    def extract_xpath(self, xpath):
        return self._extract_xpath(xpath, single=False)

    def extract_xsingle(self, xpath):
        return self._extract_xpath(xpath, single=True)

    def _extract_xpath(self, xpath, single):
        result = self._select_xpath(xpath, single)
        if isinstance(result, WebElement):
            result = result.text
        if single:
            assert isinstance(result, basestring)
        else:
            assert not any(not isinstance(s, basestring) for s in result)
        return result

    def fill_input(self, xpath, value):
        e = self.select_xsingle(xpath)
        e.clear()
        e.send_keys(value)

    def click(self, xpath):
        e = self.select_xsingle(xpath)
        e.click()

    def fill(self, xpath, value):
        self.fill_input(xpath, value)
        self.screenshot('fill', xpath, value)

    def wait(self, timeout=None):
        time.sleep(timeout or self._wait_timeout)

    def wipe_alerts(self, timeout=0.5):
        '''
        Accept all existing alerts
        :param timeout: wait for alert in second (default=0.5)
        '''
        try:
            WebDriverWait(self.get_driver(), timeout
                          ).until(expected_conditions.alert_is_present(),
                                  'Timed out waiting alert.')
            alert = self.get_driver().switch_to_alert()
            alert.accept()
        except TimeoutException:
            pass


def smoke_test_module():
    from smoothtest.webunittest.WebdriverManager import WebdriverManager
    mngr = WebdriverManager()
#    mngr.setup_display()
#    webdriver = mngr.new_webdriver()
    u = u'https://www.google.cl/?gfe_rd=cr&ei=ix0kVfH8M9PgwASPoIFo&gws_rd=ssl'
    print WebdriverUtils.Url(u).get_path_and_on()
#    browser = WebdriverUtils('', webdriver)
#    browser.get_page('http://www.google.com')
#    browser.log.i(browser.current_path())


if __name__ == "__main__":
    smoke_test_module()

